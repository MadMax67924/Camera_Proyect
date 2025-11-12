#!/usr/bin/env python3
"""
BLE Door Button Test - Control con botón GPIO
Presiona un botón físico en la Raspberry Pi para abrir la puerta
"""

import asyncio
from bleak import BleakClient, BleakScanner
import sys

# Intenta importar GPIO (solo disponible en Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠ RPi.GPIO no disponible - usando modo teclado")

# UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

# Configuración GPIO
BUTTON_PIN = 17  # GPIO17 (Pin 11 en el header)
CMD_OPEN = ord('A')


class ButtonDoorController:
    """Controlador de puerta con botón"""

    def __init__(self, use_gpio=True):
        self.client = None
        self.device_address = None
        self.connected = False
        self.use_gpio = use_gpio and GPIO_AVAILABLE
        self.button_pressed = False

        if self.use_gpio:
            self.setup_gpio()

    def setup_gpio(self):
        """Configura el botón GPIO"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            BUTTON_PIN,
            GPIO.FALLING,
            callback=self.button_callback,
            bouncetime=300
        )
        print(f"✓ GPIO configurado: Botón en GPIO{BUTTON_PIN}")

    def button_callback(self, channel):
        """Callback cuando se presiona el botón"""
        self.button_pressed = True
        print("\n🔔 ¡Botón presionado!")

    async def find_and_connect(self):
        """Busca y conecta al Arduino"""
        print("Buscando 'NanoDoorBLE'...")
        devices = await BleakScanner.discover(timeout=10)

        for device in devices:
            if device.name and "NanoDoorBLE" in device.name:
                print(f"✓ Encontrado: {device.name} [{device.address}]")
                self.device_address = device.address
                break

        if not self.device_address:
            print("✗ Dispositivo no encontrado")
            return False

        try:
            print(f"Conectando a {self.device_address}...")
            self.client = BleakClient(self.device_address)
            await self.client.connect()
            self.connected = True
            print("✓ Conectado exitosamente\n")
            return True
        except Exception as e:
            print(f"✗ Error al conectar: {e}")
            return False

    async def send_open_command(self):
        """Envía comando de apertura"""
        if not self.connected or not self.client:
            print("Error: No conectado")
            return False

        try:
            await self.client.write_gatt_char(CHAR_UUID, bytes([CMD_OPEN]))
            print("✓ Comando ABRIR enviado")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    async def run_gpio_mode(self):
        """Modo con botón GPIO"""
        print("=" * 60)
        print("  MODO BOTÓN GPIO")
        print("  Presiona el botón conectado al GPIO17 para abrir")
        print("  Presiona Ctrl+C para salir")
        print("=" * 60)

        if not await self.find_and_connect():
            return

        try:
            while True:
                if self.button_pressed:
                    self.button_pressed = False
                    await self.send_open_command()

                await asyncio.sleep(0.1)  # Check cada 100ms

        except KeyboardInterrupt:
            print("\n\nDetenido por usuario")
        finally:
            if self.client:
                await self.client.disconnect()
            GPIO.cleanup()

    async def run_keyboard_mode(self):
        """Modo con teclado (fallback si no hay GPIO)"""
        print("=" * 60)
        print("  MODO TECLADO")
        print("  Presiona ENTER para abrir la puerta")
        print("  Escribe 'q' y ENTER para salir")
        print("=" * 60)

        if not await self.find_and_connect():
            return

        try:
            while True:
                # Usar asyncio para no bloquear
                await asyncio.sleep(0.1)

                # Simulación simple: el usuario debe presionar Enter
                print("\n[Presiona ENTER para abrir, 'q'+ENTER para salir]")
                response = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )

                if response.lower() == 'q':
                    break

                print("🔔 ¡Abriendo puerta!")
                await self.send_open_command()

        except KeyboardInterrupt:
            print("\n\nDetenido por usuario")
        finally:
            if self.client:
                await self.client.disconnect()

    async def run_simple_keyboard_mode(self):
        """Modo teclado simplificado sin async input"""
        print("=" * 60)
        print("  MODO TECLADO SIMPLE")
        print("  Presiona 'a' + ENTER para abrir")
        print("  Presiona 'q' + ENTER para salir")
        print("=" * 60)

        if not await self.find_and_connect():
            return

        print("\nEsperando comandos...")
        loop = asyncio.get_event_loop()

        try:
            while True:
                # Leer input de forma no bloqueante
                try:
                    cmd = await asyncio.wait_for(
                        loop.run_in_executor(None, input, "> "),
                        timeout=1.0
                    )
                    cmd = cmd.strip().lower()

                    if cmd == 'q':
                        break
                    elif cmd == 'a':
                        print("🔔 ¡Abriendo puerta!")
                        await self.send_open_command()
                    else:
                        print("Comando no reconocido. Usa 'a' para abrir, 'q' para salir")

                except asyncio.TimeoutError:
                    # Timeout - continuar el loop
                    pass

        except KeyboardInterrupt:
            print("\n\nDetenido por usuario")
        finally:
            if self.client:
                await self.client.disconnect()
            print("Desconectado")


async def main():
    """Función principal"""
    controller = ButtonDoorController()

    if controller.use_gpio:
        await controller.run_gpio_mode()
    else:
        await controller.run_simple_keyboard_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        if GPIO_AVAILABLE:
            GPIO.cleanup()
