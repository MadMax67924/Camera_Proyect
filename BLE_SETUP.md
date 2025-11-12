# Configuración BLE - Control de Puerta

## Descripción

Sistema de control de puerta mediante Bluetooth Low Energy (BLE) que comunica la Raspberry Pi con un Arduino Nano 33 BLE.

## Arquitectura

```
Raspberry Pi 3  <--BLE-->  Arduino Nano 33 BLE  <--UART-->  Arduino UNO (Motor)
   (Python)                    (BLE Bridge)                   (Control)
```

## Componentes

### 1. Arduino Nano 33 BLE (Bridge BLE)
- Recibe comandos BLE desde la Raspberry Pi
- Reenvía comandos por UART al Arduino UNO
- Servicio BLE UUID: `12345678-1234-5678-1234-56789abcdef0`
- Característica UUID: `12345678-1234-5678-1234-56789abcdef1`

### 2. Raspberry Pi (Controlador)
- Detecta caras con el sistema de reconocimiento facial
- Envía comandos BLE para abrir/cerrar puerta
- Scripts disponibles:
  - `ble_door_controller.py` - Control completo con menú
  - `ble_door_button_test.py` - Prueba con botón físico o teclado

## Instalación

### En la Raspberry Pi

```bash
# Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install -y bluetooth bluez libbluetooth-dev

# Activar Bluetooth
sudo systemctl start bluetooth
sudo systemctl enable bluetooth

# Instalar dependencias Python
pip3 install bleak>=0.21.0
pip3 install RPi.GPIO>=0.7.1  # Solo para Raspberry Pi
```

### Verificar Bluetooth

```bash
# Ver estado
sudo systemctl status bluetooth

# Ver adaptadores
hciconfig

# Escanear dispositivos (opcional)
sudo hcitool lescan
```

## Uso

### Modo 1: Control Interactivo

```bash
python3 ble_door_controller.py
```

**Opciones:**
1. **Modo interactivo** - Control manual desde terminal
   - Busca automáticamente "NanoDoorBLE"
   - Permite escanear todos los dispositivos BLE
   - Comandos: `A` (abrir), `C` (cerrar), `Q` (salir)

2. **Modo automático** - Envía comando y sale
   - Busca, conecta, envía 'A' y desconecta

**Ejemplo de sesión:**
```
$ python3 ble_door_controller.py

Selecciona modo:
  1. Modo interactivo (manual)
  2. Modo automático (envía 'A' y sale)

Modo [1/2]: 1

Buscando 'NanoDoorBLE'...
✓ Encontrado: NanoDoorBLE [AA:BB:CC:DD:EE:FF]
Conectando a AA:BB:CC:DD:EE:FF...
✓ Conectado exitosamente
✓ Servicio encontrado: 12345678-1234-5678-1234-56789abcdef0

COMANDOS DISPONIBLES:
  A o a  - Abrir puerta
  C o c  - Cerrar puerta
  Q o q  - Salir

Comando: a
>>> Enviando comando ABRIR PUERTA
✓ Comando enviado: ABRIR (0x41)
```

### Modo 2: Prueba con Botón

```bash
python3 ble_door_button_test.py
```

**Modos de operación:**

1. **Con GPIO** (Raspberry Pi con botón físico):
   - Conecta un botón al GPIO17 (pin 11)
   - Esquema:
     ```
     GPIO17 (Pin 11) ----[Botón]---- GND (Pin 9)
     ```
   - Presiona el botón para enviar comando de apertura

2. **Con teclado** (cualquier PC):
   - Fallback automático si no hay GPIO
   - Presiona `a` + ENTER para abrir
   - Presiona `q` + ENTER para salir

**Ejemplo:**
```
$ python3 ble_door_button_test.py

✓ GPIO configurado: Botón en GPIO17
Buscando 'NanoDoorBLE'...
✓ Encontrado: NanoDoorBLE [AA:BB:CC:DD:EE:FF]
✓ Conectado exitosamente

Esperando botón... (Ctrl+C para salir)

🔔 ¡Botón presionado!
✓ Comando ABRIR enviado
```

## Comandos BLE

| Comando | Byte | Descripción |
|---------|------|-------------|
| `'A'`   | 0x41 | Abrir puerta |
| `'C'`   | 0x43 | Cerrar puerta |

## Conexión de Hardware

### Botón en Raspberry Pi (Opcional)

```
     3.3V
      |
      |
    [10kΩ] (pull-up interno)
      |
      +---- GPIO17 (Pin 11)
      |
   [Botón]
      |
     GND (Pin 9)
```

**Pines Raspberry Pi:**
- Pin 11: GPIO17 (entrada del botón)
- Pin 9: GND
- Pin 1: 3.3V (no necesario si usas pull-up interno)

## Integración con Reconocimiento Facial

Para integrar con el sistema de reconocimiento facial en `app.py`:

```python
import asyncio
from ble_door_controller import BLEDoorController

# Crear controlador global
ble_controller = BLEDoorController()

async def init_ble():
    """Inicializar BLE al arranque"""
    device = await ble_controller.find_nano_device()
    if device:
        await ble_controller.connect()

async def open_door_for_recognized_face(name):
    """Abrir puerta cuando se reconoce una cara autorizada"""
    if ble_controller.connected:
        await ble_controller.open_door()
        print(f"Puerta abierta para: {name}")
```

## Troubleshooting

### Error: "No se encontró el dispositivo"
```bash
# Verificar que el Arduino está anunciando
sudo hcitool lescan

# Reiniciar Bluetooth
sudo systemctl restart bluetooth

# Dar permisos al usuario
sudo usermod -a -G bluetooth $USER
```

### Error: "Permission denied"
```bash
# Ejecutar con sudo (no recomendado)
sudo python3 ble_door_controller.py

# O dar permisos permanentes
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3)
```

### Error: "bleak not installed"
```bash
pip3 install bleak
```

### Error: "Device disconnected"
- Verificar que el Arduino está encendido
- Verificar que está dentro del rango BLE (~10 metros)
- Reiniciar el Arduino Nano 33 BLE

### El botón no funciona
```bash
# Verificar GPIO
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"

# Ver estado del pin
gpio readall | grep 17
```

## Pruebas Rápidas

### 1. Escanear dispositivos BLE
```bash
python3 -c "
import asyncio
from bleak import BleakScanner

async def scan():
    devices = await BleakScanner.discover(timeout=5)
    for d in devices:
        print(f'{d.name} - {d.address}')

asyncio.run(scan())
"
```

### 2. Enviar comando único
```bash
python3 ble_door_controller.py 2  # Modo automático
```

### 3. Test de GPIO
```bash
python3 -c "
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print('Presiona el botón...')
try:
    while True:
        if GPIO.input(17) == GPIO.LOW:
            print('¡Botón presionado!')
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
"
```

## Notas de Desarrollo

- **Latencia BLE**: ~50-100ms típico
- **Rango**: ~10 metros en línea de vista
- **Consumo**: Muy bajo en modo BLE
- **Reconexión**: Manual (puede automatizarse)
- **Seguridad**: Considerar encriptación para producción

## Referencias

- [Bleak Documentation](https://bleak.readthedocs.io/)
- [Arduino BLE Library](https://www.arduino.cc/en/Reference/ArduinoBLE)
- [RPi.GPIO Documentation](https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/)
