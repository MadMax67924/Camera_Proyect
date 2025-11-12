# ⚡ Guía Rápida: Instalar SIN DLIB en Raspberry Pi (5 pasos)

**⏱️ Tiempo total: 20 minutos** (vs 2-3 horas con dlib)

---

## 📋 PASO 1: Preparar Raspberry Pi

Ejecuta en tu **Raspberry Pi**:

```bash
# Actualizar
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias
sudo apt-get install -y python3-pip python3-dev libjasper-dev libtiff5 libjasper1

# Crear carpeta
mkdir -p ~/camaraproject
cd ~/camaraproject
```

---

## 📥 PASO 2: Copiar archivos desde tu PC

**Desde tu PC (en la carpeta del proyecto):**

```bash
# Reemplaza 192.168.x.x con IP de tu Raspberry Pi
scp -r . pi@192.168.x.x:~/camaraproject/
```

---

## 🔧 PASO 3: Instalar paquetes (RÁPIDO)

**De vuelta en Raspberry Pi:**

```bash
cd ~/camaraproject

# Crear ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar (SIN DLIB - 15 minutos)
pip install -r requirements_no_dlib.txt
```

---

## 📸 PASO 4: Capturar fotos y entrenar

**En Raspberry Pi:**

```bash
cd ~/camaraproject
source venv/bin/activate

# Capturar fotos para cada persona (30 fotos c/u)
# Presiona ESPACIO para capturar, ESC para terminar
python3 scripts/capture_faces.py "tu_nombre"
python3 scripts/capture_faces.py "otra_persona"

# Entrenar modelo (2-5 minutos)
python3 scripts/train_model.py
```

---

## 🚀 PASO 5: Ejecutar la app

**En Raspberry Pi:**

```bash
cd ~/camaraproject
source venv/bin/activate

# Iniciar servidor
python3 app.py

# Verás: http://192.168.x.x:5000
```

**Desde tu PC abre:**
```
http://192.168.x.x:5000
```

---

## ✅ ¿Listo?

Si todo salió bien, deberías ver:
- ✓ La cámara en vivo
- ✓ Detección de rostros
- ✓ Reconocimiento de personas

---

## 🛠️ Si algo falla

```bash
# ¿No se ve la cámara?
ls -la /dev/video*

# ¿"Modelo no encontrado"?
# → Primero captura fotos (Paso 4)

# ¿Error de módulos?
pip list | grep -E "opencv|flask|scikit"

# ¿Lento?
# → Es normal en Raspberry Pi 3, aprox 5-10 FPS

# ¿Quieres volver a dlib?
# → Ver MIGRACION_SIN_DLIB_RASPI.md sección "Volver a dlib"
```

---

## 📊 Resumen

| Concepto | Tiempo |
|----------|--------|
| Instalación | 15-20 min |
| Captura de fotos | 5-10 min |
| Entrenamiento | 2-5 min |
| **Total** | **~30 min** |

**Sin dlib**: 30 minutos ✓  
**Con dlib**: 3-4 horas ✗

---

**¡Listo! Tu Raspberry Pi está lista sin dlib** 🎉
