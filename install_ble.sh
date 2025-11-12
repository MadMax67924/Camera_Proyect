#!/bin/bash
#
# Instalador BLE - Control de Puerta
# Instala todas las dependencias necesarias para el sistema BLE
#

echo "============================================"
echo "  Instalador BLE - Sistema de Puerta"
echo "============================================"
echo ""

# Detectar sistema operativo
if [ -f /proc/cpuinfo ]; then
    if grep -q "Raspberry Pi" /proc/cpuinfo; then
        PLATFORM="raspberry"
        echo "✓ Plataforma detectada: Raspberry Pi"
    else
        PLATFORM="linux"
        echo "✓ Plataforma detectada: Linux PC"
    fi
else
    PLATFORM="unknown"
    echo "⚠ Plataforma desconocida"
fi

echo ""
echo "Paso 1/4: Instalando dependencias del sistema..."
echo "----------------------------------------------"

if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y bluetooth bluez libbluetooth-dev python3-pip

    # Activar Bluetooth
    sudo systemctl start bluetooth
    sudo systemctl enable bluetooth

    echo "✓ Dependencias del sistema instaladas"
else
    echo "⚠ apt-get no disponible, instala manualmente:"
    echo "   - bluetooth"
    echo "   - bluez"
    echo "   - libbluetooth-dev"
fi

echo ""
echo "Paso 2/4: Instalando dependencias Python..."
echo "----------------------------------------------"

pip3 install bleak>=0.21.0

if [ "$PLATFORM" = "raspberry" ]; then
    pip3 install RPi.GPIO>=0.7.1
    echo "✓ RPi.GPIO instalado"
fi

echo "✓ Dependencias Python instaladas"

echo ""
echo "Paso 3/4: Verificando instalación..."
echo "----------------------------------------------"

python3 -c "import bleak; print('✓ bleak instalado correctamente')" 2>/dev/null || echo "✗ Error con bleak"

if [ "$PLATFORM" = "raspberry" ]; then
    python3 -c "import RPi.GPIO; print('✓ RPi.GPIO instalado correctamente')" 2>/dev/null || echo "⚠ RPi.GPIO no disponible (opcional)"
fi

echo ""
echo "Paso 4/4: Configurando permisos..."
echo "----------------------------------------------"

# Añadir usuario al grupo bluetooth
if getent group bluetooth > /dev/null 2>&1; then
    sudo usermod -a -G bluetooth $USER
    echo "✓ Usuario añadido al grupo bluetooth"
    echo "⚠ Debes cerrar sesión y volver a entrar para que los permisos tengan efecto"
else
    echo "⚠ Grupo bluetooth no encontrado"
fi

echo ""
echo "============================================"
echo "  ✓ INSTALACIÓN COMPLETA"
echo "============================================"
echo ""
echo "Próximos pasos:"
echo "  1. Cierra sesión y vuelve a entrar (para permisos bluetooth)"
echo "  2. Enciende tu Arduino Nano 33 BLE"
echo "  3. Ejecuta: python3 app.py --install-deps"
echo "  4. O ejecuta: python3 ble_door_controller.py"
echo ""
echo "Para probar la conexión BLE:"
echo "  python3 ble_door_button_test.py"
echo ""
echo "Documentación:"
echo "  - BLE_SETUP.md - Setup básico"
echo "  - INTEGRACION_BLE.md - Integración completa"
echo ""
