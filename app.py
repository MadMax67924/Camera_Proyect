#!/usr/bin/env python3
"""
Servidor de Streaming - 30 FPS + Detección y Reconocimiento Facial
Raspberry Pi 3 / Fedora con cámara USB
Mejorado con reconocimiento facial y selección de cámara
VERSIÓN SIN DLIB - Más rápida en instalación
"""

from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time
import os
import signal
import sys
import numpy as np
import urllib.request
import socket

# Importar módulo de reconocimiento facial (versión sin dlib)
try:
    from core.face_recognition_lite import FaceRecognizerLite
    RECOGNITION_AVAILABLE = True
    RECOGNIZER_TYPE = "lite"
    print("[OK] Usando FaceRecognizerLite (sin dlib)")
except ImportError:
    try:
        from core.face_recognition import FaceRecognizer as FaceRecognizerLite
        RECOGNITION_AVAILABLE = True
        RECOGNIZER_TYPE = "original"
        print("[WARNING] Usando FaceRecognizer original (con dlib)")
    except ImportError:
        RECOGNITION_AVAILABLE = False
        FaceRecognizerLite = None
        print("[WARNING] Módulo de reconocimiento no disponible")

app = Flask(__name__)

# Variables globales
camera = None
camera_lock = threading.Lock()
output_frame = None
frame_lock = threading.Lock()
frame_count = 0
is_capturing = False
fps_actual = 0
face_detected = False
camera_device_id = 0  # ID de la cámara a usar
detection_enabled = False  # Toggle para detección facial (por defecto desactivado para max FPS)
recognition_enabled = False  # Toggle para reconocimiento facial
face_recognizer = None  # Instancia del reconocedor
last_recognized_faces = []  # Últimos rostros reconocidos

def get_ip_address():
    """Obtiene la dirección IP local"""
    try:
        # Crear un socket para obtener la IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def find_available_cameras():
    """Busca cámaras disponibles en el sistema"""
    available_cameras = []

    # Probar los primeros 10 dispositivos de video
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()

    return available_cameras

