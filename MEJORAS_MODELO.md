# Mejoras del Modelo de Reconocimiento Facial

## Resumen de Cambios

Se ha mejorado significativamente el sistema de reconocimiento facial con:

### 1. Características Mejoradas (330 vs 278 anteriores)

**Nuevas técnicas de extracción:**
- **LBP (Local Binary Patterns)**: Captura patrones de textura facial (32 características)
- **HOG (Histogram of Oriented Gradients)**: Detecta formas y bordes (16 características)
- **Histograma ecualizado**: Mejor contraste y robustez a iluminación
- **Estadísticas extendidas**: 6 métricas (media, std, min, max, mediana, varianza)
- **Análisis de bordes mejorado**: 4 métricas de Canny

**Total:** 256 (píxeles) + 6 (stats) + 16 (hist) + 32 (LBP) + 16 (HOG) + 4 (bordes) = **330 características**

### 2. Entrenamiento Inteligente

**Nuevas funcionalidades en `train_model_improved.py`:**
- ✅ **Validación cruzada** para encontrar mejor valor de k (vecinos)
- ✅ **Búsqueda automática de umbral óptimo** usando datos de validación
- ✅ **Aumento de datos** (rotación, brillo, flip) para mayor robustez
- ✅ **División train/validation** (80/20) para evaluar precisión
- ✅ **Detector de anomalías** (Isolation Forest) para identificar desconocidos
- ✅ **Métricas detalladas** (precision, recall, F1-score)
- ✅ **Curva de umbral vs precisión** para análisis visual

### 3. Reconocimiento Mejorado

**Mejoras en `face_recognition_lite.py`:**
- ✅ Usa **umbral óptimo** calculado automáticamente durante entrenamiento
- ✅ **Doble verificación**: KNN + detector de anomalías
- ✅ **Distancia media de k vecinos** (más robusto que solo el más cercano)
- ✅ **Logs detallados** para debugging (distancias, scores, decisiones)
- ✅ Compatible con modelos antiguos y nuevos

### 4. Script de Evaluación

**Nuevo `evaluate_model.py` con 3 modos:**
- `image`: Evaluar una sola imagen
- `webcam`: Prueba en tiempo real con cámara
- `directory`: Análisis estadístico de un directorio completo

---

## Cómo Usar

### Paso 1: Entrenar el Modelo Mejorado

```bash
# Entrenamiento con todas las mejoras (recomendado)
python3 scripts/train_model_improved.py

# Sin aumento de datos (más rápido pero menos robusto)
python3 scripts/train_model_improved.py dataset/raw models/faces_model_lite.pkl false
```

**Salida esperada:**
```
======================================================================
ENTRENADOR DE MODELO FACIAL MEJORADO - SIN DLIB
Con: LBP + HOG + Validación cruzada + Aumento de datos
======================================================================

[*] Encontradas 6 personas
[*] Procesando 'FotosLucho' (45 imágenes)
  ✓ Muestras: 270 (x6 aumento) | ✗ Errores: 0
...

[*] Total de muestras: 943
[*] Dividiendo en entrenamiento (80%) y validación (20%)...

[*] Buscando mejor k (vecinos)...
  k=3: 94.21% accuracy
  k=5: 96.83% accuracy  ← MEJOR
  k=7: 95.77% accuracy
  k=9: 94.92% accuracy

[*] Buscando mejor umbral de decisión...
[OK] Mejor umbral encontrado: 75.0
[OK] Precisión en validación: 96.8%

======================================================================
[✓] MODELO ENTRENADO EXITOSAMENTE
======================================================================
[OK] Archivo: models/faces_model_lite.pkl
[OK] Tamaño: 2.45 MB
[OK] Personas: FotosLucho, FotosMaxi, FotosNacho, FotosNico, FotosPablo, FotosVictor
[OK] Muestras totales: 943
[OK] Precisión validación: 96.8%
[OK] Mejor k (vecinos): 5
[OK] Umbral recomendado: 75.0
======================================================================
```

### Paso 2: Evaluar el Modelo

**Evaluar una imagen específica:**
```bash
python3 scripts/evaluate_model.py image dataset/raw/FotosPablo/foto1.jpg
```

**Evaluar con webcam en tiempo real:**
```bash
python3 scripts/evaluate_model.py webcam
# O especificar cámara: python3 scripts/evaluate_model.py webcam 1
```

**Evaluar todo un directorio:**
```bash
python3 scripts/evaluate_model.py directory dataset/raw/FotosPablo
```

