# 📌 ÍNDICE - ¿Qué archivo leer?

## 🎯 Quiero instalar TODO rápido - **EMPIEZA AQUÍ**

**Lee en este orden:**

1. **`INSTRUCCIONES_RASPI_PASO_A_PASO.md`** ← COMIENZA AQUÍ
   - Instrucciones que copias y pegas directamente
   - 7 pasos simples
   - Errores comunes y soluciones
   - Ideal para hacer sin parar

2. **`GUIA_RAPIDA_RASPI_SIN_DLIB.md`** ← Si necesitas resumido
   - 5 pasos principales
   - Tiempo estimado: 30 minutos
   - Sin detalles técnicos

---

## 📚 Quiero entender la solución técnica - **LEE ESTO**

**`RESUMEN_SOLUCION_SIN_DLIB.md`**
- ¿Qué cambió?
- ¿Por qué sin dlib es mejor?
- Comparación: dlib vs sin dlib
- Estructura técnica
- Cómo funciona el reconocimiento

---

## 🔧 Quiero la guía completa con TODO - **LEE ESTO**

**`MIGRACION_SIN_DLIB_RASPI.md`**
- Pasos detallados
- Código Python explicado
- Solución de problemas extendida
- Archivos específicos que necesitas
- Volver a dlib si es necesario

---

## 📂 Archivos nuevos que se crearon

| Archivo | ¿Qué es? | ¿Dónde va? |
|---------|----------|-----------|
| `core/face_recognition_lite.py` | Reconocedor sin dlib | `core/` |
| `scripts/train_model_new.py` | Entrenador sin dlib | `scripts/` |
| `requirements_no_dlib.txt` | Paquetes a instalar | Raíz |
| `install_no_dlib_raspi.sh` | Script instalación automática | Raíz |

---

## ⏱️ Tiempo total estimado

| Fase | Tiempo |
|------|--------|
| Instalación paquetes | 15-20 min |
| Capturar fotos | 5-10 min |
| Entrenar modelo | 2-5 min |
| **TOTAL** | **~30 min** |

**Vs. Con dlib:** 2-3 horas ❌

---

## ✅ Verificación rápida

Después de instalación, verifica:

```bash
# En tu Raspberry Pi
cd ~/camaraproject
source venv/bin/activate

# Ver que todo está instalado
python3 -c "import cv2, flask, sklearn; print('[OK] Listo')"

# Ver que la cámara funciona
ls -la /dev/video*

# Ver que hay carpeta para fotos
ls dataset/processed/
```

---

## 🚀 3 opciones según tu necesidad

### OPCIÓN 1: Solo quiero que funcione (Sin detalles)
→ Lee: `INSTRUCCIONES_RASPI_PASO_A_PASO.md`  
→ Copia y pega los comandos  
→ Listo en 30 minutos

### OPCIÓN 2: Quiero entender qué pasó (Técnico)
→ Lee: `RESUMEN_SOLUCION_SIN_DLIB.md`  
→ Lee: `MIGRACION_SIN_DLIB_RASPI.md`  
→ Luego instala desde Opción 1

### OPCIÓN 3: Quiero instalación automática (Script)
→ En Raspberry Pi ejecuta:
```bash
cd ~/camaraproject
bash install_no_dlib_raspi.sh
```
→ Sigue las instrucciones del script

---

## 🎯 Punto de inicio recomendado

**Para la mayoría de usuarios:**
1. Abre: `INSTRUCCIONES_RASPI_PASO_A_PASO.md`
2. Sigue los 7 pasos
3. Listo

**Si algo falla:**
1. Consulta la sección "Errores comunes" en ese mismo archivo
2. Si no está, ve a `MIGRACION_SIN_DLIB_RASPI.md`

---

## 📞 Resumen de cambios en el código

### ❌ Se elimina
- `dlib` (muy lento de instalar)
- `face_recognition` library (depende de dlib)

### ✅ Se reemplaza con
- `OpenCV Cascade Classifier` (detección rápida)
- `Scikit-learn KNN` (reconocimiento rápido)

### ✅ Se mantiene
- `Flask` servidor (igual)
- `app.py` aplicación principal (igual)
- `scripts/capture_faces.py` captura de fotos (igual)
- Estructura de carpetas (igual)

---

## 🔄 Compatibilidad

- **Raspberry Pi 3:** ✅ Funciona (5-10 FPS)
- **Raspberry Pi 4:** ✅ Funciona mejor (15-20 FPS)
- **Raspberry Pi Zero:** ⚠️ Posible (muy lento)
- **PC con Linux:** ✅ Funciona
- **PC con Windows:** ⚠️ Posible (requiere ajustes)
- **Mac:** ✅ Funciona

---

## 💾 Espacio necesario

- OpenCV: ~200 MB
- Scikit-learn: ~100 MB
- Otros: ~50 MB
- **Total:** ~350 MB

(Sin dlib ahorras ~500 MB)

---

## 🆘 Soporte rápido

| Problema | Solución |
|----------|----------|
| "pip install tarda" | Es normal (10-15 min) |
| "No se ve cámara" | Conecta USB, verifica `/dev/video*` |
| "Modelo no encontrado" | Captura fotos primero |
| "Muy lento" | Normal en Pi 3 (5-10 FPS) |
| "Error de módulos" | Reinstala: `pip install -r requirements_no_dlib.txt` |

---

## 📌 Checklist final

- [ ] Leí las instrucciones
- [ ] Copié archivos a Raspberry Pi
- [ ] Instalé paquetes (`pip install -r requirements_no_dlib.txt`)
- [ ] Capturé fotos (`python3 scripts/capture_faces.py`)
- [ ] Entrené modelo (`python3 scripts/train_model.py`)
- [ ] Ejecuté la app (`python3 app.py`)
- [ ] Accedí desde navegador (`http://IP:5000`)

---

**¡Listo para comenzar! 🚀**

Empieza por: `INSTRUCCIONES_RASPI_PASO_A_PASO.md`
