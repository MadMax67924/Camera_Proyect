#!/usr/bin/env python3
"""
SETUP INICIAL - Instala todo lo necesario
Ejecutar solo UNA VEZ al principio
"""

import subprocess
import sys
import os


def run_cmd(cmd, description):
    """Ejecuta comando con descripción"""
    print(f"\n[*] {description}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"⚠️  Advertencia: {description} falló")
        return False
    return True


def main():
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  SETUP INICIAL - SISTEMA DE RECONOCIMIENTO FACIAL                ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n[1/3] Creando estructura de directorios...")
    directories = [
        "dataset/raw",
        "dataset/unknown", 
        "dataset/processed",
        "models",
        "logs",
        "config"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✓ {directory}")
    
    print("\n[2/3] Instalando dependencias Python...")
    cmd = f"{sys.executable} -m pip install -q -r requirements.txt"
    if not run_cmd(cmd, "Instalación de dependencias"):
        print("⚠️  Intentando instalación alternativa...")
        run_cmd(f"{sys.executable} -m pip install --upgrade pip", "Actualizar pip")
        run_cmd(cmd, "Reinstalar dependencias")
    
    print("\n[3/3] Verificando instalación...")
    cmd = f"{sys.executable} test_system.py"
    run_cmd(cmd, "Verificación del sistema")
    
    print("""
    
    ╔════════════════════════════════════════════════════════════════════╗
    ║  ✅ SETUP COMPLETADO                                              ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    🚀 PRÓXIMOS PASOS:
    
    1. Usar interfaz interactiva:
       python3 master.py
    
    2. O usar comandos directos:
       
       📸 Capturar imágenes:
          python3 scripts/capture_faces.py "Tu Nombre"
       
       🤖 Entrenar modelo:
          python3 scripts/train_model_new.py
       
       🌐 Iniciar servidor:
          python3 app.py
    
    📚 Para más información:
       - README.md (configuración)
       - QUICKSTART_BLE.md (control BLE)
    
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelado")
        sys.exit(1)
