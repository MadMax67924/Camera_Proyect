#!/usr/bin/env python3
"""
Servidor de Streaming - 30 FPS + Detección y Reconocimiento Facial
Raspberry Pi 3 / Fedora con cámara USB
Mejorado con reconocimiento facial y selección de cámara
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
import traceback

# Importar módulos de detección y reconocimiento
try:
    from core.face_detection import FaceDetectorMTCNN
    from core.face_recognition import FaceRecognizer
    import face_recognition
    DETECTION_AVAILABLE = True
    RECOGNITION_AVAILABLE = True
    print("[INFO] Módulos de detección y reconocimiento cargados correctamente")
except ImportError as e:
    DETECTION_AVAILABLE = False
    RECOGNITION_AVAILABLE = False
    print(f"[WARNING] Error al cargar módulos: {e}")

app = Flask(__name__)

# Inicializar detectores
detector = None
if DETECTION_AVAILABLE:
    detector = FaceDetectorMTCNN(min_confidence=0.85)

# Inicializar reconocedor
face_recognizer = None
if RECOGNITION_AVAILABLE:
    try:
        face_recognizer = FaceRecognizer()
        print("[INFO] Reconocedor facial inicializado correctamente")
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar el reconocedor: {e}")
        RECOGNITION_AVAILABLE = False

# Resto del código de inicialización...
camera = None
camera_lock = threading.Lock()
output_frame = None
frame_lock = threading.Lock()
frame_count = 0
is_capturing = False
fps_actual = 0
face_detected = False
camera_device_id = 0
detection_enabled = False
recognition_enabled = False
last_recognized_faces = []

# ... (resto de las funciones de utilidad como get_ip_address, find_available_cameras, etc.)

def detect_faces(frame):
    """
    Detecta rostros en el frame usando MTCNN
    """
    if not DETECTION_AVAILABLE or detector is None:
        return []
        
    try:
        detections = detector.detect_faces(frame)
        # Convertir al formato (x, y, w, h) esperado por el resto del código
        faces = [det['box'] for det in detections]
        return faces
    except Exception as e:
        print(f"Error en detección de rostros: {e}")
        return []

def capture_frames():
    global camera, output_frame, frame_count, is_capturing, fps_actual
    global face_detected, detection_enabled, recognition_enabled
    
    fps_counter = 0
    fps_last_time = time.time()
    detection_counter = 0
    
    while is_capturing:
        try:
            with camera_lock:
                if camera is None:
                    time.sleep(0.1)
                    continue
                    
                # Leer frame
                ret, frame = camera.read()
                if not ret:
                    print("Error al leer frame de la cámara")
                    time.sleep(0.1)
                    continue
                
                # Incrementar contador de FPS
                fps_counter += 1
                if time.time() - fps_last_time >= 1.0:
                    fps_actual = fps_counter
                    fps_counter = 0
                    fps_last_time = time.time()
                
                # Procesamiento del frame
                if recognition_enabled and RECOGNITION_AVAILABLE and face_recognizer is not None:
                    try:
                        # 1. Detección con MTCNN
                        detections = detector.detect_faces(frame)
                        face_detected = len(detections) > 0
                        
                        if face_detected:
                            # 2. Convertir a RGB para face_recognition
                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            # 3. Obtener ubicaciones en formato face_recognition
                            face_locations = [(y, x+w, y+h, x) for (x, y, w, h) in [d['box'] for d in detections]]
                            
                            # 4. Obtener encodings de las caras detectadas
                            face_encodings = face_recognition.face_encodings(
                                rgb_frame, 
                                known_face_locations=face_locations
                            )
                            
                            # 5. Para cada cara detectada
                            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                                # 6. Verificar si coincide con alguna cara conocida
                                matches = face_recognition.compare_faces(
                                    face_recognizer.known_face_encodings, 
                                    face_encoding,
                                    tolerance=face_recognizer.tolerance
                                )
                                
                                name = "Desconocido"
                                confidence = "?"
                                
                                # Calcular distancias para obtener la mejor coincidencia
                                face_distances = face_recognition.face_distance(
                                    face_recognizer.known_face_encodings, 
                                    face_encoding
                                )
                                
                                if len(face_distances) > 0:
                                    best_match_index = np.argmin(face_distances)
                                    if matches[best_match_index]:
                                        name = face_recognizer.known_face_names[best_match_index]
                                        confidence = f"{(1 - face_distances[best_match_index]) * 100:.1f}%"
                                
                                # Dibujar rectángulo y etiqueta
                                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                                cv2.putText(frame, f"{name} {confidence}", (left + 6, bottom - 6), 
                                          cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                                
                                # Actualizar últimos rostros reconocidos
                                if name != "Desconocido" and name not in last_recognized_faces:
                                    last_recognized_faces.append(name)
                                    if len(last_recognized_faces) > 5:
                                        last_recognized_faces.pop(0)
                    
                    except Exception as e:
                        print(f"Error en reconocimiento facial: {e}")
                        traceback.print_exc()
                
                # Si solo detección está activa
                elif detection_enabled and DETECTION_AVAILABLE:
                    try:
                        # Usar MTCNN para detección
                        detections = detector.detect_faces(frame)
                        face_detected = len(detections) > 0
                        
                        # Dibujar detecciones
                        for det in detections:
                            x, y, w, h = det['box']
                            confidence = det['confidence']
                            
                            # Dibujar rectángulo
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            
                            # Mostrar confianza
                            label = f"{confidence*100:.1f}%"
                            cv2.putText(frame, label, (x, y-10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    except Exception as e:
                        print(f"Error en detección: {e}")
                        face_detected = False
                
                # Mostrar FPS
                cv2.putText(frame, f"FPS: {fps_actual}", (5, 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Guardar frame para el stream
                with frame_lock:
                    output_frame = frame.copy()
                    
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            time.sleep(0.1)
    
    print("Hilo de captura detenido")

# ... (resto del código de la aplicación Flask)

if __name__ == '__main__':
    # Inicializar cámara
    try:
        camera = cv2.VideoCapture(camera_device_id)
        if camera.isOpened():
            is_capturing = True
            # Iniciar hilo de captura
            capture_thread = threading.Thread(target=capture_frames)
            capture_thread.daemon = True
            capture_thread.start()
            
            # Iniciar servidor Flask
            app.run(host='0.0.0.0', port=5000, threaded=True)
        else:
            print("No se pudo abrir la cámara")
    except Exception as e:
        print(f"Error al iniciar: {e}")
    finally:
        is_capturing = False
        if camera is not None:
            camera.release()
        cv2.destroyAllWindows()