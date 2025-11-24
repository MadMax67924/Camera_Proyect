import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

router = APIRouter(prefix="/ble", tags=["arduino"])

# ==================== CONFIGURACION ====================
class ArduinoBLE:
    """
    Controlador BLE para el Nano 33 BLE / BLE Sense.
    Usa el servicio/characteristic definido en camaraNanoBluetooth.ino para
    enviar un byte 'A' (abrir) o 'C' (cerrar) al UNO por UART.
    """

    SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
    CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"
    DEVICE_NAME = "NanoDoorBLE"

    def __init__(self):
        self.client: BleakClient | None = None
        self.connected = False
        self.enabled = False
        self.door_status = "locked"  # locked, unlocked
        self.device_address: str | None = None
        self._lock = asyncio.Lock()

    async def _is_connected(self) -> bool:
        """Resolver is_connected como propiedad o coroutine segun version de Bleak."""
        if not self.client:
            return False
        is_conn = self.client.is_connected
        if callable(is_conn):
            result = is_conn()
            return await result if asyncio.iscoroutine(result) else bool(result)
        return bool(is_conn)

    async def _find_device(self, timeout: float = 6.0):
        """Buscar el Nano por nombre o UUID de servicio."""
        devices = await BleakScanner.discover(timeout=timeout)
        for dev in devices:
            metadata = getattr(dev, "metadata", {}) or {}
            advertised_services = metadata.get("uuids", [])
            if dev.name == self.DEVICE_NAME or self.SERVICE_UUID.lower() in [str(u).lower() for u in advertised_services]:
                self.device_address = dev.address
                return dev
        return None

    async def connect(self):
        """Conectar con el Nano via BLE."""
        async with self._lock:
            if self.client and self.client.is_connected:
                self.connected = True
                return True

            device = await self._find_device()
            if not device:
                raise RuntimeError("No se encontro el dispositivo NanoDoorBLE. Asegurate de que esta encendido y anunciando.")

            try:
                self.client = BleakClient(device)
                await self.client.connect(timeout=8.0)
                self.connected = await self._is_connected()
                if self.connected:
                    # Algunas versiones de Bleak no exponen set_disconnected_callback
                    setter = getattr(self.client, "set_disconnected_callback", None)
                    if callable(setter):
                        setter(self._on_disconnect)
                return self.connected
            except BleakError as exc:
                self.connected = False
                self.client = None
                raise RuntimeError(f"Error al conectar BLE: {exc}") from exc

    async def disconnect(self):
        """Desconectar del Nano."""
        async with self._lock:
            if self.client:
                try:
                    await self.client.disconnect()
                except BleakError:
                    pass
            self.client = None
            self.connected = False
            self.enabled = False
            return True

    def _on_disconnect(self, _client):
        """Callback cuando se pierde la conexion BLE."""
        self.connected = False
        self.enabled = False

    async def send_command(self, command: str):
        """
        Enviar comando al Nano.
        - UNLOCK -> 'A'
        - LOCK   -> 'C'
        """
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Arduino no esta conectado")

        cmd = command.upper()
        if cmd == "UNLOCK":
            value = b"A"
        elif cmd == "LOCK":
            value = b"C"
        else:
            raise ValueError(f"Comando no soportado: {command}")

        try:
            await self.client.write_gatt_char(self.CHARACTERISTIC_UUID, value, response=False)
            return True
        except BleakError as exc:
            raise RuntimeError(f"No se pudo enviar el comando BLE: {exc}") from exc


# Instancia global
arduino_config = ArduinoBLE()

# ==================== RUTAS ====================


@router.get("/status")
async def get_arduino_status():
    """Obtener estado de conexion Arduino."""
    return JSONResponse({
        "connected": arduino_config.connected,
        "enabled": arduino_config.enabled,
        "door_status": arduino_config.door_status,
        "address": arduino_config.device_address
    })


@router.post("/connect")
async def connect_arduino():
    """Conectar con Arduino via BLE."""
    try:
        success = await arduino_config.connect()
        if success:
            return JSONResponse({
                "success": True,
                "message": "Arduino conectado exitosamente",
                "connected": True,
                "address": arduino_config.device_address
            })
        return JSONResponse({
            "success": False,
            "message": "No se pudo conectar con el Arduino",
            "connected": False
        }, status_code=500)
    except Exception as exc:
        return JSONResponse({
            "success": False,
            "message": f"Error de conexion: {exc}",
            "connected": False
        }, status_code=500)


@router.post("/disconnect")
async def disconnect_arduino():
    """Desconectar del Arduino."""
    await arduino_config.disconnect()
    return JSONResponse({
        "success": True,
        "message": "Arduino desconectado",
        "connected": False
    })


@router.post("/toggle")
async def toggle_arduino():
    """Activar/desactivar control del Arduino."""
    if not arduino_config.connected:
        return JSONResponse({
            "success": False,
            "message": "Arduino no esta conectado",
            "arduino_enabled": False
        }, status_code=400)

    arduino_config.enabled = not arduino_config.enabled

    return JSONResponse({
        "success": True,
        "message": f"Control Arduino {'activado' if arduino_config.enabled else 'desactivado'}",
        "arduino_enabled": arduino_config.enabled
    })


@router.post("/open_door")
async def open_door():
    """Abrir puerta (desbloquear)."""
    if not arduino_config.connected:
        return JSONResponse({
            "success": False,
            "message": "Arduino no esta conectado"
        }, status_code=400)

    if not arduino_config.enabled:
        return JSONResponse({
            "success": False,
            "message": "Control Arduino no esta activado"
        }, status_code=400)

    try:
        success = await arduino_config.send_command("UNLOCK")
    except Exception as exc:
        return JSONResponse({
            "success": False,
            "message": str(exc)
        }, status_code=500)

    if success:
        arduino_config.door_status = "unlocked"
        return JSONResponse({
            "success": True,
            "message": "Puerta abierta",
            "door_status": "unlocked"
        })

    return JSONResponse({
        "success": False,
        "message": "Error al enviar comando"
    }, status_code=500)


@router.post("/close_door")
async def close_door():
    """Cerrar puerta (bloquear)."""
    if not arduino_config.connected:
        return JSONResponse({
            "success": False,
            "message": "Arduino no esta conectado"
        }, status_code=400)

    if not arduino_config.enabled:
        return JSONResponse({
            "success": False,
            "message": "Control Arduino no esta activado"
        }, status_code=400)

    try:
        success = await arduino_config.send_command("LOCK")
    except Exception as exc:
        return JSONResponse({
            "success": False,
            "message": str(exc)
        }, status_code=500)

    if success:
        arduino_config.door_status = "locked"
        return JSONResponse({
            "success": True,
            "message": "Puerta cerrada",
            "door_status": "locked"
        })

    return JSONResponse({
        "success": False,
        "message": "Error al enviar comando"
    }, status_code=500)


# ==================== FUNCIONES AUXILIARES ====================


def shutdown():
    """Limpiar recursos al cerrar."""
    if arduino_config.connected:
        # Ejecutar desconexion de manera segura en el loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(arduino_config.disconnect())
        else:
            loop.run_until_complete(arduino_config.disconnect())
