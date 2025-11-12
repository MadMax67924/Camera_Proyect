#!/usr/bin/env python3
"""
Módulo de detección facial usando MTCNN
Optimizado para Raspberry Pi
"""

import cv2
import numpy as np
from mtcnn import MTCNN
from typing import List, Dict, Any, Tuple, Optional
import time


class FaceDetectorMTCNN:
    """Clase para detección de rostros usando MTCNN"""
    
    def __init__(self, min_confidence: float = 0.9):
        """
        Inicializa el detector MTCNN
        
        Args:
            min_confidence: Confianza mínima para considerar una detección (0-1)
        """
        self.detector = MTCNN()
        self.min_confidence = min_confidence
        
    def detect_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detecta rostros en un frame usando MTCNN
        
        Args:
            frame: Imagen BGR de OpenCV
            
        Returns:
            Lista de diccionarios con información de los rostros detectados
        """
        try:
            # Convertir a RGB (MTCNN espera RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros
            detections = self.detector.detect_faces(rgb_frame)
            
            # Filtrar por confianza mínima
            valid_detections = [
                det for det in detections 
                if det['confidence'] >= self.min_confidence
            ]
            
            return valid_detections
            
        except Exception as e:
            print(f"Error en detección MTCNN: {e}")
            return []
    
    def get_face_locations(self, detections: List[Dict]) -> List[Tuple]:
        """
        Convierte las detecciones de MTCNN al formato (top, right, bottom, left)
        que espera face_recognition
        
        Args:
            detections: Lista de detecciones de MTCNN
            
        Returns:
            Lista de tuplas (top, right, bottom, left)
        """
        locations = []
        for det in detections:
            x, y, w, h = det['box']
            # Convertir a formato (top, right, bottom, left)
            locations.append((y, x + w, y + h, x))
        return locations
