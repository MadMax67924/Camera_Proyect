#!/bin/bash
# Script de ayuda para configurar WiFi 2.4 GHz en Raspberry Pi

echo "========================================================================"
echo "  CONFIGURACIÓN DE WiFi 2.4 GHz para Raspberry Pi"
echo "========================================================================"
echo ""

# Verificar si es root
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] Este script debe ejecutarse como root"
    echo "Usa: sudo bash setup_wifi.sh"
    exit 1
fi

echo "[INFO] Verificando interfaces WiFi disponibles..."
echo ""

# Mostrar interfaces disponibles
iw dev | grep Interface

echo ""
echo "========================================================================"
echo "  INFORMACIÓN SOBRE WiFi 2.4 GHz vs 5 GHz"
echo "========================================================================"
echo ""
echo "  El Raspberry Pi 3 Model B tiene WiFi 802.11n que soporta:"
echo "  ✓ 2.4 GHz (802.11b/g/n)"
echo "  ✗ 5 GHz (NO soportado en RPi3 Model B)"
echo ""
echo "  El Raspberry Pi 3 Model B+ y superiores soportan:"
echo "  ✓ 2.4 GHz (802.11b/g/n)"
echo "  ✓ 5 GHz (802.11ac)"
echo ""
echo "========================================================================"
echo "  CONFIGURACIÓN MANUAL DE WiFi"
echo "========================================================================"
echo ""
echo "Para configurar WiFi 2.4 GHz, edita el archivo /etc/wpa_supplicant/wpa_supplicant.conf"
echo ""
echo "Ejemplo de configuración:"
echo ""
echo "country=US"
echo "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev"
echo "update_config=1"
echo ""
echo "network={"
echo '    ssid="TU_NOMBRE_WIFI"'
echo '    psk="TU_PASSWORD"'
echo "    key_mgmt=WPA-PSK"
echo "    # Para forzar 2.4 GHz (opcional):"
echo "    # freq_list=2412 2437 2462"
echo "}"
echo ""
echo "========================================================================"
echo "  COMANDOS ÚTILES"
echo "========================================================================"
echo ""
echo "Ver redes disponibles:"
echo "  sudo iwlist wlan0 scan | grep -i essid"
echo ""
echo "Ver estado de conexión:"
echo "  iwconfig wlan0"
echo ""
echo "Ver IP asignada:"
echo "  hostname -I"
echo ""
echo "Reiniciar WiFi:"
echo "  sudo systemctl restart networking"
echo "  sudo wpa_cli -i wlan0 reconfigure"
echo ""
echo "========================================================================"

# Preguntar si desea editar wpa_supplicant.conf
read -p "¿Deseas editar la configuración WiFi ahora? (s/n): " respuesta

if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
    echo ""
    echo "[INFO] Abriendo editor..."
    nano /etc/wpa_supplicant/wpa_supplicant.conf

    echo ""
    read -p "¿Reiniciar el servicio WiFi ahora? (s/n): " reiniciar

    if [ "$reiniciar" = "s" ] || [ "$reiniciar" = "S" ]; then
        echo "[INFO] Reiniciando WiFi..."
        wpa_cli -i wlan0 reconfigure
        sleep 2
        echo ""
        echo "[INFO] IP asignada:"
        hostname -I
    fi
fi

echo ""
echo "[INFO] Configuración completada"
