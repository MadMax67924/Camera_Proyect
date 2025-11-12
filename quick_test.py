#!/usr/bin/env python3
"""
Script rápido para entrenar y probar el modelo mejorado
Automatiza todo el proceso de entrenamiento y evaluación
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Imprime un encabezado bonito"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"[*] {description}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[ERROR] Falló: {description}")
        return False
    return True


def main():
    """Función principal"""

    print_header("QUICK TEST - Entrenamiento y Evaluación Rápida")

    # Verificar que existe el dataset
    dataset_path = Path("dataset/raw")
    if not dataset_path.exists():
        print("[ERROR] No existe dataset/raw")
        print("[INFO] Primero captura imágenes con: python3 scripts/capture_faces.py")
        return

    # Contar personas en el dataset
    people = [d for d in dataset_path.iterdir() if d.is_dir()]
    if not people:
        print("[ERROR] No hay personas en dataset/raw")
        return

    print(f"[OK] Encontradas {len(people)} personas en dataset:")
    for p in people:
        images = list(p.glob("*.jpg")) + list(p.glob("*.png"))
        print(f"  - {p.name}: {len(images)} imágenes")

    print("\n" + "-"*70)
    print("Opciones:")
    print("  1. Entrenar modelo mejorado (CON aumento de datos) - RECOMENDADO")
    print("  2. Entrenar modelo mejorado (SIN aumento de datos) - Más rápido")
    print("  3. Evaluar modelo existente con webcam")
    print("  4. Evaluar directorio de imágenes")
    print("  5. Todo (entrenar + evaluar con webcam)")
    print("-"*70)

    try:
        choice = input("\nSelecciona opción (1-5) [Enter = 1]: ").strip()
        if not choice:
            choice = "1"

        if choice == "1":
            print_header("ENTRENANDO MODELO CON AUMENTO DE DATOS")
            if run_command(
                "python3 scripts/train_model_improved.py dataset/raw models/faces_model_lite.pkl true",
                "Entrenar modelo mejorado"
            ):
                print("\n[OK] ✓ Modelo entrenado exitosamente")
                print("[INFO] Puedes evaluar con: python3 quick_test.py → opción 3")

        elif choice == "2":
            print_header("ENTRENANDO MODELO SIN AUMENTO DE DATOS")
            if run_command(
                "python3 scripts/train_model_improved.py dataset/raw models/faces_model_lite.pkl false",
                "Entrenar modelo mejorado"
            ):
                print("\n[OK] ✓ Modelo entrenado exitosamente")

        elif choice == "3":
            print_header("EVALUANDO CON WEBCAM")
            # Verificar que existe el modelo
            model_path = Path("models/faces_model_lite.pkl")
            if not model_path.exists():
                print("[ERROR] No existe modelo entrenado")
                print("[INFO] Primero entrena con: python3 quick_test.py → opción 1")
                return

            print("[INFO] Presiona 'q' en la ventana de video para salir")
            run_command(
                "python3 scripts/evaluate_model.py webcam",
                "Evaluar con webcam"
            )

        elif choice == "4":
            print_header("EVALUANDO DIRECTORIO")
            model_path = Path("models/faces_model_lite.pkl")
            if not model_path.exists():
                print("[ERROR] No existe modelo entrenado")
                return

            print("\nDirectorios disponibles:")
            for i, p in enumerate(people, 1):
                print(f"  {i}. {p.name}")

            try:
                dir_choice = input(f"\nSelecciona directorio (1-{len(people)}): ").strip()
                dir_index = int(dir_choice) - 1
                if 0 <= dir_index < len(people):
                    selected_dir = people[dir_index]
                    print(f"\n[*] Evaluando: {selected_dir}")
                    run_command(
                        f"python3 scripts/evaluate_model.py directory {selected_dir}",
                        "Evaluar directorio"
                    )
                else:
                    print("[ERROR] Opción inválida")
            except (ValueError, IndexError):
                print("[ERROR] Entrada inválida")

        elif choice == "5":
            print_header("ENTRENAMIENTO + EVALUACIÓN COMPLETA")

            # 1. Entrenar
            print("\n[PASO 1/2] Entrenando modelo...")
            if not run_command(
                "python3 scripts/train_model_improved.py dataset/raw models/faces_model_lite.pkl true",
                "Entrenar modelo"
            ):
                print("[ERROR] Falló el entrenamiento")
                return

            print("\n[OK] ✓ Entrenamiento completado")
            input("\nPresiona Enter para continuar con evaluación en webcam...")

            # 2. Evaluar
            print_header("[PASO 2/2] EVALUANDO CON WEBCAM")
            print("[INFO] Presiona 'q' en la ventana de video para salir")
            run_command(
                "python3 scripts/evaluate_model.py webcam",
                "Evaluar con webcam"
            )

        else:
            print("[ERROR] Opción inválida")

    except KeyboardInterrupt:
        print("\n\n[INFO] Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")

    print("\n" + "="*70)
    print("[INFO] Para iniciar el servidor completo: python3 app.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
