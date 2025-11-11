# 🔧 Solución de Problemas de Instalación

## Problema Resuelto: face_recognition_models

Si al ejecutar `python app.py` obtienes este error:

```
Please install `face_recognition_models` with this command before using `face_recognition`:
pip install git+https://github.com/ageitgey/face_recognition_models
```

### ✅ Solución (AUTOMATIZADA)

El sistema ahora se configura automáticamente. Solo ejecuta:

```bash
# 1. Configurar permisos y estructura
python3 setup.py

# 2. Instalar dependencias (incluyendo setuptools)
pip3 install -r requirements.txt
```

### 🔍 Causa del Problema

`face_recognition_models` depende de `pkg_resources` que viene en `setuptools`, pero en entornos modernos de Python 3.13, `setuptools` no siempre se instala automáticamente.

### 🛠️ Solución Manual (si la automática falla)

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar setuptools primero
pip install setuptools

# Instalar face_recognition_models
pip install face-recognition-models

# O desde git si falla:
pip install git+https://github.com/ageitgey/face_recognition_models

# Verificar que funciona
python -c "import face_recognition; print('OK')"
```

### ✨ Mejoras Implementadas

1. **[setup.py](setup.py)** - Script automático que:
   - Crea estructura de directorios
   - Configura permisos ejecutables (chmod +x)
   - Verifica archivos críticos

2. **[requirements.txt](requirements.txt)** actualizado con:
   - `setuptools>=65.0.0` (CRÍTICO para face_recognition)
   - `face-recognition-models>=0.3.0`
   - Todas las dependencias necesarias

3. **[fix_face_recognition.py](fix_face_recognition.py)** - Script de emergencia
   - Reinstala completamente face_recognition
   - Útil si algo sale mal

### 📋 Checklist de Instalación

- [ ] Ejecutar `python3 setup.py` (configura permisos)
- [ ] Ejecutar `pip3 install -r requirements.txt`
- [ ] Verificar: `python -c "import face_recognition"`
- [ ] Ejecutar: `python app.py`
- [ ] Abrir navegador: `http://IP:5000`

### ⚠️ Advertencias de pkg_resources

Al importar face_recognition verás este warning (es normal):

```
UserWarning: pkg_resources is deprecated as an API.
```

**Es solo un WARNING**, no afecta el funcionamiento. face_recognition_models aún usa pkg_resources pero funcionará correctamente.

### 🐛 Otros Problemas Comunes

#### "No module named 'dlib'"

En Raspberry Pi la compilación de dlib tarda mucho:

```bash
# Aumentar swap
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Instalar dlib (30-60 min)
pip3 install dlib --no-cache-dir
```

#### "Permission denied" en Fedora

```bash
# Agregar usuario al grupo video
sudo usermod -aG video $USER

# CERRAR SESIÓN y volver a entrar
# O forzar:
newgrp video
```

#### Cámara no detectada

```bash
# Ver cámaras disponibles
ls -l /dev/video*

# Verificar permisos
groups | grep video

# Probar cámara
v4l2-ctl --list-devices
```

### ✅ Verificación Final

Si todo funciona correctamente, `python app.py` mostrará:

```
======================================================================
  SISTEMA DE RECONOCIMIENTO FACIAL - MEJORADO
  Plataforma: PC/Laptop (Fedora) o Raspberry Pi 3
======================================================================

[OK] Cámaras encontradas: [0]
[OK] Clasificador Haar Cascade cargado correctamente
[INFO] No hay modelo entrenado (normal en primera ejecución)

======================================================================
  ✅ SISTEMA ACTIVO
======================================================================

  📹 URL Principal: http://192.168.X.X:5000
  🧠 Reconocimiento: No disponible (entrenar modelo primero)
```

Luego podrás:
1. Abrir `http://192.168.X.X:5000` en navegador
2. Ver streaming de video
3. Activar detección facial
4. Capturar fotos: `python3 scripts/capture_faces.py`
5. Entrenar modelo: `python3 scripts/train_model.py`
6. Activar reconocimiento desde interfaz web

---

**¿Sigues teniendo problemas?** Consulta [RECONOCIMIENTO.md](RECONOCIMIENTO.md) para solución de problemas más detallada.
