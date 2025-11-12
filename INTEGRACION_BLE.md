# Integración Completa: Reconocimiento Facial + Control BLE de Puerta

## Descripción General

Sistema completo que integra reconocimiento facial en tiempo real con control automático de puerta mediante Bluetooth Low Energy (BLE). Cuando el sistema reconoce una cara autorizada, envía automáticamente un comando BLE al Arduino Nano 33 BLE para abrir la puerta.

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                      RASPBERRY PI 3                             │
│                                                                 │
│  ┌────────────────┐    ┌──────────────────┐    ┌────────────┐ │
│  │   Cámara USB   │───▶│  app.py (Flask)  │───▶│  Interfaz  │ │
│  │                │    │                  │    │    Web     │ │
│  └────────────────┘    │  - Streaming     │    └────────────┘ │
│                        │  - Detección     │                    │
│                        │  - Reconocimiento│                    │
│                        └────────┬─────────┘                    │
│                                 │                              │
│                        ┌────────▼─────────┐                    │
│                        │ BLE Door Manager │                    │
│                        │                  │                    │
│                        │ - Autorización   │                    │
│                        │ - Cooldown       │                    │
│                        │ - Control BLE    │                    │
│                        └────────┬─────────┘                    │
└─────────────────────────────────┼──────────────────────────────┘
                                  │ BLE
                                  ▼
                    ┌──────────────────────────┐
                    │  Arduino Nano 33 BLE     │
                    │                          │
                    │  - Recibe comandos BLE   │
                    │  - Reenvía por UART      │
                    └────────────┬─────────────┘
                                 │ UART
                                 ▼
                    ┌──────────────────────────┐
                    │     Arduino UNO          │
                    │                          │
                    │  - Control de motor      │
                    │  - Apertura de puerta    │
                    └──────────────────────────┘
```

## Archivos Nuevos Creados

### 1. Core Modules

- **[core/ble_door_integration.py](core/ble_door_integration.py)** (395 líneas)
  - Gestor completo del sistema BLE
  - Control de usuarios autorizados
  - Sistema de cooldown para evitar aperturas repetidas
  - Logging de accesos
  - Manejo de conexión/reconexión automática

- **[core/dependency_checker.py](core/dependency_checker.py)** (296 líneas)
  - Verificación automática de dependencias al arrancar
  - Instalación automática de paquetes faltantes
  - Detección de características opcionales disponibles

### 2. Scripts de Control BLE

- **[ble_door_controller.py](ble_door_controller.py)** (233 líneas)
  - Control interactivo desde terminal
  - Modo automático para testing
  - Escaneo de dispositivos BLE
  - Comandos: Abrir (A), Cerrar (C)

- **[ble_door_button_test.py](ble_door_button_test.py)** (235 líneas)
  - Test con botón físico GPIO (Raspberry Pi)
  - Fallback a modo teclado (cualquier PC)
  - Configuración: GPIO17 (pin 11)

### 3. Configuración

- **[config/authorized_users.json](config/authorized_users.json)**
  - Lista de usuarios autorizados
  - Tiempo de apertura de puerta (3s por defecto)
  - Tiempo de cooldown (5s por defecto)

### 4. Documentación

- **[BLE_SETUP.md](BLE_SETUP.md)** - Setup BLE básico
- **[INTEGRACION_BLE.md](INTEGRACION_BLE.md)** - Este archivo

## Instalación

### 1. Instalar Dependencias

```bash
# Automáticamente al arrancar (recomendado)
python3 app.py --install-deps

# O manualmente
pip3 install bleak>=0.21.0 RPi.GPIO>=0.7.1

# En sistemas Linux (Raspberry Pi)
sudo apt-get install bluetooth bluez libbluetooth-dev
sudo systemctl start bluetooth
```

### 2. Configurar Usuarios Autorizados

Edita `config/authorized_users.json`:

```json
{
  "authorized_users": [
    "Lucho",
    "Maxi",
    "Nacho"
  ],
  "door_open_duration": 3,
  "cooldown_time": 5
}
```

### 3. Verificar Arduino Nano 33 BLE

- Debe estar ejecutando el código proporcionado
- Debe anunciar como "NanoDoorBLE"
- UUIDs correctos configurados

## Uso

### Arrancar el Sistema

```bash
# Modo normal (verificación de dependencias automática)
python3 app.py

# Con auto-instalación de dependencias faltantes
python3 app.py --install-deps

# Con auto-conexión BLE al arrancar
python3 app.py --ble-autoconnect

# Combinado
python3 app.py --install-deps --ble-autoconnect

# Sin verificación de dependencias (más rápido)
python3 app.py --no-check-deps
```

### Interfaz Web

Abre tu navegador en: `http://<IP_RASPBERRY>:5000`

**Controles disponibles:**

