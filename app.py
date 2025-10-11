#!/usr/bin/env python3
"""
Servidor de Streaming - 30 FPS + Detección Facial
Raspberry Pi 3 con cámara USB
"""

from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
import signal
import sys
import numpy as np

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

# Cargar clasificador de rostros (Haar Cascade - rápido)
# Intentar cargar desde cv2.data, si no existe, usar ruta local
try:
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
except AttributeError:
    # Buscar en rutas comunes de OpenCV
    cascade_path = '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
    if not os.path.exists(cascade_path):
        cascade_path = 'haarcascade_frontalface_default.xml'

face_cascade = cv2.CascadeClassifier(cascade_path)

class CameraStream:
    """Clase para manejar la cámara USB optimizada"""

    def __init__(self, device_id=0):
        print(f"[INFO] Configurando cámara /dev/video{device_id}...")

        # Intentar abrir cámara con diferentes backends
        backends = [
            (cv2.CAP_V4L2, "V4L2"),
            (cv2.CAP_ANY, "ANY"),
            (None, "Default")
        ]

        self.camera = None
        for backend, name in backends:
            print(f"[INFO] Probando backend: {name}")
            if backend is None:
                self.camera = cv2.VideoCapture(device_id)
            else:
                self.camera = cv2.VideoCapture(device_id, backend)

            if self.camera.isOpened():
                print(f"[OK] Cámara abierta con backend: {name}")
                break
            else:
                print(f"[FAIL] Backend {name} no funcionó")
                if self.camera:
                    self.camera.release()
                self.camera = None

        if not self.camera or not self.camera.isOpened():
            raise Exception(f"No se pudo abrir /dev/video{device_id} con ningún backend")

        # CONFIGURACIÓN CRÍTICA PARA 30 FPS
        # 1. Resolución BAJA (crítico para Raspberry Pi 3)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # Bajado a 320
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Bajado a 240

        # 2. FPS alto
        self.camera.set(cv2.CAP_PROP_FPS, 30)

        # 3. Formato MJPEG (más eficiente)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

        # 4. Buffer MÍNIMO (crítico para baja latencia)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Descartar frames iniciales
        for _ in range(3):
            self.camera.read()

        # Verificar configuración real
        w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.camera.get(cv2.CAP_PROP_FPS))

        print(f"[OK] Cámara configurada: {w}x{h} @ {fps} FPS")

    def read(self):
        return self.camera.read()

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
    Captura frames a máxima velocidad con detección facial
    """
    global camera, output_frame, frame_count, is_capturing, fps_actual, face_detected

    print("[INFO] Iniciando captura optimizada para 30 FPS...")

    try:
        with camera_lock:
            camera = CameraStream(device_id=0)

        is_capturing = True

        # Variables para medir FPS
        fps_counter = 0
        fps_start_time = time.time()

        # Contador para detección (no detectar en cada frame)
        detection_counter = 0

        while is_capturing:
            loop_start = time.time()

            # Leer frame
            ret, frame = camera.read()

            if not ret or frame is None:
                continue

            # DETECCIÓN FACIAL CADA 3 FRAMES (para mantener FPS alto)
            faces = []
            if detection_counter % 3 == 0:
                faces = detect_faces(frame)
                face_detected = len(faces) > 0
            detection_counter += 1

            # Dibujar rectángulos en rostros detectados
            for (x, y, w, h) in faces:
                # Rectángulo verde alrededor del rostro
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                # Texto "ROSTRO DETECTADO"
                cv2.putText(frame, "ROSTRO", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Timestamp simple (solo hora)
            timestamp = time.strftime("%H:%M:%S")
            cv2.putText(frame, timestamp, (5, 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Mostrar FPS en el frame
            cv2.putText(frame, f"FPS: {fps_actual:.1f}", (5, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            # Indicador de detección
            if face_detected:
                cv2.putText(frame, "CARA DETECTADA", (5, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Codificar a JPEG con CALIDAD BAJA (velocidad > calidad)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)

            if ret:
                with frame_lock:
                    output_frame = buffer.tobytes()
                    frame_count += 1
                    fps_counter += 1

            # Calcular FPS real cada segundo
            current_time = time.time()
            elapsed = current_time - fps_start_time
            if elapsed >= 1.0:
                fps_actual = fps_counter / elapsed
                print(f"[FPS] {fps_actual:.1f} fps | Rostros: {len(faces)}")
                fps_counter = 0
                fps_start_time = current_time

            # NO SLEEP - máxima velocidad
            # La cámara controlará el framerate

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
    return jsonify({
        'camera_active': camera is not None,
        'is_capturing': is_capturing,
        'fps': round(fps_actual, 1),
        'face_detected': face_detected,
        'total_frames': frame_count
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
    global is_capturing

    signal.signal(signal.SIGINT, signal_handler)

    print("\n" + "="*70)
    print("  SISTEMA DE DETECCIÓN FACIAL - 30 FPS")
    print("  Raspberry Pi 3")
    print("="*70)

    if not os.path.exists('/dev/video0'):
        print("\n[ERROR] /dev/video0 no encontrado")
        return

    # Verificar que el clasificador existe
    cascade_paths = [
        '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
        '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml',
        'haarcascade_frontalface_default.xml'
    ]

    cascade_found = False
    for path in cascade_paths:
        if os.path.exists(path):
            cascade_found = True
            print(f"[OK] Clasificador encontrado en: {path}")
            break

    if not cascade_found:
        print("\n[ERROR] No se encontró el clasificador de rostros")
        print("Descárgalo con:")
        print("wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml")
        return

    print("\n[OK] Clasificador de rostros cargado")
    print("[OK] /dev/video0 detectado")

    # Iniciar captura
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()

    time.sleep(2)

    if not is_capturing:
        print("\n[ERROR] No se pudo iniciar")
        return

    print("\n" + "="*70)
    print("  ✅ SISTEMA ACTIVO")
    print("="*70)
    print(f"\n  📹 URL: http://192.168.43.159:5000")
    print(f"  📊 Stats: http://192.168.43.159:5000/stats")
    print(f"\n  🎯 Objetivo: 30 FPS")
    print(f"  👤 Detección facial: ACTIVA")
    print(f"  📐 Resolución: 320x240 (optimizado para RPi3)")
    print("\n  Presiona CTRL+C para salir")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)

if __name__ == '__main__':
    main()
