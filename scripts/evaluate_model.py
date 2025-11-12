#!/usr/bin/env python3
"""
Script de evaluación del modelo entrenado
Permite probar el reconocimiento con imágenes de prueba
"""

import cv2
import sys
import os
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.face_recognition_lite import FaceRecognizerLite


def evaluate_single_image(image_path: str, model_path: str = "models/faces_model_lite.pkl"):
    """
    Evalúa una sola imagen
    """
    print(f"\n[*] Evaluando imagen: {image_path}")

    # Cargar reconocedor
    recognizer = FaceRecognizerLite(model_path=model_path)

    if not recognizer.is_lite_model and not recognizer.known_face_encodings:
        print("[ERROR] No hay modelo cargado")
        return

    # Leer imagen
    img = cv2.imread(image_path)
    if img is None:
        print(f"[ERROR] No se pudo leer la imagen: {image_path}")
        return

    print(f"[*] Tamaño de imagen: {img.shape[1]}x{img.shape[0]}")

    # Reconocer rostros
    faces = recognizer.recognize_faces(img, scale_factor=1.0)

    if not faces:
        print("[!] No se detectaron rostros en la imagen")
        return

    print(f"\n[OK] Detectados {len(faces)} rostro(s):\n")

    for i, face in enumerate(faces, 1):
        print(f"  Rostro #{i}:")
        print(f"    Nombre: {face['name']}")
        print(f"    Confianza: {face['confidence']*100:.1f}%")
        print(f"    Distancia: {face['distance']:.4f}")
        print(f"    Ubicación: {face['box']}")
        print()

    # Dibujar y mostrar
    img_annotated = recognizer.draw_faces(img, faces, show_confidence=True)

    # Mostrar imagen
    cv2.imshow("Evaluación - Presiona cualquier tecla para cerrar", img_annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def evaluate_webcam(model_path: str = "models/faces_model_lite.pkl", camera_id: int = 0):
    """
    Evalúa usando webcam en tiempo real
    """
    print(f"\n[*] Iniciando evaluación con cámara {camera_id}")
    print("[INFO] Presiona 'q' para salir")

    # Cargar reconocedor
    recognizer = FaceRecognizerLite(model_path=model_path)

    if not recognizer.is_lite_model and not recognizer.known_face_encodings:
        print("[ERROR] No hay modelo cargado")
        return

    # Abrir cámara
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir cámara {camera_id}")
        return

    print("[OK] Cámara iniciada correctamente")

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] No se pudo leer frame")
            break

        frame_count += 1

        # Reconocer cada 5 frames para mejor rendimiento
        if frame_count % 5 == 0:
            faces = recognizer.recognize_faces(frame, scale_factor=0.5)

            if faces:
                frame = recognizer.draw_faces(frame, faces, show_confidence=True)

                # Mostrar nombres en pantalla
                y_offset = 30
                for face in faces:
                    text = f"{face['name']} ({face['confidence']*100:.0f}%)"
                    cv2.putText(frame, text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    y_offset += 30

        # Mostrar FPS
        cv2.putText(frame, f"Frame: {frame_count}", (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Evaluación Webcam - Presiona 'q' para salir", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Evaluación finalizada")


def evaluate_directory(directory: str, model_path: str = "models/faces_model_lite.pkl"):
    """
    Evalúa todas las imágenes de un directorio
    """
    print(f"\n[*] Evaluando directorio: {directory}")

    # Cargar reconocedor
    recognizer = FaceRecognizerLite(model_path=model_path)

    if not recognizer.is_lite_model and not recognizer.known_face_encodings:
        print("[ERROR] No hay modelo cargado")
        return

    # Obtener imágenes
    dir_path = Path(directory)
    image_files = list(dir_path.glob("*.jpg")) + \
                 list(dir_path.glob("*.png")) + \
                 list(dir_path.glob("*.jpeg"))

    if not image_files:
        print(f"[ERROR] No se encontraron imágenes en {directory}")
        return

    print(f"[*] Encontradas {len(image_files)} imágenes")

    results = {
        'total': len(image_files),
        'with_faces': 0,
        'without_faces': 0,
        'recognized': {},
        'unknown': 0
    }

    for img_path in image_files:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        faces = recognizer.recognize_faces(img, scale_factor=1.0)

        if faces:
            results['with_faces'] += 1
            for face in faces:
                name = face['name']
                if name == "Desconocido":
                    results['unknown'] += 1
                else:
                    results['recognized'][name] = results['recognized'].get(name, 0) + 1
        else:
            results['without_faces'] += 1

    # Mostrar resultados
    print("\n" + "="*60)
    print("RESULTADOS DE EVALUACIÓN")
    print("="*60)
    print(f"Total de imágenes: {results['total']}")
    print(f"Con rostros detectados: {results['with_faces']}")
    print(f"Sin rostros: {results['without_faces']}")
    print(f"Desconocidos: {results['unknown']}")
    print("\nPersonas reconocidas:")
    for name, count in sorted(results['recognized'].items()):
        print(f"  {name}: {count} veces")
    print("="*60)


def main():
    """Función principal"""

    if len(sys.argv) < 2:
        print("\n" + "="*60)
        print("EVALUADOR DE MODELO FACIAL")
        print("="*60)
        print("\nUso:")
        print("  python3 scripts/evaluate_model.py <modo> [opciones]")
        print("\nModos:")
        print("  image <ruta>       - Evaluar una imagen")
        print("  webcam [id]        - Evaluar con webcam (id=0 por defecto)")
        print("  directory <ruta>   - Evaluar directorio de imágenes")
        print("\nEjemplos:")
        print("  python3 scripts/evaluate_model.py image dataset/raw/FotosPablo/foto1.jpg")
        print("  python3 scripts/evaluate_model.py webcam")
        print("  python3 scripts/evaluate_model.py webcam 1")
        print("  python3 scripts/evaluate_model.py directory dataset/raw/FotosPablo")
        print("="*60)
        return

    mode = sys.argv[1]

    if mode == "image":
        if len(sys.argv) < 3:
            print("[ERROR] Falta la ruta de la imagen")
            return
        evaluate_single_image(sys.argv[2])

    elif mode == "webcam":
        camera_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        evaluate_webcam(camera_id=camera_id)

    elif mode == "directory":
        if len(sys.argv) < 3:
            print("[ERROR] Falta la ruta del directorio")
            return
        evaluate_directory(sys.argv[2])

    else:
        print(f"[ERROR] Modo desconocido: {mode}")
        print("[INFO] Modos válidos: image, webcam, directory")


if __name__ == "__main__":
    main()
