#!/usr/bin/env python3
"""
Setup BLE con output detallado
Muestra claramente el progreso de instalación
"""

import subprocess
import sys
import time

def print_header(text):
    """Imprime un encabezado destacado"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(step_num, total_steps, description):
    """Imprime el paso actual"""
    print(f"\n{'#'*70}")
    print(f"#  PASO {step_num}/{total_steps}: {description}")
    print(f"{'#'*70}\n")

def run_command(command, description, show_output=True):
    """Ejecuta un comando y muestra el progreso"""
    print(f"[→] {description}")
    print(f"[→] Comando: {' '.join(command)}")
    print(f"[→] Ejecutando...")
    print("")

    if show_output:
        # Mostrar output en tiempo real
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Leer línea por línea
        for line in process.stdout:
            print(f"    {line}", end='')

        process.wait()
        return_code = process.returncode
    else:
        # Ejecutar sin mostrar output
        result = subprocess.run(command, capture_output=True, text=True)
        return_code = result.returncode

    if return_code == 0:
        print(f"\n[✓] {description} - COMPLETADO")
        return True
    else:
        print(f"\n[✗] {description} - ERROR (código: {return_code})")
        return False

def check_package(package_name):
    """Verifica si un paquete está instalado"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    print_header("INSTALACIÓN BLE - MODO DETALLADO")

    print("Este script instalará las dependencias necesarias para el")
    print("sistema BLE de control de puerta.")
    print("")
    print("Pasos a realizar:")
    print("  1. Verificar Python y pip")
    print("  2. Instalar bleak (comunicación BLE)")
    print("  3. Instalar RPi.GPIO (si es Raspberry Pi)")
    print("  4. Verificar instalación")
    print("")

    input("Presiona ENTER para continuar...")

    # PASO 1: Verificar Python y pip
    print_step(1, 4, "VERIFICANDO PYTHON Y PIP")

    print(f"[→] Python: {sys.version}")
    print(f"[→] Ejecutable: {sys.executable}")
    print("")

    # Verificar pip
    result = subprocess.run(
        [sys.executable, '-m', 'pip', '--version'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"[✓] pip instalado: {result.stdout.strip()}")
    else:
        print(f"[✗] pip no está disponible")
        print(f"[→] Instala pip primero: sudo apt install python3-pip")
        sys.exit(1)

    # PASO 2: Instalar bleak
    print_step(2, 4, "INSTALANDO BLEAK (comunicación BLE)")

    if check_package('bleak'):
        print("[✓] bleak ya está instalado")
        print("[→] Actualizando a la última versión...")

    success = run_command(
        [sys.executable, '-m', 'pip', 'install', 'bleak>=0.21.0', '--upgrade'],
        "Instalar/actualizar bleak",
        show_output=True
    )

    if not success:
        print("\n[!] Si la instalación falló, intenta:")
        print("    sudo apt-get install python3-dev libbluetooth-dev")
        print("    pip3 install bleak")
        sys.exit(1)

    # PASO 3: Instalar RPi.GPIO (solo Raspberry Pi)
    print_step(3, 4, "INSTALANDO RPi.GPIO (solo Raspberry Pi)")

    # Detectar si es Raspberry Pi
    is_raspberry = False
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' in f.read():
                is_raspberry = True
    except:
        pass

    if is_raspberry:
        print("[→] Raspberry Pi detectado")

        if check_package('RPi.GPIO'):
            print("[✓] RPi.GPIO ya está instalado")
        else:
            success = run_command(
                [sys.executable, '-m', 'pip', 'install', 'RPi.GPIO>=0.7.1'],
                "Instalar RPi.GPIO",
                show_output=True
            )

            if not success:
                print("\n[!] RPi.GPIO es opcional. El sistema funcionará sin él.")
    else:
        print("[→] No es Raspberry Pi - RPi.GPIO no es necesario")
        print("[✓] Paso omitido")

    # PASO 4: Verificar instalación
    print_step(4, 4, "VERIFICANDO INSTALACIÓN")

    print("[→] Verificando paquetes instalados...\n")

    packages_to_check = [
        ('bleak', 'Comunicación BLE', True),
        ('RPi.GPIO', 'Control GPIO', is_raspberry),
    ]

    all_ok = True

    for package_name, description, required in packages_to_check:
        print(f"  Verificando {package_name}... ", end='')
        sys.stdout.flush()

        time.sleep(0.3)  # Pausa para efecto visual

        if check_package(package_name.replace('-', '_')):
            print("✓")
        else:
            if required:
                print("✗ (REQUERIDO)")
                all_ok = False
            else:
                print("⊘ (opcional)")

    print("")

    # Resumen final
    print_header("INSTALACIÓN COMPLETADA")

    if all_ok:
        print("✓✓✓ TODOS LOS PAQUETES INSTALADOS CORRECTAMENTE ✓✓✓")
        print("")
        print("Próximos pasos:")
        print("")
        print("  1. Enciende tu Arduino Nano 33 BLE")
        print("  2. Verifica que anuncia como 'NanoDoorBLE'")
        print("  3. Ejecuta el sistema:")
        print("")
        print("     python3 app.py")
        print("")
        print("  4. El sistema se conectará automáticamente")
        print("     (Desactiva con: python3 app.py --no-ble-autoconnect)")
        print("")
        print("Documentación:")
        print("  - QUICKSTART_BLE.md - Inicio rápido")
        print("  - INTEGRACION_BLE.md - Documentación completa")
        print("")
    else:
        print("✗✗✗ ALGUNOS PAQUETES NO SE INSTALARON ✗✗✗")
        print("")
        print("Intenta instalar manualmente:")
        print("")
        print("  pip3 install bleak>=0.21.0")
        print("")
        print("Si sigues teniendo problemas:")
        print("")
        print("  sudo apt-get install python3-dev libbluetooth-dev")
        print("  sudo apt-get install bluetooth bluez")
        print("")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[✗] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
