#!/usr/bin/env python3
"""
BLE Door Integration Module
Integra el control de puerta BLE con el sistema de reconocimiento facial
"""

import asyncio
import threading
import time
from typing import Optional, List, Set
import json
import os

try:
    from bleak import BleakClient, BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False
    print("[WARNING] Bleak no disponible. Instala: pip3 install bleak")


# UUIDs del Arduino Nano 33 BLE
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

# Comandos
CMD_OPEN = ord('A')
CMD_CLOSE = ord('C')

# Configuración
CONFIG_FILE = "config/authorized_users.json"
DEFAULT_DOOR_OPEN_TIME = 3  # segundos que la puerta permanece abierta
COOLDOWN_TIME = 5  # segundos antes de poder abrir de nuevo para la misma persona


class BLEDoorManager:
    """
    Gestor de puerta BLE con integración de reconocimiento facial
    Maneja conexión, envío de comandos y lista de usuarios autorizados
    """

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None
        self.connected = False
        self.connection_lock = threading.Lock()

        # Control de acceso
        self.authorized_users: Set[str] = set()
        self.last_access_times = {}  # {nombre: timestamp}
        self.door_open_duration = DEFAULT_DOOR_OPEN_TIME
        self.cooldown_time = COOLDOWN_TIME

        # Estadísticas
        self.access_log = []
        self.total_accesses = 0

        # Loop asyncio para operaciones BLE
        self.loop = None
        self.loop_thread = None

        # Cargar configuración
        self.load_config()

    def load_config(self):
        """Carga la configuración de usuarios autorizados"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.authorized_users = set(config.get('authorized_users', []))
                    self.door_open_duration = config.get('door_open_duration', DEFAULT_DOOR_OPEN_TIME)
                    self.cooldown_time = config.get('cooldown_time', COOLDOWN_TIME)
                    print(f"[BLE] Configuración cargada: {len(self.authorized_users)} usuarios autorizados")
            else:
                print(f"[BLE] Archivo de configuración no encontrado: {self.config_file}")
                print(f"[BLE] Usando configuración por defecto (todos autorizados)")
        except Exception as e:
            print(f"[BLE] Error cargando configuración: {e}")
            self.authorized_users = set()

    def save_config(self):
        """Guarda la configuración actual"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config = {
                'authorized_users': list(self.authorized_users),
                'door_open_duration': self.door_open_duration,
                'cooldown_time': self.cooldown_time
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"[BLE] Configuración guardada")
        except Exception as e:
            print(f"[BLE] Error guardando configuración: {e}")

    def add_authorized_user(self, name: str):
        """Añade un usuario autorizado"""
        self.authorized_users.add(name)
        self.save_config()
        print(f"[BLE] Usuario autorizado añadido: {name}")

    def remove_authorized_user(self, name: str):
        """Elimina un usuario autorizado"""
        if name in self.authorized_users:
            self.authorized_users.remove(name)
            self.save_config()
            print(f"[BLE] Usuario autorizado eliminado: {name}")

    def is_authorized(self, name: str) -> bool:
        """Verifica si un usuario está autorizado"""
        # Si no hay lista, todos están autorizados
        if not self.authorized_users:
            return True
        return name in self.authorized_users

    def can_access_now(self, name: str) -> bool:
        """Verifica si el usuario puede acceder ahora (cooldown)"""
        if name not in self.last_access_times:
            return True

        elapsed = time.time() - self.last_access_times[name]
        return elapsed >= self.cooldown_time

    def start_event_loop(self):
        """Inicia el event loop asyncio en un thread separado"""
        if self.loop_thread is not None and self.loop_thread.is_alive():
            return

        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()

        # Esperar a que el loop esté listo
        while self.loop is None:
            time.sleep(0.1)

        print("[BLE] Event loop iniciado")

    async def _find_nano_device(self, timeout: int = 10) -> Optional[str]:
        """Busca el dispositivo Arduino Nano BLE"""
        print(f"\n[BLE] ========================================")
        print(f"[BLE] Escaneando dispositivos BLE...")
        print(f"[BLE] Buscando 'NanoDoorBLE' (timeout: {timeout}s)")
        print(f"[BLE] ========================================")

        devices = await BleakScanner.discover(timeout=timeout)

        print(f"[BLE] Dispositivos encontrados: {len(devices)}")

        # Mostrar todos los dispositivos para debugging
        for i, device in enumerate(devices):
            name = device.name if device.name else "Sin nombre"
            print(f"[BLE]   {i+1}. {name} - {device.address}")

        # Buscar NanoDoorBLE (case-insensitive)
        for device in devices:
            if device.name and "nanodoorble" in device.name.lower():
                print(f"\n[BLE] ✓✓✓ ENCONTRADO: {device.name} [{device.address}]")
                print(f"[BLE] RSSI: {device.rssi if hasattr(device, 'rssi') else 'N/A'} dBm")
                return device.address

        print(f"\n[BLE] ✗✗✗ 'NanoDoorBLE' no encontrado entre {len(devices)} dispositivos")
        print(f"[BLE] Verifica que el Arduino Nano 33 BLE esté:")
        print(f"[BLE]   1. Encendido")
        print(f"[BLE]   2. Ejecutando el código correcto")
        print(f"[BLE]   3. Cerca del dispositivo (< 10 metros)")
        return None

    async def _connect_async(self) -> bool:
        """Conecta al dispositivo BLE (async)"""
        try:
            # Verificar si ya está conectado
            if self.connected and self.client:
                try:
                    if await self.client.is_connected():
                        print("[BLE] Ya está conectado")
                        return True
                except:
                    pass  # Si falla la verificación, intentar reconectar

            # Buscar dispositivo si no tenemos la dirección
            if not self.device_address:
                print("[BLE] No hay dirección guardada, buscando dispositivo...")
                self.device_address = await self._find_nano_device(timeout=15)
                if not self.device_address:
                    return False

            # Intentar conectar
            print(f"\n[BLE] ========================================")
            print(f"[BLE] Iniciando conexión...")
            print(f"[BLE] Dispositivo: {self.device_address}")
            print(f"[BLE] Timeout: 20 segundos")
            print(f"[BLE] ========================================")

            self.client = BleakClient(self.device_address, timeout=20.0)

            print(f"[BLE] Conectando... (puede tomar 5-10 segundos)")
            await self.client.connect()

            # Verificar servicios
            print(f"[BLE] ✓ Conexión establecida")
            print(f"[BLE] Verificando servicios...")

            services = self.client.services
            service_found = False

            for service in services:
                if SERVICE_UUID.lower() in service.uuid.lower():
                    service_found = True
                    print(f"[BLE] ✓ Servicio encontrado: {service.uuid}")
                    break

            if not service_found:
                print(f"[BLE] ⚠ Servicio {SERVICE_UUID} no encontrado")
                print(f"[BLE] Servicios disponibles:")
                for service in services:
                    print(f"[BLE]   - {service.uuid}")

            self.connected = True
            print(f"\n[BLE] ✓✓✓ CONECTADO EXITOSAMENTE ✓✓✓")
            return True

        except Exception as e:
            print(f"\n[BLE] ✗✗✗ ERROR AL CONECTAR ✗✗✗")
            print(f"[BLE] Error: {e}")
            print(f"[BLE] Tipo: {type(e).__name__}")

            # Sugerencias según el error
            if "timeout" in str(e).lower():
                print(f"[BLE] → El dispositivo no respondió a tiempo")
                print(f"[BLE] → Intenta acercarte más al Arduino")
            elif "not found" in str(e).lower():
                print(f"[BLE] → Dispositivo no encontrado")
                print(f"[BLE] → Verifica que el Arduino esté encendido")
            elif "permission" in str(e).lower():
                print(f"[BLE] → Error de permisos")
                print(f"[BLE] → Ejecuta: sudo usermod -a -G bluetooth $USER")

            self.connected = False
            return False

    def connect(self) -> bool:
        """Conecta al dispositivo BLE (síncrono)"""
        if not BLE_AVAILABLE:
            print("[BLE] Bleak no disponible")
            return False

        with self.connection_lock:
            if self.loop is None:
                self.start_event_loop()

            future = asyncio.run_coroutine_threadsafe(
                self._connect_async(),
                self.loop
            )

            try:
                return future.result(timeout=20)
            except Exception as e:
                print(f"[BLE] Error en conexión síncrona: {e}")
                return False

    async def _send_command_async(self, command: int) -> bool:
        """Envía un comando al Arduino (async)"""
        try:
            if not self.connected or not self.client:
                print("[BLE] No conectado, intentando reconectar...")
                if not await self._connect_async():
                    return False

            cmd_byte = bytes([command])
            cmd_name = "ABRIR" if command == CMD_OPEN else "CERRAR"
            print(f"[BLE] Enviando: {cmd_name} (byte: {command} / 0x{command:02X})")
            
            await self.client.write_gatt_char(CHAR_UUID, cmd_byte)
            print(f"[BLE] ✓ Comando enviado: {cmd_name}")
            return True

        except Exception as e:
            print(f"[BLE] ✗ Error enviando comando: {e}")
            self.connected = False
            return False

    def send_command(self, command: int) -> bool:
        """Envía un comando (síncrono)"""
        if not BLE_AVAILABLE:
            return False

        if self.loop is None:
            self.start_event_loop()

        future = asyncio.run_coroutine_threadsafe(
            self._send_command_async(command),
            self.loop
        )

        try:
            return future.result(timeout=5)
        except Exception as e:
            print(f"[BLE] Error enviando comando: {e}")
            return False

    def open_door(self) -> bool:
        """Abre la puerta"""
        return self.send_command(CMD_OPEN)

    def close_door(self) -> bool:
        """Cierra la puerta"""
        return self.send_command(CMD_CLOSE)

    def open_door_timed(self, duration: Optional[float] = None) -> bool:
        """Abre la puerta por un tiempo determinado, luego envía cerrar"""
        if duration is None:
            duration = self.door_open_duration

        def timed_sequence():
            if self.open_door():
                print(f"[BLE] Puerta abierta por {duration}s")
                time.sleep(duration)
                self.close_door()
                print(f"[BLE] Puerta cerrada")

        thread = threading.Thread(target=timed_sequence, daemon=True)
        thread.start()
        return True  # Retornar True para indicar que se inició exitosamente

    def handle_recognized_face(self, name: str, confidence: float = 0.0, is_unknown: bool = False):
        """
        Maneja el reconocimiento de una cara
        Verifica autorización y cooldown antes de enviar comando
        
        Args:
            name: Nombre de la persona reconocida
            confidence: Nivel de confianza (0-1)
            is_unknown: True si es persona desconocida (envía 'C'), False si es conocida (envía 'A')
        """
        # Registrar intento
        timestamp = time.time()
        
        # Determinar comando a enviar
        if is_unknown:
            # Persona desconocida: enviar 'C' (CLOSE/CERRAR)
            print(f"[BLE] ⚠️  DESCONOCIDO detectado: {name} (confianza: {confidence:.1%})")
            print(f"[BLE] Enviando comando: C (CERRAR/ALARMA)")
            command = CMD_CLOSE
            access_status = "DESCONOCIDO"
        else:
            # Persona conocida y autorizada: enviar 'A' (ABRIR)
            if not self.is_authorized(name):
                print(f"[BLE] ✗ Acceso denegado: {name} no está en lista de autorización")
                command = CMD_CLOSE
                access_status = "NO_AUTORIZADO"
            elif not self.can_access_now(name):
                elapsed = time.time() - self.last_access_times.get(name, 0)
                remaining = self.cooldown_time - elapsed
                print(f"[BLE] ⏳ Cooldown activo para {name}: {remaining:.1f}s restantes")
                return False
            else:
                print(f"[BLE] ✓ CONOCIDO autorizado: {name} (confianza: {confidence:.1%})")
                print(f"[BLE] Enviando comando: A (ABRIR)")
                command = CMD_OPEN
                access_status = "AUTORIZADO"
        
        # Actualizar timestamp de último acceso
        self.last_access_times[name] = timestamp
        self.total_accesses += 1
        
        # Registrar en log
        access_record = {
            'name': name,
            'confidence': confidence,
            'status': access_status,
            'command': 'A' if command == CMD_OPEN else 'C',
            'timestamp': timestamp,
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        }
        self.access_log.append(access_record)
        
        # Enviar comando al Arduino
        self.send_command(command)
        
        return True

    def get_status(self) -> dict:
        """Retorna el estado actual del sistema"""
        return {
            'ble_available': BLE_AVAILABLE,
            'connected': self.connected,
            'device_address': self.device_address,
            'authorized_users': list(self.authorized_users),
            'total_accesses': self.total_accesses,
            'recent_accesses': self.access_log[-10:] if self.access_log else []
        }

    def disconnect(self):
        """Desconecta del dispositivo BLE"""
        if self.client and self.connected:
            if self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.client.disconnect(),
                    self.loop
                )
            self.connected = False
            print("[BLE] Desconectado")

    def __del__(self):
        """Limpieza al destruir el objeto"""
        self.disconnect()
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)


