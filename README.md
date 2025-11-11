# 🎥 Sistema de Reconocimiento Facial - Raspberry Pi 3 y Fedora

Sistema completo de streaming de video con **detección y reconocimiento facial** en tiempo real, optimizado para Raspberry Pi 3 y compatible con Fedora/PC Linux.

## 🆕 Características Nuevas (ACTUALIZACIÓN)

- ✨ **Reconocimiento facial real** - Identifica personas específicas
- ✨ **Selección de cámara** desde interfaz web
- ✨ **Scripts de entrenamiento** incluidos
- ✨ **Interfaz web mejorada** con controles avanzados
- ✨ **Documentación completa** paso a paso

## Características Principales

- **Modo rápido: 60+ FPS** sin procesamiento
- **Detección Haar: 25-30 FPS** detecta rostros
- **Reconocimiento: 15-20 FPS** identifica personas
- **Toggle independiente** para cada modo
- Streaming de video optimizado (MJPEG)
- Detección facial usando Haar Cascade
- **Reconocimiento facial** usando face_recognition (dlib)
- Descarga automática del clasificador
- Detección automática de IP local
- **Selección dinámica de cámara**
- Compatible con Raspberry Pi y Fedora/PC Linux
- Optimizado para WiFi 2.4 GHz
- Interfaz web moderna y responsive

## Requisitos

### Raspberry Pi 3

- Raspberry Pi 3 (Model B o B+)
- Cámara USB compatible
- Python 3.7+
- Conexión WiFi 2.4 GHz (o Ethernet)

### Fedora/PC Linux

- Fedora 30+ (o cualquier distribución Linux)
- Cámara web integrada o USB
- Python 3.7+
- Conexión WiFi o Ethernet

## 🚀 Inicio Rápido

### Paso 0: Configuración Inicial (Primera vez)

```bash
# Configurar permisos y estructura
python3 setup.py

# Instalar dependencias
pip3 install -r requirements.txt
```

**⚠️ IMPORTANTE**: La instalación puede tardar:
- **Fedora/PC**: 5-10 minutos
- **Raspberry Pi**: 30-60 minutos (¡es normal! No canceles)

### Guías Rápidas

- 📖 **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - Guía de 5 minutos
- 📚 **[RECONOCIMIENTO.md](RECONOCIMIENTO.md)** - Documentación completa

## Instalación Detallada

### Método 1: Instalación automática (Recomendado)

```bash
bash install.sh
```

Este script instala automáticamente todas las dependencias para:

- Raspberry Pi OS (Debian/Raspbian)
- Fedora/RHEL/CentOS
- Ubuntu/Debian

### Método 2: Instalación manual

#### Para Raspberry Pi

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv v4l-utils
pip3 install -r requirements.txt
```

#### Para Fedora

```bash
sudo dnf install -y python3-pip python3-opencv v4l-utils mesa-libGL
sudo usermod -aG video $USER  # Dar permisos de acceso a la cámara
pip3 install --user -r requirements.txt
```

**Importante para Fedora**: Después de ejecutar `usermod`, cierra sesión y vuelve a entrar para que los permisos surtan efecto.

### Configurar WiFi 2.4 GHz (solo Raspberry Pi)

El Raspberry Pi 3 Model B solo soporta 2.4 GHz. Para configurar tu red WiFi:

```bash
sudo bash setup_wifi.sh
```

O manualmente edita `/etc/wpa_supplicant/wpa_supplicant.conf`:

```conf
network={
    ssid="TU_NOMBRE_WIFI"
    psk="TU_PASSWORD"
    key_mgmt=WPA-PSK
}
```

## Ejecutar el sistema

```bash
python3 app.py
```

El sistema:

1. Detectará automáticamente si estás en Raspberry Pi o PC
2. Buscará cámaras disponibles en tu sistema
3. Descargará el clasificador Haar Cascade si no existe
4. Mostrará la URL para acceder desde tu navegador

## Uso

Una vez iniciado, el sistema mostrará:

```text
======================================================================
  SISTEMA DE DETECCIÓN FACIAL - 30 FPS
  Plataforma: Raspberry Pi 3 (o PC/Laptop (Fedora))
======================================================================

[INFO] Buscando cámaras disponibles...
[OK] Cámaras encontradas: [0]
[INFO] Usando cámara /dev/video0
[OK] Clasificador de rostros cargado correctamente

======================================================================
  ✅ SISTEMA ACTIVO
======================================================================

  📹 URL: http://192.168.X.X:5000
  📊 Stats: http://192.168.X.X:5000/stats

  🎯 Objetivo: 30 FPS
  👤 Detección facial: ACTIVA
  📐 Resolución: 320x240 (optimizado para RPi3)
  🌐 IP Local: 192.168.X.X

  Presiona CTRL+C para salir
