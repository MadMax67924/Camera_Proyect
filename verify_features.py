#!/usr/bin/env python3
"""
Verificación rápida: Feature dimension compatibility
Comprueba que training y reconocimiento usan el mismo número de features
"""

import sys
import numpy as np
from pathlib import Path

# Agregar ruta del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.face_recognition_lite import FaceRecognizerLite
from scripts.train_model_new import extract_face_features as train_extract_features

def check_feature_dimensions():
    print("\n" + "="*70)
    print("✓ VERIFICACIÓN: Dimensiones de Features")
    print("="*70)
    
    # Crear imagen dummy
    import cv2
    dummy_face = np.zeros((64, 64, 3), dtype=np.uint8)
    dummy_face[:, :] = (100, 100, 100)  # Gris
    
    # Test 1: Función de training
    print("\n[TEST 1] Dimensión en training (train_model_new.py)...")
    train_features = train_extract_features(np.zeros((100, 100, 3), dtype=np.uint8), (10, 10, 50, 50))
    if train_features is not None:
        train_dim = len(train_features)
        print(f"  ✓ Dimensión: {train_dim}")
    else:
        train_dim = None
        print("  ✗ Error al extraer features de training")
    
    # Test 2: Función de reconocimiento (lite)
    print("\n[TEST 2] Dimensión en reconocimiento (FaceRecognizerLite)...")
    recognizer = FaceRecognizerLite()
    test_features = recognizer.extract_features(dummy_face)
    recog_dim = len(test_features)
    print(f"  ✓ Dimensión: {recog_dim}")
    
    # Test 3: Comparar
    print("\n[TEST 3] Comparación...")
    if train_dim is not None:
        if train_dim == recog_dim:
            print(f"  ✅ COINCIDEN: {train_dim} features en ambos")
            print("\n  ✓ El sistema está correctamente sincronizado")
            return True
        else:
            print(f"  ❌ NO COINCIDEN:")
            print(f"     Training: {train_dim} features")
            print(f"     Recognition: {recog_dim} features")
            print(f"     Diferencia: {abs(train_dim - recog_dim)} features")
            return False
    else:
        print(f"  ⚠️  No se pudo verificar (error en training)")
        return False

if __name__ == "__main__":
    success = check_feature_dimensions()
    print("\n" + "="*70)
    if success:
        print("✅ SISTEMA LISTO PARA USAR")
    else:
        print("❌ NECESITA REPARACIÓN")
    print("="*70 + "\n")
    sys.exit(0 if success else 1)
