#!/usr/bin/env python3
"""
Script para preparar dataset de personas DESCONOCIDAS
Usa LFW (Labeled Faces in the Wild) u otro dataset público
"""

import os
import sys
import shutil
import random
from pathlib import Path
from tqdm import tqdm
import tarfile
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False


def download_lfw(output_dir: str = "dataset/unknown"):
    """
    Descarga y prepara el dataset LFW (Labeled Faces in the Wild)
    """
    print("\n" + "="*70)
    print("DESCARGA DE DATASET LFW - PERSONAS DESCONOCIDAS")
    print("="*70)

    # URLs del dataset (probamos múltiples mirrors)
    lfw_urls = [
        "http://vis-www.cs.umass.edu/lfw/lfw.tgz",
        "https://vis-www.cs.umass.edu/lfw/lfw.tgz",  # Intentar HTTPS
        "http://vis-www.cs.umass.edu/lfw/lfw-deepfunneled.tgz"  # Mirror alternativo
    ]
    lfw_file = "lfw.tgz"

    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)

    # Descargar si no existe
    if not os.path.exists(lfw_file):
        print(f"\n[*] Descargando LFW dataset (~173 MB)...")

        success = False
        for attempt, lfw_url in enumerate(lfw_urls, 1):
            print(f"\n[*] Intento {attempt}/{len(lfw_urls)}: {lfw_url}")

            try:
                if HAS_REQUESTS:
                    # Usar requests con timeout y mejor manejo
                    response = requests.get(lfw_url, stream=True, timeout=30)
                    response.raise_for_status()

                    total_size = int(response.headers.get('content-length', 0))

                    with open(lfw_file, 'wb') as f, tqdm(
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        desc="Descargando"
                    ) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))

                    print("[OK] Descarga completada")
                    success = True
                    break
                else:
                    # Fallback a urllib con timeout
                    def show_progress(block_num, block_size, total_size):
                        downloaded = block_num * block_size
                        percent = min(100, downloaded * 100 / total_size if total_size > 0 else 0)
                        print(f"\r[{'=' * int(percent // 2)}{' ' * (50 - int(percent // 2))}] {percent:.1f}%", end='')

                    # Configurar timeout
                    import socket
                    socket.setdefaulttimeout(30)

                    urllib.request.urlretrieve(lfw_url, lfw_file, show_progress)
                    print("\n[OK] Descarga completada")
                    success = True
                    break

            except Exception as e:
                print(f"[!] Falló: {e}")
                if attempt < len(lfw_urls):
                    print("[*] Probando siguiente URL...")
                    time.sleep(2)

        if not success:
            print(f"\n[ERROR] No se pudo descargar desde ningún mirror")

            # Intentar métodos alternativos de descarga
            print("\n[*] Probando métodos alternativos de descarga...")

            # Método 1: Intentar con subprocess y cambio de DNS temporal
            try:
                import subprocess
                print("[*] Intentando descarga con DNS alternativo (1.1.1.1)...")

                # Intentar con curl usando DNS de Cloudflare
                result = subprocess.run([
                    "curl", "-L",
                    "--dns-servers", "1.1.1.1,8.8.8.8",
                    "-o", lfw_file,
                    "--connect-timeout", "30",
                    "--progress-bar",
                    "http://vis-www.cs.umass.edu/lfw/lfw.tgz"
                ], capture_output=False)

                if result.returncode == 0 and os.path.exists(lfw_file):
                    print("\n[OK] Descarga completada con curl+DNS alternativo")
                    success = True
            except Exception as e:
                print(f"[!] Método alternativo falló: {e}")

            if not success:
                print(f"\n[ERROR] Todos los métodos de descarga fallaron")
                print("\n[INFO] Esto parece ser un problema de DNS.")
                print("\nSOLUCIONES ALTERNATIVAS:")
                print("="*70)

                print("\n1. DESCARGA DESDE KAGGLE (Recomendado):")
                print("   pip install kaggle")
                print("   kaggle datasets download -d jessicali9530/lfw-dataset")
                print("   unzip lfw-dataset.zip")
                print("   mv lfw-dataset/lfw.tgz ./")

                print("\n2. DESCARGA MANUAL:")
                print("   - Abre en navegador: http://vis-www.cs.umass.edu/lfw/lfw.tgz")
                print("   - Guarda como: lfw.tgz")
                print("   - Vuelve a ejecutar este script")

                print("\n3. USA TU PROPIO DATASET:")
                print("   python3 scripts/setup_unknown_dataset.py custom /path/to/imagenes")

                print("\n4. USA SCRIPT ALTERNATIVO:")
                print("   python3 scripts/download_lfw_alternative.py")

                print("="*70)
                return False
    else:
        print(f"[INFO] Archivo {lfw_file} ya existe, saltando descarga")

    # Extraer
    print("\n[*] Extrayendo dataset...")
    try:
        with tarfile.open(lfw_file, 'r:gz') as tar:
            tar.extractall('.')
        print("[OK] Extracción completada")
    except Exception as e:
        print(f"[ERROR] Falló la extracción: {e}")
        return False

    # Mover y organizar
    print("\n[*] Organizando imágenes de desconocidos...")
    lfw_dir = Path("lfw")

    if not lfw_dir.exists():
        print("[ERROR] Directorio lfw/ no encontrado")
        return False

    # Contar personas y imágenes
    all_persons = list(lfw_dir.iterdir())
    print(f"[INFO] Encontradas {len(all_persons)} personas en LFW")

    # Seleccionar subset aleatorio (50-100 personas)
    num_unknown = min(100, len(all_persons))
    selected_persons = random.sample(all_persons, num_unknown)

    print(f"[*] Seleccionando {num_unknown} personas como desconocidos...")

    # Crear estructura
    unknown_dir = Path(output_dir)
    unknown_dir.mkdir(exist_ok=True)

    total_images = 0

    for person_dir in tqdm(selected_persons, desc="Copiando"):
        if not person_dir.is_dir():
            continue

        # Copiar todas las imágenes a un directorio plano
        images = list(person_dir.glob("*.jpg"))
        for img in images:
            # Renombrar para evitar conflictos
            new_name = f"{person_dir.name}_{img.name}"
            dest = unknown_dir / new_name
            shutil.copy2(img, dest)
            total_images += 1

    print(f"\n[OK] {total_images} imágenes de desconocidos copiadas a {output_dir}")

    # Limpiar
    print("\n[*] ¿Eliminar archivos temporales? (lfw/ y lfw.tgz)")
    print("    Esto liberará ~500 MB de espacio")
    response = input("    Eliminar? (s/N): ").strip().lower()

    if response == 's':
        if lfw_dir.exists():
            shutil.rmtree(lfw_dir)
        if os.path.exists(lfw_file):
            os.remove(lfw_file)
        print("[OK] Archivos temporales eliminados")

    print("\n" + "="*70)
    print("[✓] DATASET DE DESCONOCIDOS PREPARADO")
    print("="*70)
    print(f"[OK] Ubicación: {output_dir}/")
    print(f"[OK] Imágenes: {total_images}")
    print(f"[OK] Personas: {num_unknown}")
    print("\n[INFO] Ahora entrena con: python3 scripts/train_model_with_unknowns.py")
    print("="*70 + "\n")

    return True