1. **Detección Facial** - Activa/desactiva detección de rostros
2. **Reconocimiento Facial** - Activa/desactiva reconocimiento
3. **Control BLE** (nuevos):
   - **Conectar BLE** - Conecta al Arduino Nano
   - **Activar Control Automático** - Habilita apertura automática
   - **Abrir Puerta** - Apertura manual
   - **Cerrar Puerta** - Cierre manual

### API REST - Endpoints BLE

#### Ver Estado del Sistema BLE
```bash
curl http://localhost:5000/ble/status
```

Respuesta:
```json
{
  "available": true,
  "enabled": false,
  "connected": true,
  "device_address": "AA:BB:CC:DD:EE:FF",
  "authorized_users": ["Lucho", "Maxi", "Nacho"],
  "total_accesses": 5,
  "recent_accesses": [
    {
      "name": "Lucho",
      "confidence": 0.95,
      "timestamp": 1234567890,
      "time_str": "2024-01-15 10:30:45"
    }
  ]
}
```

#### Conectar al Dispositivo BLE
```bash
curl -X POST http://localhost:5000/ble/connect
```

#### Activar/Desactivar Control Automático
```bash
curl -X POST http://localhost:5000/ble/toggle
```

#### Abrir Puerta Manualmente
```bash
curl -X POST http://localhost:5000/ble/open_door
```

#### Cerrar Puerta
```bash
curl -X POST http://localhost:5000/ble/close_door
```

#### Añadir Usuario Autorizado
```bash
curl -X POST http://localhost:5000/ble/add_user \
  -H "Content-Type: application/json" \
  -d '{"name": "NuevoUsuario"}'
```

#### Eliminar Usuario Autorizado
```bash
curl -X POST http://localhost:5000/ble/remove_user \
  -H "Content-Type: application/json" \
  -d '{"name": "UsuarioAEliminar"}'
```

## Flujo de Operación

### Apertura Automática

1. **Cámara captura frame** (60 FPS)
2. **Reconocimiento activado** → Procesa cada 5 frames
3. **Cara detectada y reconocida** → Obtiene nombre y confianza
4. **Verificación de autorización**:
   - ¿El nombre está en la lista de autorizados?
   - ¿Pasó el tiempo de cooldown?
   - ¿La confianza es > 50%?
5. **Si TODO es OK** → Enviar comando BLE 'A' (abrir)
6. **Arduino Nano 33 BLE** recibe y reenvía por UART
7. **Arduino UNO** activa el motor
8. **Puerta abierta por 3 segundos**
9. **Comando automático 'C'** (cerrar) después de 3s
10. **Cooldown activado** para esa persona (5s)

### Ejemplo de Log

```
[FPS] 18.5 fps | Rostros: 1 | Proc: 54.2ms
[BLE] ✓ Acceso concedido: Lucho (confianza: 95.3%)
[BLE] Puerta abierta por 3s
[BLE] ✓ Comando enviado: ABRIR
[BLE] Puerta cerrada
[BLE] ✓ Comando enviado: CERRAR
```

## Seguridad y Control de Acceso

### Sistema de Cooldown

Evita aperturas repetidas inmediatas:

```python
# En config/authorized_users.json
"cooldown_time": 5  # segundos
```

Si una persona ya abrió la puerta, debe esperar 5 segundos antes de poder abrir de nuevo.

**Ejemplo:**
```
10:30:00 - Lucho abre la puerta ✓
10:30:02 - Lucho intenta abrir → ✗ Cooldown activo (3s restantes)
10:30:05 - Lucho puede abrir de nuevo ✓
```

### Lista de Autorizados

**Modo 1: Lista específica** (recomendado)
```json
{
  "authorized_users": ["Lucho", "Maxi", "Nacho"]
}
```
Solo estas 3 personas pueden abrir la puerta.

**Modo 2: Todos autorizados**
```json
{
  "authorized_users": []
}
```
Lista vacía = todas las caras conocidas pueden abrir.

### Umbral de Confianza

El código verifica `confidence > 0.5` (50%):

```python
if name != 'Unknown' and confidence > 0.5:
    ble_manager.handle_recognized_face(name, confidence)
```

