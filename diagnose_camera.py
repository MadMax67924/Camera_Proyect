#!/usr/bin/env python3
"""
Script de diagnóstico de cámara
Identifica problemas de FPS y latencia
"""

import cv2
import time
import sys

def test_camera(device_id=0):
    print("="*70)
    print("  DIAGNÓSTICO DE CÁMARA")
    print("="*70)
    print()

    # Probar backends
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_ANY, "ANY"),
        (None, "Default")
    ]

    for backend, name in backends:
        print(f"\n[TEST] Backend: {name}")
        print("-" * 50)

        try:
            if backend is None:
                cap = cv2.VideoCapture(device_id)
            else:
                cap = cv2.VideoCapture(device_id, backend)

            if not cap.isOpened():
                print(f"❌ No se pudo abrir la cámara con {name}")
                continue

            print(f"✅ Cámara abierta con {name}")

            # Configuraciones a probar
            resolutions = [(320, 240), (640, 480)]
            formats = [
                (cv2.VideoWriter_fourcc('M','J','P','G'), "MJPEG"),
                (cv2.VideoWriter_fourcc('Y','U','Y','V'), "YUYV"),
            ]

            for width, height in resolutions:
                print(f"\n  Resolución: {width}x{height}")

                for fourcc, fmt_name in formats:
                    # Configurar cámara
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_FOURCC, fourcc)

                    # Verificar configuración
                    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
                    buffer_size = int(cap.get(cv2.CAP_PROP_BUFFERSIZE))

                    print(f"    Formato: {fmt_name}")
                    print(f"      Config real: {actual_w}x{actual_h} @ {actual_fps} FPS (buffer: {buffer_size})")

                    # Descartar frames iniciales
                    for _ in range(5):
                        cap.read()

                    # Medir FPS real
                    fps_counter = 0
                    start_time = time.time()
                    latencies = []

                    for i in range(60):  # Capturar 60 frames
                        frame_start = time.time()
                        ret, frame = cap.read()
                        frame_time = time.time() - frame_start

                        if ret:
                            fps_counter += 1
                            latencies.append(frame_time * 1000)  # en ms

                    elapsed = time.time() - start_time
                    actual_fps_measured = fps_counter / elapsed
                    avg_latency = sum(latencies) / len(latencies) if latencies else 0
                    max_latency = max(latencies) if latencies else 0

                    print(f"      FPS medido: {actual_fps_measured:.1f}")
                    print(f"      Latencia promedio: {avg_latency:.1f}ms")
                    print(f"      Latencia máxima: {max_latency:.1f}ms")

                    # Evaluar resultados
                    if actual_fps_measured >= 25:
                        print(f"      ✅ BUENO - FPS adecuado")
                    elif actual_fps_measured >= 15:
                        print(f"      ⚠️  ACEPTABLE - FPS bajo")
                    else:
                        print(f"      ❌ MALO - FPS muy bajo")

                    if avg_latency < 40:
                        print(f"      ✅ BUENO - Latencia baja")
                    elif avg_latency < 100:
                        print(f"      ⚠️  ACEPTABLE - Latencia moderada")
                    else:
                        print(f"      ❌ MALO - Latencia alta (retraso notable)")

            cap.release()
            print()

        except Exception as e:
            print(f"❌ Error: {e}")

    print("="*70)
    print("  RECOMENDACIONES")
    print("="*70)
    print()
    print("Si tienes FPS bajos:")
    print("  1. Usa resolución 320x240 (más rápido)")
    print("  2. Usa formato MJPEG (más eficiente para USB)")
    print("  3. Usa backend V4L2 en Linux")
    print()
    print("Si tienes latencia alta:")
    print("  1. El buffer de la cámara puede estar acumulando frames viejos")
    print("  2. Intenta leer múltiples frames en cada iteración")
    print("  3. Verifica que BUFFERSIZE=1 sea respetado")
    print()
    print("En Fedora:")
    print("  - Verifica permisos: groups | grep video")
    print("  - Lista cámaras: v4l2-ctl --list-devices")
    print("  - Info detallada: v4l2-ctl -d /dev/video0 --all")
    print()

if __name__ == "__main__":
    camera_id = 0
    if len(sys.argv) > 1:
        camera_id = int(sys.argv[1])

    print(f"\nProbando /dev/video{camera_id}...\n")
    test_camera(camera_id)
