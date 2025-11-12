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
        print(f"[BLE] Buscando 'NanoDoorBLE'... ({timeout}s)")
        devices = await BleakScanner.discover(timeout=timeout)

        for device in devices:
            if device.name and "NanoDoorBLE" in device.name:
                print(f"[BLE] ✓ Encontrado: {device.name} [{device.address}]")
                return device.address

        print("[BLE] ✗ Dispositivo no encontrado")
        return None

    async def _connect_async(self) -> bool:
        """Conecta al dispositivo BLE (async)"""
        try:
            if self.connected and self.client and await self.client.is_connected():
                return True

            if not self.device_address:
                self.device_address = await self._find_nano_device()
                if not self.device_address:
                    return False

            print(f"[BLE] Conectando a {self.device_address}...")
            self.client = BleakClient(self.device_address, timeout=15.0)
            await self.client.connect()
            self.connected = True
            print("[BLE] ✓ Conectado exitosamente")
            return True

        except Exception as e:
            print(f"[BLE] ✗ Error al conectar: {e}")
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

            await self.client.write_gatt_char(CHAR_UUID, bytes([command]))
            cmd_name = "ABRIR" if command == CMD_OPEN else "CERRAR"
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

    def open_door_timed(self, duration: Optional[float] = None):
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

    def handle_recognized_face(self, name: str, confidence: float = 0.0):
        """
        Maneja el reconocimiento de una cara
        Verifica autorización y cooldown antes de abrir
        """
        # Verificar si está autorizado
        if not self.is_authorized(name):
            print(f"[BLE] ✗ Acceso denegado: {name} no autorizado")
            return False

        # Verificar cooldown
        if not self.can_access_now(name):
            elapsed = time.time() - self.last_access_times[name]
            remaining = self.cooldown_time - elapsed
            print(f"[BLE] ⏳ Cooldown activo para {name}: {remaining:.1f}s restantes")
            return False

        # Registrar acceso
        timestamp = time.time()
        self.last_access_times[name] = timestamp
        self.total_accesses += 1

        access_record = {
            'name': name,
            'confidence': confidence,
            'timestamp': timestamp,
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        }
        self.access_log.append(access_record)

        # Abrir puerta
        print(f"[BLE] ✓ Acceso concedido: {name} (confianza: {confidence:.1%})")
        self.open_door_timed()

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
