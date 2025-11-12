#!/usr/bin/env python3
"""
Control de Arduino para la aplicación de reconocimiento facial
Soporta comunicación por puerto serial
"""

import serial
import time
import threading
from typing import Optional, Callable


class ArduinoController:
    """
    Controlador para Arduino
    Maneja comunicación serial y envío de comandos
    """
    
    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 9600):
        """
        Inicializa el controlador de Arduino
        
        Args:
            port: Puerto serial (ej: /dev/ttyACM0 en Linux, COM3 en Windows)
            baudrate: Velocidad de comunicación (por defecto 9600)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_port: Optional[serial.Serial] = None
        self.connected = False
        self.lock = threading.Lock()
        
    def connect(self) -> bool:
        """
        Conecta con Arduino
        
        Returns:
            True si se conectó exitosamente, False en caso contrario
        """
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)  # Esperar a que Arduino se reinicie
            self.connected = True
            print(f"[OK] Conectado a Arduino en {self.port}")
            return True
        except Exception as e:
            print(f"[WARNING] No se pudo conectar a Arduino: {e}")
            print(f"[INFO] Arduino no disponible. Continuando sin control de puerta.")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta de Arduino"""
        if self.serial_port and self.connected:
            try:
                self.serial_port.close()
                self.connected = False
                print("[OK] Desconectado de Arduino")
            except Exception as e:
                print(f"[WARNING] Error al desconectar: {e}")
    
    def send_command(self, command: str) -> bool:
        """
        Envía un comando a Arduino
        
        Args:
            command: Comando a enviar (ej: "UNLOCK", "LOCK", "LED_ON", etc.)
            
        Returns:
            True si se envió exitosamente
        """
        if not self.connected:
            print("[WARNING] Arduino no está conectado")
            return False
        
        try:
            with self.lock:
                # Asegurarse de que el comando termina con newline
                if not command.endswith('\n'):
                    command += '\n'
                
                self.serial_port.write(command.encode())
                print(f"[OK] Comando enviado a Arduino: {command.strip()}")
                return True
        except Exception as e:
            print(f"[ERROR] Error enviando comando a Arduino: {e}")
            self.connected = False
            return False
    
    def read_response(self, timeout: float = 1.0) -> Optional[str]:
        """
        Lee respuesta de Arduino
        
        Args:
            timeout: Tiempo máximo de espera
            
        Returns:
            Respuesta del Arduino o None si no hay respuesta
        """
        if not self.connected:
            return None
        
        try:
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < timeout:
                if self.serial_port.in_waiting > 0:
                    char = self.serial_port.read(1).decode('utf-8', errors='ignore')
                    response += char
                    if char == '\n':
                        return response.strip()
            
            return response.strip() if response else None
        except Exception as e:
            print(f"[WARNING] Error leyendo respuesta: {e}")
            return None
    
    def unlock_door(self) -> bool:
        """Abre/desbloquea la puerta"""
        return self.send_command("UNLOCK")
    
    def lock_door(self) -> bool:
        """Cierra/bloquea la puerta"""
        return self.send_command("LOCK")
    
    def toggle_led(self, on: bool) -> bool:
        """
        Enciende/apaga LED
        
        Args:
            on: True para encender, False para apagar
        """
        command = "LED_ON" if on else "LED_OFF"
        return self.send_command(command)
    
    def custom_command(self, command: str) -> bool:
        """
        Envía un comando personalizado
        
        Args:
            command: Comando personalizado
        """
        return self.send_command(command)
    
    def is_connected(self) -> bool:
        """Retorna el estado de conexión"""
        return self.connected


# Instancia global de Arduino
arduino_controller: Optional[ArduinoController] = None


def init_arduino(port: str = "/dev/ttyACM0", baudrate: int = 9600) -> ArduinoController:
    """
    Inicializa el controlador de Arduino global
    
    Args:
        port: Puerto serial
        baudrate: Velocidad de comunicación
        
    Returns:
        Instancia del controlador
    """
    global arduino_controller
    arduino_controller = ArduinoController(port, baudrate)
    arduino_controller.connect()
    return arduino_controller


def get_arduino() -> Optional[ArduinoController]:
    """Retorna la instancia global de Arduino"""
    return arduino_controller
