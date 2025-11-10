# Solución al problema de 3 FPS

## ¿Por qué solo 3 FPS?

Si estás obteniendo solo 3 FPS, hay varias causas posibles:

### 1. Formato YUYV en lugar de MJPEG

**Causa más común**: La cámara está usando formato YUYV sin comprimir en lugar de MJPEG.

#### Verificar formato actual

```bash
v4l2-ctl -d /dev/video0 --get-fmt-video
```

Si ves `YUYV` en lugar de `MJPG`, ese es tu problema.

#### Solución

```bash
# Forzar formato MJPEG
v4l2-ctl -d /dev/video0 --set-fmt-video=width=320,height=240,pixelformat=MJPG
```

### 2. Resolución demasiado alta

Si la cámara está capturando en resolución alta (640x480 o mayor) con YUYV, el ancho de banda USB no es suficiente.

#### Solución

```bash
# Reducir resolución
v4l2-ctl -d /dev/video0 --set-fmt-video=width=320,height=240
```

### 3. USB 2.0 vs USB 3.0

- **USB 2.0**: Máximo ~35 MB/s
- **YUYV 640x480@30fps**: ~37 MB/s (NO CABE en USB 2.0)
- **MJPEG 640x480@30fps**: ~5-10 MB/s (SÍ CABE)

#### Verificar conexión USB

```bash
lsusb -t
```

Busca tu cámara y verifica si dice "480M" (USB 2.0) o "5000M" (USB 3.0).

### 4. Backend incorrecto

Algunos backends de OpenCV no configuran correctamente el formato.

#### En el código

El código ya prioriza V4L2:
```python
backends = [
    (cv2.CAP_V4L2, "V4L2"),  # Mejor para Linux
    (cv2.CAP_ANY, "ANY"),
    (None, "Default")
]
```

### 5. La cámara no soporta MJPEG

Algunas cámaras baratas solo soportan YUYV.

#### Verificar formatos soportados

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

Busca si `MJPG` aparece en la lista.

## Pasos de diagnóstico

### Paso 1: Ejecutar diagnóstico

```bash
python3 diagnose_camera.py
```

Esto probará todos los formatos y te dirá cuál funciona mejor.

### Paso 2: Verificar formato actual

```bash
v4l2-ctl -d /dev/video0 --all | grep -A5 "Video Capture"
```

### Paso 3: Listar formatos disponibles

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

### Paso 4: Forzar MJPEG + resolución baja

```bash
# Resetear dispositivo
sudo rmmod uvcvideo
sudo modprobe uvcvideo

# Configurar formato
v4l2-ctl -d /dev/video0 --set-fmt-video=width=320,height=240,pixelformat=MJPG

# Verificar
v4l2-ctl -d /dev/video0 --get-fmt-video
```

### Paso 5: Ejecutar app y verificar

```bash
python3 app.py
```

Observa la salida:
```
[OK] Cámara configurada: 320x240 @ 30 FPS (buffer: 1)
```

Y luego los FPS reales:
```
[FPS] 28.5 fps | Rostros: 0 | Proc: 15.2ms
```

## Cálculo de ancho de banda

### YUYV (sin comprimir)

```
Tamaño = width × height × 2 bytes
320x240 = 153,600 bytes/frame = 150 KB/frame
@ 30 FPS = 4.5 MB/s ✅ CABE en USB 2.0

640x480 = 614,400 bytes/frame = 600 KB/frame
@ 30 FPS = 18 MB/s ✅ CABE en USB 2.0 (justo)

1280x720 = 1,843,200 bytes/frame = 1.8 MB/frame
@ 30 FPS = 54 MB/s ❌ NO CABE en USB 2.0
```

### MJPEG (comprimido)

```
Calidad 50: ~10-20% del tamaño YUYV
320x240 @ 30 FPS = ~1-2 MB/s ✅✅ MUY EFICIENTE
640x480 @ 30 FPS = ~3-6 MB/s ✅✅ MUY EFICIENTE
1280x720 @ 30 FPS = ~8-15 MB/s ✅ CABE cómodamente
```

