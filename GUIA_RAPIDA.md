# Guía Rápida de Uso

## Inicio rápido

```bash
# 1. Instalar
bash install.sh

# 2. Configurar cámara (si tienes 3 FPS)
bash setup_camera.sh

# 3. Ejecutar
python3 app.py
```

## Modos de operación

### Modo Rápido (por defecto) - 60+ FPS

- **Sin detección facial**
- Máximo rendimiento
- Latencia mínima
- Ideal para streaming en tiempo real

### Modo con Detección - 25-30 FPS

- **Con detección facial**
- Dibuja rectángulos en rostros
- Muestra "ROSTRO" sobre caras detectadas
- Usa más CPU

## Cambiar entre modos

### Desde la interfaz web

1. Abre http://TU_IP:5000
2. Haz clic en "👤 Activar Detección"
3. El botón cambia a "🚫 Desactivar Detección" (rojo)
4. Haz clic de nuevo para desactivar

### Desde API REST

```bash
# Activar detección
curl -X POST http://localhost:5000/set_detection/1

# Desactivar detección
curl -X POST http://localhost:5000/set_detection/0

# Toggle (alternar)
curl -X POST http://localhost:5000/toggle_detection
```

### Verificar estado

```bash
curl http://localhost:5000/status
```

Respuesta:
```json
{
  "camera_active": true,
  "is_capturing": true,
  "fps": 62.3,
  "face_detected": false,
  "total_frames": 15234,
  "detection_enabled": false
}
```

## Solución de problemas

### Solo obtengo 3 FPS

**Causa**: Tu cámara está usando formato YUYV en lugar de MJPEG.

**Solución**:
```bash
bash setup_camera.sh
# Selecciona opción 1: MJPEG 320x240 @ 30 FPS
```

### La imagen tiene delay/retraso

**Causa**: Buffer de la cámara acumulando frames viejos.

**Solución**: El código ya incluye optimizaciones automáticas. Si persiste:
```bash
python3 diagnose_camera.py
```

### No detecta la cámara

**Fedora**:
```bash
sudo usermod -aG video $USER
# Cierra sesión y vuelve a entrar
```

**Raspberry Pi**:
```bash
ls -l /dev/video*
# Verifica que la cámara USB esté conectada
```

### FPS bajos con detección activada

**Normal**: La detección facial consume CPU. Si tienes menos de 20 FPS:
- Usa resolución 320x240 (ya configurada por defecto)
- Verifica que estés usando MJPEG
- Desactiva la detección si solo necesitas streaming

## Endpoints disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Interfaz web principal |
| `/video_feed` | GET | Stream MJPEG directo |
| `/status` | GET | Estado del sistema (JSON) |
| `/stats` | GET | Estadísticas HTML |
| `/toggle_detection` | POST | Alternar detección |
| `/set_detection/1` | POST | Activar detección |
| `/set_detection/0` | POST | Desactivar detección |

## Acceso remoto

### Desde la misma red

```
http://IP_DEL_RASPBERRY:5000
```

Ejemplo: `http://192.168.1.100:5000`

### Ver tu IP

```bash
hostname -I
```

### Desde otro dispositivo

1. Asegúrate de estar en la misma red WiFi
2. Abre un navegador en tu teléfono/tablet/PC
3. Navega a `http://IP_DEL_RASPBERRY:5000`

## Integración con otros sistemas

### Python

```python
import requests
import cv2
import numpy as np

# Obtener un frame
response = requests.get('http://192.168.1.100:5000/video_feed', stream=True)

# Leer frames
for chunk in response.iter_content(chunk_size=1024):
    # Procesar frame...
    pass
```

### Node.js

```javascript
const fetch = require('node-fetch');

// Obtener estado
fetch('http://192.168.1.100:5000/status')
  .then(res => res.json())
  .then(data => {
    console.log(`FPS: ${data.fps}`);
    console.log(`Detección: ${data.detection_enabled}`);
  });

// Activar detección
fetch('http://192.168.1.100:5000/set_detection/1', { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(data.message));
```

### curl

```bash
# Ver estadísticas
curl -s http://localhost:5000/status | jq .

# Activar detección y ver resultado
curl -s -X POST http://localhost:5000/toggle_detection | jq .

# Loop de monitoreo
while true; do
    curl -s http://localhost:5000/status | jq '{fps: .fps, detection: .detection_enabled}'
    sleep 1
done
```

## Performance esperado

| Configuración | FPS | Latencia | CPU |
|---------------|-----|----------|-----|
| 320x240 MJPEG sin detección | 60+ | <50ms | ~30% |
| 320x240 MJPEG con detección | 25-30 | <80ms | ~70% |
| 640x480 MJPEG sin detección | 45-60 | <60ms | ~40% |
| 640x480 MJPEG con detección | 15-25 | <100ms | ~90% |
| 320x240 YUYV | 15-20 | <100ms | ~50% |

*Basado en Raspberry Pi 3 Model B*

## Scripts útiles

| Script | Uso |
|--------|-----|
| `install.sh` | Instalar dependencias |
| `setup_camera.sh` | Configurar formato de cámara |
| `setup_wifi.sh` | Configurar WiFi 2.4 GHz (RPi) |
| `diagnose_camera.py` | Diagnosticar problemas de FPS |

## Logs y debug

Ver FPS en tiempo real:
```
[FPS] 62.3 fps | Rostros: 0 | Proc: 8.2ms
[FPS] 28.5 fps | Rostros: 1 | Proc: 24.3ms
```

- **fps**: FPS reales alcanzados
- **Rostros**: Número de caras detectadas (0 si detección desactivada)
- **Proc**: Tiempo de procesamiento por frame en milisegundos

## Optimizaciones aplicadas

El sistema incluye automáticamente:

1. **Buffer mínimo** (BUFFERSIZE=1)
2. **Formato MJPEG** prioritario
3. **Backend V4L2** para Linux
4. **Descarte agresivo de buffer** en modo rápido
5. **Detección espaciada** (cada 3 frames) cuando está activa
6. **Codificación JPEG optimizada** (calidad 30 sin detección, 50 con detección)

## FAQ

**¿Puedo usar 1080p?**
- En Raspberry Pi 3: No recomendado, FPS muy bajos
- En PC/Laptop con CPU potente: Sí, pero modifica la resolución en el código

**¿Funciona con cámara USB barata?**
- Sí, pero verifica que soporte MJPEG. Si solo tiene YUYV, usa 320x240 máximo.

**¿Puedo detectar más cosas además de rostros?**
- Sí, OpenCV incluye otros clasificadores (ojos, sonrisas, cuerpo completo, etc.)

**¿Cómo grabo el stream?**
```bash
ffmpeg -i http://localhost:5000/video_feed -c copy output.mp4
```

**¿Puedo usar múltiples cámaras?**
- El código actual soporta una cámara. Para múltiples cámaras, necesitas modificar app.py para crear múltiples streams.

## Soporte

- Documentación completa: [README.md](README.md)
- Solución 3 FPS: [SOLUCION_3FPS.md](SOLUCION_3FPS.md)
- Optimización: [OPTIMIZACION.md](OPTIMIZACION.md)
