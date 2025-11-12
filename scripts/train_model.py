#!/usr/bin/env python3
"""
Script para entrenar modelo de reconocimiento facial - SIN DLIB
Lee fotos del directorio dataset/raw/ y genera modelo entrenado
Usa core.face_recognition_lite en lugar de face_recognition (dlib)
"""

import os
import sys
import pickle
from pathlib import Path
import cv2
from tqdm import tqdm

# Importar el reconocedor sin dlib
try:
    from core.face_recognition_lite import FaceRecognizerLite
except ImportError:
    print("[ERROR] No se pudo importar FaceRecognizerLite")
    print("[INFO] Asegúrate de que core/face_recognition_lite.py existe")
    sys.exit(1)


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
    print("  ENTRENAMIENTO SIN DLIB - Cargando datos")
    print("="*70)
    print(f"\n[INFO] Directorio: {dataset_path}")
    print(f"[INFO] Personas encontradas: {len(person_dirs)}\n")

    total_images = 0
    failed_images = 0

    # Inicializar reconocedor (para extractor de características)
    recognizer = FaceRecognizerLite()

    # Procesar cada persona
    for person_dir in sorted(person_dirs):
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
                # Cargar imagen con OpenCV
                image = cv2.imread(str(image_path))

                if image is None:
                    print(f"\n  [WARNING] No se pudo cargar: {image_path.name}")
                    failed_images += 1
                    continue

                # Detectar rostros con MediaPipe
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = recognizer.face_detector.process(rgb_image)

                if not results.detections:
                    print(f"\n  [WARNING] No se detectó rostro en: {image_path.name}")
                    failed_images += 1
                    continue

                if len(results.detections) > 1:
                    print(f"\n  [WARNING] Múltiples rostros en: {image_path.name} (usando el primero)")

                # Extraer primer rostro
                detection = results.detections[0]
                bbox = detection.location_data.relative_bounding_box

                h, w = rgb_image.shape[:2]
                left = int(bbox.xmin * w)
                top = int(bbox.ymin * h)
                right = int((bbox.xmin + bbox.width) * w)
                bottom = int((bbox.ymin + bbox.height) * h)

                # Asegurar límites
                left = max(0, left)
                top = max(0, top)
                right = min(w, right)
                bottom = min(h, bottom)

                if right <= left or bottom <= top:
                    print(f"\n  [WARNING] Bbox inválido en: {image_path.name}")
                    failed_images += 1
                    continue

                # Extraer región del rostro
                face_image = image[top:bottom, left:right]

                # Extraer características
                encoding = recognizer.extract_features(face_image)

                if encoding is not None and len(encoding) > 0:
                    encodings.append(encoding)
                    names.append(person_name)
                    total_images += 1
                else:
                    print(f"\n  [WARNING] No se pudo extraer encoding de: {image_path.name}")
                    failed_images += 1

            except Exception as e:
                print(f"\n  [WARNING] Error procesando {image_path.name}: {e}")
                failed_images += 1
                continue

        print(f"  ✓ {person_name}: {sum(1 for n in names if n == person_name)} rostros extraídos")

    return encodings, names


def train_model(encodings, names, output_path: str = "models/faces_model.pkl"):
    """
    Entrena y guarda el modelo

    Args:
        encodings: Lista de encodings (características)
        names: Lista de nombres correspondientes
        output_path: Ruta donde guardar el modelo
    """
    if not encodings or not names:
        print("[ERROR] No hay datos para entrenar")
        return False

    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Preparar datos
        data = {
            'encodings': encodings,
            'names': names
        }

        # Guardar modelo
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)

        print(f"\n[OK] Modelo guardado: {output_path}")
        print(f"[OK] Total: {len(encodings)} rostros de {len(set(names))} personas")
        return True

    except Exception as e:
        print(f"[ERROR] No se pudo guardar el modelo: {e}")
        return False


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("  ENTRENADOR DE RECONOCIMIENTO FACIAL - SIN DLIB")
    print("="*70)

    # Cargar datos
    encodings, names = load_training_data("dataset/raw")

    if encodings is None:
        print("\n[ERROR] No se pudieron cargar los datos")
        return False

    print(f"\n[OK] Datos cargados correctamente")
    print(f"    - Total rostros: {len(encodings)}")
    print(f"    - Personas únicas: {len(set(names))}")

    # Entrenar
    success = train_model(encodings, names)

    if success:
        print("\n" + "="*70)
        print("  ✓ ENTRENAMIENTO COMPLETADO")
        print("="*70)
        print("\n[INFO] Ya puedes usar el modelo en app.py")
        print("[INFO] El modelo está optimizado sin dlib - instalación rápida!")
        return True
    else:
        print("\n[ERROR] El entrenamiento falló")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