# Instancia global (singleton)
_ble_manager_instance: Optional[BLEDoorManager] = None


def get_ble_manager() -> BLEDoorManager:
    """Obtiene la instancia global del gestor BLE"""
    global _ble_manager_instance
    if _ble_manager_instance is None:
        _ble_manager_instance = BLEDoorManager()
    return _ble_manager_instance


def init_ble_system(auto_connect: bool = True) -> bool:
    """
    Inicializa el sistema BLE
    Retorna True si se inicializó correctamente
    """
    if not BLE_AVAILABLE:
        print("[BLE] Sistema BLE no disponible (bleak no instalado)")
        return False

    manager = get_ble_manager()

    if auto_connect:
        print("[BLE] Intentando conectar al dispositivo...")
        success = manager.connect()
        if success:
            print("[BLE] ✓ Sistema BLE inicializado y conectado")
        else:
            print("[BLE] ⚠ Sistema BLE inicializado pero no conectado")
        return success
    else:
        print("[BLE] Sistema BLE inicializado (sin auto-conexión)")
        return True


if __name__ == "__main__":
    # Prueba del módulo
    print("=== Prueba del Módulo BLE Door Integration ===\n")

    if not BLE_AVAILABLE:
        print("ERROR: bleak no está instalado")
        print("Instala con: pip3 install bleak")
        exit(1)

    # Crear gestor
    manager = BLEDoorManager()

    # Intentar conectar
    if manager.connect():
        print("\nPrueba de apertura de puerta...")
        manager.handle_recognized_face("Test Usuario", confidence=0.95)

        time.sleep(5)

        print("\nEstadísticas:")
        status = manager.get_status()
        print(f"  Conectado: {status['connected']}")
        print(f"  Dispositivo: {status['device_address']}")
        print(f"  Accesos totales: {status['total_accesses']}")

        manager.disconnect()
    else:
        print("\nNo se pudo conectar al dispositivo BLE")
