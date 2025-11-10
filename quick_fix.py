#!/usr/bin/env python3
"""
Script rápido para forzar configuración de cámara y probar FPS
"""

import cv2
import time

print("="*70)
print("  DIAGNÓSTICO Y CONFIGURACIÓN RÁPIDA")
print("="*70)
print()

# Abrir cámara
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

if not cap.isOpened():
    print("[ERROR] No se pudo abrir la cámara")
    exit(1)

print("[OK] Cámara abierta")
print()

# Mostrar configuración actual
print("Configuración ANTES de cambios:")
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
buffer_size = int(cap.get(cv2.CAP_PROP_BUFFERSIZE))

print(f"  Resolución: {w}x{h}")
print(f"  FPS: {fps}")
print(f"  Formato: {fourcc_str}")
print(f"  Buffer: {buffer_size}")
print()

# Probar diferentes configuraciones
configs = [
    # (width, height, fourcc, name)
    (320, 240, cv2.VideoWriter_fourcc('M','J','P','G'), "MJPEG 320x240"),
    (640, 480, cv2.VideoWriter_fourcc('M','J','P','G'), "MJPEG 640x480"),
    (320, 240, cv2.VideoWriter_fourcc('Y','U','Y','V'), "YUYV 320x240"),
    (640, 480, cv2.VideoWriter_fourcc('Y','U','Y','V'), "YUYV 640x480"),
]

print("Probando configuraciones:")
print("-" * 70)

best_config = None
best_fps = 0

for width, height, fourcc, name in configs:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Descartar frames iniciales
    for _ in range(5):
        cap.read()

    # Verificar configuración real
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Medir FPS
    start = time.time()
    count = 0
    times = []

    for i in range(30):
        t1 = time.time()
        ret, frame = cap.read()
        t2 = time.time()

        if ret:
            count += 1
            times.append((t2 - t1) * 1000)

    elapsed = time.time() - start
    measured_fps = count / elapsed if elapsed > 0 else 0
    avg_time = sum(times) / len(times) if times else 0

    print(f"\n{name}")
    print(f"  Pedido: {width}x{height}")
    print(f"  Real: {actual_w}x{actual_h}")
    print(f"  FPS medido: {measured_fps:.1f}")
    print(f"  Tiempo/frame: {avg_time:.1f}ms")

    # Evaluar
    if measured_fps > best_fps and abs(actual_w - width) < 50:
        best_fps = measured_fps
        best_config = (width, height, fourcc, name, actual_w, actual_h)

cap.release()

print()
print("="*70)
print("  RESULTADO")
print("="*70)
print()

if best_config:
    width, height, fourcc, name, actual_w, actual_h = best_config
    print(f"✅ MEJOR CONFIGURACIÓN: {name}")
    print(f"   Resolución pedida: {width}x{height}")
    print(f"   Resolución real: {actual_w}x{actual_h}")
    print(f"   FPS alcanzado: {best_fps:.1f}")
    print()

    # Código para app.py
    fourcc_code = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    print("Código para app.py:")
    print()
    print(f"    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, {width})")
    print(f"    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, {height})")
    print(f"    self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('{fourcc_code[0]}','{fourcc_code[1]}','{fourcc_code[2]}','{fourcc_code[3]}'))")
    print()

    if best_fps < 15:
        print("⚠️  FPS bajo detectado")
        print("   Posibles causas:")
        print("   1. Cámara solo soporta YUYV (sin compresión)")
        print("   2. Resolución demasiado alta")
        print("   3. Ancho de banda USB limitado")
        print()
        print("   Recomendaciones:")
        print("   - Usa la resolución más baja posible (320x240 o menor)")
        print("   - Si la cámara soporta MJPEG, úsalo en lugar de YUYV")
        print("   - Verifica que esté conectada a un puerto USB 2.0 o superior")
else:
    print("❌ No se pudo encontrar una configuración funcional")

print()
print("="*70)
