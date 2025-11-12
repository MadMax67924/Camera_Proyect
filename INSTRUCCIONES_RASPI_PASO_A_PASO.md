# 🔴 INSTRUCCIONES PARA RASPBERRY PI - Copia y Pega

**Este documento tiene instrucciones que copias y pegas directamente en tu Raspberry Pi**

---

## 📋 Paso 1: En tu Raspberry Pi - Preparación inicial

Abre terminal SSH o conéctate directamente. Copia y pega esto:

```bash
# Actualizar sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias del sistema
sudo apt-get install -y python3-pip python3-dev python3-venv libjasper-dev libtiff5

# Crear carpeta del proyecto
mkdir -p ~/camaraproject
cd ~/camaraproject
```

**Tiempo:** 5-10 minutos  
**Resultado esperado:** Sin errores

---

## 📥 Paso 2: En tu PC - Copiar archivos

Abre terminal en tu PC, en la carpeta del proyecto. Copia y pega:

```bash
# Reemplaza 192.168.1.100 con la IP de tu Raspberry Pi
# (Pregunta: ¿Cómo sé la IP? → En tu router o ejecuta: hostname -I en Raspberry Pi)

scp -r . pi@192.168.1.100:~/camaraproject/

# Si pide contraseña, es "raspberry" (por defecto)
```

**Si no funciona scp:**

```bash
# Alternativa con tar
tar czf project.tar.gz .
scp project.tar.gz pi@192.168.1.100:~/
# Luego en Raspberry Pi: cd ~/ && tar xzf project.tar.gz && mv * camaraproject/
```

---

## 🔧 Paso 3: En tu Raspberry Pi - Instalación

Vuelve a la terminal de Raspberry Pi. Copia y pega:

```bash
cd ~/camaraproject

# Crear ambiente virtual
python3 -m venv venv

# Activar ambiente
source venv/bin/activate

# Actualizar pip (importante)
pip install --upgrade pip setuptools wheel

# Instalar paquetes (ESTO TARDA 10-15 MINUTOS)
# No cierres la terminal, déjalo trabajar
pip install -r requirements_no_dlib.txt

# Si termina sin errores, verás algo como:
# Successfully installed flask-2.0.0 opencv-python-4.5.0 ...
```

**⚠️ Esto tardará:**
- opencv-python: 5-8 minutos (está compilando)
- scikit-learn: 3-5 minutos (está compilando)
- El resto: 1-2 minutos

**Paciencia!** No interrumpas aunque parezca congelado.

---

## 📸 Paso 4: Capturar fotos de cada persona

**Aún en tu Raspberry Pi**, sigue estos pasos:

```bash
# Asegúrate de estar en la carpeta correcta
cd ~/camaraproject
source venv/bin/activate

# Capturar fotos - PRIMERA PERSONA
python3 scripts/capture_faces.py "Luis"

# Verás:
# - Una ventana se abre con la cámara
# - Presiona ESPACIO para capturar foto (captura 30-50 fotos)
# - Presiona ESC cuando termines
# - Las fotos se guardan en: dataset/processed/Luis/

# Repetir para cada persona
python3 scripts/capture_faces.py "Max"
python3 scripts/capture_faces.py "Victor"
python3 scripts/capture_faces.py "Nico"

# (O los nombres que uses)
```

**Tips:**
- Mueve la cabeza a diferentes ángulos mientras capturas
- Captura desde cerca y desde lejos
- Diferentes iluminaciones
- Total: 30-50 fotos por persona mínimo

---

## 🏋️ Paso 5: Entrenar el modelo

**En tu Raspberry Pi:**

```bash
cd ~/camaraproject
source venv/bin/activate

# Entrenar el modelo (2-5 minutos)
python3 scripts/train_model.py

# Verás algo como:
# [*] Encontradas 4 personas
# [*] Procesando 'Luis' (45 imágenes)
# [*] Procesando 'Max' (38 imágenes)
# [*] Procesando 'Victor' (42 imágenes)
# [*] Procesando 'Nico' (40 imágenes)
# [*] Total de muestras: 165
# [✓] MODELO ENTRENADO EXITOSAMENTE
# [OK] Archivo: models/faces_model_lite.pkl
# [OK] Tamaño: 28.45 MB
# [OK] Personas: Luis, Max, Nico, Victor
```

**Si termina con éxito:** ¡Listo para usar!

---

## 🚀 Paso 6: Ejecutar la aplicación

**En tu Raspberry Pi:**

```bash
cd ~/camaraproject
source venv/bin/activate

# Iniciar servidor Flask
python3 app.py

# Verás algo como:
# [OK] Servidor escuchando en http://192.168.1.100:5000
# [OK] Usando FaceRecognizerLite (sin dlib)
# [OK] 4 personas registradas
# WARNING: This is a development server. Do not use it in production.
#  * Running on http://0.0.0.0:5000
```

---

## 💻 Paso 7: Ver desde tu PC

Abre tu navegador web y ve a:

```
http://192.168.1.100:5000
```

(Reemplaza 192.168.1.100 con la IP de tu Raspberry Pi)