def prepare_custom_unknowns(input_dir: str, output_dir: str = "dataset/unknown",
                            max_images: int = 500):
    """
    Prepara dataset personalizado de desconocidos
    Útil si ya tienes un dataset propio
    """
    print("\n" + "="*70)
    print("PREPARAR DATASET PERSONALIZADO DE DESCONOCIDOS")
    print("="*70)

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"[ERROR] Directorio no existe: {input_dir}")
        return False

    output_path.mkdir(exist_ok=True)

    # Buscar todas las imágenes recursivamente
    image_extensions = ['*.jpg', '*.jpeg', '*.png']
    all_images = []

    for ext in image_extensions:
        all_images.extend(input_path.rglob(ext))

    print(f"[INFO] Encontradas {len(all_images)} imágenes")

    if len(all_images) > max_images:
        print(f"[INFO] Seleccionando {max_images} imágenes aleatorias...")
        all_images = random.sample(all_images, max_images)

    # Copiar imágenes
    print("[*] Copiando imágenes...")
    for i, img_path in enumerate(tqdm(all_images), 1):
        dest = output_path / f"unknown_{i:04d}{img_path.suffix}"
        shutil.copy2(img_path, dest)

    print(f"\n[OK] {len(all_images)} imágenes copiadas a {output_dir}")
    print("="*70 + "\n")

    return True


def main():
    """Función principal"""

    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("SETUP DATASET DE DESCONOCIDOS")
        print("="*70)
        print("\nUso:")
        print("  python3 scripts/setup_unknown_dataset.py <opcion>")
        print("\nOpciones:")
        print("  lfw                    - Descargar LFW (Labeled Faces in the Wild)")
        print("  custom <directorio>    - Usar dataset personalizado")
        print("\nEjemplos:")
        print("  python3 scripts/setup_unknown_dataset.py lfw")
        print("  python3 scripts/setup_unknown_dataset.py custom /path/to/images")
        print("="*70 + "\n")
        return

    option = sys.argv[1]

    if option == "lfw":
        download_lfw()

    elif option == "custom":
        if len(sys.argv) < 3:
            print("[ERROR] Falta la ruta del directorio")
            print("Uso: python3 scripts/setup_unknown_dataset.py custom <directorio>")
            return

        input_dir = sys.argv[2]
        prepare_custom_unknowns(input_dir)

    else:
        print(f"[ERROR] Opción desconocida: {option}")
        print("Opciones válidas: lfw, custom")


if __name__ == "__main__":
    main()
