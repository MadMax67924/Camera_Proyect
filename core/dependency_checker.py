#!/usr/bin/env python3
"""
Dependency Checker - Verifica e instala dependencias faltantes
"""

import sys
import subprocess
import importlib
import os


def check_package(package_name: str, import_name: str = None) -> bool:
    """
    Verifica si un paquete está instalado

    Args:
        package_name: Nombre del paquete en pip (ej: 'opencv-python')
        import_name: Nombre para importar (ej: 'cv2'). Si es None, usa package_name

    Returns:
        True si está instalado, False si no
    """
    if import_name is None:
        import_name = package_name.replace('-', '_')

    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def install_package(package_name: str, version: str = None) -> bool:
    """
    Instala un paquete usando pip

    Args:
        package_name: Nombre del paquete
        version: Versión específica (ej: '>=0.21.0')

    Returns:
        True si se instaló correctamente, False si falló
    """
    try:
        package_spec = f"{package_name}{version}" if version else package_name
        print(f"[INSTALL] Instalando {package_spec}...")

        # Usar pip del python actual
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', package_spec],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )

        print(f"[INSTALL] ✓ {package_name} instalado")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[INSTALL] ✗ Error instalando {package_name}: {e}")
        return False
    except Exception as e:
        print(f"[INSTALL] ✗ Error inesperado: {e}")
        return False


# Definición de dependencias
CORE_DEPENDENCIES = [
    ('flask', 'flask', '>=2.0.0'),
    ('opencv-python', 'cv2', '>=4.5.0'),
    ('numpy', 'numpy', '>=1.19.0'),
    ('Pillow', 'PIL', '>=8.0.0'),
]

OPTIONAL_DEPENDENCIES = [
    ('bleak', 'bleak', '>=0.21.0', 'Control BLE de puerta'),
    ('RPi.GPIO', 'RPi.GPIO', '>=0.7.1', 'GPIO en Raspberry Pi (solo RPi)'),
    ('mediapipe', 'mediapipe', None, 'Detección facial rápida'),
    ('scipy', 'scipy', None, 'Cálculos de distancia mejorados'),
    ('tqdm', 'tqdm', '>=4.50.0', 'Barras de progreso'),
]

# Dependencias pesadas (solo para reconocimiento con dlib)
HEAVY_DEPENDENCIES = [
    ('face_recognition', 'face_recognition', '>=1.3.0'),
    ('face-recognition-models', None, '>=0.3.0'),
    ('dlib', 'dlib', '>=19.22.0'),
]


def check_core_dependencies(auto_install: bool = False) -> bool:
    """
    Verifica dependencias core del sistema

    Args:
        auto_install: Si True, intenta instalar las faltantes

    Returns:
        True si todas están disponibles, False si falta alguna
    """
    print("\n[DEPS] Verificando dependencias CORE...")

    all_ok = True
    missing = []

    for package_name, import_name, version in CORE_DEPENDENCIES:
        if check_package(package_name, import_name):
            print(f"  ✓ {package_name}")
        else:
            print(f"  ✗ {package_name} - FALTANTE")
            all_ok = False
            missing.append((package_name, version))

    if not all_ok:
        if auto_install:
            print("\n[DEPS] Instalando dependencias faltantes...")
            for package_name, version in missing:
                install_package(package_name, version)

            # Re-verificar
            print("\n[DEPS] Re-verificando...")
            return check_core_dependencies(auto_install=False)
        else:
            print("\n[DEPS] ✗ Faltan dependencias CORE")
            print("[DEPS] Instala con: pip3 install -r requirements.txt")
            print("[DEPS] O ejecuta con: python3 app.py --install-deps")
            return False

    print("[DEPS] ✓ Todas las dependencias CORE están disponibles\n")
    return True


