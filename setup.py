#!/usr/bin/env python3
"""
Script de configuración inicial del proyecto
Configura permisos y estructura necesaria
"""

import os
import sys
import stat
from pathlib import Path


def make_executable(filepath):
    """Hace un archivo ejecutable"""
    try:
        current = os.stat(filepath)
        os.chmod(filepath, current.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"  ✓ {filepath} configurado como ejecutable")
        return True
    except Exception as e:
        print(f"  ✗ Error en {filepath}: {e}")
        return False


def ensure_directory(dirpath):
    """Asegura que un directorio existe"""
    try:
        Path(dirpath).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Directorio asegurado: {dirpath}")
        return True
    except Exception as e:
        print(f"  ✗ Error creando {dirpath}: {e}")
        return False


def main():
    """Configuración principal"""
    print("\n" + "="*70)
    print("  CONFIGURACIÓN INICIAL DEL PROYECTO")
    print("="*70 + "\n")

    # Directorios a asegurar
    directories = [
        'dataset/raw',
        'dataset/processed',
        'models',
        'logs',
        'core',
        'scripts'
    ]

    print("[1/3] Asegurando estructura de directorios...")
    for directory in directories:
        ensure_directory(directory)

    # Scripts a hacer ejecutables
    scripts = [
        'app.py',
        'scripts/capture_faces.py',
        'scripts/train_model.py',
        'diagnose_camera.py',
        'quick_fix.py'
    ]

    print("\n[2/3] Configurando permisos de ejecución...")
    for script in scripts:
        if os.path.exists(script):
            make_executable(script)
        else:
            print(f"  ⚠ No encontrado: {script}")

    # Scripts bash
    bash_scripts = [
        'install.sh',
        'setup_camera.sh',
        'setup_wifi.sh'
    ]

    print("\n[3/3] Configurando scripts bash...")
    for script in bash_scripts:
        if os.path.exists(script):
            make_executable(script)
        else:
            print(f"  ⚠ No encontrado: {script}")

    # Verificar archivos críticos
    print("\n" + "-"*70)
    print("Verificando archivos críticos...")

    critical_files = [
        ('app.py', 'Aplicación principal'),
        ('requirements.txt', 'Dependencias Python'),
        ('core/face_recognition.py', 'Módulo de reconocimiento'),
        ('scripts/capture_faces.py', 'Script de captura'),
        ('scripts/train_model.py', 'Script de entrenamiento'),
    ]

    all_ok = True
    for filepath, description in critical_files:
        if os.path.exists(filepath):
            print(f"  ✓ {description}: {filepath}")
        else:
            print(f"  ✗ FALTANTE - {description}: {filepath}")
            all_ok = False

    print("\n" + "="*70)
    if all_ok:
        print("  ✅ CONFIGURACIÓN COMPLETADA")
        print("="*70)
        print("\n  Siguiente paso: Instalar dependencias")
        print("  Ejecuta: pip3 install -r requirements.txt\n")
        return 0
    else:
        print("  ⚠️  CONFIGURACIÓN COMPLETADA CON ADVERTENCIAS")
        print("="*70)
        print("\n  Algunos archivos no se encontraron")
        print("  El sistema podría no funcionar correctamente\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
