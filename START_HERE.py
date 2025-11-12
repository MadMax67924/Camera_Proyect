#!/usr/bin/env python3
"""
START_HERE.py - Punto de entrada principal del sistema
Ejecutar esto primero para comenzar
"""

import sys
import os
from pathlib import Path


def main():
    print("""
    
    ╔════════════════════════════════════════════════════════════════════╗
    ║                                                                    ║
    ║         🎥 SISTEMA DE RECONOCIMIENTO FACIAL - INICIO             ║
    ║                                                                    ║
    ║                  ¡Bienvenido! 👋 Creemos en ti                   ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    print("""
    Este script te guiará a través del primer inicio.
    
    ¿Qué necesitas hacer?
    """)
    
    options = [
        ("🚀 PRIMERA VEZ - Configuración inicial completa", "first_time"),
        ("📸 Capturar imágenes de rostro", "capture"),
        ("🤖 Entrenar modelo", "train"),
        ("🌐 Iniciar servidor web", "web"),
        ("✅ Verificar que todo funciona", "verify"),
        ("🔧 Interfaz interactiva (todas las opciones)", "master"),
        ("📚 Ver guía rápida", "guide"),
    ]
    
    for i, (desc, _) in enumerate(options, 1):
        print(f"  {i}. {desc}")
    print(f"  0. Salir")
    print()
    
    choice = input("Selecciona una opción (0-7): ").strip()
    
    if choice == "0":
        print("\n👋 ¡Hasta luego!\n")
        return 0
    
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(options):
            print("❌ Opción no válida")
            return 1
        
        _, cmd = options[idx]
        
        if cmd == "first_time":
            print("\n[*] Ejecutando configuración inicial...\n")
            os.system("python3 setup_initial.py")
        
        elif cmd == "capture":
            name = input("\n¿Cuál es tu nombre? ").strip()
            if name:
                os.system(f"python3 scripts/capture_faces.py \"{name}\"")
        
        elif cmd == "train":
            os.system("python3 scripts/train_model_new.py")
        
        elif cmd == "web":
            os.system("python3 app.py")
        
        elif cmd == "verify":
            os.system("python3 test_system.py")
        
        elif cmd == "master":
            os.system("python3 master.py")
        
        elif cmd == "guide":
            os.system("less GUIA_RAPIDA.md || cat GUIA_RAPIDA.md")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    # Cambiar a directorio del proyecto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Programa terminado\n")
        sys.exit(0)
