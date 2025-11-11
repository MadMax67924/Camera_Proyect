# 🚀 Inicio Rápido - Reconocimiento Facial

Guía rápida para poner en marcha el sistema en 5 minutos.

---

## ⚡ Instalación Express (Primera vez)

### Fedora / Laptop
```bash
# 1. Instalar dependencias del sistema
sudo dnf install -y python3-pip python3-opencv v4l-utils gcc-c++ cmake
sudo usermod -aG video $USER
# ⚠️ Cerrar sesión y volver a entrar

# 2. Instalar Python packages
pip3 install --user -r requirements.txt
# ⚠️ Esto tardará varios minutos (face_recognition + dlib)
```

### Raspberry Pi
```bash
# 1. Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv v4l-utils
sudo apt-get install -y libatlas-base-dev cmake build-essential

# 2. Instalar Python packages
pip3 install -r requirements.txt
# ⚠️ Esto tardará 30-60 minutos en Raspberry Pi (es normal)
```

---

## 📸 Paso 1: Capturar Fotos (5 minutos)

```bash
python3 scripts/capture_faces.py
```

**Responde:**
- Nombre: `TuNombre` (sin espacios)
- Fotos: `15` (Enter para default 20)
- Cámara: `0` (Enter para default)

**Durante captura:**
- Presiona **ESPACIO** para cada foto
- Varía tu posición entre fotos
- Captura 15-20 fotos

---

## 🤖 Paso 2: Entrenar Modelo (2 minutos)

```bash
python3 scripts/train_model.py
```

Esperarás ver:
```
✅ ENTRENAMIENTO COMPLETADO
Modelo guardado en: models/faces_model.pkl
Total de muestras: 20
Personas registradas: 1
```

---

## 🎥 Paso 3: Ejecutar Sistema

```bash
python3 app.py
```

**Selecciona cámara** (si tienes múltiples):
```
Cámaras disponibles: [0, 2]
Selecciona cámara (Enter = 0): 0
```

Verás:
```
✅ SISTEMA ACTIVO
📹 URL Principal: http://192.168.X.X:5000
🧠 Reconocimiento: Disponible (1 personas)
```

---

## 🌐 Paso 4: Abrir Interfaz Web

Abre tu navegador en: **http://[IP_MOSTRADA]:5000**

### Botones importantes:

1. **🧠 Activar Reconocimiento** ← ¡Presiona esto!
2. **👤 Activar Detección** (opcional, más rápido)
3. **📷 Cambiar Cámara** (si tienes múltiples)

---

## 🎯 Verificar que Funciona

✅ **Reconocimiento activo** cuando veas:
- Tu nombre aparece sobre tu rostro en el video
- Porcentaje de confianza (ej: "TuNombre 95%")
- Rectángulo verde alrededor de tu cara
- En la interfaz: "✅ Personas Reconocidas: TuNombre"

---

## 🐛 Problemas Comunes

### "No se detectó rostro" al capturar
→ Acércate más a la cámara (50-100cm)
→ Mejora la iluminación

### "No hay modelo entrenado"
→ Ejecuta: `python3 scripts/train_model.py`

### "Cámara no disponible" (Fedora)
→ Cierra sesión y vuelve a entrar (permisos)
→ O ejecuta: `newgrp video`

### FPS muy bajo (< 10)
→ Desactiva reconocimiento, usa solo detección
→ O reduce resolución en app.py (línea 160-161)

### No reconoce correctamente
→ Captura más fotos (20-30)
→ Vuelve a entrenar: `python3 scripts/train_model.py`

---

## 📚 Documentación Completa

- [RECONOCIMIENTO.md](RECONOCIMIENTO.md) - Guía detallada
- [README.md](README.md) - Info general del proyecto
- [SOLUCION_3FPS.md](SOLUCION_3FPS.md) - Optimización de cámara

---

## ➕ Agregar Más Personas

```bash
# Capturar fotos de otra persona
python3 scripts/capture_faces.py
# Nombre: "Maria"

# Re-entrenar con ambas personas
python3 scripts/train_model.py

# Reiniciar sistema
python3 app.py
```

---

## 🎓 Modos de Operación

| Modo | Botón | FPS | Descripción |
|------|-------|-----|-------------|
| **Streaming** | Ninguno | 60+ | Solo video, sin procesar |
| **Detección** | 👤 Activar | 25-30 | Detecta rostros (sin identificar) |
| **Reconocimiento** | 🧠 Activar | 15-20 | Identifica personas específicas |

💡 **Tip**: Usa solo detección para mejor rendimiento si no necesitas identificar personas.

---

## 🔥 Comandos Útiles

```bash
# Ver cámaras disponibles
ls -l /dev/video*

# Verificar modelo entrenado
ls -lh models/faces_model.pkl

# Ver dataset capturado
ls -R dataset/raw/

# Configurar cámara óptima
bash setup_camera.sh

# Diagnosticar rendimiento
python3 diagnose_camera.py
```

---

**¡Listo! Tu sistema de reconocimiento facial está funcionando 🎉**

Si algo falla, consulta [RECONOCIMIENTO.md](RECONOCIMIENTO.md) para solución de problemas detallada.