def check_optional_dependencies(auto_install: bool = False) -> dict:
    """
    Verifica dependencias opcionales

    Args:
        auto_install: Si True, intenta instalar las faltantes

    Returns:
        Dict con {feature: available}
    """
    print("\n[DEPS] Verificando dependencias OPCIONALES...")

    results = {}
    missing = []

    for package_name, import_name, version, description in OPTIONAL_DEPENDENCIES:
        # RPi.GPIO solo en Raspberry Pi
        if package_name == 'RPi.GPIO':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    if 'Raspberry Pi' not in f.read():
                        print(f"  ⊘ {package_name} - Omitido (no es Raspberry Pi)")
                        results[package_name] = False
                        continue
            except:
                print(f"  ⊘ {package_name} - Omitido (no es Raspberry Pi)")
                results[package_name] = False
                continue

        if check_package(package_name, import_name):
            print(f"  ✓ {package_name} - {description}")
            results[package_name] = True
        else:
            print(f"  ✗ {package_name} - {description} (OPCIONAL)")
            results[package_name] = False
            missing.append((package_name, version, description))

    if missing and auto_install:
        print("\n[DEPS] Instalando dependencias opcionales...")
        for package_name, version, description in missing:
            if package_name == 'RPi.GPIO':
                continue  # Ya se filtró arriba
            install_package(package_name, version)

        # Re-verificar
        print("\n[DEPS] Re-verificando opcionales...")
        return check_optional_dependencies(auto_install=False)

    print()
    return results


def check_ble_support() -> bool:
    """Verifica si el soporte BLE está disponible"""
    return check_package('bleak', 'bleak')


def check_gpio_support() -> bool:
    """Verifica si el soporte GPIO está disponible"""
    return check_package('RPi.GPIO', 'RPi.GPIO')


def print_system_summary(optional_deps: dict):
    """Imprime un resumen del sistema"""
    print("="*70)
    print("  RESUMEN DEL SISTEMA")
    print("="*70)

    # Funcionalidades disponibles
    print("\n📦 Funcionalidades:")
    print(f"  • Streaming de video: ✓ Disponible")
    print(f"  • Detección facial: ✓ Disponible")
    print(f"  • Reconocimiento facial: ✓ Disponible")

    # BLE
    if optional_deps.get('bleak', False):
        print(f"  • Control BLE de puerta: ✓ Disponible")
    else:
        print(f"  • Control BLE de puerta: ✗ No disponible")
        print(f"    Instala con: pip3 install bleak>=0.21.0")

    # GPIO
    if optional_deps.get('RPi.GPIO', False):
        print(f"  • Control GPIO: ✓ Disponible")
    else:
        print(f"  • Control GPIO: ⊘ No disponible (no es Raspberry Pi o no instalado)")

    # MediaPipe
    if optional_deps.get('mediapipe', False):
        print(f"  • Detección rápida (MediaPipe): ✓ Disponible")
    else:
        print(f"  • Detección rápida (MediaPipe): ✗ No disponible")
        print(f"    Instala con: pip3 install mediapipe")

    print()


def verify_and_install(auto_install: bool = False) -> bool:
    """
    Función principal de verificación

    Args:
        auto_install: Si True, instala automáticamente las faltantes

    Returns:
        True si el sistema puede arrancar, False si no
    """
    print("\n" + "="*70)
    print("  VERIFICACIÓN DE DEPENDENCIAS")
    print("="*70)

    # Verificar core (necesarias)
    if not check_core_dependencies(auto_install=auto_install):
        return False

    # Verificar opcionales (no bloquean arranque)
    optional = check_optional_dependencies(auto_install=auto_install)

    # Mostrar resumen
    print_system_summary(optional)

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Verifica e instala dependencias')
    parser.add_argument('--install', action='store_true',
                       help='Instalar dependencias faltantes automáticamente')

    args = parser.parse_args()

    success = verify_and_install(auto_install=args.install)

    if success:
        print("✓ Sistema listo para arrancar\n")
        sys.exit(0)
    else:
        print("✗ Faltan dependencias críticas\n")
        sys.exit(1)
