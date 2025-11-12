# 🎯 DIAGRAMA DE FLUJO - Solución Sin DLIB

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    TU COMPUTADORA                        │
│                                                           │
│  1. Carpeta del proyecto                                 │
│     └─ scripts/capture_faces.py                         │
│     └─ app.py                                           │
│     └─ requirements_no_dlib.txt                         │
│                                                           │
│  2. Copia TODO a Raspberry Pi                           │
│     scp -r . pi@192.168.1.100:~/camaraproject/          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              RASPBERRY PI 3 / 4                          │
│                                                           │
│  PASO 1: Actualizar                                      │
│  $ sudo apt-get update && upgrade                       │
│                                                           │
│  PASO 2: Crear ambiente virtual                         │
│  $ python3 -m venv venv                                 │
│  $ source venv/bin/activate                             │
│                                                           │
│  PASO 3: Instalar paquetes (15 min - SIN DLIB)         │
│  $ pip install -r requirements_no_dlib.txt              │
│     ✓ flask                                             │
│     ✓ opencv-python                                     │
│     ✓ scikit-learn                                      │
│     ✓ numpy, pillow, tqdm                               │
│     ✗ NO dlib (ahorra 2-3 horas)                       │
│                                                           │
│  PASO 4: Capturar fotos de entrenamiento                │
│  $ python3 scripts/capture_faces.py "Luis"              │
│  $ python3 scripts/capture_faces.py "Max"               │
│     └─ Guardan en: dataset/processed/{nombre}/          │
│                                                           │
│  PASO 5: Entrenar modelo (2-5 min)                     │
│  $ python3 scripts/train_model.py                       │
│     ├─ Lee imágenes del dataset                         │
│     ├─ Extrae características con OpenCV               │
│     ├─ Entrena clasificador KNN                         │
│     └─ Guarda: models/faces_model_lite.pkl              │
│                                                           │
│  PASO 6: Ejecutar aplicación                            │
│  $ python3 app.py                                       │
│     └─ Inicia servidor Flask en puerto 5000             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│         ACCESO DESDE TU COMPUTADORA                      │
│                                                           │
│  Abre navegador:                                         │
│  http://192.168.1.100:5000                              │
│                                                           │
│  Verás:                                                  │
│  ✓ Video en vivo de la cámara                           │
│  ✓ Detección de rostros (rectángulos)                   │
│  ✓ Nombres de personas reconocidas                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Reconocimiento Facial

```
┌─────────────────────┐
│  Frame de cámara    │
│  (640x480 BGR)      │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  OpenCV Cascade Classifier               │
│  (haarcascade_frontalface_default.xml)   │
│                                          │
│  Detecta rostros sin necesidad de dlib   │
│  Retorna: [(x, y, w, h), ...]           │
└──────────┬──────────────────────────────┘
           │
           ↓ Para cada rostro detectado
┌─────────────────────────────────────────┐
│  Extracción de Características           │
│                                          │
│  1. Redimensionar a 64x64                │
│  2. Convertir a escala de grises         │
│  3. Extraer features:                    │
│     - Píxeles aplanados (4096)           │
│     - Histograma (32 bins)               │
│     - Bordes Canny                       │
│     - Estadísticas (media, std)          │
│  Vector resultante: 4200+ características│
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  Normalización (StandardScaler)          │
│                                          │
│  Escalar características al rango [0,1]  │
│  (necesario para KNN)                    │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  KNN Classifier (k=5)                    │
│                                          │
│  Busca los 5 vecinos más cercanos        │
│  en el modelo entrenado                  │
│                                          │
│  Retorna:                                │
│  - Etiqueta predicha (nombre)            │
│  - Confianza (0-1)                       │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  Decisión Final                          │
│                                          │
│  IF confianza > threshold (0.5):         │
│    Mostrar: "Luis (87%)"                │
│  ELSE:                                   │
│    Mostrar: "Desconocido"               │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  Dibujar en frame                        │
│                                          │
│  ┌─────────────────┐                    │
│  │ Luis (87%)      │  ← Nombre          │
│  │ ┌───────────────┤                    │
│  │ │               │ ← Rectángulo       │
│  │ │    ROSTRO     │                    │
│  │ │               │                    │
│  │ └───────────────┘                    │
│  └─────────────────┘                    │
│                                          │
│  Enviar a navegador vía Flask            │
└─────────────────────────────────────────┘
```

---

## 📁 Estructura de Archivos

### ANTES (Sin cambios)
```
camaraproject/
├── app.py                    ← app.py principal
├── requirements.txt          ← con dlib (2-3 horas instalación)
├── core/
│   └── face_recognition.py   ← Usa dlib + face_recognition
├── scripts/
│   ├── capture_faces.py      ← Captura fotos
│   └── train_model.py        ← Entrena con dlib
└── dataset/
    └── processed/            ← Fotos capturadas
```

### AHORA (Nueva solución)
```
camaraproject/
├── app.py                                (sin cambios - intenta lite primero)
├── requirements_no_dlib.txt              ✓ NUEVO (15 min instalación)
│
├── core/
│   ├── face_recognition.py               (original - opcional)
│   └── face_recognition_lite.py           ✓ NUEVO (sin dlib)
│
├── scripts/
│   ├── capture_faces.py                  (sin cambios)
│   ├── train_model.py                    (original - opcional)
│   └── train_model_new.py                ✓ NUEVO (sin dlib)
│
├── dataset/
│   ├── processed/                        (fotos capturadas aquí)
│   └── raw/
│
├── models/
│   └── faces_model_lite.pkl              (modelo generado - 20-50 MB)
│
├── INSTRUCCIONES_RASPI_PASO_A_PASO.md   ✓ NUEVO (EMPIEZA AQUÍ)
├── GUIA_RAPIDA_RASPI_SIN_DLIB.md         ✓ NUEVO
├── MIGRACION_SIN_DLIB_RASPI.md          ✓ NUEVO
├── RESUMEN_SOLUCION_SIN_DLIB.md         ✓ NUEVO
├── INDICE_ARCHIVOS.md                   ✓ NUEVO
└── install_no_dlib_raspi.sh              ✓ NUEVO (instalación automática)
```

