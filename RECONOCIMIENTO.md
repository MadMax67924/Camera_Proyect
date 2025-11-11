# 🧠 Guía de Reconocimiento Facial

Sistema mejorado de reconocimiento facial para Raspberry Pi 3 y Fedora/PC Linux.

## 📋 Contenido

- [Características](#características)
- [Instalación](#instalación)
- [Uso Rápido](#uso-rápido)
- [Capturar Fotos](#capturar-fotos)
- [Entrenar Modelo](#entrenar-modelo)
- [Ejecutar Sistema](#ejecutar-sistema)
- [Solución de Problemas](#solución-de-problemas)

---

## ✨ Características

### Nuevas Funcionalidades

- ✅ **Reconocimiento facial en tiempo real** usando face_recognition (dlib)
- ✅ **Selección de cámara** desde la interfaz web
- ✅ **Toggle independiente** para detección Haar y reconocimiento facial
- ✅ **Mejoras en detección** con parámetros optimizados
- ✅ **Scripts completos** para captura y entrenamiento
- ✅ **Interfaz web mejorada** con feedback visual
- ✅ **Optimizado** para Raspberry Pi 3 y Fedora

### Modos de Operación

1. **Modo Rápido (60+ FPS)**: Sin procesamiento, solo streaming
2. **Detección Haar (25-30 FPS)**: Detecta rostros, sin identificar
3. **Reconocimiento (15-20 FPS)**: Identifica personas específicas

---

## 🚀 Instalación

### 1. Requisitos Previos

#### Raspberry Pi
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv v4l-utils
sudo apt-get install -y libatlas-base-dev libopenblas-dev
sudo apt-get install -y cmake build-essential
```

#### Fedora
```bash
sudo dnf install -y python3-pip python3-opencv v4l-utils
sudo dnf install -y gcc-c++ cmake atlas-devel openblas-devel
sudo usermod -aG video $USER  # Importante para permisos de cámara
# Cerrar sesión y volver a entrar
```

### 2. Instalar Dependencias Python

```bash
pip3 install -r requirements.txt
```

**⚠️ IMPORTANTE**: En Raspberry Pi, la instalación de `face_recognition` y `dlib` puede tardar **30-60 minutos**. Es normal.

### 3. Instalación Alternativa (si falla)

Si `face_recognition` falla al instalar:

#### Raspberry Pi
```bash
# Instalar dlib primero (tarda ~40 min)
pip3 install dlib --no-cache-dir

# Luego face_recognition
pip3 install face_recognition
```

#### Fedora
```bash
# Instalar dependencias del sistema
sudo dnf install -y cmake gcc-c++ boost-devel

# Instalar Python packages
pip3 install --user dlib face_recognition
```

---

## 🎯 Uso Rápido

### Paso 1: Capturar Fotos de Entrenamiento

```bash
python3 scripts/capture_faces.py
```

El script te pedirá:
- Nombre de la persona
- Número de fotos a capturar (recomendado: 15-20)
- Cámara a usar (si tienes múltiples)

**Instrucciones durante captura:**
- Posiciona tu rostro frente a la cámara
- Mantén buena iluminación
- Presiona **ESPACIO** para capturar cada foto
- Varía la posición entre fotos:
  - Gira ligeramente la cabeza
  - Cambia expresiones
  - Muévete un poco

Las fotos se guardan en: `dataset/raw/[nombre_persona]/`

### Paso 2: Entrenar el Modelo

```bash
python3 scripts/train_model.py
```

Este script:
- Lee todas las fotos de `dataset/raw/`
- Extrae encodings faciales (128 dimensiones)
- Guarda el modelo en `models/faces_model.pkl`

**Tiempo estimado:**
- Raspberry Pi: 2-5 minutos
- PC/Fedora: 30 segundos - 1 minuto

### Paso 3: Ejecutar el Sistema

```bash
python3 app.py
```

El sistema:
- Detecta cámaras disponibles
- Te permite elegir cual usar
- Carga el modelo de reconocimiento
- Inicia el servidor web en puerto 5000

Abre tu navegador: `http://[IP_LOCAL]:5000`

---

## 📸 Capturar Fotos - Guía Detallada

### Mejores Prácticas

1. **Iluminación**
   - Usa luz natural o artificial frontal
   - Evita contraluz
   - No uses flash directo

2. **Posición**
   - Mantén el rostro a 50-100cm de la cámara
   - Centra tu cara en el encuadre
   - Asegúrate de que el sistema detecte tu rostro (rectángulo verde)

3. **Variedad** (MUY IMPORTANTE)
   - Captura con diferentes ángulos:
     - Frente (50% de las fotos)
     - Girado ligeramente izquierda (25%)
     - Girado ligeramente derecha (25%)
   - Varía expresiones: neutral, sonrisa, serio
   - Si usas lentes, captura con y sin ellos

4. **Cantidad**
   - Mínimo: 10 fotos
   - Recomendado: 15-20 fotos
   - Máximo práctico: 30 fotos

### Capturar Múltiples Personas

```bash
# Persona 1
python3 scripts/capture_faces.py
# Ingresa: "Juan"

# Persona 2
python3 scripts/capture_faces.py
# Ingresa: "Maria"

# Persona 3
python3 scripts/capture_faces.py
# Ingresa: "Pedro"

# Entrenar con todas las personas
python3 scripts/train_model.py
```

### Estructura de Archivos

```
dataset/raw/
├── juan/
│   ├── juan_001_20250110_143022.jpg
│   ├── juan_002_20250110_143025.jpg
│   └── ...
├── maria/
│   ├── maria_001_20250110_143122.jpg
│   └── ...
└── pedro/
    ├── pedro_001_20250110_143222.jpg
    └── ...
```

---

## 🤖 Entrenar Modelo - Detalles

### Proceso de Entrenamiento

El script `train_model.py`:

1. **Lee** todas las imágenes de `dataset/raw/`
2. **Detecta** rostros en cada imagen (usando HOG)
3. **Extrae** encodings faciales de 128 dimensiones
4. **Guarda** en formato pickle para uso rápido

### Parámetros de Entrenamiento

Puedes personalizar:

```bash
# Usar otro directorio de dataset
python3 scripts/train_model.py --dataset mi_dataset/

# Guardar modelo en otra ubicación
python3 scripts/train_model.py --output mi_modelo.pkl
```

### Verificar Modelo

```python
# Desde Python
import pickle

with open('models/faces_model.pkl', 'rb') as f:
    data = pickle.load(f)
    print(f"Personas: {set(data['names'])}")
    print(f"Total muestras: {len(data['names'])}")
```

### Re-entrenar

Si capturas fotos nuevas o agregas personas:

```bash
# Simplemente vuelve a entrenar
python3 scripts/train_model.py
```

El modelo se sobrescribirá con los datos actualizados.

---

## 🖥️ Ejecutar Sistema - Interfaz Web

### Iniciar Servidor

```bash
python3 app.py
```

**Salida esperada:**
```
======================================================================
  SISTEMA DE RECONOCIMIENTO FACIAL - MEJORADO
  Plataforma: PC/Laptop (Fedora)
======================================================================

[INFO] Buscando cámaras disponibles...
[OK] Cámaras encontradas: [0, 2]

[INFO] Múltiples cámaras disponibles: [0, 2]
Selecciona cámara (Enter = 0): 0

[INFO] Usando cámara /dev/video0
[OK] Clasificador Haar Cascade cargado correctamente

[INFO] Intentando cargar modelo de reconocimiento facial...
[OK] Modelo cargado: 3 personas registradas
[INFO] Personas: Juan, Maria, Pedro

======================================================================
  ✅ SISTEMA ACTIVO
======================================================================

  📹 URL Principal: http://192.168.1.100:5000
  📊 Estadísticas: http://192.168.1.100:5000/stats

  🎯 FPS Objetivo: 25-30 FPS
  👤 Detección: Haar Cascade (Toggle en interfaz)
  🧠 Reconocimiento: Disponible (3 personas)
  📐 Resolución: 320x240
  🌐 IP Local: 192.168.1.100
  📷 Cámaras: [0, 2] (usando 0)

  Presiona CTRL+C para salir
======================================================================
```

### Interfaz Web - Controles

#### Botones Principales

1. **👤 Activar Detección**
   - Activa detección Haar Cascade
   - ~25-30 FPS
   - Solo dibuja rectángulos, no identifica

2. **🧠 Activar Reconocimiento**
   - Activa reconocimiento facial completo
   - ~15-20 FPS
   - Identifica personas específicas
   - Muestra nombres y confianza (%)

3. **📷 Cambiar Cámara**
   - Lista cámaras disponibles
   - Cambio en caliente (sin reiniciar)
   - Útil para laptops con múltiples cámaras

4. **🔄 Refrescar**
   - Reinicia el stream
   - Útil si hay delay acumulado

5. **⛶ Pantalla Completa**
   - Vista inmersiva del video

6. **📊 Estadísticas**
   - Abre ventana con stats detalladas

#### Indicadores

- **FPS actual**: Se muestra en tiempo real
- **Rostros detectados**: Contador
- **Personas reconocidas**: Lista con nombres
- **Modo activo**: Detección ON/OFF, Reconocimiento ON/OFF

---

## 🔧 Configuración Avanzada

### Ajustar Parámetros de Reconocimiento

Edita `core/face_recognition.py`:

```python
# Línea 22-24
def __init__(self, model_path: str = "models/faces_model.pkl",
             tolerance: float = 0.6,  # ← Ajustar aquí
             model_type: str = "hog"):
```

**tolerance** (umbral de similitud):
- `0.4`: Muy estricto (puede rechazar a la misma persona)
- `0.6`: **Recomendado** (balance)
- `0.8`: Permisivo (puede confundir personas)

### Cambiar Resolución

Edita `app.py`, línea ~160:

```python
# Cambiar de 320x240 a 640x480
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
```

**⚠️ Advertencia**: Mayor resolución = menor FPS

### Optimizar para Raspberry Pi

Si el reconocimiento es muy lento:

1. **Reducir frecuencia de reconocimiento** (`app.py`, línea ~297):
   ```python
   # Cambiar de cada 5 frames a cada 10
   if detection_counter % 10 == 0:
   ```

2. **Reducir scale_factor** (`app.py`, línea ~300):
   ```python
   # Procesar imagen más pequeña (más rápido)
   recognized_faces = face_recognizer.recognize_faces(frame, scale_factor=0.2)
   ```

3. **Usar solo 1 persona** para pruebas iniciales

---

## 🐛 Solución de Problemas

### 1. Error al instalar face_recognition

**Síntoma:**
```
ERROR: Could not build wheels for dlib
```

**Solución Fedora:**
```bash
sudo dnf install -y gcc-c++ cmake atlas-devel
pip3 install --user dlib
pip3 install --user face_recognition
```

**Solución Raspberry Pi:**
```bash
# Instalar con más memoria swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Cambiar CONF_SWAPSIZE=100 a CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Reintentar
pip3 install dlib --no-cache-dir
```

### 2. "No hay modelo entrenado"

**Síntoma:**
```
[INFO] No hay modelo entrenado
[INFO] Para entrenar: python3 scripts/train_model.py
```

**Solución:**
1. Captura fotos: `python3 scripts/capture_faces.py`
2. Entrena modelo: `python3 scripts/train_model.py`
3. Reinicia app: `python3 app.py`

### 3. "No se detecta rostro" al capturar fotos

**Causas comunes:**
- Iluminación insuficiente
- Rostro muy pequeño en la imagen
- Cámara desenfocada

**Solución:**
- Acércate más a la cámara (50-100cm)
- Mejora la iluminación
- Limpia el lente de la cámara

### 4. Reconocimiento muy lento (< 10 FPS)

**Solución:**
```python
# En app.py, línea ~297-300
# Cambiar a reconocer cada 10 frames
if detection_counter % 10 == 0:
    recognized_faces = face_recognizer.recognize_faces(
        frame,
        scale_factor=0.2  # Más pequeño = más rápido
    )
```

### 5. Confunde personas / Falsos positivos

**Solución 1:** Ajustar tolerance (más estricto)
```python
# core/face_recognition.py, línea 23
tolerance: float = 0.5  # Reducir de 0.6 a 0.5
```

**Solución 2:** Capturar más fotos variadas
- Añade 10-15 fotos más de cada persona
- Vuelve a entrenar el modelo

### 6. "Cámara no disponible" en Fedora

**Solución:**
```bash
# Verificar grupo video
groups | grep video

# Si no aparece:
sudo usermod -aG video $USER

# Cerrar sesión y volver a entrar
# O forzar con:
newgrp video
```

### 7. FPS bajos en general

**Checklist:**
- [ ] ¿Usas resolución 320x240? (ver línea 160-161 en app.py)
- [ ] ¿Cámara en formato MJPEG? (ejecuta `bash setup_camera.sh`)
- [ ] ¿Múltiples programas usando la cámara? (cierra otros)
- [ ] ¿Raspberry Pi overheating? (verifica temperatura: `vcgencmd measure_temp`)

---

## 📊 Rendimiento Esperado

### Raspberry Pi 3

| Modo | FPS | CPU | Comentarios |
|------|-----|-----|-------------|
| Solo streaming | 60+ | ~20% | Sin procesamiento |
| Detección Haar | 25-30 | ~40% | Cada 3 frames |
| Reconocimiento | 12-18 | ~60% | Cada 5 frames, scale 0.25 |

### PC/Fedora (i5 o superior)

| Modo | FPS | CPU | Comentarios |
|------|-----|-----|-------------|
| Solo streaming | 60+ | ~5% | Sin procesamiento |
| Detección Haar | 30-40 | ~15% | Cada 3 frames |
| Reconocimiento | 20-30 | ~30% | Cada 5 frames, scale 0.25 |

---

## 🎓 Información Técnica

### Algoritmo de Reconocimiento

1. **Detección**: HOG (Histogram of Oriented Gradients)
   - Rápido en CPU
   - Buena precisión frontal
   - Alternativa: CNN (más lento, más preciso)

2. **Encoding**: 128-D facial embedding
   - Red neuronal pre-entrenada (dlib)
   - Captura características únicas del rostro
   - Invariante a iluminación (parcialmente)

3. **Matching**: Distancia Euclidiana
   - Compara embeddings
   - Umbral configurable (tolerance)
   - O(n) donde n = personas registradas

### Estructura del Modelo

Archivo `models/faces_model.pkl`:
```python
{
    'encodings': [
        array([0.1, 0.2, ...]),  # 128 valores
        array([0.3, 0.1, ...]),
        ...
    ],
    'names': [
        'Juan',
        'Maria',
        ...
    ]
}
```

---

## 🚀 Próximas Mejoras (TODOs)

- [ ] Base de datos SQLite para logs
- [ ] Exportar detecciones a CSV
- [ ] Gráficos de estadísticas (Chart.js)
- [ ] Integración con Arduino/relé
- [ ] API REST para integraciones
- [ ] Notificaciones push
- [ ] Modo noche (detección con IR)

---

## 📝 Notas Finales

- **Privacidad**: Los encodings faciales no son reversibles, pero las fotos sí contienen información sensible. Guárdalas de forma segura.
- **Rendimiento**: El sistema prioriza velocidad sobre máxima precisión. Para aplicaciones críticas, considera usar CNN en lugar de HOG.
- **Escalabilidad**: Funciona bien hasta ~50 personas. Para más, considera clustering o bases de datos vectoriales.

---

## 📞 Soporte

Si encuentras problemas no cubiertos aquí:

1. Revisa logs en la terminal donde ejecutaste `python3 app.py`
2. Ejecuta diagnósticos: `python3 diagnose_camera.py`
3. Verifica permisos de cámara: `ls -l /dev/video*`
4. Comprueba espacio en disco: `df -h`

---

**¡Disfruta del sistema de reconocimiento facial! 🎉**
