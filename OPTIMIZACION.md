# Guía de Optimización de FPS y Latencia

## Problema común: Buffer de la cámara

El problema más frecuente de FPS bajos y delay en la imagen es el **buffer interno de la cámara**.

### ¿Qué es el buffer de la cámara?

Las cámaras USB mantienen un buffer (cola) de frames capturados. Si tu aplicación no los consume lo suficientemente rápido, los frames se acumulan en el buffer y obtienes frames "viejos" con retraso.

### Síntomas

- ✅ FPS reportado es bueno (25-30 FPS)
- ❌ Pero la imagen se ve retrasada al mover la mano
- ❌ Delay notable entre el movimiento real y lo que ves

## Soluciones implementadas

### 1. BUFFERSIZE mínimo

```python
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
```

**Problema**: No todos los backends/drivers respetan esta configuración.

### 2. Fast Read (descarte de buffer)

```python
# Leer frame principal
ret, frame = camera.read()

# Si el procesamiento fue rápido, leer otro frame
# Esto descarta el frame viejo del buffer
if last_process_time < 0.025:  # 25ms
    ret_new, frame_new = camera.read()
    if ret_new:
        frame = frame_new  # Usar el más reciente
```

**Ventaja**: Funciona incluso si el driver no respeta BUFFERSIZE.

### 3. Formato MJPEG

```python
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
```

MJPEG es más eficiente para cámaras USB porque los frames ya vienen comprimidos en JPEG.

### 4. Backend V4L2

En Linux, V4L2 (Video4Linux2) es el backend más eficiente:

```python
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
```

### 5. Detección facial espaciada

```python
# Solo detectar rostros cada 3 frames
if frame_counter % 3 == 0:
    faces = detect_faces(frame)
```

Reduce carga de CPU sin sacrificar mucho la experiencia.

## Diagnóstico

### Ejecutar script de diagnóstico

```bash
python3 diagnose_camera.py
```

Esto te dirá:
- Qué backend funciona mejor
- Qué formato da mejor FPS
- Cuál es la latencia real

### Comandos útiles

```bash
# Ver información de la cámara
v4l2-ctl -d /dev/video0 --all

# Ver formatos soportados
v4l2-ctl -d /dev/video0 --list-formats-ext

# Ver qué formato está usando actualmente
v4l2-ctl -d /dev/video0 --get-fmt-video

# Establecer formato manualmente (prueba)
v4l2-ctl -d /dev/video0 --set-fmt-video=width=320,height=240,pixelformat=MJPG
```

## Comparación de formatos

| Formato | Pros | Contras | FPS típico |
|---------|------|---------|------------|
| MJPEG   | - Comprimido en cámara<br>- Menor ancho de banda USB<br>- Más rápido | - Menor calidad<br>- No todas las cámaras lo soportan | 25-30 FPS |
| YUYV    | - Mayor calidad<br>- Soportado universalmente | - Sin comprimir<br>- Más ancho de banda<br>- Más lento | 10-20 FPS |

## Optimizaciones por plataforma

### Raspberry Pi 3

**CPU limitada** - Priorizar:
1. Resolución baja (320x240)
2. MJPEG si la cámara lo soporta
3. Detección facial espaciada (cada 3-5 frames)
4. Backend V4L2

### Fedora (PC/Laptop)

**CPU más potente** - Puedes:
1. Usar resolución mayor (640x480) si lo deseas
2. Detección facial en cada frame si la CPU lo soporta
3. Probar diferentes backends

## Mediciones de referencia

### Excelente
- FPS: 25-30
- Latencia: < 40ms
- Experiencia: Sin retraso perceptible

### Aceptable
- FPS: 15-24
- Latencia: 40-100ms
- Experiencia: Ligero retraso

### Pobre
- FPS: < 15
- Latencia: > 100ms
- Experiencia: Retraso muy notable

## Soluciones adicionales

### Si nada funciona

1. **Probar otra cámara USB**
   - Algunas cámaras tienen mejor soporte de drivers
   - Busca cámaras con "UVC" (USB Video Class)

2. **Actualizar drivers**
   ```bash
   # Fedora
   sudo dnf update

   # Raspberry Pi
   sudo apt-get update && sudo apt-get upgrade
   ```

3. **Modo agresivo de descarte**

   Puedes modificar el código para descartar más frames:
   ```python
   # En lugar de leer 1 frame adicional, leer 2-3
   for _ in range(2):
       ret_new, frame_new = camera.read()
       if ret_new:
           frame = frame_new
   ```

   **Trade-off**: Mayor FPS, pero mayor uso de CPU/USB.

## Preguntas frecuentes

### ¿Por qué v4l2-ctl muestra 30 FPS pero yo veo menos?

`v4l2-ctl` muestra la capacidad de la cámara, no el FPS real de tu aplicación. El FPS real depende de:
- Velocidad de procesamiento de tu código
- Ancho de banda USB disponible
- Carga de CPU del sistema

### ¿Debo usar resolución mayor?

**NO** si quieres 30 FPS en Raspberry Pi 3. La CPU no puede procesar 640x480 @ 30 FPS con detección facial.

En Fedora/PC más potentes, sí puedes usar 640x480.

### ¿Puedo desactivar la detección facial para más FPS?

Sí, comenta estas líneas en `app.py`:

```python
# Comentar esto:
# faces = detect_faces(frame)
# face_detected = len(faces) > 0

# Y esto:
# for (x, y, w, h) in faces:
#     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
```

Ganarás 5-10 FPS adicionales.

## Conclusión

El delay/latencia en la cámara es un problema común pero solucionable. Las optimizaciones implementadas en este proyecto deberían dar buenos resultados en la mayoría de cámaras USB estándar.

Si el problema persiste, ejecuta `diagnose_camera.py` y comparte los resultados para ayuda adicional.
