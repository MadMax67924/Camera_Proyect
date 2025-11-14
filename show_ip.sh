#!/bin/bash

# Script para mostrar IPs disponibles

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🌐 Direcciones IP disponibles"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Método 1: hostname -I
if command -v hostname &> /dev/null; then
    echo "📍 IPs detectadas (hostname):"
    IPS=$(hostname -I)
    for ip in $IPS; do
        echo "   ├─ $ip"
    done
    echo ""
fi

# Método 2: ip addr show
if command -v ip &> /dev/null; then
    echo "📍 Interfaces de red:"
    ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | while read ip; do
        interface=$(ip -4 addr show | grep -B 2 "$ip" | head -1 | awk '{print $2}' | sed 's/:$//')
        if [ "$ip" != "127.0.0.1" ]; then
            echo "   ├─ $interface: $ip ✅ (usar esta)"
        else
            echo "   ├─ $interface: $ip (localhost)"
        fi
    done
    echo ""
fi

# Sugerencia de URL
MAIN_IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -n 1)

if [ -n "$MAIN_IP" ]; then
    echo "═══════════════════════════════════════════════════════════"
    echo "✨ URL para compartir en la red local:"
    echo ""
    echo "   🔗 http://$MAIN_IP:8000"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "💡 Cómo usar:"
    echo "   1. Copia la URL de arriba"
    echo "   2. Ábrela en cualquier navegador de la misma red"
    echo "   3. ¡Listo! Verás el stream de la cámara"
    echo ""
    echo "📱 Compatible con:"
    echo "   ✓ Computadoras (Windows, Mac, Linux)"
    echo "   ✓ Smartphones (Android, iOS)"
    echo "   ✓ Tablets"
    echo "   ✓ Cualquier dispositivo con navegador web"
    echo ""
else
    echo "⚠️  No se pudo detectar una IP de red"
    echo "   Verifica tu conexión de red"
fi

echo "═══════════════════════════════════════════════════════════"
echo ""