**Salida esperada (directory):**
```
======================================================================
RESULTADOS DE EVALUACIÓN
======================================================================
Total de imágenes: 20
Con rostros detectados: 19
Sin rostros: 1
Desconocidos: 0

Personas reconocidas:
  FotosPablo: 19 veces
======================================================================
```

### Paso 3: Usar en Producción

```bash
# Iniciar servidor con el modelo mejorado
python3 app.py
```

El sistema automáticamente:
1. Carga el modelo `models/faces_model_lite.pkl`
2. Lee el **umbral óptimo** guardado durante entrenamiento
3. Usa el **detector de anomalías** para identificar desconocidos
4. Muestra logs detallados de cada reconocimiento

---

## Comparación: Antes vs Ahora

| Aspecto | Antes | Ahora | Mejora |
|---------|-------|-------|--------|
| **Características** | 278 (píxeles + histograma) | 330 (LBP + HOG + más) | +18% |
| **Umbral** | Manual (60) | Auto-calculado (~75) | ✅ Óptimo |
| **Validación** | No | Sí (80/20 split) | ✅ Métricas |
| **Aumento de datos** | No | Sí (x6 muestras) | ✅ Robustez |
| **Detector desconocidos** | Solo umbral | Umbral + Anomalías | ✅ Doble filtro |
| **Evaluación** | Manual | Script automatizado | ✅ 3 modos |
| **Logs** | Básicos | Detallados (distancias) | ✅ Debugging |

---

## Entender los Logs de Reconocimiento

Cuando el sistema reconoce un rostro, verás logs como estos:

```python
# Caso 1: RECONOCIDO correctamente
[DEBUG] Reconocido: FotosPablo | Dist: 42.35 | Umbral: 75.0
# → Distancia < Umbral → Es persona conocida ✅

# Caso 2: DESCONOCIDO por distancia
[DEBUG] Fuera de umbral - Dist: 98.72 | Umbral: 75.0
# → Distancia > Umbral → No es nadie conocido ❌

# Caso 3: DESCONOCIDO por anomalía
[DEBUG] Anomalía detectada (score: -0.1234) - Probablemente desconocido
[DEBUG] Rechazado - Dist media: 67.89 | Anomalía: True
# → Isolation Forest detectó patrón anómalo → Desconocido ❌
```

**Interpretación:**
- **Distancia baja** (<50): Muy seguro de la identidad
- **Distancia media** (50-75): Probable, dentro del umbral
- **Distancia alta** (>75): Desconocido o poca confianza
- **Anomalía detectada**: Patrón muy diferente a los conocidos

---

## Solución de Problemas

### Problema: Muchos falsos positivos (reconoce desconocidos como conocidos)

**Solución:** Aumentar el umbral
```python
# Editar app.py, línea ~645
face_recognizer = FaceRecognizerLite(
    model_path="models/faces_model_lite.pkl",
    tolerance=90.0  # Aumentar de 75 a 90 (más estricto)
)
```

### Problema: Muchos falsos negativos (no reconoce a personas conocidas)

**Solución:** Disminuir el umbral
```python
face_recognizer = FaceRecognizerLite(
    model_path="models/faces_model_lite.pkl",
    tolerance=60.0  # Disminuir de 75 a 60 (más permisivo)
)
```

### Problema: Baja precisión en general

**Soluciones:**
1. **Más fotos por persona** (mínimo 30-50 recomendado)
2. **Fotos variadas** (diferentes ángulos, iluminación, expresiones)
3. **Calidad de imagen** (evitar borrosas o mal iluminadas)
4. **Re-entrenar con aumento de datos**:
   ```bash
   python3 scripts/train_model_improved.py dataset/raw models/faces_model_lite.pkl true
   ```

---

## Próximas Mejoras Potenciales

- [ ] Agregar embeddings de redes neuronales (FaceNet, ArcFace)
- [ ] Implementar seguimiento temporal (tracking) para mayor estabilidad
- [ ] Sistema de actualización incremental (agregar personas sin re-entrenar todo)
- [ ] Interfaz web para ajustar umbral en tiempo real
- [ ] Exportar métricas a dashboard (Grafana/Prometheus)

---

## Archivos Modificados

1. **`scripts/train_model_improved.py`** - Nuevo script de entrenamiento mejorado
2. **`core/face_recognition_lite.py`** - Actualizado con nuevas características y lógica
3. **`scripts/evaluate_model.py`** - Nuevo script de evaluación
4. **`MEJORAS_MODELO.md`** - Esta documentación

---

## Créditos

Mejoras implementadas el 12/11/2024:
- Extracción de características mejorada (LBP + HOG)
- Validación cruzada automática
- Detector de anomalías para desconocidos
- Sistema de evaluación completo
