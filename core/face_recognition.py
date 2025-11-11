#!/usr/bin/env python3
"""
Módulo de reconocimiento facial usando face_recognition (dlib)
Optimizado para Raspberry Pi 3 y Fedora
"""

import cv2
import face_recognition
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict, Optional
import time


class FaceRecognizer:
    """
    Clase para reconocer rostros usando face_recognition library
    """

    def __init__(self, model_path: str = "models/faces_model.pkl",
                 tolerance: float = 0.6,
                 model_type: str = "hog"):
        """
        Inicializa el reconocedor facial

        Args:
            model_path: Ruta al archivo del modelo entrenado
            tolerance: Umbral de similitud (0.6 = 60% de confianza, menor = más estricto)
            model_type: "hog" (más rápido, CPU) o "cnn" (más preciso, GPU)
        """
        self.model_path = model_path
        self.tolerance = tolerance
        self.model_type = model_type  # "hog" es mejor para Raspberry Pi

        # Almacenar encodings conocidos
        self.known_face_encodings = []
        self.known_face_names = []

        # Caché para optimización
        self.last_detection_time = {}
        self.detection_cache = {}

        # Cargar modelo si existe
        self.load_model()

    def load_model(self) -> bool:
        """
        Carga el modelo entrenado desde archivo pickle

        Returns:
            True si se cargó correctamente, False si no existe
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

            print(f"[OK] Modelo cargado: {len(self.known_face_names)} personas registradas")
            print(f"[INFO] Personas: {', '.join(set(self.known_face_names))}")
            return True

        except Exception as e:
            print(f"[ERROR] No se pudo cargar el modelo: {e}")
            return False

    def recognize_faces(self, frame: np.ndarray,
                       scale_factor: float = 0.25) -> List[Dict]:
        """
        Reconoce rostros en un frame

        Args:
            frame: Imagen BGR de OpenCV
            scale_factor: Factor de escala para acelerar (0.25 = 4x más rápido)

        Returns:
            Lista de diccionarios con información de rostros detectados:
            [
                {
                    'name': str,           # Nombre de la persona
                    'confidence': float,   # Confianza (0-1)
                    'location': tuple,     # (top, right, bottom, left)
                    'box': tuple          # (x, y, w, h) para OpenCV
                }
            ]
        """
        if not self.known_face_encodings:
            return []

        results = []

        # Convertir BGR a RGB (face_recognition usa RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Reducir tamaño para acelerar procesamiento
        if scale_factor < 1.0:
            small_frame = cv2.resize(rgb_frame, (0, 0),
                                    fx=scale_factor,
                                    fy=scale_factor)
        else:
            small_frame = rgb_frame

        # Detectar ubicaciones de rostros
        face_locations = face_recognition.face_locations(small_frame,
                                                         model=self.model_type)

        if not face_locations:
            return []

        # Obtener encodings de los rostros detectados
        face_encodings = face_recognition.face_encodings(small_frame,
                                                          face_locations)

        # Comparar con rostros conocidos
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Calcular distancias con todos los rostros conocidos
            face_distances = face_recognition.face_distance(
                self.known_face_encodings,
                face_encoding
            )

            # Encontrar el mejor match
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]

            # Verificar si está dentro del umbral de tolerancia
            if best_distance <= self.tolerance:
                name = self.known_face_names[best_match_index]
                confidence = 1 - best_distance  # Convertir distancia a confianza
            else:
                name = "Desconocido"
                confidence = 0.0

            # Ajustar coordenadas si se usó scale_factor
            top, right, bottom, left = face_location
            if scale_factor < 1.0:
                top = int(top / scale_factor)
                right = int(right / scale_factor)
                bottom = int(bottom / scale_factor)
                left = int(left / scale_factor)

            # Convertir a formato OpenCV (x, y, w, h)
            x = left
            y = top
            w = right - left
            h = bottom - top

            results.append({
                'name': name,
                'confidence': confidence,
                'location': (top, right, bottom, left),
                'box': (x, y, w, h),
                'distance': best_distance
            })

        return results

    def draw_faces(self, frame: np.ndarray,
                   faces: List[Dict],
                   show_confidence: bool = True) -> np.ndarray:
        """
        Dibuja rectángulos y nombres en los rostros detectados

        Args:
            frame: Imagen BGR de OpenCV
            faces: Lista de rostros detectados por recognize_faces()
            show_confidence: Mostrar porcentaje de confianza

        Returns:
            Frame con anotaciones dibujadas
        """
        for face in faces:
            x, y, w, h = face['box']
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
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            # Dibujar etiqueta con fondo
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
                                           0.6, 2)
            label_y = max(y - 10, label_size[1])

            # Fondo para el texto
            cv2.rectangle(frame,
                         (x, label_y - label_size[1] - 5),
                         (x + label_size[0], label_y + 5),
                         color,
                         cv2.FILLED)

            # Texto
            cv2.putText(frame, label, (x, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame

    def get_person_count(self) -> int:
        """Retorna el número de personas registradas"""
        return len(set(self.known_face_names))

    def get_registered_names(self) -> List[str]:
        """Retorna lista de nombres únicos registrados"""
        return list(set(self.known_face_names))


# Función auxiliar para uso rápido
def quick_recognize(frame: np.ndarray,
                   model_path: str = "models/faces_model.pkl",
                   draw: bool = True) -> Tuple[np.ndarray, List[Dict]]:
    """
    Función rápida para reconocer y dibujar rostros en un frame

    Args:
        frame: Imagen BGR de OpenCV
        model_path: Ruta al modelo entrenado
        draw: Si True, dibuja las detecciones en el frame

    Returns:
        Tupla (frame_anotado, lista_de_rostros)
    """
    recognizer = FaceRecognizer(model_path=model_path)
    faces = recognizer.recognize_faces(frame)

    if draw and faces:
        frame = recognizer.draw_faces(frame, faces)

    return frame, faces
