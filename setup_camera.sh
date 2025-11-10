#!/bin/bash
# Script para configurar la cámara para máximo rendimiento

DEVICE="${1:-/dev/video0}"

echo "========================================================================"
echo "  CONFIGURACIÓN DE CÁMARA PARA MÁXIMO FPS"
echo "========================================================================"
echo ""
echo "Dispositivo: $DEVICE"
echo ""

# Verificar que el dispositivo existe
if [ ! -e "$DEVICE" ]; then
    echo "[ERROR] $DEVICE no existe"
    echo ""
    echo "Dispositivos disponibles:"
    ls -l /dev/video* 2>/dev/null || echo "  No se encontraron dispositivos de video"
    exit 1
fi

echo "[INFO] Configuración actual:"
v4l2-ctl -d $DEVICE --get-fmt-video
echo ""

echo "[INFO] Formatos soportados:"
v4l2-ctl -d $DEVICE --list-formats-ext | grep -E "MJPG|YUYV" | head -10
echo ""

# Preguntar qué hacer
echo "Opciones de configuración:"
echo "  1) MJPEG 320x240 @ 30 FPS (Recomendado para 60+ FPS)"
echo "  2) MJPEG 640x480 @ 30 FPS (Más calidad, ~30-45 FPS)"
echo "  3) YUYV 320x240 @ 30 FPS (Si MJPEG no está disponible)"
echo "  4) Solo mostrar información (no cambiar nada)"
echo ""
read -p "Selecciona una opción [1-4]: " option

case $option in
    1)
        echo ""
        echo "[INFO] Configurando MJPEG 320x240 @ 30 FPS..."
        v4l2-ctl -d $DEVICE --set-fmt-video=width=320,height=240,pixelformat=MJPG
        v4l2-ctl -d $DEVICE --set-parm=30
        ;;
    2)
        echo ""
        echo "[INFO] Configurando MJPEG 640x480 @ 30 FPS..."
        v4l2-ctl -d $DEVICE --set-fmt-video=width=640,height=480,pixelformat=MJPG
        v4l2-ctl -d $DEVICE --set-parm=30
        ;;
    3)
        echo ""
        echo "[INFO] Configurando YUYV 320x240 @ 30 FPS..."
        v4l2-ctl -d $DEVICE --set-fmt-video=width=320,height=240,pixelformat=YUYV
        v4l2-ctl -d $DEVICE --set-parm=30
        ;;
    4)
        echo ""
        echo "[INFO] No se realizaron cambios"
        ;;
    *)
        echo ""
        echo "[ERROR] Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "  CONFIGURACIÓN FINAL"
echo "========================================================================"
echo ""
v4l2-ctl -d $DEVICE --get-fmt-video
echo ""
v4l2-ctl -d $DEVICE --get-parm
echo ""

echo "========================================================================"
echo "  INFORMACIÓN DE RENDIMIENTO"
echo "========================================================================"
echo ""

# Obtener formato actual
FORMAT=$(v4l2-ctl -d $DEVICE --get-fmt-video | grep "Pixel Format" | awk '{print $NF}' | tr -d "'")
WIDTH=$(v4l2-ctl -d $DEVICE --get-fmt-video | grep "Width/Height" | awk '{print $3}' | tr -d ',')
HEIGHT=$(v4l2-ctl -d $DEVICE --get-fmt-video | grep "Width/Height" | awk '{print $5}')

echo "Formato: $FORMAT"
echo "Resolución: ${WIDTH}x${HEIGHT}"
echo ""

if [ "$FORMAT" = "MJPG" ]; then
    echo "✅ MJPEG detectado - Excelente rendimiento esperado"
    if [ "$WIDTH" = "320" ]; then
        echo "   FPS esperado sin detección: 60+ FPS"
        echo "   FPS esperado con detección: 25-30 FPS"
    elif [ "$WIDTH" = "640" ]; then
        echo "   FPS esperado sin detección: 45-60 FPS"
        echo "   FPS esperado con detección: 20-30 FPS"
    fi
elif [ "$FORMAT" = "YUYV" ]; then
    echo "⚠️  YUYV detectado - Rendimiento limitado"
    if [ "$WIDTH" = "320" ]; then
        echo "   FPS esperado: 15-20 FPS máximo"
        echo "   Recomendación: Cambiar a MJPEG si es posible"
    else
        echo "   FPS esperado: 3-10 FPS"
        echo "   Recomendación: Usar resolución 320x240 o cambiar a MJPEG"
    fi
fi

echo ""
echo "Ejecuta la aplicación:"
echo "  python3 app.py"
echo ""
echo "Para diagnóstico completo:"
echo "  python3 diagnose_camera.py"
echo ""
echo "========================================================================"