Puedes ajustar este valor en [app.py:362](app.py#L362).

## Configuración Avanzada

### Tiempo de Apertura de Puerta

Edita `config/authorized_users.json`:

```json
{
  "door_open_duration": 5  // 5 segundos en lugar de 3
}
```

### Cambiar Cooldown

```json
{
  "cooldown_time": 10  // 10 segundos entre aperturas
}
```

### Reconexión Automática BLE

El sistema intenta reconectar automáticamente si se pierde la conexión:

```python
async def _send_command_async(self, command: int) -> bool:
    if not self.connected or not self.client:
        print("[BLE] No conectado, intentando reconectar...")
        if not await self._connect_async():
            return False
    # ... enviar comando
```

## Testing y Debugging

### Test 1: Verificar Dependencias

```bash
python3 core/dependency_checker.py
```

Muestra qué dependencias están instaladas y cuáles faltan.

### Test 2: Verificar Conexión BLE

```bash
python3 ble_door_controller.py
```

Modo interactivo para probar la conexión y comandos BLE.

### Test 3: Test con Botón

```bash
python3 ble_door_button_test.py
```

Prueba apertura con botón físico o teclado.

### Test 4: Test del Módulo BLE

```bash
python3 core/ble_door_integration.py
```

Test unitario del gestor BLE.

### Debugging

Activa logs detallados:

```bash
# En app.py, línea 355-364, ya hay prints para debugging
[BLE] ✓ Acceso concedido: Lucho (confianza: 95.3%)
[BLE] ⏳ Cooldown activo para Lucho: 3.2s restantes
[BLE] ✗ Acceso denegado: Desconocido no autorizado
```

## Troubleshooting

### Error: "Module BLE not available"

```bash
pip3 install bleak>=0.21.0
# Si falla, verifica que tienes Python 3.7+
python3 --version
```

### Error: "Device not found"

1. Verifica que el Arduino Nano 33 BLE está encendido
2. Verifica que está anunciando como "NanoDoorBLE"
3. Escanea manualmente:
   ```bash
   sudo hcitool lescan
   ```
4. Reinicia Bluetooth:
   ```bash
   sudo systemctl restart bluetooth
   ```

### Error: "Permission denied" al conectar BLE

```bash
# Opción 1: Ejecutar con sudo (no recomendado)
sudo python3 app.py

# Opción 2: Dar permisos al usuario
sudo usermod -a -G bluetooth $USER
# Luego cierra sesión y vuelve a entrar

# Opción 3: Dar capacidades a Python
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3)
```

### La puerta no abre automáticamente

Checklist:
- [ ] ¿Reconocimiento facial activado? (botón en interfaz)
- [ ] ¿Control BLE conectado? (botón "Conectar BLE")
- [ ] ¿Control automático activado? (botón "Activar Control")
- [ ] ¿La persona está en la lista de autorizados?
- [ ] ¿Pasó el tiempo de cooldown?
- [ ] ¿La confianza es > 50%?

Verifica logs en la terminal donde corre `python3 app.py`.

### Apertura manual funciona pero automática no

Verifica que el reconocimiento está funcionando:

1. Activa reconocimiento en la interfaz web
2. Verifica que aparece el nombre de la persona en el video
3. Verifica en la terminal si hay mensajes de reconocimiento
4. Si no reconoce caras, puede que el modelo necesite reentrenamiento:
   ```bash
   python3 scripts/train_model_with_unknowns.py
   ```

## Estadísticas y Monitoreo

### Ver Accesos Recientes

```bash
curl http://localhost:5000/ble/status | jq '.recent_accesses'
```

Respuesta:
```json
[
  {
    "name": "Lucho",
    "confidence": 0.95,
    "timestamp": 1705318245,
    "time_str": "2024-01-15 10:30:45"
  },
  {
    "name": "Maxi",
    "confidence": 0.92,
    "timestamp": 1705318300,
    "time_str": "2024-01-15 10:31:40"
  }
]
```

### Total de Accesos

```bash
curl http://localhost:5000/ble/status | jq '.total_accesses'
```

## Mejoras Futuras

### Implementadas ✓
- [x] Verificación automática de dependencias
- [x] Instalación automática de paquetes
- [x] Sistema de cooldown
- [x] Lista de usuarios autorizados
- [x] Logging de accesos
- [x] API REST completa
- [x] Reconexión automática BLE

### Por Implementar
- [ ] Interfaz web mejorada con panel de control BLE
- [ ] Notificaciones push cuando alguien abre
- [ ] Historial persistente de accesos (base de datos)
- [ ] Fotos de los accesos guardadas
- [ ] Modo "desbloqueo temporal" para invitados
- [ ] Integración con Google Calendar (horarios)
- [ ] App móvil para control remoto
- [ ] Encriptación de comandos BLE

## Notas de Rendimiento

### Impacto en FPS

- **Sin BLE**: 60+ FPS (modo rápido)
- **Con reconocimiento + BLE**: 15-20 FPS
- **Overhead BLE**: ~5-10ms por comando

El sistema está optimizado para no afectar el rendimiento:
- Comandos BLE en threads separados
- No bloquea el loop principal de captura
- Cooldown evita envío excesivo de comandos

### Consumo de Recursos

- **CPU**: +5-10% con BLE activo
- **Memoria**: +20MB para módulo BLE
- **Batería**: Mínimo impacto (BLE Low Energy)

## Referencias

- [Bleak Documentation](https://bleak.readthedocs.io/)
- [Arduino BLE Library](https://www.arduino.cc/en/Reference/ArduinoBLE)
- [BLE GATT Services](https://www.bluetooth.com/specifications/gatt/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## Licencia

Este proyecto es parte del curso de Microcontroladores (8vo semestre).

## Soporte

Si encuentras problemas:

1. Revisa la sección Troubleshooting
2. Verifica los logs en la terminal
3. Prueba los scripts de test individuales
4. Verifica el estado BLE: `curl http://localhost:5000/ble/status`
