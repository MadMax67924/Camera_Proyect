#!/bin/bash

# Script de inicio para Raspberry Pi Camera Stream
# Compatible con Raspberry Pi y Fedora Linux

# Hacer ejecutables todos los scripts
chmod +x "$0" 2>/dev/null
if [ -f "show_ip.sh" ]; then
    chmod +x show_ip.sh 2>/dev/null
fi

echo "🚀 Iniciando Raspberry Pi Camera Stream..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detectar sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    echo -e "${GREEN}Sistema detectado: $OS${NC}"
else
    echo -e "${YELLOW}No se pudo detectar el sistema operativo${NC}"
fi

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Entorno virtual no encontrado. Creando...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Entorno virtual creado${NC}"
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias si es necesario
echo "📦 Verificando dependencias..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo -e "${GREEN}✅ Dependencias instaladas${NC}"
echo ""

# Mostrar información de red
echo "🌐 Información de red:"
if command -v ip &> /dev/null; then
    IP_ADDR=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -n 1)
else
    IP_ADDR=$(hostname -I | awk '{print $1}')
fi

echo -e "${GREEN}   IP Local: $IP_ADDR${NC}"
echo -e "${GREEN}   Puerto: 5000${NC}"
echo ""
echo -e "${YELLOW}📱 Accede desde:${NC}"
echo -e "   Local:  http://localhost:5000"
echo -e "   Red:    http://$IP_ADDR:5000"
echo ""

# Verificar si hay una cámara disponible
echo "📹 Verificando cámara..."
if [ -e /dev/video0 ]; then
    echo -e "${GREEN}✅ Cámara detectada en /dev/video0${NC}"
else
    echo -e "${YELLOW}⚠️  No se detectó cámara en /dev/video0${NC}"
    echo -e "${YELLOW}   La aplicación intentará detectar cámaras disponibles${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎥 Iniciando servidor...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}📱 URLs de acceso:${NC}"
echo ""
echo -e "${GREEN}   Desde este equipo:${NC}"
echo -e "   └─ http://localhost:5000"
echo -e "   └─ http://127.0.0.1:5000"
echo ""
echo -e "${GREEN}   Desde otros equipos en la red:${NC}"
echo -e "   └─ http://${IP_ADDR}:5000"
echo ""
echo -e "${YELLOW}💡 Tip: Comparte la URL http://${IP_ADDR}:5000 con otros dispositivos${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Iniciar servidor con uvicorn
# Usar --reload solo en desarrollo
uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
