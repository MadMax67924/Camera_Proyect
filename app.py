#!/usr/bin/env python3
"""
Servidor de Streaming de Cámara Web
Raspberry Pi 3 con cámara USB SPCA2650
Autor: Sistema de reconocimiento facial
"""

from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
import signal
import sys

# Configuración
app = Flask(__name__)

# Variables globales
camera = None
camera_lock = threading.Lock()
output_frame = None
frame_lock = threading.Lock()
frame_count = 0
is_capturing = False

class CameraStream:
    """Clase para manejar la cámara USB"""
    
    def __init__(self, device_id=0):
        """
        Inicializa la cámara
        Args:
            device_id: ID del dispositivo de video (default: 0 para /dev/video0)
        """
        print(f"[INFO] Abriendo /dev/video{device_id}...")
        
        # Abrir cámara con backend V4L2 (recomendado para Linux)
        self.camera = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
        
        if not self.camera.isOpened():
            raise Exception(f"No se pudo abrir /dev/video{device_id}")
        
        # Configurar propiedades de la cámara
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 20)
        
        # Configurar formato MJPEG (mejor para cámaras USB)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        
        # Descartar primeros frames (suelen estar corruptos)
        for _ in range(5):
            self.camera.read()
        
        print("[INFO] Cámara inicializada correctamente")
    
    def read(self):
        """Lee un frame de la cámara"""
        return self.camera.read()
    
    def release(self):
        """Libera la cámara"""
        if self.camera is not None:
            self.camera.release()
            print("[INFO] Cámara liberada")

def capture_frames():
    """
    Función que corre en un hilo separado
    Captura frames continuamente de la cámara
    """
    global camera, output_frame, frame_count, is_capturing
    
    print("[INFO] Iniciando captura de frames...")
    
    try:
        # Inicializar cámara
        with camera_lock:
            camera = CameraStream(device_id=0)
        
        is_capturing = True
        
        while is_capturing:
            # Leer frame
            ret, frame = camera.read()
            
            if not ret or frame is None:
                print("[WARNING] No se pudo leer frame")
                time.sleep(0.1)
                continue
            
            # Añadir información al frame
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, f"Frame: {frame_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Codificar frame a JPEG
            ret, buffer = cv2.imencode('.jpg', frame, 
                                      [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            if ret:
                # Guardar frame en variable global
                with frame_lock:
                    output_frame = buffer.tobytes()
                    frame_count += 1
            
            # Control de FPS (~20 FPS)
            time.sleep(0.05)
    
    except Exception as e:
        print(f"[ERROR] Error en captura: {e}")
        is_capturing = False
    
    finally:
        # Liberar cámara al terminar
        if camera:
            camera.release()

def generate_stream():
    """
    Generador que envía frames para el streaming
    """
    global output_frame
    
    while True:
        # Esperar hasta que haya un frame disponible
        with frame_lock:
            if output_frame is None:
                continue
            frame = output_frame
        
        # Enviar frame en formato MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# ============== RUTAS DE LA APLICACIÓN ==============

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """
    Ruta para el streaming de video
    Retorna un stream MJPEG
    """
    return Response(generate_stream(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    """
    API endpoint para verificar el estado del servidor
    Retorna JSON con información del sistema
    """
    return jsonify({
        'camera_active': camera is not None,
        'is_capturing': is_capturing,
        'total_frames': frame_count,
        'has_current_frame': output_frame is not None
    })

@app.route('/stats')
def stats():
    """Página con estadísticas del sistema"""
    info = {
        'Cámara Activa': 'Sí' if camera else 'No',
        'Capturando': 'Sí' if is_capturing else 'No',
        'Frames Totales': frame_count,
        'Frame Actual Disponible': 'Sí' if output_frame else 'No',
        'Dispositivo': '/dev/video0'
    }
    
    html = '<html><head><title>Estadísticas</title></head><body>'
    html += '<h1>Estadísticas del Sistema</h1>'
    html += '<table border="1" cellpadding="10">'
    for key, value in info.items():
        html += f'<tr><td><b>{key}</b></td><td>{value}</td></tr>'
    html += '</table>'
    html += '<br><a href="/">Volver al stream</a>'
    html += '</body></html>'
    
    return html

def signal_handler(sig, frame):
    """Manejador de señales para cerrar limpiamente"""
    global is_capturing
    print("\n[INFO] Deteniendo servidor...")
    is_capturing = False
    if camera:
        camera.release()
    sys.exit(0)

# ============== FUNCIÓN PRINCIPAL ==============

def main():
    """Función principal"""
    global is_capturing
    
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n" + "="*60)
    print("  SERVIDOR DE STREAMING DE CÁMARA")
    print("  Raspberry Pi 3 - Flask + OpenCV")
    print("="*60)
    
    # Verificar que el dispositivo existe
    if not os.path.exists('/dev/video0'):
        print("\n[ERROR] /dev/video0 no encontrado")
        print("Verifica que la cámara USB esté conectada")
        return
    
    print("\n[OK] /dev/video0 detectado")
    
    # Iniciar hilo de captura
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()
    
    # Esperar a que la cámara se inicialice
    print("\n[INFO] Esperando inicialización...")
    time.sleep(3)
    
    if not is_capturing:
        print("\n[ERROR] No se pudo iniciar la captura")
        return
    
    print("\n" + "="*60)
    print("  ✓ SERVIDOR INICIADO CORRECTAMENTE")
    print("="*60)
    print("\n  Accede desde tu navegador:")
    print(f"    • Local:     http://localhost:5000")
    print(f"    • Red:       http://192.168.43.159:5000")
    print(f"    • Status:    http://192.168.43.159:5000/status")
    print(f"    • Stats:     http://192.168.43.159:5000/stats")
    print("\n  Presiona CTRL+C para detener")
    print("="*60 + "\n")
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)

if __name__ == '__main__':
    main()