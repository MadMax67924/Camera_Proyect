#!/usr/bin/env python3
"""
Fix para face_recognition en Python 3.13
Fuerza la reinstalación correcta de face_recognition_models
"""

import subprocess
import sys


def run_command(cmd):
    """Ejecuta comando y muestra salida"""
    print(f"\n▶ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


def main():
    print("\n" + "="*70)
    print("  FIX PARA FACE_RECOGNITION - Python 3.13")
    print("="*70 + "\n")

    # Desinstalar versiones antiguas
    print("[1/4] Desinstalando versiones antiguas...")
    run_command("pip uninstall -y face-recognition-models face_recognition_models")

    # Reinstalar face_recognition
    print("\n[2/4] Reinstalando face_recognition...")
    if not run_command("pip install --force-reinstall --no-cache-dir face_recognition"):
        print("\n❌ Error reinstalando face_recognition")
        return 1

    # Instalar modelos desde git
    print("\n[3/4] Instalando modelos desde git...")
    if not run_command("pip install --no-cache-dir git+https://github.com/ageitgey/face_recognition_models"):
        print("\n❌ Error instalando modelos")
        return 1

    # Verificar instalación
    print("\n[4/4] Verificando instalación...")
    result = subprocess.run(
        [sys.executable, "-c", "import face_recognition; print('✓ face_recognition OK')"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("\n" + "="*70)
        print("  ✅ INSTALACIÓN CORRECTA")
        print("="*70)
        print("\n  face_recognition está listo para usar")
        print("  Ahora puedes ejecutar: python app.py\n")
        return 0
    else:
        print("\n" + "="*70)
        print("  ❌ AÚN HAY PROBLEMAS")
        print("="*70)
        print("\n" + result.stderr)
        print("\nPosibles soluciones:")
        print("  1. Usar Python 3.11 en lugar de 3.13")
        print("  2. Usar solo detección Haar (sin reconocimiento)")
        print("  3. Instalar desde código fuente\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
