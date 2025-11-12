#!/usr/bin/env python3
"""
Script de diagnóstico - Sistema sin DLIB
Verifica que todo esté instalado y funcionando correctamente
"""

import sys
import os

def check_import(module_name, display_name):
    """Intenta importar un módulo y retorna True si es exitoso"""
    try:
        mod = __import__(module_name)
        version = getattr(mod, '__version__', 'desconocida')
        print(f"  ✅ {display_name:30s} v{version}")
        return True
    except ImportError as e:
        print(f"  ❌ {display_name:30s} - {str(e)}")
        return False

def check_file(path, display_name):
    """Verifica si un archivo existe"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"  {status} {display_name:30s} {'[OK]' if exists else '[NO ENCONTRADO]'}")
    return exists

def check_directory(path, display_name):
    """Verifica si un directorio existe y crea si es necesario"""
    exists = os.path.isdir(path)
    if exists:
        print(f"  ✅ {display_name:30s} [OK]")
    else:
        print(f"  ⚠️  {display_name:30s} [CREAR]")
    return exists

def main():
    print("\n" + "="*70)
    print("  🔍 DIAGNÓSTICO - Sistema sin DLIB")
    print("="*70)

    all_ok = True

    # ===== VERIFICAR PYTHON =====
    print("\n📦 Python:")
    print(f"  Versión: Python {sys.version}")
    if sys.version_info < (3, 7):
        print(f"  ❌ Se requiere Python 3.7+")
        all_ok = False
    else:
        print(f"  ✅ Versión compatible")

    # ===== VERIFICAR MÓDULOS CRÍTICOS =====
    print("\n📚 Módulos críticos:")
    all_ok &= check_import("cv2", "OpenCV")
    all_ok &= check_import("numpy", "NumPy")
    all_ok &= check_import("flask", "Flask")
    all_ok &= check_import("mediapipe", "MediaPipe")
    all_ok &= check_import("scipy", "SciPy")

    # ===== VERIFICAR MÓDULOS OPCIONALES =====
    print("\n📚 Módulos opcionales:")
    check_import("PIL", "Pillow")
    check_import("tqdm", "tqdm")

    # ===== VERIFICAR ESTRUCTURA DE ARCHIVOS =====
    print("\n📁 Estructura de archivos:")
    check_directory("dataset", "Directorio dataset/")
    check_directory("dataset/raw", "Directorio dataset/raw/")
    check_directory("models", "Directorio models/")
    check_directory("logs", "Directorio logs/")
    check_directory("core", "Directorio core/")
    check_directory("scripts", "Directorio scripts/")
    check_directory("templates", "Directorio templates/")

    # ===== VERIFICAR MÓDULOS DEL PROYECTO =====
    print("\n🎯 Módulos del proyecto:")
    check_file("core/face_recognition_lite.py", "face_recognition_lite.py")
    check_file("core/__init__.py", "core/__init__.py")
    check_file("scripts/train_model.py", "train_model.py")
    check_file("scripts/capture_faces.py", "capture_faces.py")
    check_file("app.py", "app.py")
    check_file("templates/index.html", "index.html")

    # ===== VERIFICAR MODELO ENTRENADO =====
    print("\n🧠 Modelo de reconocimiento:")
    model_exists = check_file("models/faces_model.pkl", "faces_model.pkl")
    if not model_exists:
        print("  💡 Consejo: Ejecuta 'python3 scripts/train_model.py' para crear el modelo")

    # ===== PROBAR CÁMARA =====
    print("\n📷 Cámara:")
    try:
        import cv2
        available = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        
        if available:
            print(f"  ✅ Cámaras detectadas: {available}")
        else:
            print(f"  ❌ No se detectaron cámaras")
            all_ok = False
    except Exception as e:
        print(f"  ❌ Error verificando cámaras: {e}")
        all_ok = False

    # ===== PRUEBA DE MÓDULO LITE =====
    print("\n🚀 Prueba del módulo FaceRecognizerLite:")
    try:
        from core.face_recognition_lite import FaceRecognizerLite
        print(f"  ✅ FaceRecognizerLite cargado correctamente")
        
        # Intentar crear instancia
        recognizer = FaceRecognizerLite()
        print(f"  ✅ Instancia creada correctamente")
        print(f"  💡 Personas registradas: {recognizer.get_person_count()}")
    except Exception as e:
        print(f"  ❌ Error con FaceRecognizerLite: {e}")
        all_ok = False

    # ===== RESUMEN =====
    print("\n" + "="*70)
    if all_ok:
        print("  ✅ DIAGNÓSTICO COMPLETADO - SISTEMA LISTO")
        print("="*70)
        print("\n🎉 Todo está configurado correctamente!")
        print("\nPróximos pasos:")
        print("  1. Capturar fotos: python3 scripts/capture_faces.py")
        print("  2. Entrenar modelo: python3 scripts/train_model.py")
        print("  3. Ejecutar servidor: python3 app.py")
        return 0
    else:
        print("  ⚠️  DIAGNÓSTICO COMPLETADO - HAY PROBLEMAS")
        print("="*70)
        print("\n❌ Se encontraron problemas. Soluciona los errores arriba.")
        print("\nRecomendaciones:")
        print("  - Verifica la instalación: pip install -r requirements_no_dlib.txt")
        print("  - Lee INSTALACION_SIN_DLIB.md para más información")
        print("  - Ejecuta: bash install_no_dlib.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
