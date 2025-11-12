#!/usr/bin/env python3
"""
FIXALL - Detecta y corrige problemas automáticamente
"""

import sys
import os
from pathlib import Path
import pickle
import json


def fix_model_compatibility():
    """Asegura compatibilidad de modelos"""
    print("\n[*] Verificando compatibilidad de modelos...")
    
    models_dir = Path("models")
    if not models_dir.exists():
        print("  ℹ No hay carpeta de modelos")
        return
    
    for model_file in models_dir.glob("*.pkl"):
        try:
            with open(model_file, 'rb') as f:
                data = pickle.load(f)
            
            # Verificar campos requeridos
            required = ['classifier', 'scaler', 'names']
            missing = [k for k in required if k not in data]
            
            if missing:
                print(f"  ⚠️  {model_file.name}: faltan campos {missing}")
            else:
                print(f"  ✓ {model_file.name}: OK")
                
        except Exception as e:
            print(f"  ❌ {model_file.name}: {e}")


def fix_config():
    """Asegura que config.json existe"""
    print("\n[*] Verificando configuración...")
    
    config_file = Path("config/authorized_users.json")
    
    if not config_file.exists():
        print(f"  ℹ Creando configuración por defecto...")
        config_file.parent.mkdir(exist_ok=True)
        
        default_config = {
            "authorized_users": ["Usuario1", "Usuario2"],
            "door_open_duration": 3,
            "cooldown_time": 5
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Configuración creada: {config_file}")
    else:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"  ✓ Configuración OK")
        except Exception as e:
            print(f"  ❌ Error en configuración: {e}")


def fix_directories():
    """Asegura que todos los directorios existen"""
    print("\n[*] Verificando directorios...")
    
    dirs = [
        "dataset/raw",
        "dataset/unknown",
        "dataset/processed",
        "models",
        "logs",
        "config",
        "templates"
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}")


def fix_python_cache():
    """Limpia caché de Python"""
    print("\n[*] Limpiando caché de Python...")
    
    import subprocess
    result = subprocess.run(
        ["find", ".", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("  ✓ Caché limpiada")
    else:
        print("  ⚠️  No se pudo limpiar toda la caché")


def verify_imports():
    """Verifica que los imports críticos funcionan"""
    print("\n[*] Verificando imports críticos...")
    
    imports = [
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("flask", "Flask"),
        ("sklearn", "Scikit-learn"),
        ("scipy", "SciPy"),
        ("tqdm", "TQDM"),
        ("requests", "Requests"),
        ("bleak", "Bleak (BLE)"),
    ]
    
    failed = []
    for module, name in imports:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ⚠️  {name} no disponible (intentaremos instalar)")
            failed.append(module)
    
    if failed:
        print(f"\n[*] Instalando paquetes faltantes: {', '.join(failed)}")
        import subprocess
        for pkg in failed:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg])
            except:
                pass


def main():
    print("""
    
    ╔════════════════════════════════════════════════════════════════════╗
    ║  FIXALL - Reparación automática del sistema                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        fix_directories()
        fix_config()
        verify_imports()
        fix_python_cache()
        fix_model_compatibility()
        
        print("\n" + "="*70)
        print("✅ REPARACIÓN COMPLETADA")
        print("="*70)
        print("\nEjecutar: python3 test_system.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
