#!/bin/bash
# Script de instalación automática SIN DLIB para Raspberry Pi
# Uso: bash install_no_dlib.sh

set -e  # Salir si hay error

echo "========================================"
echo "Instalador SIN DLIB - Raspberry Pi"
echo "========================================"
echo ""

# Verificar que estamos en Raspberry Pi
if ! grep -q "Raspberry\|BCM" /proc/cpuinfo 2>/dev/null; then
    echo "[!] Advertencia: Este script está optimizado para Raspberry Pi"
    echo "[!] Continuando de todas formas..."
fi

# Paso 1: Actualizar sistema
echo "[1/6] Actualizando sistema..."
sudo apt-get update -q
sudo apt-get upgrade -y -q

# Paso 2: Instalar dependencias del sistema
echo "[2/6] Instalando dependencias del sistema..."
sudo apt-get install -y -q \
    python3-pip \
    python3-dev \
    python3-venv \
    libjasper-dev \
    libtiff5 \
    libjasper1 \
    libharfbuzz0b \
    libwebp6 \
    python3-numpy

# Paso 3: Crear ambiente virtual
echo "[3/6] Creando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Paso 4: Actualizar pip
echo "[4/6] Actualizando pip..."
pip install --upgrade pip setuptools wheel -q

# Paso 5: Instalar paquetes Python (SIN DLIB)
echo "[5/6] Instalando paquetes Python..."
echo "      (esto puede tardar 5-10 minutos)"

# Instalar con verbosidad reducida
pip install -q \
    numpy \
    opencv-python \
    flask \
    scikit-learn \
    pillow \
    tqdm

# Paso 6: Crear carpetas necesarias
echo "[6/6] Creando estructura de carpetas..."
mkdir -p models
mkdir -p dataset/processed
mkdir -p dataset/raw
mkdir -p logs

echo ""
echo "========================================"
echo "✓ INSTALACIÓN COMPLETADA"
echo "========================================"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Capturar fotos:"
echo "   source venv/bin/activate"
echo "   python3 scripts/capture_faces.py 'tu_nombre'"
echo ""
echo "2. Entrenar modelo:"
echo "   python3 scripts/train_model.py"
echo ""
echo "3. Ejecutar aplicación:"
echo "   python3 app.py"
echo ""
echo "Accede desde tu PC:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
