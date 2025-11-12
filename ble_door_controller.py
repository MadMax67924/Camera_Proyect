#!/usr/bin/env python3
"""
BLE Door Controller para Raspberry Pi
Comunica con Arduino Nano 33 BLE para controlar apertura de puerta
"""

import asyncio
from bleak import BleakClient, BleakScanner
import sys

# UUIDs del servicio y característica (deben coincidir con el Arduino)
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

# Comandos
CMD_OPEN = ord('A')    # Abrir puerta
CMD_CLOSE = ord('C')   # Cerrar puerta


class BLEDoorController:
    """Controlador BLE para el sistema de puerta"""

    def __init__(self):
        self.client = None
        self.device_address = None
        self.connected = False

    async def scan_devices(self, timeout=10):
        """Escanea dispositivos BLE cercanos"""
        print(f"Escaneando dispositivos BLE por {timeout} segundos...")
        devices = await BleakScanner.discover(timeout=timeout)

        print(f"\nDispositivos encontrados ({len(devices)}):")
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device.name or 'Sin nombre'} - {device.address}")

        return devices

    async def find_nano_device(self, timeout=10):
        """Busca específicamente el Arduino Nano BLE"""
        print("Buscando 'NanoDoorBLE'...")
        devices = await BleakScanner.discover(timeout=timeout)

        for device in devices:
            if device.name and "NanoDoorBLE" in device.name:
                print(f"✓ Encontrado: {device.name} [{device.address}]")
                self.device_address = device.address
                return device

        print("✗ No se encontró el dispositivo 'NanoDoorBLE'")
        return None

    async def connect(self, address=None):
        """Conecta al dispositivo BLE"""
        if address:
            self.device_address = address

        if not self.device_address:
            print("Error: No se especificó dirección del dispositivo")
            return False

        try:
            print(f"Conectando a {self.device_address}...")
            self.client = BleakClient(self.device_address)
            await self.client.connect()
            self.connected = True
            print("✓ Conectado exitosamente")

            # Verificar que el servicio existe
            services = await self.client.get_services()
            if SERVICE_UUID.lower() in [s.uuid.lower() for s in services]:
                print(f"✓ Servicio encontrado: {SERVICE_UUID}")
            else:
                print(f"⚠ Advertencia: Servicio {SERVICE_UUID} no encontrado")

            return True

        except Exception as e:
            print(f"✗ Error al conectar: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Desconecta del dispositivo"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            print("Desconectado")

    async def send_command(self, command):
        """Envía un comando al Arduino"""
        if not self.connected or not self.client:
            print("Error: No conectado al dispositivo")
            return False

        try:
            # Enviar el byte del comando
            await self.client.write_gatt_char(CHAR_UUID, bytes([command]))
            cmd_name = "ABRIR" if command == CMD_OPEN else "CERRAR"
            print(f"✓ Comando enviado: {cmd_name} (0x{command:02X})")
            return True

        except Exception as e:
            print(f"✗ Error al enviar comando: {e}")
            return False

    async def open_door(self):
        """Envía comando para abrir la puerta"""
        print("\n>>> Enviando comando ABRIR PUERTA")
        return await self.send_command(CMD_OPEN)

    async def close_door(self):
        """Envía comando para cerrar la puerta"""
        print("\n>>> Enviando comando CERRAR PUERTA")
        return await self.send_command(CMD_CLOSE)


async def interactive_test():
    """Modo interactivo de prueba"""
    controller = BLEDoorController()

    print("=" * 60)
    print("  BLE DOOR CONTROLLER - Modo Interactivo")
    print("=" * 60)

    # Buscar el dispositivo
    device = await controller.find_nano_device(timeout=10)

    if not device:
        print("\n¿Qué deseas hacer?")
        print("  1. Escanear todos los dispositivos")
        print("  2. Ingresar dirección MAC manualmente")
        print("  3. Salir")

        choice = input("\nOpción: ").strip()

        if choice == "1":
            devices = await controller.scan_devices()
            if devices:
                idx = input("\nSelecciona el número del dispositivo: ").strip()
                try:
                    device = devices[int(idx) - 1]
                    controller.device_address = device.address
                except (ValueError, IndexError):
                    print("Selección inválida")
                    return
        elif choice == "2":
            mac = input("Ingresa la dirección MAC (ej: AA:BB:CC:DD:EE:FF): ").strip()
            controller.device_address = mac
        else:
            return

    # Conectar
    if not await controller.connect():
        return

    print("\n" + "=" * 60)
    print("COMANDOS DISPONIBLES:")
    print("  A o a  - Abrir puerta")
    print("  C o c  - Cerrar puerta")
    print("  Q o q  - Salir")
    print("=" * 60)

    try:
        while True:
            cmd = input("\nComando: ").strip().upper()

            if cmd == 'Q':
                break
            elif cmd == 'A':
                await controller.open_door()
            elif cmd == 'C':
                await controller.close_door()
            else:
                print("Comando no reconocido. Usa A, C, o Q")

    except KeyboardInterrupt:
        print("\n\nInterrumpido por usuario")

    finally:
        await controller.disconnect()


async def auto_test():
    """Prueba automática: conectar y enviar comando de apertura"""
    controller = BLEDoorController()

    print("=" * 60)
    print("  BLE DOOR CONTROLLER - Modo Automático")
    print("=" * 60)

    # Buscar y conectar
    device = await controller.find_nano_device(timeout=10)
    if not device:
        print("No se pudo encontrar el dispositivo")
        return

    if not await controller.connect():
        return

    # Enviar comando de apertura
    await asyncio.sleep(0.5)  # Pequeña pausa
    await controller.open_door()

    await asyncio.sleep(1)
    await controller.disconnect()


def main():
    """Punto de entrada principal"""
    print("\nSelecciona modo:")
    print("  1. Modo interactivo (manual)")
    print("  2. Modo automático (envía 'A' y sale)")

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = input("\nModo [1/2]: ").strip()

    if mode == "2":
        asyncio.run(auto_test())
    else:
        asyncio.run(interactive_test())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma terminado por usuario")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
