#!/bin/bash
# Script de instalación universal para Raspberry Pi y Fedora/RHEL

set -e

echo "========================================================================"
echo "  INSTALACIÓN DEL SISTEMA DE DETECCIÓN FACIAL"
echo "========================================================================"
echo ""

# Detectar distribución
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo "[ERROR] No se pudo detectar el sistema operativo"
    exit 1
fi

echo "[INFO] Sistema detectado: $OS $VERSION"
echo ""

# Función para Raspberry Pi (Debian/Raspbian)
install_raspberry() {
    echo "[INFO] Instalando dependencias para Raspberry Pi..."
    echo ""

    # Actualizar repositorios
    sudo apt-get update

    # Instalar Python y dependencias del sistema
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-opencv \
        libopencv-dev \
        libatlas-base-dev \
        libjasper-dev \
        libqtgui4 \
        libqt4-test \
        libhdf5-dev \
        libhdf5-serial-dev \
        v4l-utils

    # Instalar dependencias de Python
    pip3 install --upgrade pip
    pip3 install -r requirements.txt

    echo ""
    echo "[INFO] Verificando cámaras disponibles..."
    v4l2-ctl --list-devices || echo "[WARNING] No se encontraron cámaras USB"

    echo ""
    echo "[OK] Instalación completada para Raspberry Pi"
}

# Función para Fedora
install_fedora() {
    echo "[INFO] Instalando dependencias para Fedora..."
    echo ""

    # Instalar Python y dependencias del sistema
    sudo dnf install -y \
        python3 \
        python3-pip \
        python3-devel \
        opencv \
        opencv-devel \
        python3-opencv \
        gcc \
        gcc-c++ \
        cmake \
        v4l-utils \
        mesa-libGL

    # Agregar usuario al grupo video para acceso a la cámara
    sudo usermod -aG video $USER
    echo ""
    echo "[INFO] Usuario $USER agregado al grupo 'video'"
    echo "[WARNING] Necesitas cerrar sesión y volver a entrar para que los cambios tengan efecto"

    # Instalar dependencias de Python
    pip3 install --user --upgrade pip
    pip3 install --user -r requirements.txt

    echo ""
    echo "[INFO] Verificando cámaras disponibles..."
    v4l2-ctl --list-devices || echo "[WARNING] No se encontraron cámaras"

    echo ""
    echo "[OK] Instalación completada para Fedora"
}

# Función para Ubuntu/Debian
install_debian() {
    echo "[INFO] Instalando dependencias para Debian/Ubuntu..."
    echo ""

    # Actualizar repositorios
    sudo apt-get update

    # Instalar Python y dependencias del sistema
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-opencv \
        libopencv-dev \
        v4l-utils

    # Agregar usuario al grupo video
    sudo usermod -aG video $USER
    echo ""
    echo "[INFO] Usuario $USER agregado al grupo 'video'"

    # Instalar dependencias de Python
    pip3 install --upgrade pip
    pip3 install -r requirements.txt

    echo ""
    echo "[INFO] Verificando cámaras disponibles..."
    v4l2-ctl --list-devices || echo "[WARNING] No se encontraron cámaras"

    echo ""
    echo "[OK] Instalación completada para Debian/Ubuntu"
}

# Ejecutar instalación según el sistema operativo
case $OS in
    raspbian|debian)
        # Verificar si es Raspberry Pi
        if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
            install_raspberry
        else
            install_debian
        fi
        ;;
    fedora|rhel|centos)
        install_fedora
        ;;
    ubuntu)
        install_debian
        ;;
    *)
        echo "[ERROR] Sistema operativo no soportado: $OS"
        echo "Soportados: Raspberry Pi OS, Fedora, Ubuntu, Debian"
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "  ✅ INSTALACIÓN COMPLETADA"
echo "========================================================================"
echo ""
echo "Siguiente paso:"
echo "  python3 app.py"
echo ""
echo "Si la cámara no funciona en Fedora:"
echo "  1. Cierra sesión y vuelve a entrar (para aplicar permisos)"
echo "  2. Verifica: groups | grep video"
echo "  3. Lista cámaras: ls -l /dev/video*"
echo ""
echo "========================================================================"
