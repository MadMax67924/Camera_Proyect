#!/usr/bin/env python3
"""
Script para entrenar el modelo de reconocimiento facial
Lee fotos del directorio dataset/raw/ y genera modelo entrenado
"""

import face_recognition
import os
import sys
import pickle
from pathlib import Path
import cv2
from tqdm import tqdm


def load_training_data(dataset_path: str = "dataset/raw"):
    """
    Carga datos de entrenamiento desde el directorio

    Args:
        dataset_path: Ruta al directorio con subdirectorios por persona

    Returns:
        Tupla (encodings, names) con los datos de entrenamiento
    """
    encodings = []
    names = []

    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        print(f"[ERROR] No existe el directorio: {dataset_path}")
        return None, None

    # Obtener lista de personas (subdirectorios)
    person_dirs = [d for d in dataset_path.iterdir() if d.is_dir()]

    if not person_dirs:
        print(f"[ERROR] No hay subdirectorios en {dataset_path}")
        print("\n[INFO] Estructura esperada:")
        print("  dataset/raw/")
        print("    ├── persona1/")
        print("    │   ├── foto1.jpg")
        print("    │   ├── foto2.jpg")
        print("    │   └── ...")
        print("    ├── persona2/")
        print("    │   └── ...")
        return None, None

    print("\n" + "="*70)
    print("  CARGANDO DATOS DE ENTRENAMIENTO")
    print("="*70)
    print(f"\n[INFO] Directorio: {dataset_path}")
    print(f"[INFO] Personas encontradas: {len(person_dirs)}\n")

    total_images = 0
    failed_images = 0

    # Procesar cada persona
    for person_dir in person_dirs:
        person_name = person_dir.name
        image_files = list(person_dir.glob("*.jpg")) + \
                     list(person_dir.glob("*.jpeg")) + \
                     list(person_dir.glob("*.png"))

        if not image_files:
            print(f"[WARNING] No hay imágenes para: {person_name}")
            continue

        print(f"\n[INFO] Procesando: {person_name} ({len(image_files)} imágenes)")

        # Procesar cada imagen con barra de progreso
        for image_path in tqdm(image_files, desc=f"  {person_name}", ncols=70):
            try:
                # Cargar imagen
                image = face_recognition.load_image_file(str(image_path))

                # Detectar rostros en la imagen
                face_locations = face_recognition.face_locations(image, model="hog")

                if len(face_locations) == 0:
                    print(f"\n  [WARNING] No se detectó rostro en: {image_path.name}")
                    failed_images += 1
                    continue

                if len(face_locations) > 1:
                    print(f"\n  [WARNING] Múltiples rostros en: {image_path.name} (usando el primero)")

                # Obtener encoding del primer rostro
                face_encodings = face_recognition.face_encodings(image, face_locations)

                if face_encodings:
                    encodings.append(face_encodings[0])
                    names.append(person_name)
                    total_images += 1
                else:
                    print(f"\n  [WARNING] No se pudo obtener encoding de: {image_path.name}")
                    failed_images += 1

            except Exception as e:
                print(f"\n  [ERROR] Error procesando {image_path.name}: {e}")
                failed_images += 1

    print("\n" + "-"*70)
    print(f"[INFO] Imágenes procesadas exitosamente: {total_images}")
    if failed_images > 0:
        print(f"[WARNING] Imágenes con errores: {failed_images}")

    return encodings, names


def save_model(encodings, names, output_path: str = "models/faces_model.pkl"):
    """
    Guarda el modelo entrenado en formato pickle

    Args:
        encodings: Lista de encodings faciales
        names: Lista de nombres correspondientes
        output_path: Ruta donde guardar el modelo
    """
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Preparar datos
    data = {
        'encodings': encodings,
        'names': names
    }

    # Guardar
    try:
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
        print(f"\n[OK] Modelo guardado en: {output_path}")
        return True
    except Exception as e:
        print(f"\n[ERROR] No se pudo guardar el modelo: {e}")
        return False


def show_summary(encodings, names):
    """Muestra resumen del modelo entrenado"""
    print("\n" + "="*70)
    print("  RESUMEN DEL MODELO")
    print("="*70)

    # Contar muestras por persona
    from collections import Counter
    person_counts = Counter(names)

    print(f"\n[INFO] Total de muestras: {len(encodings)}")
    print(f"[INFO] Personas únicas: {len(person_counts)}\n")

    print("Muestras por persona:")
    for person, count in sorted(person_counts.items()):
        bar = "█" * min(count, 50)
        print(f"  {person:20s} : {count:3d} {bar}")

    print("\n" + "="*70)


def train_model(dataset_path: str = "dataset/raw",
               output_path: str = "models/faces_model.pkl"):
    """
    Función principal de entrenamiento

    Args:
        dataset_path: Directorio con fotos de entrenamiento
        output_path: Donde guardar el modelo

    Returns:
        True si el entrenamiento fue exitoso
    """
    print("\n" + "="*70)
    print("  ENTRENAMIENTO DE MODELO DE RECONOCIMIENTO FACIAL")
    print("="*70)

    # Cargar datos
    encodings, names = load_training_data(dataset_path)

    if encodings is None or len(encodings) == 0:
        print("\n[ERROR] No se pudieron cargar datos de entrenamiento")
        return False

    # Mostrar resumen
    show_summary(encodings, names)

    # Guardar modelo
    print("\n[INFO] Guardando modelo...")
    success = save_model(encodings, names, output_path)

    if success:
        print("\n" + "="*70)
        print("  ✅ ENTRENAMIENTO COMPLETADO")
        print("="*70)
        print(f"\n[INFO] Modelo guardado en: {output_path}")
        print(f"[INFO] Total de muestras: {len(encodings)}")
        print(f"[INFO] Personas registradas: {len(set(names))}")
        print("\n[INFO] Siguiente paso: Probar el reconocimiento")
        print("  Ejecuta: python3 app.py")
        print("="*70 + "\n")
        return True
    else:
        return False


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Entrena modelo de reconocimiento facial"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="dataset/raw",
        help="Directorio con fotos de entrenamiento (default: dataset/raw)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/faces_model.pkl",
        help="Archivo de salida del modelo (default: models/faces_model.pkl)"
    )

    args = parser.parse_args()

    # Verificar que face_recognition está instalado
    try:
        import face_recognition
        print("[OK] face_recognition detectado")
    except ImportError:
        print("\n[ERROR] face_recognition no está instalado")
        print("\nInstala con:")
        print("  pip3 install face_recognition")
        print("\nEn Raspberry Pi puede tardar varios minutos")
        return 1

    # Entrenar
    success = train_model(
        dataset_path=args.dataset,
        output_path=args.output
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