**Deberías ver:**
- Video en vivo de la cámara
- Rectángulos alrededor de los rostros
- Nombres de las personas reconocidas

---

## 🛑 Para detener la aplicación

En la terminal de Raspberry Pi donde está corriendo, presiona:

```
Ctrl + C
```

---

## ⚙️ Mantener la aplicación corriendo en segundo plano

Si desconectas SSH y quieres que siga corriendo:

```bash
# En Raspberry Pi
cd ~/camaraproject

# Usar screen (si no está instalado: sudo apt-get install screen)
screen -S camara
source venv/bin/activate
python3 app.py

# Presiona Ctrl+A, luego D para desconectarte (app sigue corriendo)
# Luego puedes cerrar la terminal

# Para volver a conectar:
screen -r camara
```

---

## 🔍 Verificación - Checklist

- [ ] Raspberry Pi actualizada (`sudo apt-get update` sin errores)
- [ ] Dependencias instaladas (no hubo errores de `apt-get`)
- [ ] Archivos copiados (ls -la ~/camaraproject muestra archivos)
- [ ] Ambiente virtual activo (ves `(venv)` al inicio de línea)
- [ ] Paquetes instalados (pip list muestra opencv, flask, scikit-learn)
- [ ] Fotos capturadas (ls dataset/processed/ muestra carpetas)
- [ ] Modelo entrenado (ls -lh models/faces_model_lite.pkl muestra archivo)
- [ ] Aplicación corriendo (ves "Running on http://...")
- [ ] Acceso desde PC (abre http://IP:5000 en navegador)

---

## 🆘 Errores comunes y soluciones

### Error: "No module named 'flask'"

```bash
source venv/bin/activate
pip install flask
```

### Error: "No module named 'cv2'"

```bash
source venv/bin/activate
pip install opencv-python
# Esto tarda 5-8 minutos
```

### Error: "No se encuentra la cámara"

```bash
# Verificar dispositivos de video
ls -la /dev/video*

# Si no sale nada, la cámara no está conectada o no es detectada
# Conecta/reconecta la cámara USB
# Si sigue sin funcionar: sudo modprobe uvcvideo
```

### Error: "Permission denied" en /dev/video0

```bash
# Agregarte al grupo video
sudo usermod -a -G video pi

# Desconecta y vuelve a conectar SSH
exit
# Vuelve a conectar
```

### Error: "pip install tarda mucho"

```bash
# Es NORMAL - opencv-python y scikit-learn compilan en Raspberry Pi
# opencv-python tarda 5-8 minutos
# scikit-learn tarda 3-5 minutos
# Total: 10-15 minutos
# NO INTERRUMPAS

# Si está colgado más de 30 minutos, presiona Ctrl+C y prueba:
pip install --no-cache-dir opencv-python scikit-learn
```

### Error: "Modelo no encontrado"

```bash
# Primero captura fotos
python3 scripts/capture_faces.py "tu_nombre"

# Luego entrena
python3 scripts/train_model.py

# Verifica que se creó el modelo
ls -lh models/faces_model_lite.pkl
```

### Error: "Solo reconoce a una persona"

- Captura más fotos (mínimo 30-40 por persona)
- Desde diferentes ángulos
- Con diferente iluminación
- Vuelve a entrenar: `python3 scripts/train_model.py`

### Error: "Es muy lento (1-2 FPS)"

```bash
# Esto es normal en Raspberry Pi 3
# Sin dlib sigue siendo más rápido
# Si necesitas más velocidad:
# 1. Upgraatea a Raspberry Pi 4
# 2. Reduce resolución de cámara (en app.py)
# 3. Aumenta scale_factor en recognize_faces
```

---

## 📊 Verificar instalación

Para verificar que todo está bien instalado:

```bash
cd ~/camaraproject
source venv/bin/activate

python3 << 'EOF'
import cv2
import flask
import sklearn
import numpy as np
print("[✓] OpenCV:", cv2.__version__)
print("[✓] Flask:", flask.__version__)
print("[✓] Scikit-learn:", sklearn.__version__)
print("[✓] NumPy:", np.__version__)
print("[✓] Todos los módulos están instalados correctamente")
EOF
```

---

## 📞 Resumen: Comandos principales

```bash
# Activar ambiente (siempre primero)
cd ~/camaraproject && source venv/bin/activate

# Capturar fotos
python3 scripts/capture_faces.py "nombre_persona"

# Entrenar modelo
python3 scripts/train_model.py

# Ejecutar aplicación
python3 app.py

# Detener (en terminal con app corriendo)
Ctrl + C

# Ver modelo
ls -lh models/faces_model_lite.pkl

# Ver fotos capturadas
ls dataset/processed/
```

---

## ✅ Listo!

Si llegaste hasta aquí sin errores, **¡Tu sistema está funcionando!**

El tiempo total debería ser:
- Instalación: 15-20 minutos
- Captura de fotos: 5-10 minutos
- Entrenamiento: 2-5 minutos
- **Total: ~30 minutos**

**Vs. Con dlib: 3-4 horas**

---

**Versión:** 1.0  
**Fecha:** 12 de noviembre de 2025  
**Plataforma:** Raspberry Pi (probado en Pi 3 y Pi 4)
