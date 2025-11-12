#!/usr/bin/env python3
"""
Diagnóstico completo del sistema de reconocimiento facial
Verifica que todo esté funcionando correctamente
"""

import sys
from pathlib import Path

def check_files():
    """Verifica archivos críticos"""
    print("\n" + "="*70)
    print("1. VERIFICACIÓN DE ARCHIVOS")
    print("="*70)
    
    critical_files = [
        "app.py",
        "core/face_recognition_lite.py",
        "scripts/train_model_new.py",
        "scripts/train_model_with_unknowns.py",
        "models/faces_model_lite.pkl"
    ]
    
    all_ok = True
    for file in critical_files:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"  ✓ {file} ({size:.1f} KB)")
        else:
            print(f"  ✗ {file} (FALTA)")
            all_ok = False
    
    return all_ok

def check_dataset():
    """Verifica dataset"""
    print("\n" + "="*70)
    print("2. VERIFICACIÓN DE DATASET")
    print("="*70)
    
    raw_path = Path("dataset/raw")
    
    if not raw_path.exists():
        print("  ✗ dataset/raw/ NO EXISTE")
        return False
    
    people = [d for d in raw_path.iterdir() if d.is_dir()]
    
    if not people:
        print("  ✗ dataset/raw/ está VACÍO")
        return False
    
    total_images = 0
    for person in people:
        images = list(person.glob("*.jpg")) + list(person.glob("*.png"))
        total_images += len(images)
        print(f"  ✓ {person.name}: {len(images)} imágenes")
    
    print(f"\n  Total: {len(people)} personas, {total_images} imágenes")
    return True

def check_model():
    """Verifica que el modelo funcione"""
    print("\n" + "="*70)
    print("3. VERIFICACIÓN DE MODELO")
    print("="*70)
    
    try:
        from core.face_recognition_lite import FaceRecognizerLite
        
        recognizer = FaceRecognizerLite(model_path="models/faces_model_lite.pkl")
        
        if recognizer.is_lite_model or recognizer.known_face_encodings:
            print(f"  ✓ Modelo cargado correctamente")
            print(f"  ✓ Tipo: {'KNN' if recognizer.is_lite_model else 'Encodings'}")
            print(f"  ✓ Personas: {', '.join(recognizer.get_registered_names())}")
            print(f"  ✓ Umbral: {recognizer.tolerance}")
            return True
        else:
            print("  ✗ Modelo no cargado")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_features():
    """Verifica compatibilidad de features"""
    print("\n" + "="*70)
    print("4. VERIFICACIÓN DE FEATURES")
    print("="*70)
    
    try:
        import numpy as np
        from core.face_recognition_lite import FaceRecognizerLite
        from scripts.train_model_new import extract_face_features
        
        # Test training
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        train_features = extract_face_features(dummy_img, (10, 10, 50, 50))
        
        if train_features is None:
            print("  ✗ Error en extracción de features (training)")
            return False
        
        train_dim = len(train_features)
        
        # Test recognition
        recognizer = FaceRecognizerLite()
        dummy_face = np.zeros((64, 64, 3), dtype=np.uint8)
        recog_features = recognizer.extract_features(dummy_face)
        recog_dim = len(recog_features)
        
        print(f"  Training: {train_dim} features")
        print(f"  Recognition: {recog_dim} features")
        
        if train_dim == recog_dim:
            print(f"  ✓ COINCIDEN ({train_dim} features)")
            return True
        else:
            print(f"  ✗ NO COINCIDEN (diferencia: {abs(train_dim - recog_dim)})")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_dependencies():
    """Verifica dependencias"""
    print("\n" + "="*70)
    print("5. VERIFICACIÓN DE DEPENDENCIAS")
    print("="*70)
    
    required = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'flask': 'Flask',
        'sklearn': 'Scikit-learn',
        'scipy': 'SciPy',
        'tqdm': 'tqdm'
    }
    
    optional = {
        'mediapipe': 'MediaPipe (opcional)',
        'bleak': 'Bleak (BLE, opcional)',
        'serial': 'PySerial (Arduino, opcional)'
    }
    
    all_ok = True
    
    print("\n  Dependencias requeridas:")
    for module, name in required.items():
        try:
            __import__(module)
            print(f"    ✓ {name}")
        except ImportError:
            print(f"    ✗ {name} (FALTA)")
            all_ok = False
    
    print("\n  Dependencias opcionales:")
    for module, name in optional.items():
        try:
            __import__(module)
            print(f"    ✓ {name}")
        except ImportError:
            print(f"    ○ {name} (no instalado)")
    
    return all_ok

def main():
    """Ejecuta diagnóstico completo"""
    print("\n" + "="*70)
    print("DIAGNÓSTICO COMPLETO DEL SISTEMA")
    print("="*70)
    
    results = {
        'Archivos': check_files(),
        'Dataset': check_dataset(),
        'Modelo': check_model(),
        'Features': check_features(),
        'Dependencias': check_dependencies()
    }
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    
    for check, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"  {symbol} {check}")
    
    all_ok = all(results.values())
    
    print("\n" + "="*70)
    if all_ok:
        print("✅ SISTEMA FUNCIONANDO CORRECTAMENTE")
        print("="*70)
        print("\nPuedes ejecutar:")
        print("  python3 app.py")
    else:
        print("⚠️ HAY PROBLEMAS QUE RESOLVER")
        print("="*70)
        print("\nPasos recomendados:")
        if not results['Dependencias']:
            print("  1. pip3 install -r requirements.txt")
        if not results['Dataset']:
            print("  2. Añade imágenes a dataset/raw/")
        if not results['Modelo']:
            print("  3. python3 scripts/train_model_new.py")
    
    print("="*70 + "\n")
    
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
