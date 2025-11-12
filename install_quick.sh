#!/bin/bash
# ===========================================================================
# INSTALACIÓN RÁPIDA - Sistema de Reconocimiento Facial
# Ejecutar una sola vez: bash install_quick.sh
# ===========================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  INSTALACIÓN RÁPIDA - SISTEMA RECONOCIMIENTO FACIAL               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Detectar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Instálalo primero."
    exit 1
fi

PYTHON=$(which python3)
echo "[✓] Python: $PYTHON"
echo ""

# Paso 1: Crear estructura de directorios
echo "[1/3] Creando estructura de directorios..."
mkdir -p dataset/raw dataset/unknown dataset/processed models logs config
echo "  ✓ dataset/raw"
echo "  ✓ dataset/unknown"
echo "  ✓ dataset/processed"
echo "  ✓ models"
echo "  ✓ logs"
echo "  ✓ config"
echo ""

# Paso 2: Instalar dependencias
echo "[2/3] Instalando dependencias Python..."
echo "  (Esto puede tomar 2-5 minutos...)"
echo ""

$PYTHON -m pip install -q --upgrade pip
$PYTHON -m pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "  ✓ Dependencias instaladas"
else
    echo ""
    echo "  ⚠️  Algunas dependencias fallaron, continuando..."
fi

echo ""

# Paso 3: Verificar instalación
echo "[3/3] Verificando instalación..."
$PYTHON test_system.py

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ INSTALACIÓN COMPLETADA                                         ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 PRÓXIMOS PASOS:"
echo ""
echo "  1. Interfaz interactiva (recomendado):"
echo "     python3 master.py"
echo ""
echo "  2. O comandos directos:"
echo "     python3 scripts/capture_faces.py \"Tu Nombre\""
echo "     python3 scripts/train_model_new.py"
echo "     python3 app.py"
echo ""
echo "📚 Para más información:"
echo "     cat GUIA_RAPIDA.md"
echo ""
