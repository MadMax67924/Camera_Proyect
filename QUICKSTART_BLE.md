# Quick Start - Sistema BLE de Puerta

## Instalación Rápida (5 minutos)

### 1. Instalar Dependencias BLE

```bash
# Opción A: Script automático (recomendado)
./install_ble.sh

# Opción B: Manual
pip3 install bleak>=0.21.0
sudo apt-get install bluetooth bluez libbluetooth-dev
```

### 2. Configurar Usuarios Autorizados

Edita `config/authorized_users.json`:

```json
{
  "authorized_users": ["Lucho", "Maxi", "Nacho", "Nico", "Pablo", "Victor"],
  "door_open_duration": 3,
  "cooldown_time": 5
}
```

### 3. Arrancar el Sistema

```bash
# Con auto-instalación de dependencias
python3 app.py --install-deps

# Con auto-conexión BLE
python3 app.py --ble-autoconnect

# Completo
python3 app.py --install-deps --ble-autoconnect
```

## Uso Básico

### Interfaz Web

1. Abre `http://<IP_RASPBERRY>:5000`
2. Activa **"Reconocimiento Facial"**
3. Click en **"Conectar BLE"**
4. Click en **"Activar Control Automático"**
5. ✓ El sistema abrirá la puerta automáticamente cuando reconozca caras autorizadas

### Comandos API

```bash
# Ver estado
curl http://localhost:5000/ble/status

# Conectar
curl -X POST http://localhost:5000/ble/connect

# Activar control automático
curl -X POST http://localhost:5000/ble/toggle

# Abrir puerta manualmente
curl -X POST http://localhost:5000/ble/open_door
```

## Pruebas Rápidas

### Test 1: Verificar BLE disponible
```bash
python3 core/dependency_checker.py
```

### Test 2: Probar conexión BLE
```bash
python3 ble_door_controller.py
```

### Test 3: Test con botón/teclado
```bash
python3 ble_door_button_test.py
```

## Troubleshooting Express

| Problema | Solución |
|----------|----------|
| "BLE not available" | `pip3 install bleak` |
| "Device not found" | Verifica que Arduino está encendido y anunciando |
| "Permission denied" | `sudo usermod -a -G bluetooth $USER` (cierra sesión después) |
| No abre automáticamente | 1. Activa reconocimiento<br>2. Conecta BLE<br>3. Activa control automático |

## Flujo de Trabajo Típico

```
1. Arrancar: python3 app.py --ble-autoconnect
2. Abrir navegador: http://192.168.1.X:5000
3. Activar reconocimiento facial
4. Activar control BLE automático
5. ✓ Sistema funcionando
```

## Archivos Importantes

- `app.py` - Servidor principal (YA MODIFICADO ✓)
- `core/ble_door_integration.py` - Gestor BLE (NUEVO ✓)
- `config/authorized_users.json` - Lista de usuarios (NUEVO ✓)
- `ble_door_controller.py` - Control manual (NUEVO ✓)
- `INTEGRACION_BLE.md` - Documentación completa

## Características

- ✓ Reconocimiento facial en tiempo real
- ✓ Control BLE de puerta
- ✓ Lista de usuarios autorizados
- ✓ Sistema de cooldown (evita aperturas repetidas)
- ✓ Apertura automática y manual
- ✓ API REST completa
- ✓ Verificación automática de dependencias
- ✓ Instalación automática de paquetes

## Comandos Útiles

```bash
# Ver logs en tiempo real
python3 app.py | grep BLE

# Ver estado BLE
curl http://localhost:5000/ble/status | jq

# Añadir usuario autorizado
curl -X POST http://localhost:5000/ble/add_user \
  -H "Content-Type: application/json" \
  -d '{"name": "NuevoUsuario"}'

# Escanear dispositivos BLE
sudo hcitool lescan

# Reiniciar Bluetooth
sudo systemctl restart bluetooth
```

## Parámetros de Arranque

```bash
python3 app.py                    # Normal
python3 app.py --install-deps     # Auto-instalar dependencias
python3 app.py --ble-autoconnect  # Auto-conectar BLE
python3 app.py --no-check-deps    # Sin verificar dependencias (más rápido)
```

## Documentación Completa

Para más detalles, consulta:
- [INTEGRACION_BLE.md](INTEGRACION_BLE.md) - Documentación completa
- [BLE_SETUP.md](BLE_SETUP.md) - Setup detallado
- [README.md](README.md) - Información general del proyecto
