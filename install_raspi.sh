#!/bin/bash

# ============================================================================
# SCRIPT DE INSTALACIÓN PARA RASPBERRY PI CON CONEXIÓN LENTA
# ============================================================================
# Este script instala las dependencias con manejo de timeouts y reintentos

set -e  # Salir si hay error

echo "=================================================="
echo "🚀 Instalación de Dependencias - Raspberry Pi"
echo "=================================================="
echo ""

# Configurar pip para tolerar timeouts
export PIP_DEFAULT_TIMEOUT=300

# Actualizar pip primero
echo "📦 Actualizando pip..."
python3 -m pip install --upgrade pip --no-cache-dir -q

echo ""
echo "📥 Instalando dependencias (con reintentos automáticos)..."
echo ""

# Instalar con reintentos y timeouts más largos
python3 -m pip install \
    --default-timeout=300 \
    --retries 5 \
    --no-cache-dir \
    -r requirements_raspi.txt

echo ""
echo "=================================================="
echo "✅ Instalación completada exitosamente"
echo "=================================================="
echo ""
echo "Dependencias instaladas:"
python3 -m pip list | grep -E "flask|opencv|numpy|Pillow|scikit|scipy|pyserial"
echo ""
echo "Próximos pasos:"
echo "1. Ejecuta: python3 scripts/train_model_new.py"
echo "2. O prueba: python3 app.py"
echo ""