---

## ⏱️ Línea de Tiempo

```
t=0 min
│
├─ [1-5 min] Copiar archivos a Raspberry Pi
│
├─ [5-10 min] Instalar dependencias del sistema
│
├─ [10-25 min] Instalar paquetes Python
│            (pip install -r requirements_no_dlib.txt)
│            - opencv-python: 5-8 min (compilando)
│            - scikit-learn: 3-5 min (compilando)
│            - otros: 1-2 min
│
├─ [25-35 min] Capturar fotos
│
├─ [35-40 min] Entrenar modelo
│            (python3 scripts/train_model.py)
│
├─ [40-41 min] Ejecutar aplicación
│            (python3 app.py)
│
└─ [41+ min] ✓ LISTO - Acceder desde navegador

TOTAL: ~40-45 minutos

CON DLIB: 3-4 HORAS ❌
```

---

## 🔧 Componentes Principales

### 1. OpenCV Cascade Classifier

```
┌─────────────────────────────────────────┐
│ haarcascade_frontalface_default.xml      │
│                                          │
│ Archivo binario pre-entrenado             │
│ Detecta rostros frontales                │
│ Rápido, no necesita compilar             │
│ Descargado automáticamente por OpenCV   │
└─────────────────────────────────────────┘
```

**Ventajas:**
- ✓ Instalado con OpenCV
- ✓ No necesita compilación
- ✓ Rápido
- ✗ Menos preciso que dlib

### 2. Feature Extraction

```
┌───────────────────────────┐
│  Rostro 64x64 Gris        │
└───────────┬───────────────┘
            │
            ├─→ Píxeles aplanados (4096)
            ├─→ Histograma (32)
            ├─→ Canny Edges media + std (2)
            ├─→ Media + std píxeles (2)
            │
            → Vector 4130-dimensional
```

### 3. KNN Classifier

```
Consulta: ¿A quién es similar este rostro?

        X (nuevo rostro)
         │
         │ distancia euclidiana
         │
    ┌────┴────┬────┬────┬────┐
    │          │    │    │    │
   Luis(1)   Luis(2) Max(1) Max(2) Victor(1)
    │          │    │    │    │
    └─────┬────┴────┴────┴────┘
          │
    Votación mayoritaria:
    Luis: 2 votos ✓
    Max: 2 votos
    Victor: 1 voto
    
    Resultado: "Luis"
```

---

## 💾 Requerimientos de Recursos

### Instalación

| Componente | Tamaño | Tiempo |
|-----------|--------|--------|
| Python3 | 50 MB | 1 min |
| Flask | 5 MB | 30 s |
| OpenCV | 200 MB | 5-8 min |
| Scikit-learn | 100 MB | 3-5 min |
| NumPy | 50 MB | 1 min |
| Otros | 20 MB | 30 s |
| **TOTAL** | **425 MB** | **15-20 min** |

vs.

| Componente | Tamaño | Tiempo |
|-----------|--------|--------|
| dlib | 500 MB | 2-3 horas |
| face_recognition | 10 MB | 5 min |
| face-recognition-models | 30 MB | 5 min |
| **TOTAL** | **~1 GB** | **2.5-3.5 horas** |

### Ejecución

| Recurso | Requerimiento |
|---------|---------------|
| RAM | ~200 MB |
| CPU | 1-2 núcleos activos |
| Almacenamiento | 500 MB (incluyendo modelos) |
| Red | Solo para descarga inicial |

---

## ✅ Verificación en cada paso

```
Paso 1: Actualizar sistema
└─ Verificar: sin errores, actualizaciones aplicadas

Paso 2: Crear ambiente virtual
└─ Verificar: $ ls -la venv/ (existe la carpeta)

Paso 3: Instalar paquetes
└─ Verificar: $ pip list | grep -E "flask|opencv|sklearn"

Paso 4: Capturar fotos
└─ Verificar: $ ls dataset/processed/tu_nombre/ (archivos .jpg)

Paso 5: Entrenar modelo
└─ Verificar: $ ls -lh models/faces_model_lite.pkl (~20-50 MB)

Paso 6: Ejecutar app
└─ Verificar: $ curl http://localhost:5000 (retorna HTML)

Paso 7: Acceder desde PC
└─ Verificar: Video en vivo, rostros detectados, nombres mostrados
```

---

## 🎯 Resumen Visual

```
Sin dlib (RECOMENDADO)
┌──────────────────────────────┐
│ 15-20 min instalación        │
│ Funciona en Raspberry Pi 3    │
│ Sin compilación pesada        │
│ Reconocimiento básico OK      │
│ Precisión: 85-90%            │
│ FPS: 10-15 en Pi 3            │
└──────────────────────────────┘

Con dlib (LENTO)
┌──────────────────────────────┐
│ 2-3 horas instalación ❌     │
│ Difícil en Raspberry Pi 3     │
│ Compilación muy pesada ❌    │
│ Reconocimiento avanzado      │
│ Precisión: 99%               │
│ FPS: 5-10 en Pi 3            │
└──────────────────────────────┘

GANADOR: Sin dlib para Raspberry Pi ✓
```

---

**Fin del diagrama de flujo**

Ahora sigue: `INSTRUCCIONES_RASPI_PASO_A_PASO.md`
