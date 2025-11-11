#!/usr/bin/env python3
"""
Script para capturar fotos de rostros para entrenamiento
Captura múltiples fotos de una persona desde la webcam
"""

import cv2
import os
import sys
import time
from datetime import datetime


def find_available_cameras():
    """Busca cámaras disponibles"""
    available = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available


def setup_camera(camera_id=0):
    """Configura la cámara para captura"""
    print(f"\n[INFO] Abriendo cámara {camera_id}...")

    # Probar backends
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_ANY, "ANY"),
        (None, "Default")
    ]

    camera = None
    for backend, name in backends:
        if backend is None:
            camera = cv2.VideoCapture(camera_id)
        else:
            camera = cv2.VideoCapture(camera_id, backend)

        if camera.isOpened():
            print(f"[OK] Cámara abierta con backend: {name}")
            break
        else:
            if camera:
                camera.release()
            camera = None

    if not camera or not camera.isOpened():
        return None

    # Configurar resolución
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Limpiar buffer inicial
    for _ in range(5):
        camera.read()

    return camera


def capture_training_photos(person_name: str,
                           num_photos: int = 20,
                           camera_id: int = 0,
                           output_dir: str = "dataset/raw"):
    """
    Captura fotos de una persona para entrenamiento

    Args:
        person_name: Nombre de la persona
        num_photos: Número de fotos a capturar
        camera_id: ID de la cámara a usar
        output_dir: Directorio donde guardar las fotos
    """

    # Validar nombre
    if not person_name or person_name.strip() == "":
        print("[ERROR] Debes proporcionar un nombre válido")
        return False

    person_name = person_name.strip().replace(" ", "_")

    # Crear directorio para la persona
    person_dir = os.path.join(output_dir, person_name)
    os.makedirs(person_dir, exist_ok=True)

    print("\n" + "="*70)
    print(f"  CAPTURA DE FOTOS - {person_name.upper()}")
    print("="*70)

    # Configurar cámara
    camera = setup_camera(camera_id)
    if not camera:
        print(f"\n[ERROR] No se pudo abrir la cámara {camera_id}")
        return False

    print(f"\n[INFO] Se capturarán {num_photos} fotos")
    print("\n[INSTRUCCIONES]")
    print("  • Posiciona tu rostro frente a la cámara")
    print("  • Mantén buena iluminación")
    print("  • Varía ligeramente la posición entre fotos:")
    print("    - Gira un poco la cabeza")
    print("    - Cambia expresiones faciales")
    print("    - Muévete ligeramente")
    print("\n  Presiona ESPACIO para capturar foto")
    print("  Presiona ESC para cancelar")
    print("\n" + "-"*70)

    captured = 0
    countdown_active = False
    countdown_start = 0

    # Cargar clasificador Haar para mostrar detección
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    try:
        while captured < num_photos:
            ret, frame = camera.read()
            if not ret:
                print("[ERROR] No se pudo leer frame")
                break

            # Detectar rostros para feedback visual
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))

            # Dibujar rectángulos en rostros
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Rostro detectado", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Mostrar contador
            info_text = f"Fotos capturadas: {captured}/{num_photos}"
            cv2.putText(frame, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Mostrar instrucciones
            if len(faces) == 0:
                cv2.putText(frame, "No se detecta rostro", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Presiona ESPACIO", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Countdown visual si está activo
            if countdown_active:
                elapsed = time.time() - countdown_start
                remaining = max(0, 3 - int(elapsed))

                if remaining > 0:
                    cv2.putText(frame, str(remaining),
                               (frame.shape[1]//2 - 50, frame.shape[0]//2),
                               cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 0), 8)
                else:
                    countdown_active = False

            cv2.imshow('Captura de Fotos', frame)

            key = cv2.waitKey(1) & 0xFF

            # ESC - Cancelar
            if key == 27:
                print("\n[INFO] Captura cancelada por el usuario")
                break

            # ESPACIO - Capturar foto
            elif key == 32 and len(faces) > 0:
                # Guardar foto
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{person_name}_{captured+1:03d}_{timestamp}.jpg"
                filepath = os.path.join(person_dir, filename)

                cv2.imwrite(filepath, frame)
                captured += 1

                print(f"[OK] Foto {captured}/{num_photos} guardada: {filename}")

                # Feedback visual
                countdown_active = True
                countdown_start = time.time()

                # Pausa breve
                time.sleep(0.3)

    except KeyboardInterrupt:
        print("\n[INFO] Captura interrumpida")

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print("\n" + "="*70)
    if captured >= num_photos:
        print(f"  ✅ CAPTURA COMPLETADA")
        print(f"  {captured} fotos guardadas en: {person_dir}")
        print("\n  Siguiente paso: Entrenar el modelo")
        print("  Ejecuta: python3 scripts/train_model.py")
    else:
        print(f"  ⚠️  CAPTURA INCOMPLETA")
        print(f"  {captured}/{num_photos} fotos capturadas")
        print(f"  Fotos guardadas en: {person_dir}")
    print("="*70 + "\n")

    return captured >= num_photos


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("  SISTEMA DE CAPTURA DE FOTOS PARA ENTRENAMIENTO")
    print("="*70)

    # Buscar cámaras
    print("\n[INFO] Buscando cámaras disponibles...")
    cameras = find_available_cameras()

    if not cameras:
        print("\n[ERROR] No se encontraron cámaras")
        print("\nVerifica:")
        print("  • La cámara está conectada")
        print("  • Tienes permisos (grupo video)")
        print("  • Ejecuta: ls -l /dev/video*")
        return 1

    print(f"[OK] Cámaras disponibles: {cameras}")

    # Seleccionar cámara
    camera_id = cameras[0]
    if len(cameras) > 1:
        print(f"\n[INFO] Cámaras disponibles: {cameras}")
        try:
            camera_id = int(input(f"Selecciona cámara (Enter = {cameras[0]}): ") or cameras[0])
            if camera_id not in cameras:
                print(f"[WARNING] Cámara {camera_id} no disponible, usando {cameras[0]}")
                camera_id = cameras[0]
        except ValueError:
            print(f"[WARNING] Entrada inválida, usando cámara {cameras[0]}")

    # Solicitar nombre
    print("\n" + "-"*70)
    person_name = input("Ingresa el NOMBRE de la persona: ").strip()

    if not person_name:
        print("[ERROR] Nombre vacío")
        return 1

    # Solicitar número de fotos
    try:
        num_photos = int(input("Número de fotos a capturar (Enter = 20): ") or "20")
        if num_photos < 5:
            print("[WARNING] Se recomienda al menos 10 fotos")
        elif num_photos > 100:
            print("[WARNING] Muchas fotos pueden tardar mucho")
            num_photos = min(num_photos, 100)
    except ValueError:
        print("[INFO] Usando valor por defecto: 20 fotos")
        num_photos = 20

    # Capturar fotos
    success = capture_training_photos(
        person_name=person_name,
        num_photos=num_photos,
        camera_id=camera_id
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
