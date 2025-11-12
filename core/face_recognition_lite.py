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
                 tolerance: float = 60.0,
                 use_distance: str = "euclidean"):
        """
        Inicializa el reconocedor facial

        Args:
            model_path: Ruta al archivo del modelo entrenado
            tolerance: Umbral de similitud para KNN (mayor = más permisivo). Para este modelo: ~60
            use_distance: "cosine" o "euclidean" para comparación
        """
        self.model_path = model_path
        self.tolerance = tolerance
        self.use_distance = use_distance

        # Almacenar encodings conocidos
        self.known_face_encodings = []
        self.known_face_names = []
        self.encoding_dim = 135  # Por defecto, se actualizará al cargar modelo

        # Variables para modelo KNN (formato lite nuevo)
        self.knn_classifier = None
        self.scaler = None
        self.is_lite_model = False
        self.anomaly_detector = None  # Detector de desconocidos (Isolation Forest)

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

    def _extract_lbp_features(self, gray_face: np.ndarray) -> np.ndarray:
        """Extrae características LBP (Local Binary Patterns)"""
        def get_pixel(img, center, x, y):
            new_value = 0
            try:
                if img[x][y] >= center:
                    new_value = 1
            except:
                pass
            return new_value

        lbp = np.zeros_like(gray_face)
        h, w = gray_face.shape

        for i in range(1, h-1):
            for j in range(1, w-1):
                center = gray_face[i, j]
                val = 0
                val |= get_pixel(gray_face, center, i-1, j-1) << 7
                val |= get_pixel(gray_face, center, i-1, j) << 6
                val |= get_pixel(gray_face, center, i-1, j+1) << 5
                val |= get_pixel(gray_face, center, i, j+1) << 4
                val |= get_pixel(gray_face, center, i+1, j+1) << 3
                val |= get_pixel(gray_face, center, i+1, j) << 2
                val |= get_pixel(gray_face, center, i+1, j-1) << 1
                val |= get_pixel(gray_face, center, i, j-1) << 0
                lbp[i, j] = val

        # Histograma LBP
        hist, _ = np.histogram(lbp.ravel(), bins=32, range=(0, 256))
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-6)

        return hist

    def _extract_hog_features(self, gray_face: np.ndarray) -> np.ndarray:
        """Extrae características HOG (Histogram of Oriented Gradients)"""
        # Calcular gradientes
        gx = cv2.Sobel(gray_face, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray_face, cv2.CV_32F, 0, 1, ksize=3)

        # Magnitud y ángulo
        mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)

        # Histograma de 16 bins
        hist, _ = np.histogram(ang.ravel(), bins=16, range=(0, 360), weights=mag.ravel())
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-6)

        return hist

    def extract_features(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extrae características MEJORADAS del rostro
        Debe coincidir con extract_face_features en train_model_improved.py
        330 características = LBP + HOG + Histograma + Bordes
        """
        if face_image is None or face_image.size == 0:
            return np.zeros(330)

        try:
            # Redimensionar a tamaño estándar
            face_resized = cv2.resize(face_image, (64, 64))

            # Convertir a escala de grises
            if len(face_resized.shape) == 3:
                face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
            else:
                face_gray = face_resized

            # Ecualizar histograma para mejor contraste
            face_gray = cv2.equalizeHist(face_gray)

            features = []

            # 1. Píxeles aplanados reducidos (16x16 = 256)
            face_small = cv2.resize(face_gray, (16, 16))
            features.extend(face_small.flatten().tolist())

            # 2. Estadísticas básicas (6)
            features.append(float(face_gray.mean()))
            features.append(float(face_gray.std()))
            features.append(float(np.min(face_gray)))
            features.append(float(np.max(face_gray)))
            features.append(float(np.median(face_gray)))
            features.append(float(face_gray.var()))

            # 3. Histograma global (16)
            hist = cv2.calcHist([face_gray], [0], None, [16], [0, 256])
            features.extend(hist.flatten().tolist())

            # 4. LBP - Patrones locales binarios (32)
            lbp_hist = self._extract_lbp_features(face_gray)
            features.extend(lbp_hist.tolist())

            # 5. HOG - Histograma de gradientes orientados (16)
            hog_hist = self._extract_hog_features(face_gray)
            features.extend(hog_hist.tolist())

            # 6. Características de bordes (4)
            edges = cv2.Canny(face_gray, 100, 200)
            features.append(float(edges.mean()))
            features.append(float(edges.std()))
            features.append(float(edges.sum() / (64 * 64)))
            features.append(float(np.count_nonzero(edges) / (64 * 64)))

            # Total: 256 + 6 + 16 + 32 + 16 + 4 = 330 características
            return np.array(features, dtype=np.float32)

        except Exception as e:
            print(f"[WARNING] Error extrayendo características: {e}")
            return np.zeros(330)

    def load_model(self) -> bool:
        """
        Carga el modelo entrenado desde archivo pickle
        Compatible con dos formatos:
        1. Formato lite: {'classifier': KNN, 'scaler': StandardScaler, 'names': [...]}
        2. Formato dlib: {'encodings': [...], 'names': [...]}
        """
        if not os.path.exists(self.model_path):
            print(f"[INFO] No se encontró modelo en: {self.model_path}")
            print("[INFO] Usa train_model.py para crear uno")
            return False

        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)

            # Detectar formato del modelo
            if 'classifier' in data and 'scaler' in data:
                # Formato LITE (nuevo con KNN)
                print("[INFO] Detectado formato LITE (KNN + StandardScaler)")
                self.knn_classifier = data['classifier']
                self.scaler = data['scaler']
                self.known_face_names = data['names']
                self.is_lite_model = True

                # Cargar umbral óptimo si está disponible
                if 'best_threshold' in data:
                    self.tolerance = data['best_threshold']
                    print(f"[OK] Umbral óptimo cargado: {self.tolerance:.1f}")

                # Cargar detector de anomalías si está disponible
                if 'anomaly_detector' in data:
                    self.anomaly_detector = data['anomaly_detector']
                    print(f"[OK] Detector de desconocidos cargado")
                else:
                    self.anomaly_detector = None

                print(f"[OK] Modelo KNN cargado: {len(self.known_face_names)} muestras")
                print(f"[OK] Personas: {', '.join(sorted(set(self.known_face_names)))}")

                # Mostrar información de validación si está disponible
                if 'validation_accuracy' in data:
                    print(f"[OK] Precisión en validación: {data['validation_accuracy']*100:.1f}%")

                return True
                
            elif 'encodings' in data:
                # Formato DLIB (antiguo con encodings)
                print("[INFO] Detectado formato DLIB (Encodings)")
                self.known_face_encodings = data['encodings']
                self.known_face_names = data['names']
                self.is_lite_model = False

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
            else:
                print(f"[ERROR] Formato de modelo no reconocido. Keys disponibles: {data.keys()}")
                return False

        except Exception as e:
            print(f"[ERROR] No se pudo cargar el modelo: {e}")
            import traceback
            traceback.print_exc()
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
        # Verificar si hay modelo cargado (KNN o encodings)
        if not self.known_face_encodings and not self.is_lite_model:
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

                # Reconocimiento usando KNN (formato lite nuevo)
                if self.is_lite_model and self.knn_classifier is not None:
                    # Normalizar con scaler
                    encoding_scaled = self.scaler.transform([encoding])

                    # Verificar primero con detector de anomalías si está disponible
                    is_anomaly = False
                    if self.anomaly_detector is not None:
                        anomaly_score = self.anomaly_detector.score_samples(encoding_scaled)[0]
                        is_anomaly = self.anomaly_detector.predict(encoding_scaled)[0] == -1
                        if is_anomaly:
                            print(f"[DEBUG] Anomalía detectada (score: {anomaly_score:.4f}) - Probablemente desconocido")

                    # Predicción y distancia con KNN
                    distances, indices = self.knn_classifier.kneighbors(encoding_scaled)
                    best_distance = distances[0][0]  # Distancia del vecino más cercano
                    best_match_index = indices[0][0]  # Índice en y_train

                    # Calcular distancia media de los k vecinos (más robusto)
                    mean_distance = np.mean(distances[0][:min(3, len(distances[0]))])

                    # Obtener nombre del mejor match
                    if best_match_index < len(self.known_face_names):
                        best_name = self.known_face_names[best_match_index]

                        # Verificar umbral (usar distancia media o si es anomalía)
                        if is_anomaly or mean_distance > self.tolerance * 1.5:
                            name = "Desconocido"
                            confidence = 0.0
                            print(f"[DEBUG] Rechazado - Dist media: {mean_distance:.2f} | Anomalía: {is_anomaly}")
                        elif best_distance <= self.tolerance:
                            name = best_name
                            confidence = self._distance_to_confidence(best_distance)
                            print(f"[DEBUG] Reconocido: {name} | Dist: {best_distance:.2f} | Umbral: {self.tolerance:.1f}")
                        else:
                            name = "Desconocido"
                            confidence = 0.0
                            print(f"[DEBUG] Fuera de umbral - Dist: {best_distance:.2f} | Umbral: {self.tolerance:.1f}")
                    else:
                        print(f"[ERROR] Índice {best_match_index} fuera de rango. Nombres disponibles: {len(self.known_face_names)}")
                        name = "Desconocido"
                        confidence = 0.0
                
                # Reconocimiento usando encodings (formato dlib antiguo)
                elif self.known_face_encodings:
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
                else:
                    continue

                results.append({
                    'name': name,
                    'confidence': confidence,
                    'location': (top, right, bottom, left),
                    'box': (left, top, right - left, bottom - top),
                    'distance': best_distance
                })

            except Exception as e:
                print(f"[WARNING] Error procesando rostro: {e}")
                import traceback
                traceback.print_exc()
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