def detect_platform():
    """Detecta la plataforma (Raspberry Pi o PC)"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                return 'raspberry'
    except:
        pass

    return 'pc'

def download_haarcascade():
    """Descarga el archivo haarcascade si no existe"""
    local_path = 'haarcascade_frontalface_default.xml'

    if os.path.exists(local_path):
        print(f"[OK] Clasificador encontrado: {local_path}")
        return local_path

    url = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'

    try:
        print(f"[INFO] Descargando clasificador desde GitHub...")
        urllib.request.urlretrieve(url, local_path)
        print(f"[OK] Clasificador descargado: {local_path}")
        return local_path
    except Exception as e:
        print(f"[ERROR] No se pudo descargar el clasificador: {e}")
        return None

# Cargar clasificador de rostros (Haar Cascade - rápido)
# Intentar cargar desde cv2.data, si no existe, usar ruta local
cascade_path = None
try:
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    if not os.path.exists(cascade_path):
        raise FileNotFoundError
    print(f"[OK] Usando clasificador de OpenCV: {cascade_path}")
except (AttributeError, FileNotFoundError):
    # Buscar en rutas comunes de OpenCV
    common_paths = [
        '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
        '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml',
        'haarcascade_frontalface_default.xml'
    ]

    for path in common_paths:
        if os.path.exists(path):
            cascade_path = path
            print(f"[OK] Clasificador encontrado: {path}")
            break

    # Si no se encuentra, descargar automáticamente
    if cascade_path is None or not os.path.exists(cascade_path):
        cascade_path = download_haarcascade()

face_cascade = cv2.CascadeClassifier(cascade_path) if cascade_path else None

class CameraStream:
    """Clase para manejar la cámara USB optimizada"""

    def __init__(self, device_id=0):
        print(f"[INFO] Configurando cámara /dev/video{device_id}...")

        # Priorizar V4L2 en Linux para mejor rendimiento
        backends = [
            (cv2.CAP_V4L2, "V4L2"),
            (cv2.CAP_ANY, "ANY"),
            (None, "Default")
        ]

        self.camera = None
        self.backend_name = None
        for backend, name in backends:
            print(f"[INFO] Probando backend: {name}")
            if backend is None:
                self.camera = cv2.VideoCapture(device_id)
            else:
                self.camera = cv2.VideoCapture(device_id, backend)

            if self.camera.isOpened():
                print(f"[OK] Cámara abierta con backend: {name}")
                self.backend_name = name
                break
            else:
                print(f"[FAIL] Backend {name} no funcionó")
                if self.camera:
                    self.camera.release()
                self.camera = None

        if not self.camera or not self.camera.isOpened():
            raise Exception(f"No se pudo abrir /dev/video{device_id} con ningún backend")

        # CONFIGURACIÓN CRÍTICA PARA 30 FPS Y BAJA LATENCIA

        # 1. Buffer MÍNIMO primero (antes de todo)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # 2. Primero establecer formato MJPEG
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

        # 3. Resolución - la cámara elegirá la mejor disponible
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        # 4. FPS alto
        self.camera.set(cv2.CAP_PROP_FPS, 30)

        # 5. Desactivar autoexposición para FPS estables (si es posible)
        try:
            self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Manual mode
        except:
            pass

        # 6. Desactivar autofocus si es posible
        try:
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        except:
            pass

        # Descartar frames iniciales del buffer
        print("[INFO] Limpiando buffer inicial...")
        for _ in range(5):
            self.camera.read()

        # Verificar configuración real
        w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.camera.get(cv2.CAP_PROP_FPS))
        buffer_size = int(self.camera.get(cv2.CAP_PROP_BUFFERSIZE))

        print(f"[OK] Cámara configurada: {w}x{h} @ {fps} FPS (buffer: {buffer_size})")

    def read(self):
        """Lee frame y descarta buffer viejo para baja latencia"""
        # Leer y descartar frames viejos del buffer (reduce latencia)
        ret, frame = self.camera.read()

        # Opcional: leer múltiples veces para obtener el frame más reciente
        # Esto ayuda si el buffer de la cámara acumula frames viejos
        # for _ in range(1):
        #     ret_new, frame_new = self.camera.read()
        #     if ret_new:
        #         ret, frame = ret_new, frame_new

        return ret, frame

    def release(self):
        if self.camera is not None:
            self.camera.release()
            print("[INFO] Cámara liberada")

def detect_faces(frame):
    """
    Detecta rostros en el frame - OPTIMIZADO
    """
    # Convertir a escala de grises (más rápido)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detección con parámetros optimizados para velocidad
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,      # Menos escalas = más rápido
        minNeighbors=3,       # Menos vecinos = más rápido (pero menos preciso)
        minSize=(30, 30),     # Tamaño mínimo de rostro
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    return faces

def capture_frames():
    """
    Captura frames a máxima velocidad
    - 60+ FPS sin detección
    - 25-30 FPS con detección Haar
    - 15-20 FPS con reconocimiento facial (más pesado)
    """
    global camera, output_frame, frame_count, is_capturing, fps_actual, face_detected
    global camera_device_id, detection_enabled, recognition_enabled, face_recognizer, last_recognized_faces

    mode_parts = []
    if detection_enabled:
        mode_parts.append("DETECCIÓN")
    if recognition_enabled:
        mode_parts.append("RECONOCIMIENTO")
    if not mode_parts:
        mode_parts.append("MODO RÁPIDO (60+ FPS)")

    mode = " + ".join(mode_parts)
    print(f"[INFO] Iniciando captura - {mode}")

    try:
        with camera_lock:
            camera = CameraStream(device_id=camera_device_id)

        is_capturing = True

        # Variables para medir FPS
        fps_counter = 0
        fps_start_time = time.time()

        # Contador para detección/reconocimiento (no procesar cada frame)
        detection_counter = 0

        # Variables para diagnóstico de delay
        last_process_time = 0

        while is_capturing:
            loop_start = time.time()

            # Leer frame - OPTIMIZADO
            ret, frame = camera.read()
            if not ret or frame is None:
                continue

            # Reducir latencia si la cámara es lenta
            if fps_actual < 20 and last_process_time < 0.030:
                ret_new, frame_new = camera.read()
                if ret_new and frame_new is not None:
                    frame = frame_new

            # DETECCIÓN Y/O RECONOCIMIENTO FACIAL
            faces = []
            recognized_faces = []

            # Si el reconocimiento está activo, úsalo (incluye detección)
            if recognition_enabled and face_recognizer:
                # Reconocer cada 5 frames (más pesado que detección simple)
                if detection_counter % 5 == 0:
                    try:
                        recognized_faces = face_recognizer.recognize_faces(frame, scale_factor=0.25)
                        last_recognized_faces = recognized_faces
                        face_detected = len(recognized_faces) > 0
                    except Exception as e:
                        print(f"[ERROR] Reconocimiento falló: {e}")
                        recognized_faces = []

                # Usar caché si no tocaba procesar
                else:
                    recognized_faces = last_recognized_faces

                # Dibujar rostros reconocidos
                if recognized_faces:
                    frame = face_recognizer.draw_faces(frame, recognized_faces, show_confidence=True)

            # Si solo detección está activa (sin reconocimiento)
            elif detection_enabled:
                # Detectar cada 3 frames
                if detection_counter % 3 == 0:
                    faces = detect_faces(frame)
                    face_detected = len(faces) > 0

                detection_counter += 1

                # Dibujar rectángulos en rostros detectados
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, "ROSTRO", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            detection_counter += 1

            # Información en pantalla (mínima para no afectar FPS)
            cv2.putText(frame, f"FPS: {fps_actual:.0f}", (5, 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Indicador de modo
            y_offset = 40
            if detection_enabled:
                cv2.putText(frame, "DETECCION: ON", (5, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                y_offset += 20
            if recognition_enabled:
                color = (0, 255, 0) if face_recognizer else (0, 0, 255)
                text = "RECONOCIMIENTO: ON" if face_recognizer else "RECONOCIMIENTO: NO MODEL"
                cv2.putText(frame, text, (5, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Codificar a JPEG con calidad ajustable
            if recognition_enabled or detection_enabled:
                encode_quality = 60  # Mayor calidad para ver detalles
            else:
                encode_quality = 30  # Máxima velocidad

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), encode_quality]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)

            if ret:
                with frame_lock:
                    output_frame = buffer.tobytes()
                    frame_count += 1
                    fps_counter += 1

            # Calcular tiempo de procesamiento del loop
            last_process_time = time.time() - loop_start

            # Calcular FPS real cada segundo
            current_time = time.time()
            elapsed = current_time - fps_start_time
            if elapsed >= 1.0:
                fps_actual = fps_counter / elapsed
                avg_process_ms = (last_process_time * 1000)

                status_parts = [f"{fps_actual:.1f} fps"]
                if detection_enabled or recognition_enabled:
                    status_parts.append(f"Rostros: {len(recognized_faces) if recognized_faces else len(faces)}")
                status_parts.append(f"Proc: {avg_process_ms:.1f}ms")

                print(f"[FPS] {' | '.join(status_parts)}")
                fps_counter = 0
                fps_start_time = current_time

            # NO SLEEP - máxima velocidad

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        is_capturing = False

    finally:
        if camera:
            camera.release()

def generate_stream():
    """Generador de stream optimizado"""
    global output_frame

    while True:
        with frame_lock:
            if output_frame is None:
                time.sleep(0.01)
                continue
            frame = output_frame

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Cache-Control: no-cache\r\n'
               b'\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    response = Response(generate_stream(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route('/status')
def status():
    recognized_names = []
    if last_recognized_faces:
        recognized_names = [f['name'] for f in last_recognized_faces if f['name'] != 'Desconocido']

    return jsonify({
        'camera_active': camera is not None,
        'is_capturing': is_capturing,
        'fps': round(fps_actual, 1),
        'face_detected': face_detected,
        'total_frames': frame_count,
        'detection_enabled': detection_enabled,
        'recognition_enabled': recognition_enabled,
        'recognition_available': RECOGNITION_AVAILABLE,
        'model_loaded': face_recognizer is not None,
        'recognized_names': recognized_names,
        'camera_id': camera_device_id
    })

@app.route('/toggle_detection', methods=['POST'])
def toggle_detection():
    global detection_enabled
    detection_enabled = not detection_enabled
    mode = "ACTIVADA" if detection_enabled else "DESACTIVADA"
    print(f"[INFO] Detección facial {mode}")
    return jsonify({
        'detection_enabled': detection_enabled,
        'message': f'Detección facial {mode}'
    })

@app.route('/set_detection/<int:value>', methods=['POST'])
def set_detection(value):
    global detection_enabled
    detection_enabled = bool(value)
    mode = "ACTIVADA" if detection_enabled else "DESACTIVADA"
    print(f"[INFO] Detección facial {mode}")
    return jsonify({
        'detection_enabled': detection_enabled,
        'message': f'Detección facial {mode}'
    })

@app.route('/toggle_recognition', methods=['POST'])
def toggle_recognition():
    global recognition_enabled
    if not RECOGNITION_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Módulo de reconocimiento no disponible'
        }), 400

    if not face_recognizer:
        return jsonify({
            'success': False,
            'message': 'No hay modelo entrenado. Ejecuta train_model.py primero'
        }), 400

    recognition_enabled = not recognition_enabled
    mode = "ACTIVADO" if recognition_enabled else "DESACTIVADO"
    print(f"[INFO] Reconocimiento facial {mode}")
    return jsonify({
        'recognition_enabled': recognition_enabled,
        'message': f'Reconocimiento facial {mode}'
    })

@app.route('/cameras')
def get_cameras():
    """Retorna lista de cámaras disponibles"""
    cameras = find_available_cameras()
    return jsonify({
        'cameras': cameras,
        'current': camera_device_id
    })

@app.route('/set_camera/<int:camera_id>', methods=['POST'])
def set_camera(camera_id):
    """Cambia la cámara activa"""
    global camera_device_id, is_capturing, camera

    # Verificar que la cámara existe
    available = find_available_cameras()
    if camera_id not in available:
        return jsonify({
            'success': False,
            'message': f'Cámara {camera_id} no disponible'
        }), 400

    # Detener captura actual
    old_camera_id = camera_device_id
    is_capturing = False
    time.sleep(0.5)  # Esperar a que termine el thread

    # Liberar cámara anterior
    if camera:
        try:
            camera.release()
        except:
            pass

    # Cambiar a nueva cámara
    camera_device_id = camera_id

    # Reiniciar captura
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()

    time.sleep(1)  # Esperar a que inicie

    print(f"[INFO] Cámara cambiada de {old_camera_id} a {camera_id}")

    return jsonify({
        'success': True,
        'message': f'Cámara cambiada a /dev/video{camera_id}',
        'camera_id': camera_id
    })

@app.route('/stats')
def stats():
    html = f'''
    <html>
    <head>
        <title>Stats</title>
        <meta http-equiv="refresh" content="1">
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            td {{ padding: 10px; border: 1px solid #ddd; }}
            .good {{ color: green; font-weight: bold; }}
            .bad {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>📊 Estadísticas en Tiempo Real</h1>
        <table>
            <tr><td>FPS Actual</td><td class="{'good' if fps_actual >= 25 else 'bad'}">{fps_actual:.1f}</td></tr>
            <tr><td>Rostro Detectado</td><td class="{'good' if face_detected else ''}">{face_detected}</td></tr>
            <tr><td>Frames Totales</td><td>{frame_count}</td></tr>
            <tr><td>Cámara Activa</td><td>{camera is not None}</td></tr>
        </table>
        <br><a href="/">← Volver</a>
    </body>
    </html>
    '''
    return html

def signal_handler(sig, frame):
    global is_capturing
    print("\n[INFO] Cerrando...")
    is_capturing = False
    if camera:
        camera.release()
    sys.exit(0)

def main():
    global is_capturing, camera_device_id, face_recognizer

    signal.signal(signal.SIGINT, signal_handler)

    # Detectar plataforma
    platform = detect_platform()
    platform_name = "Raspberry Pi 3" if platform == 'raspberry' else "PC/Laptop (Fedora)"

    print("\n" + "="*70)
    print("  SISTEMA DE RECONOCIMIENTO FACIAL - MEJORADO")
    print(f"  Plataforma: {platform_name}")
    print("="*70)

    # Buscar cámaras disponibles
    print("\n[INFO] Buscando cámaras disponibles...")
    available_cameras = find_available_cameras()

    if not available_cameras:
        print("\n[ERROR] No se encontraron cámaras")
        print("\nEn Fedora, verifica:")
        print("  1. La cámara está conectada")
        print("  2. Tienes permisos: sudo usermod -aG video $USER")
        print("  3. Lista dispositivos: ls -l /dev/video*")
        print("\nEn Raspberry Pi, verifica:")
        print("  1. La cámara USB está conectada")
        print("  2. Ejecuta: ls -l /dev/video*")
        return

    print(f"[OK] Cámaras encontradas: {available_cameras}")

    # Seleccionar cámara
    camera_device_id = available_cameras[0]
    if len(available_cameras) > 1:
        print(f"\n[INFO] Múltiples cámaras disponibles: {available_cameras}")
        try:
            user_choice = input(f"Selecciona cámara (Enter = {available_cameras[0]}): ").strip()
            if user_choice:
                camera_device_id = int(user_choice)
                if camera_device_id not in available_cameras:
                    print(f"[WARNING] Cámara {camera_device_id} no válida, usando {available_cameras[0]}")
                    camera_device_id = available_cameras[0]
        except (ValueError, KeyboardInterrupt):
            pass

    print(f"[INFO] Usando cámara /dev/video{camera_device_id}")

    # Verificar que el clasificador fue cargado correctamente
    if face_cascade is None or face_cascade.empty():
        print("\n[ERROR] No se pudo cargar el clasificador de rostros")
        print("El sistema intentó descargarlo automáticamente pero falló")
        return

    print("[OK] Clasificador Haar Cascade cargado correctamente")

    # Intentar cargar modelo de reconocimiento facial
    if RECOGNITION_AVAILABLE:
        print("\n[INFO] Intentando cargar modelo de reconocimiento facial...")
        try:
            face_recognizer = FaceRecognizerLite(model_path="models/faces_model.pkl")
            if face_recognizer.known_face_encodings:
                print(f"[OK] Modelo de reconocimiento cargado")
                print(f"[INFO] Personas registradas: {', '.join(face_recognizer.get_registered_names())}")
            else:
                print("[INFO] No hay modelo entrenado")
                print("[INFO] Para entrenar: python3 scripts/train_model.py")
                face_recognizer = None
        except Exception as e:
            print(f"[WARNING] No se pudo cargar reconocimiento: {e}")
            face_recognizer = None
    else:
        print("\n[WARNING] Módulo de reconocimiento no disponible")
        print("[INFO] Instala con: pip3 install mediapipe scipy")

    # Iniciar captura
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()

    time.sleep(2)

    if not is_capturing:
        print("\n[ERROR] No se pudo iniciar la captura")
        return

    # Obtener IP dinámica
    ip_address = get_ip_address()

    print("\n" + "="*70)
    print("  ✅ SISTEMA ACTIVO")
    print("="*70)
    print(f"\n  📹 URL Principal: http://{ip_address}:5000")
    print(f"  📊 Estadísticas: http://{ip_address}:5000/stats")
    print(f"\n  🎯 FPS Objetivo: 25-30 FPS")
    print(f"  👤 Detección: Haar Cascade (Toggle en interfaz)")
    if face_recognizer:
        print(f"  🧠 Reconocimiento: Disponible ({face_recognizer.get_person_count()} personas)")
    else:
        print(f"  🧠 Reconocimiento: No disponible")
    print(f"  📐 Resolución: 320x240")
    print(f"  🌐 IP Local: {ip_address}")
    print(f"  📷 Cámaras: {available_cameras} (usando {camera_device_id})")
    print("\n  Presiona CTRL+C para salir")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)

if __name__ == '__main__':
    main()
