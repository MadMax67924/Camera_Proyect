#!/usr/bin/env python3
"""
Módulo de reconocimiento facial MEJORADO - SIN DLIB
Usa MediaPipe para detección y características propias para reconocimiento
Mucho más rápido en instalación y ejecución que face_recognition (dlib)
"""

import cv2
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict, Optional
import time
from scipy.spatial.distance import euclidean, cosine
from pathlib import Path

# Intentar importar MediaPipe, pero no es obligatorio
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[WARNING] MediaPipe no disponible, usando solo OpenCV")


class FaceRecognizerLite:
    """
    Reconocedor facial rápido sin DLIB
    - MediaPipe para detección de rostros
    - OpenCV deep features para descripción
    - Distancia euclidiana para matching
    """

    def __init__(self, model_path: str = "models/faces_model.pkl",
                 tolerance: float = 0.5,
                 use_distance: str = "cosine"):
        """
        Inicializa el reconocedor facial

        Args:
            model_path: Ruta al archivo del modelo entrenado
            tolerance: Umbral de similitud (menor = más estricto)
            use_distance: "cosine" o "euclidean" para comparación
        """
        self.model_path = model_path
        self.tolerance = tolerance
        self.use_distance = use_distance

        # Almacenar encodings conocidos
        self.known_face_encodings = []
        self.known_face_names = []
        self.encoding_dim = 135  # Por defecto, se actualizará al cargar modelo

        # Inicializar MediaPipe (opcional)
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_detection = mp.solutions.face_detection
            self.face_detector = self.mp_face_detection.FaceDetection(
                model_selection=1,  # 1 para corto rango (más rápido)
                min_detection_confidence=0.5
            )
        else:
            self.mp_face_detection = None
            self.face_detector = None
            print("[INFO] Usando detección con Haar Cascade (OpenCV)")

        # Cargar Haar Cascade como fallback
        self.haar_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Inicializar extractor de características de OpenCV (DNN)
        self.net = None
        self._init_feature_extractor()

        # Caché para optimización
        self.detection_cache = {}

        # Cargar modelo si existe
        self.load_model()

    def _init_feature_extractor(self):
        """Inicializa el extractor de características OpenCV DNN"""
        try:
            # Usar modelo ResNet 100x100 de OpenFace (alternativa a dlib)
            modelFile = "models/openface_nn4.small2.v1.t7"
            
            # Si el archivo no existe, crear un alternativo más simple
            if not os.path.exists(modelFile):
                print("[WARNING] Modelo OpenFace no encontrado, usando extractor simple...")
                self.net = None
                return

            self.net = cv2.dnn.readNetFromTorch(modelFile)
            print(f"[OK] Extractor de características cargado: {modelFile}")
        except Exception as e:
            print(f"[WARNING] No se pudo cargar modelo de características: {e}")
            self.net = None

    def _extract_features_simple(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extrae características simples del rostro si no hay DNN disponible
        Usa momentos de Hu y características básicas
        """
        # Redimensionar a 100x100
        face_resized = cv2.resize(face_image, (100, 100))
        
        # Convertir a escala de grises
        if len(face_resized.shape) == 3:
            gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_resized
        
        # Calcular momentos de Hu (características invariantes)
        contours, _ = cv2.findContours(
            cv2.Canny(gray, 50, 150),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE
        )
        
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            hu_moments = cv2.HuMoments(cnt).flatten()
        else:
            hu_moments = np.zeros(7)
        
        # Características estadísticas del histograma
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        # Redimensionar histograma para consistencia
        if len(hist) < 128:
            hist = np.pad(hist, (0, 128 - len(hist)), 'constant')
        else:
            hist = hist[:128]
        
        # Combinar características
        features = np.concatenate([hu_moments, hist])
        
        # Normalizar
        features = features / (np.linalg.norm(features) + 1e-6)
        
        return features

    def _extract_features_dnn(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extrae características usando red neuronal si está disponible
        """
        # Redimensionar a 100x100 (tamaño esperado por OpenFace)
        face = cv2.resize(face_image, (100, 100))
        
        # Normalizar
        face = face.astype('float32')
        face = (face - 127.5) / 128.0
        
        # Crear blob
        blob = cv2.dnn.blobFromImage(face, 1.0, (100, 100))
        
        # Forward pass
        self.net.setInput(blob)
        vec = self.net.forward()
        
        # Normalizar salida
        vec = vec / (np.linalg.norm(vec) + 1e-6)
        
        return vec.flatten()

    def extract_features(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extrae características del rostro
        Adapta automáticamente a la dimensionalidad esperada por el modelo
        """
        if self.net is not None:
            try:
                features = self._extract_features_dnn(face_image)
            except Exception as e:
                features = self._extract_features_simple(face_image)
        else:
            features = self._extract_features_simple(face_image)
        
        # Adaptar dimensionalidad si es necesario
        if len(features) != self.encoding_dim:
            if self.encoding_dim == 128:
                # Convertir de 135 a 128 (truncar los últimos 7)
                features = features[:128]
            elif self.encoding_dim == 135:
                # Asegurar que tenemos 135
                if len(features) < 135:
                    features = np.pad(features, (0, 135 - len(features)), mode='constant')
                else:
                    features = features[:135]
        
        return features

    def load_model(self) -> bool:
        """
        Carga el modelo entrenado desde archivo pickle
        Detecta automáticamente la dimensionalidad de los encodings
        """
        if not os.path.exists(self.model_path):
            print(f"[INFO] No se encontró modelo en: {self.model_path}")
            print("[INFO] Usa train_model.py para crear uno")
            return False

        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.known_face_encodings = data['encodings']
                self.known_face_names = data['names']

            # Detectar dimensionalidad del modelo
            if len(self.known_face_encodings) > 0:
                encoding_dim = len(self.known_face_encodings[0])
                self.encoding_dim = encoding_dim
                if encoding_dim == 128:
                    print(f"[OK] Modelo dlib detectado (128 dimensiones)")
                elif encoding_dim == 135:
                    print(f"[OK] Modelo lite detectado (135 dimensiones)")
                else:
                    print(f"[OK] Modelo personalizado ({encoding_dim} dimensiones)")

            print(f"[OK] Modelo cargado: {len(self.known_face_names)} rostros registrados")
            personas_unicas = set(self.known_face_names)
            print(f"[OK] Personas: {', '.join(sorted(personas_unicas))}")
            return True

        except Exception as e:
            print(f"[ERROR] No se pudo cargar el modelo: {e}")
            return False

    def _distance_to_confidence(self, distance: float) -> float:
        """
        Convierte distancia a confianza (0-1)
        """
        if self.use_distance == "cosine":
            # La distancia coseno está entre 0 y 2
            confidence = 1.0 - (distance / 2.0)
        else:
            # Euclidiana: normalizar según umbral
            confidence = 1.0 - (distance / (self.tolerance * 2.0))
        
        return max(0.0, min(1.0, confidence))

    def recognize_faces(self, frame: np.ndarray,
                       scale_factor: float = 1.0) -> List[Dict]:
        """
        Reconoce rostros en un frame

        Args:
            frame: Imagen BGR de OpenCV
            scale_factor: Factor de escala para acelerar

        Returns:
            Lista de diccionarios con información de rostros detectados
        """
        if not self.known_face_encodings:
            return []

        results = []

        # Convertir a RGB para MediaPipe o usar directamente para Haar
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Reducir tamaño si es necesario
        if scale_factor < 1.0:
            h, w = rgb_frame.shape[:2]
            rgb_frame_small = cv2.resize(rgb_frame, (int(w * scale_factor), int(h * scale_factor)))
            gray_frame_small = cv2.resize(gray_frame, (int(w * scale_factor), int(h * scale_factor)))
        else:
            rgb_frame_small = rgb_frame
            gray_frame_small = gray_frame

        # Detección: usar MediaPipe si está disponible, si no usar Haar Cascade
        if self.face_detector is not None:
            # Detección con MediaPipe
            try:
                results_det = self.face_detector.process(rgb_frame_small)
                detections = []
                
                if results_det.detections:
                    h, w = rgb_frame_small.shape[:2]
                    for detection in results_det.detections:
                        bbox = detection.location_data.relative_bounding_box
                        left = int(bbox.xmin * w)
                        top = int(bbox.ymin * h)
                        right = int((bbox.xmin + bbox.width) * w)
                        bottom = int((bbox.ymin + bbox.height) * h)
                        detections.append((left, top, right - left, bottom - top))
            except Exception as e:
                print(f"[WARNING] MediaPipe falló: {e}, usando Haar Cascade")
                detections = []
                self.face_detector = None  # Deshabilitar MediaPipe
        else:
            detections = []

        # Fallback a Haar Cascade si MediaPipe no tenía detecciones
        if not detections and hasattr(self, 'haar_cascade') and self.haar_cascade is not None:
            # Detección con Haar Cascade
            faces_haar = self.haar_cascade.detectMultiScale(
                gray_frame_small,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            for (x, y, w, h) in faces_haar:
                detections.append((x, y, w, h))

        # Si todavía no hay detecciones, retornar vacío
        if not detections:
            return []

        h_orig, w_orig = frame.shape[:2]
        
        # Procesar cada rostro detectado
        for det in detections:
            x, y, w, h = det
            
            # Ajustar coordenadas si se usó scale_factor
            if scale_factor < 1.0:
                x = int(x / scale_factor)
                y = int(y / scale_factor)
                w = int(w / scale_factor)
                h = int(h / scale_factor)

            # Asegurar que están dentro de los límites
            left = max(0, x)
            top = max(0, y)
            right = min(w_orig, x + w)
            bottom = min(h_orig, y + h)

            if right <= left or bottom <= top:
                continue

            # Extraer región del rostro
            face_image = frame[top:bottom, left:right]

            try:
                # Extraer características
                encoding = self.extract_features(face_image)

                # Comparar con rostros conocidos
                if self.use_distance == "cosine":
                    distances = [cosine(encoding, known_enc) for known_enc in self.known_face_encodings]
                else:
                    distances = [euclidean(encoding, known_enc) for known_enc in self.known_face_encodings]

                # Encontrar mejor match
                best_match_index = np.argmin(distances)
                best_distance = distances[best_match_index]

                # Verificar si está dentro del umbral
                if best_distance <= self.tolerance:
                    name = self.known_face_names[best_match_index]
                    confidence = self._distance_to_confidence(best_distance)
                else:
                    name = "Desconocido"
                    confidence = 0.0

                results.append({
                    'name': name,
                    'confidence': confidence,
                    'location': (top, right, bottom, left),
                    'box': (left, top, right - left, bottom - top),
                    'distance': best_distance
                })

            except Exception as e:
                print(f"[WARNING] Error procesando rostro: {e}")
                continue

        return results

    def draw_faces(self, frame: np.ndarray,
                   faces: List[Dict],
                   show_confidence: bool = True) -> np.ndarray:
        """
        Dibuja rectángulos y nombres en los rostros detectados
        """
        for face in faces:
            left, top, w, h = face['box']
            right = left + w
            bottom = top + h
            name = face['name']
            confidence = face['confidence']

            # Color según si es conocido o desconocido
            if name == "Desconocido":
                color = (0, 0, 255)  # Rojo
                label = "Desconocido"
            else:
                color = (0, 255, 0)  # Verde
                if show_confidence:
                    label = f"{name} ({confidence*100:.0f}%)"
                else:
                    label = name

            # Dibujar rectángulo
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Dibujar etiqueta con fondo
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
                                           0.6, 2)
            label_y = max(top - 10, label_size[1])

            # Fondo para el texto
            cv2.rectangle(frame,
                         (left, label_y - label_size[1] - 5),
                         (left + label_size[0], label_y + 5),
                         color,
                         cv2.FILLED)

            # Texto
            cv2.putText(frame, label, (left, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame

    def get_person_count(self) -> int:
        """Retorna el número de personas registradas"""
        return len(set(self.known_face_names))

    def get_registered_names(self) -> List[str]:
        """Retorna lista de nombres únicos registrados"""
        return list(set(self.known_face_names))


# Función auxiliar para uso rápido (compatible con la original)
def quick_recognize(frame: np.ndarray,
                   model_path: str = "models/faces_model.pkl",
                   draw: bool = True) -> Tuple[np.ndarray, List[Dict]]:
    """
    Función rápida para reconocer y dibujar rostros en un frame
    """
    recognizer = FaceRecognizerLite(model_path=model_path)
    faces = recognizer.recognize_faces(frame)

    if draw and faces:
        frame = recognizer.draw_faces(frame, faces)

    return frame, faces