## Soluciones específicas por cámara

### Logitech C270, C310, C920

Estas cámaras soportan MJPEG nativamente:

```bash
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=MJPG
```

Deberías obtener 30 FPS sin problemas.

### Cámaras genéricas USB (sin marca)

Muchas solo soportan YUYV. Solución:

1. Usar resolución 320x240 máximo
2. Aceptar ~15-20 FPS máximo con YUYV
3. O cambiar a una cámara mejor con MJPEG

### Cámara integrada de laptop

La mayoría soporta MJPEG. Si no:

```bash
# Probar diferentes resoluciones
v4l2-ctl -d /dev/video0 --list-formats-ext

# Usar la resolución más baja que soporte MJPEG
v4l2-ctl -d /dev/video0 --set-fmt-video=width=320,height=240,pixelformat=MJPG
```

## Configuración óptima por plataforma

### Raspberry Pi 3

```bash
# Máxima velocidad sin detección
Resolución: 320x240
Formato: MJPEG
FPS esperado: 60+ FPS

# Con detección facial
Resolución: 320x240
Formato: MJPEG
FPS esperado: 25-30 FPS
```

### Fedora/Laptop

```bash
# Máxima velocidad sin detección
Resolución: 640x480
Formato: MJPEG
FPS esperado: 60+ FPS

# Con detección facial
Resolución: 320x240
Formato: MJPEG
FPS esperado: 30-45 FPS
```

## Script de configuración rápida

```bash
#!/bin/bash
# Configurar cámara para máximo FPS

DEVICE="/dev/video0"

echo "Configurando cámara para máximo rendimiento..."

# Resetear dispositivo
sudo rmmod uvcvideo 2>/dev/null
sudo modprobe uvcvideo

# Esperar que se reconozca
sleep 2

# Configurar MJPEG + resolución baja
v4l2-ctl -d $DEVICE --set-fmt-video=width=320,height=240,pixelformat=MJPG

# Configurar FPS
v4l2-ctl -d $DEVICE --set-parm=30

# Verificar configuración
echo ""
echo "Configuración actual:"
v4l2-ctl -d $DEVICE --get-fmt-video
v4l2-ctl -d $DEVICE --get-parm

echo ""
echo "Ejecuta: python3 app.py"
```

Guarda como `setup_camera.sh` y ejecuta:

```bash
chmod +x setup_camera.sh
sudo ./setup_camera.sh
```

## Verificación final

Después de configurar, deberías ver:

```
[INFO] Configurando cámara /dev/video0...
[INFO] Probando backend: V4L2
[OK] Cámara abierta con backend: V4L2
[INFO] Limpiando buffer inicial...
[OK] Cámara configurada: 320x240 @ 30 FPS (buffer: 1)
```

Y luego:

```
[FPS] 60.2 fps | Rostros: 0 | Proc: 8.5ms  <- SIN detección
[FPS] 28.7 fps | Rostros: 1 | Proc: 22.3ms <- CON detección
```

## Si nada funciona

1. **Probar con otra cámara** que soporte MJPEG nativamente
2. **Actualizar drivers**:
   ```bash
   sudo dnf update  # Fedora
   sudo apt-get update && sudo apt-get upgrade  # Raspberry Pi
   ```
3. **Verificar que no hay otros procesos usando la cámara**:
   ```bash
   lsof /dev/video0
   ```
4. **Reiniciar el sistema** después de actualizar drivers

## Resumen

- **3 FPS** = Probablemente YUYV a resolución alta
- **15-20 FPS** = YUYV a resolución baja (320x240)
- **30 FPS** = MJPEG a 320x240 (con detección)
- **60+ FPS** = MJPEG a 320x240 (sin detección)

La clave es **usar MJPEG** en lugar de YUYV.