======================================================================
```

Abre tu navegador y accede a la URL mostrada para ver el streaming.

## Endpoints

- `/` - Interfaz principal con streaming de video
- `/video_feed` - Stream MJPEG directo
- `/status` - Estado del sistema (JSON)
- `/stats` - Estadísticas en tiempo real

## Notas sobre WiFi

### Raspberry Pi 3 Model B

- ✓ Soporta 2.4 GHz (802.11b/g/n)
- ✗ NO soporta 5 GHz

### Raspberry Pi 3 Model B+

- ✓ Soporta 2.4 GHz (802.11b/g/n)
- ✓ Soporta 5 GHz (802.11ac)

Para forzar 2.4 GHz en redes duales, agrega a tu configuración WiFi:

```conf
freq_list=2412 2437 2462
```

## Controles de la interfaz

La interfaz web incluye:

- **Botón "Activar/Desactivar Detección"**: Alterna entre modo rápido (60+ FPS) y modo con detección (25-30 FPS)
- **FPS en tiempo real**: Muestra los FPS actuales
- **Refrescar**: Reinicia el stream
- **Pantalla completa**: Vista inmersiva
- **Estadísticas**: Información detallada del sistema

### Usar el toggle de detección

1. Por defecto, la detección está **desactivada** para máximo FPS (60+)
2. Haz clic en "👤 Activar Detección" para activar la detección facial
3. El botón cambia a "🚫 Desactivar Detección" (rojo)
4. Vuelve a hacer clic para desactivar y recuperar 60+ FPS

## Problema de 3 FPS

Si obtienes solo **3 FPS**, el problema más común es que tu cámara está usando formato **YUYV** en lugar de **MJPEG**.

### Solución rápida

```bash
# Configurar cámara automáticamente
bash setup_camera.sh
```

Este script interactivo te permitirá:
- Ver la configuración actual de tu cámara
- Seleccionar el formato óptimo (MJPEG recomendado)
- Ver FPS esperado según tu configuración

### Solución manual

```bash
# Forzar MJPEG a resolución baja (60+ FPS)
v4l2-ctl -d /dev/video0 --set-fmt-video=width=320,height=240,pixelformat=MJPG

# Verificar
v4l2-ctl -d /dev/video0 --get-fmt-video
```

**Lee [SOLUCION_3FPS.md](SOLUCION_3FPS.md) para más detalles.**

## Diagnóstico de rendimiento

Si experimentas FPS bajos o delay en la imagen, ejecuta el script de diagnóstico:

```bash
python3 diagnose_camera.py
```

Este script te mostrará:

- Backends disponibles (V4L2, ANY, Default)
- FPS real alcanzado con diferentes configuraciones
- Latencia promedio y máxima
- Recomendaciones específicas para tu cámara

## Solución de problemas

### FPS bajos o imagen con retraso (delay)

El problema más común es el **buffer de la cámara** que acumula frames viejos. Soluciones:

#### 1. Ejecutar diagnóstico

```bash
python3 diagnose_camera.py
```

#### 2. Verificar configuración de la cámara

```bash
# Ver capacidades de la cámara
v4l2-ctl -d /dev/video0 --all

# Ver formatos soportados
v4l2-ctl -d /dev/video0 --list-formats-ext
```

#### 3. Optimizaciones aplicadas en el código

El sistema ya incluye estas optimizaciones:

- Buffer mínimo (BUFFERSIZE=1)
- Formato MJPEG (más eficiente para USB)
- Resolución 320x240 (más rápido)
- Backend V4L2 prioritario en Linux
- Descarte de frames viejos del buffer
- Detección facial cada 3 frames

#### 4. Si el problema persiste

Algunas cámaras/drivers no respetan BUFFERSIZE=1. El código incluye un modo de "fast read" que automáticamente descarta frames del buffer cuando el procesamiento es rápido.

### La cámara no se detecta

#### En Fedora

```bash
# Verificar que la cámara existe
ls -l /dev/video*

# Verificar permisos
groups | grep video

# Si no estás en el grupo video
sudo usermod -aG video $USER
# Luego cierra sesión y vuelve a entrar

# Ver información de la cámara
v4l2-ctl --list-devices
```

#### En Raspberry Pi

```bash
# Verificar cámara USB
ls -l /dev/video*

# Información detallada
v4l2-ctl --list-devices
```

### Verificar conexión WiFi

```bash
# Ver IP asignada
hostname -I

# Estado WiFi (Raspberry Pi)
iwconfig wlan0

# Estado red (Fedora)
nmcli device status
```

### El clasificador no se descarga

Si tienes problemas de conexión, descarga manualmente:

```bash
wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml
```

### Error de permisos en Fedora

Si obtienes errores de permisos al acceder a la cámara:

```bash
# Verificar grupos del usuario
groups

# Agregar al grupo video
sudo usermod -aG video $USER

# Aplicar cambios (cierra sesión)
newgrp video

# Verificar dispositivos
ls -l /dev/video*
```

## Optimizaciones

El sistema está optimizado para:

- Resolución 320x240 (balance entre calidad y rendimiento)
- Detección facial cada 3 frames (reducir carga de CPU)
- Codificación JPEG con calidad 50 (mayor velocidad)
- Buffer mínimo de cámara (baja latencia)

## Licencia

MIT
