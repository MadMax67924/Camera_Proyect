#!/bin/bash

# Script de instalación automática - Sistema sin DLIB
# Instala todas las dependencias necesarias en minutos (no horas)

set -e  # Exit on error

echo "==========================================================================="
echo "  🚀 INSTALADOR AUTOMÁTICO - Reconocimiento Facial SIN DLIB"
echo "==========================================================================="
echo ""

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "[INFO] Sistema detectado: Linux"
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "[INFO] Sistema detectado: macOS"
    OS="macos"
else
    echo "[ERROR] Sistema operativo no soportado: $OSTYPE"
    exit 1
fi

echo ""
echo "==========================================================================="
echo "  PASO 1: Actualizar sistema"
echo "==========================================================================="

if [ "$OS" = "linux" ]; then
    echo "[INFO] Actualizando repositorios..."
    sudo apt update -y
    
    echo "[INFO] Instalando dependencias del sistema..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-dev \
        libopencv-dev \
        python3-opencv \
        libatlas-base-dev \
        libjasper-dev \
        libtiff-dev \
        libjasper-dev \
        libharfbuzz0b \
        libwebp6 \
        libtiff5 \
        libjasper1 \
        libatlas3-base \
        libharfbuzz-icu0 \
        git \
        wget
elif [ "$OS" = "macos" ]; then
    echo "[INFO] Verificando Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "[INFO] Instalando Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "[INFO] Instalando dependencias con Homebrew..."
    brew install python3 opencv
fi

echo "[OK] Dependencias del sistema instaladas"

echo ""
echo "==========================================================================="
echo "  PASO 2: Crear entorno virtual"
echo "==========================================================================="

if [ ! -d "venv" ]; then
    echo "[INFO] Creando entorno virtual..."
    python3 -m venv venv
    echo "[OK] Entorno virtual creado"
else
    echo "[INFO] Entorno virtual ya existe"
fi

# Activar entorno
source venv/bin/activate

echo ""
echo "==========================================================================="
echo "  PASO 3: Actualizar pip y setuptools"
echo "==========================================================================="

pip install --upgrade pip setuptools wheel -q

echo "[OK] pip actualizado"

echo ""
echo "==========================================================================="
echo "  PASO 4: Instalar dependencias Python (SIN DLIB)"
echo "==========================================================================="

echo "[INFO] Instalando paquetes Python..."

packages=(
    "flask>=2.0.0"
    "opencv-python>=4.5.0"
    "numpy>=1.19.0"
    "mediapipe>=0.8.0"
    "scipy>=1.7.0"
    "tqdm>=4.50.0"
    "Pillow>=8.0.0"
)

for package in "${packages[@]}"; do
    echo "[INFO] Instalando $package..."
    pip install "$package" -q
done

echo "[OK] Dependencias Python instaladas"

echo ""
echo "==========================================================================="
echo "  PASO 5: Verificar instalación"
echo "==========================================================================="

echo "[INFO] Verificando paquetes instalados..."

python3 -c "
import cv2
print('[OK] OpenCV:', cv2.__version__)

import numpy as np
print('[OK] NumPy:', np.__version__)

import mediapipe as mp
print('[OK] MediaPipe:', mp.__version__)

import scipy
print('[OK] SciPy:', scipy.__version__)

import flask
print('[OK] Flask:', flask.__version__)
" || {
    echo "[ERROR] Algún paquete no se instaló correctamente"
    exit 1
}

echo ""
echo "==========================================================================="
echo "  PASO 6: Crear estructura de directorios"
echo "==========================================================================="

mkdir -p dataset/raw
mkdir -p models
mkdir -p logs

echo "[OK] Estructura de directorios creada"

echo ""
echo "==========================================================================="
echo "  ✅ INSTALACIÓN COMPLETADA"
echo "==========================================================================="
echo ""
echo "🎉 ¡Listo para usar!"
echo ""
echo "Próximos pasos:"
echo ""
echo "1️⃣  CAPTURAR FOTOS DE ENTRENAMIENTO:"
echo "    $ source venv/bin/activate"
echo "    $ python3 scripts/capture_faces.py"
echo ""
echo "2️⃣  ENTRENAR MODELO:"
echo "    $ python3 scripts/train_model.py"
echo ""
echo "3️⃣  EJECUTAR SERVIDOR:"
echo "    $ python3 app.py"
echo ""
echo "4️⃣  ABRIR EN NAVEGADOR:"
echo "    http://localhost:5000"
echo ""
echo "==========================================================================="
echo "  📚 INFORMACIÓN IMPORTANTE"
echo "==========================================================================="
echo ""
echo "✅ Sistema sin DLIB:"
echo "   - ⚡ Instalación rápida (5-10 minutos)"
echo "   - 🚀 Reconocimiento en tiempo real"
echo "   - 📱 Compatible con Raspberry Pi"
echo ""
echo "📋 Dependencias instaladas:"
echo "   - Flask (servidor web)"
echo "   - OpenCV (procesamiento de imágenes)"
echo "   - MediaPipe (detección facial)"
echo "   - NumPy y SciPy (cálculos)"
echo ""
echo "📖 Para más información:"
echo "   $ cat INSTALACION_SIN_DLIB.md"
echo ""
echo "==========================================================================="
