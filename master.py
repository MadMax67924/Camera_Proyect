#!/usr/bin/env python3
"""
SCRIPT MAESTRO - Interfaz única para todas las operaciones
Simplifica todo: entrenamiento, testing, ejecución
"""

import sys
import subprocess
import os
from pathlib import Path


def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_menu():
    """Muestra el menú principal"""
    print_header("MENÚ PRINCIPAL")
    print("""
1. 📸 Capturar imágenes de rostro
   (Crea dataset para una persona)

2. 🤖 Entrenar modelo
   (Genera el modelo a partir del dataset)

3. 🤖 Entrenar con desconocidos
   (Entrena detectando personas desconocidas)

4. 🌐 Iniciar servidor web
   (Inicia app.py - accesible en localhost:5000)

5. ✅ Verificar sistema
   (Comprueba que todo está funcionando)

6. 📊 Diagnosticar sistema
   (Información completa del sistema)

0. Salir

    """)


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n[*] {description}...")
    print(f"    Comando: {' '.join(cmd)}")
    print("-"*70)
    
    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        if result.returncode == 0:
            print("-"*70)
            print(f"✅ {description} completado exitosamente")
            return True
        else:
            print("-"*70)
            print(f"❌ {description} falló (código: {result.returncode})")
            return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False


def capture_faces():
    """Captura imágenes de rostro"""
    print_header("CAPTURAR IMÁGENES DE ROSTRO")
    print("""
Este script capturará imágenes de tu rostro para entrenar el modelo.

Instrucciones:
1. Se abrirá una ventana de video
2. Muestra tu rostro a la cámara
3. Presiona ESPACIO para capturar una imagen
4. Presiona 'q' para terminar

¿Cuál es tu nombre?
    """)
    
    name = input("Nombre (o presiona Enter para cancelar): ").strip()
    
    if not name:
        print("❌ Cancelado")
        return False
    
    cmd = [sys.executable, "scripts/capture_faces.py", name]
    return run_command(cmd, f"Captura de imágenes para {name}")


def train_model():
    """Entrena el modelo"""
    print_header("ENTRENAR MODELO")
    print("""
Este script entrenará el modelo con el dataset actual.

Requisitos:
- Mínimo 2 imágenes por persona
- Carpeta: dataset/raw/

El modelo se guardará en: models/faces_model_lite.pkl
    """)
    
    confirm = input("\n¿Continuar con entrenamiento? (s/n): ").strip().lower()
    
    if confirm != 's':
        print("❌ Cancelado")
        return False
    
    cmd = [sys.executable, "scripts/train_model_new.py"]
    return run_command(cmd, "Entrenamiento de modelo")


def train_with_unknowns():
    """Entrena modelo con detección de desconocidos"""
    print_header("ENTRENAR CON DETECCIÓN DE DESCONOCIDOS")
    print("""
Este script entrenará un modelo mejorado que detecta desconocidos.

Requisitos:
- Dataset de personas conocidas: dataset/raw/
- Dataset de desconocidos (opcional): dataset/unknown/

El modelo se guardará en: models/faces_model_lite.pkl
    """)
    
    confirm = input("\n¿Continuar con entrenamiento? (s/n): ").strip().lower()
    
    if confirm != 's':
        print("❌ Cancelado")
        return False
    
    cmd = [sys.executable, "scripts/train_model_with_unknowns.py"]
    return run_command(cmd, "Entrenamiento con desconocidos")


def start_server():
    """Inicia el servidor Flask"""
    print_header("SERVIDOR WEB")
    print("""
Iniciando servidor Flask...

Accesible en: http://localhost:5000

Características:
- Streaming en vivo de cámara (30 FPS)
- Reconocimiento facial
- Control BLE de puerta (si disponible)
- Control Arduino (si disponible)

Presiona Ctrl+C para detener el servidor
    """)
    
    cmd = [sys.executable, "app.py"]
    return run_command(cmd, "Servidor Flask")


def verify_system():
    """Verifica el sistema"""
    print_header("VERIFICACIÓN DEL SISTEMA")
    
    cmd = [sys.executable, "test_system.py"]
    return run_command(cmd, "Verificación")


def diagnose_system():
    """Diagnostica el sistema"""
    print_header("DIAGNÓSTICO DEL SISTEMA")
    
    cmd = [sys.executable, "diagnose_system.py"]
    return run_command(cmd, "Diagnóstico")


def main():
    print("""
    
    ╔════════════════════════════════════════════════════════════════════╗
    ║                                                                    ║
    ║         SISTEMA DE RECONOCIMIENTO FACIAL CON CÁMARA               ║
    ║                                                                    ║
    ║         Laptop + Raspberry Pi (BLE + Arduino)                     ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Cambiar a directorio del proyecto
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    while True:
        print_menu()
        choice = input("Selecciona una opción: ").strip()
        
        try:
            if choice == '1':
                capture_faces()
            elif choice == '2':
                train_model()
            elif choice == '3':
                train_with_unknowns()
            elif choice == '4':
                start_server()
            elif choice == '5':
                verify_system()
            elif choice == '6':
                diagnose_system()
            elif choice == '0':
                print("\n👋 ¡Hasta luego!\n")
                break
            else:
                print("❌ Opción no válida")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Operación cancelada")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programa terminado\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)
