# 🚀 Guía Rápida: Dataset de Desconocidos

## Problema
El script `train_model_with_unknowns.py` necesita imágenes de personas **desconocidas** (que NO están en tu dataset de entrenamiento) para mejorar la detección de intrusos.

## Solución (3 opciones)

### ✅ Opción 1: Crear dataset local RECOMENDADO (Sin descargas)
```bash
# 1. Crear carpeta
mkdir -p dataset/unknown

# 2. Copiar imágenes de desconocidos aquí
# Pueden ser fotos de otras personas, Google Images, etc.
# Estructura:
# dataset/unknown/
# ├── foto1.jpg
# ├── foto2.jpg
# └── foto3.jpg

# 3. O usar subcarpetas:
# dataset/unknown/
# ├── person1/
# │   ├── foto1.jpg
# │   └── foto2.jpg
# └── person2/
#     └── foto1.jpg

# 4. Entrenar
python3 scripts/train_model_with_unknowns.py
```

### ✅ Opción 2: Verificar estructura
```bash
# Ver estado actual
python3 scripts/setup_unknown_dataset.py check
```

### ⚠️ Opción 3: Entrenar SIN desconocidos (Menos preciso)
```bash
# Si NO tienes dataset de desconocidos, usa:
python3 scripts/train_model_new.py

# Esto funciona pero será menos preciso detectando intrusos
```

## Archivos de imágenes soportados
- `.jpg`
- `.png`
- `.jpeg`

## ¿De dónde obtener imágenes de desconocidos?

1. **Google Images** (Legal para uso educativo)
   - Busca: "face photos", "people", "portrait"
   - Descarga ~100-200 imágenes
   - Cópialas a `dataset/unknown/`

2. **Datasets públicos**
   - LFW (Labeled Faces in the Wild)
   - VGGFace2
   - CASIA-WebFace

3. **Tus propias fotos**
   - De familia, amigos, etc.
   - Cualquier persona que NO sea Luis, Victor, max, nico

## Estructura final esperada
```
camaraproject/
├── dataset/
│   ├── raw/                 (Personas CONOCIDAS)
│   │   ├── Luis/
│   │   ├── Victor/
│   │   └── ...
│   └── unknown/             (Personas DESCONOCIDAS) ← NUEVA
│       ├── person1/
│       ├── person2/
│       └── ...
├── scripts/
│   ├── train_model_with_unknowns.py  (NUEVO SCRIPT)
│   ├── train_model_new.py
│   └── ...
└── ...
```

## Cómo entrenar paso a paso

### Paso 1: Preparar datos
```bash
# Verificar estado
python3 scripts/setup_unknown_dataset.py check

# Debería decir:
# [OK] Directorio dataset/unknown EXISTE
# [OK] Encontradas X imágenes
```

### Paso 2: Entrenar modelo
```bash
python3 scripts/train_model_with_unknowns.py

# O especificando rutas:
python3 scripts/train_model_with_unknowns.py dataset/raw dataset/unknown
```

### Paso 3: Ver resultados
```bash
# El script mostrará:
# - Total de personas CONOCIDAS: 4 (Luis, Victor, max, nico)
# - Muestras conocidos: 111
# - Muestras desconocidos: 150
# - Precisión validación: 98.5%
# - Detección de anomalías: 85.3% en desconocidos
```

## Solución de problemas

### "No hay imágenes en dataset/unknown"
```bash
# Crear carpeta
mkdir -p dataset/unknown

# Copiar imágenes (reemplaza /path/to/images)
cp /path/to/images/*.jpg dataset/unknown/
```

### "No se detectan imágenes"
```bash
# Verificar archivos
ls -la dataset/unknown/

# Deben ser: .jpg, .png o .jpeg (minúsculas)
# Si están comprimidas, descomprimirlas primero
```

### "El modelo sigue siendo lento"
- Los desconocidos solo mejoran la PRECISIÓN, no la velocidad
- La velocidad depende de:
  - Tamaño del dataset (más fotos = más tiempo)
  - Hardware (RPi es lenta naturalmente)
  - Si usas reconocimiento facial

## Diferencias entre scripts

| Script | Entrada | Salida | Caso de uso |
|--------|---------|--------|------------|
| `train_model_new.py` | Solo conocidos | Modelo KNN | Básico, más rápido |
| `train_model_with_unknowns.py` | Conocidos + desconocidos | KNN + Anomaly Detector | **Recomendado**, detecta intrusos |
| `train_model_dual.py` | Conocidos + desconocidos | 2 modelos separados | Experimental |

## Próximos pasos

```bash
# 1. Llenar dataset de desconocidos
mkdir -p dataset/unknown
# Copiar imágenes aquí

# 2. Entrenar
python3 scripts/train_model_with_unknowns.py

# 3. Probar
python3 app.py
# Abre: http://localhost:5000
```

---

**¿Dudas?** El script `train_model_with_unknowns.py` busca automáticamente en:
- `dataset/unknown/` (imágenes directas)
- `dataset/unknown/*/` (subcarpetas)

¡No necesitas hacer nada especial! Solo copia imágenes y ejecuta el script. 🚀
