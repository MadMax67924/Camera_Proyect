#!/usr/bin/env python3
"""
DIAGNÓSTICO: Dataset de Desconocidos - Solución Rápida
"""

from pathlib import Path

def diagnose():
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO: Dataset de Desconocidos")
    print("="*70)
    
    # Verificar estructura
    print("\n📂 Estructura de carpetas:")
    print("-" * 70)
    
    raw_path = Path("dataset/raw")
    unknown_path = Path("dataset/unknown")
    processed_path = Path("dataset/processed")
    
    print(f"\n✓ dataset/raw/ (CONOCIDOS):")
    if raw_path.exists():
        dirs = [d for d in raw_path.iterdir() if d.is_dir()]
        for d in sorted(dirs):
            images = list(d.glob("*.jpg")) + list(d.glob("*.png"))
            print(f"    └─ {d.name}/ ({len(images)} fotos)")
    else:
        print("    └─ ❌ NO EXISTE")
    
    print(f"\n✓ dataset/unknown/ (DESCONOCIDOS):")
    if unknown_path.exists():
        dirs = [d for d in unknown_path.iterdir() if d.is_dir()]
        images = list(unknown_path.glob("*.jpg")) + list(unknown_path.glob("*.png"))
        if dirs:
            for d in sorted(dirs):
                imgs = list(d.glob("*.jpg")) + list(d.glob("*.png"))
                print(f"    └─ {d.name}/ ({len(imgs)} fotos)")
        elif images:
            print(f"    └─ ({len(images)} fotos directas)")
        else:
            print("    └─ ⚠️  EXISTE pero está VACÍO")
    else:
        print("    └─ ⚠️  NO EXISTE (se creará automáticamente)")
    
    print(f"\n✓ dataset/processed/ (ALTERNATIVO):")
    if processed_path.exists():
        dirs = [d for d in processed_path.iterdir() if d.is_dir()]
        images = list(processed_path.glob("*.jpg")) + list(processed_path.glob("*.png"))
        if dirs or images:
            print(f"    └─ ✓ DISPONIBLE ({len(list(processed_path.glob('*.jpg')))} fotos)")
        else:
            print("    └─ EXISTE pero vacío")
    else:
        print("    └─ ❌ NO EXISTE")
    
    # Diagnostico
    print("\n" + "="*70)
    print("🎯 DIAGNÓSTICO:")
    print("="*70)
    
    has_unknown = unknown_path.exists() and len(list(unknown_path.glob("*.jpg")) + list(unknown_path.glob("*.png")) + list(unknown_path.glob("*/*.jpg"))) > 0
    
    if has_unknown:
        print("\n✅ TODO LISTO - Puedes entrenar con desconocidos:")
        print("\n   python3 scripts/train_model_with_unknowns.py")
    else:
        print("\n⚠️  FALTA DATASET DE DESCONOCIDOS")
        print("\n   Tienes 3 opciones:")
        print("\n   1️⃣  CREAR dataset/unknown/ Y COPIAR IMÁGENES")
        print("       mkdir -p dataset/unknown")
        print("       # Copia fotos de desconocidos aquí")
        print("       python3 scripts/train_model_with_unknowns.py")
        print("\n   2️⃣  USAR dataset/processed/ COMO DESCONOCIDOS")
        if processed_path.exists():
            print("       python3 scripts/train_model_with_unknowns.py dataset/raw dataset/processed")
        else:
            print("       # Primero crea dataset/processed con imágenes")
        print("\n   3️⃣  ENTRENAR SIN DESCONOCIDOS (menos preciso)")
        print("       python3 scripts/train_model_new.py")
    
    print("\n" + "="*70)
    print("📋 ARCHIVOS DISPONIBLES:")
    print("="*70)
    print("\n✓ scripts/train_model_with_unknowns.py - Con soporte a desconocidos")
    print("✓ scripts/train_model_new.py          - Solo conocidos")
    print("✓ scripts/setup_unknown_dataset.py    - Gestor de dataset desconocidos")
    print("✓ GUIA_DATASET_DESCONOCIDOS.md        - Guía completa")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    diagnose()
