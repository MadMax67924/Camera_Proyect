from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/ble", tags=["arduino"])

# ==================== CONFIGURACIoN ====================
class ArduinoConfig:
    def __init__(self):
        self.connected = False
        self.enabled = False
        self.door_status = "locked"  # locked, unlocked

    def connect(self):
        """Simular conexion BLE con Arduino"""
        # TODO: Implementar conexion BLE real
        # Aquo iro el codigo para conectarse voa BLE al Arduino
        self.connected = True
        return True

    def disconnect(self):
        """Desconectar del Arduino"""
        self.connected = False
        self.enabled = False
        return True

    def send_command(self, command):
        """Enviar comando al Arduino"""
        if not self.connected:
            return False

        # TODO: Implementar envoo de comandos BLE
        # Por ahora solo simulamos
        print(f"Enviando comando al Arduino: {command}")
        return True

# Instancia global
arduino_config = ArduinoConfig()

# ==================== RUTAS ====================

@router.get("/status")
async def get_arduino_status():
    """Obtener estado de conexion Arduino"""
    return JSONResponse({
        "connected": arduino_config.connected,
        "enabled": arduino_config.enabled,
        "door_status": arduino_config.door_status
    })

@router.post("/connect")
async def connect_arduino():
    """Conectar con Arduino voa BLE"""
    try:
        # Intentar conectar
        success = arduino_config.connect()

        if success:
            return JSONResponse({
                "success": True,
                "message": "Arduino conectado exitosamente",
                "connected": True
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "No se pudo conectar con el Arduino",
                "connected": False
            }, status_code=500)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Error de conexion: {str(e)}",
            "connected": False
        }, status_code=500)

@router.post("/disconnect")
async def disconnect_arduino():
    """Desconectar del Arduino"""
    arduino_config.disconnect()

    return JSONResponse({
        "success": True,
        "message": "Arduino desconectado",
        "connected": False
    })

@router.post("/toggle")
async def toggle_arduino():
    """Activar/desactivar control del Arduino"""
    if not arduino_config.connected:
        return JSONResponse({
            "success": False,
            "message": "Arduino no esto conectado",
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
    """Abrir puerta (desbloquear)"""
    if not arduino_config.connected:
        return JSONResponse({
            "success": False,
            "message": "Arduino no esto conectado"
        }, status_code=400)

    if not arduino_config.enabled:
        return JSONResponse({
            "success": False,
            "message": "Control Arduino no esto activado"
        }, status_code=400)

    # Enviar comando de abrir
    success = arduino_config.send_command("UNLOCK")

    if success:
        arduino_config.door_status = "unlocked"
        return JSONResponse({
            "success": True,
            "message": "Puerta abierta",
            "door_status": "unlocked"
        })
    else:
        return JSONResponse({
            "success": False,
            "message": "Error al enviar comando"
        }, status_code=500)

@router.post("/close_door")
async def close_door():
    """Cerrar puerta (bloquear)"""
    if not arduino_config.connected:
        return JSONResponse({
            "success": False,
            "message": "Arduino no esto conectado"
        }, status_code=400)

    if not arduino_config.enabled:
        return JSONResponse({
            "success": False,
            "message": "Control Arduino no esto activado"
        }, status_code=400)

    # Enviar comando de cerrar
    success = arduino_config.send_command("LOCK")

    if success:
        arduino_config.door_status = "locked"
        return JSONResponse({
            "success": True,
            "message": "Puerta cerrada",
            "door_status": "locked"
        })
    else:
        return JSONResponse({
            "success": False,
            "message": "Error al enviar comando"
        }, status_code=500)

# ==================== FUNCIONES AUXILIARES ====================

def shutdown():
    """Limpiar recursos al cerrar"""
    if arduino_config.connected:
        arduino_config.disconnect()
