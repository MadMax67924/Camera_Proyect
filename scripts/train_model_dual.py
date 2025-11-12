#!/usr/bin/env python3
"""
Entrenador de modelo facial DUAL - SIN DLIB
Entrena DOS modelos:
1. Modelo de CONOCIDOS - Identifica personas específicas
2. Modelo de DESCONOCIDOS - Detecta si es alguien desconocido

Versión optimizada para Raspberry Pi
Usa OpenCV + Scikit-learn
"""

import cv2
import numpy as np
import pickle
import os
import sys
from pathlib import Path
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import IsolationForest


def extract_face_features(frame: np.ndarray, face_rect: tuple) -> np.ndarray:
    """
    Extrae características de un rostro detectado - VERSIÓN OPTIMIZADA
    Reduce características de 4132 a ~278 para mejor velocidad
    
    Args:
        frame: Imagen BGR
        face_rect: Tupla (x, y, w, h)
        
    Returns:
        Vector de características
    """
    x, y, w, h = face_rect
    
    # Validar coordenadas
    if x < 0 or y < 0 or x+w > frame.shape[1] or y+h > frame.shape[0]:
        return None
    
    # Extraer región del rostro
    face_roi = frame[y:y+h, x:x+w]
    
    if face_roi.size == 0:
        return None
    
    # Redimensionar a tamaño más pequeño (32x32)
    face_resized = cv2.resize(face_roi, (32, 32))
    
    # Convertir a escala de grises
    face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
    
    # Extraer características optimizadas
    features = []
    
    # 1. Píxeles aplanados pequeños (16x16 = 256)
    face_small = cv2.resize(face_gray, (16, 16))
    features.extend(face_small.flatten().tolist())
    
    # 2. Estadísticas básicas (4)
    features.append(float(face_gray.mean()))
    features.append(float(face_gray.std()))
    features.append(float(np.min(face_gray)))
    features.append(float(np.max(face_gray)))
    
    # 3. Histograma reducido (16)
    hist = cv2.calcHist([face_gray], [0], None, [16], [0, 256])
    features.extend(hist.flatten().tolist())
    
    # 4. Características de bordes (2)
    edges = cv2.Canny(face_gray, 100, 200)
    features.append(float(edges.mean()))
    features.append(float(edges.sum() / (32 * 32)))
    
    # Total: 256 + 4 + 16 + 2 = 278 características
    return np.array(features, dtype=np.float32)


def train_dual_model(dataset_dir: str = "dataset/raw",
                     output_known: str = "models/faces_model_known.pkl",
                     output_unknown: str = "models/faces_model_unknown.pkl"):
    """
    Entrena DOS modelos desde el dataset
    
    1. MODELO CONOCIDOS: KNN para identificar personas específicas
    2. MODELO DESCONOCIDOS: Isolation Forest para detectar anomalías
    
    Estructura esperada:
    dataset/raw/
        ├── Persona1/
        │   ├── img1.jpg
        │   └── img2.jpg
        └── Persona2/
            ├── img1.jpg
            └── img2.jpg
    
    Args:
        dataset_dir: Ruta al directorio con imágenes
        output_known: Ruta del modelo de conocidos
        output_unknown: Ruta del modelo de desconocidos
        
    Returns:
        True si se entrenó exitosamente
    """
    
    print("\n" + "="*70)
    print("ENTRENADOR DE MODELO FACIAL DUAL - SIN DLIB")
    print("Modelos: CONOCIDOS (KNN) + DESCONOCIDOS (Isolation Forest)")
    print("="*70)
    print(f"[*] Dataset: {dataset_dir}")
    print(f"[*] Modelo conocidos: {output_known}")
    print(f"[*] Modelo desconocidos: {output_unknown}")
    
    # Crear carpetas de modelos si no existen
    os.makedirs(os.path.dirname(output_known) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_unknown) or ".", exist_ok=True)
    
    # Cargar clasificador Haar Cascade
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    print(f"[OK] Cascade Classifier cargado")
    
    # Buscar carpetas de personas en el dataset
    dataset_path = Path(dataset_dir)
    
    if not dataset_path.exists():
        print(f"[ERROR] Dataset no encontrado: {dataset_dir}")
        return False
    
    person_dirs = sorted([d for d in dataset_path.iterdir() if d.is_dir()])
    
    if not person_dirs:
        print("[ERROR] No hay carpetas en dataset/raw")
        return False
    
    print(f"[OK] Personas encontradas: {len(person_dirs)}")
    
    X_train = []
    y_train = []
    
    images_processed = 0
    images_failed = 0
    
    # Procesar cada persona
    for person_dir in person_dirs:
        person_name = person_dir.name
        image_files = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.png"))
        
        if not image_files:
            print(f"  ⚠ {person_name}: sin imágenes")
            continue
        
        images_processed_person = 0
        images_failed_person = 0
        
        for img_path in tqdm(image_files, desc=f"  {person_name}", leave=False):
            try:
                # Leer imagen
                img = cv2.imread(str(img_path))
                if img is None:
                    images_failed_person += 1
                    continue
                
                # Convertir a escala de grises
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Detectar rostros
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                # Procesar cada rostro detectado
                for (x, y, w, h) in faces:
                    features = extract_face_features(img, (x, y, w, h))
                    if features is not None:
                        X_train.append(features)
                        y_train.append(person_name)
                        images_processed += 1
                        images_processed_person += 1
                
            except Exception as e:
                images_failed += 1
                images_failed_person += 1
                continue
        
        print(f"  ✓ Procesadas: {images_processed_person} | ✗ Errores: {images_failed_person}")
    
    if not X_train:
        print("[ERROR] No se extrajeron características de ninguna imagen")
        return False
    
    print()
    print(f"[*] Total de muestras: {len(X_train)}")
    print(f"[*] Personas únicas: {len(set(y_train))}")
    
    # ============================================================
    # MODELO 1: CONOCIDOS (KNN para clasificación)
    # ============================================================
    print("\n" + "="*70)
    print("ENTRENANDO MODELO 1: CONOCIDOS (KNN)")
    print("="*70)
    
    # Normalizar características
    print("[*] Normalizando características...")
    scaler_known = StandardScaler()
    X_train_scaled = scaler_known.fit_transform(X_train)
    
    # Entrenar clasificador KNN
    print("[*] Entrenando clasificador KNN (k=5)...")
    knn = KNeighborsClassifier(n_neighbors=5, n_jobs=-1)
    knn.fit(X_train_scaled, y_train)
    
    # Guardar modelo de conocidos
    print(f"[*] Guardando modelo de conocidos en {output_known}...")
    model_known_data = {
        'classifier': knn,
        'scaler': scaler_known,
        'names': y_train,  # Lista completa con nombres repetidos
        'unique_names': list(set(y_train)),  # Personas únicas
        'model_type': 'known'
    }
    
    with open(output_known, 'wb') as f:
        pickle.dump(model_known_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    model_size_mb = os.path.getsize(output_known) / (1024*1024)
    print(f"[OK] Archivo: {output_known}")
    print(f"[OK] Tamaño: {model_size_mb:.2f} MB")
    print(f"[OK] Personas: {', '.join(sorted(set(y_train)))}")
    
    # ============================================================
    # MODELO 2: DESCONOCIDOS (Isolation Forest para anomalías)
    # ============================================================
    print("\n" + "="*70)
    print("ENTRENANDO MODELO 2: DESCONOCIDOS (Isolation Forest)")
    print("="*70)
    
    print("[*] Entrenando detector de anomalías (Isolation Forest)...")
    # Usar los datos normalizados del modelo anterior
    iso_forest = IsolationForest(
        contamination=0.1,  # 10% de anomalías esperadas
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train_scaled)
    
    # Guardar modelo de desconocidos
    print(f"[*] Guardando modelo de desconocidos en {output_unknown}...")
    model_unknown_data = {
        'anomaly_detector': iso_forest,
        'scaler': scaler_known,  # Usar el mismo scaler
        'model_type': 'unknown'
    }
    
    with open(output_unknown, 'wb') as f:
        pickle.dump(model_unknown_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    model_size_mb = os.path.getsize(output_unknown) / (1024*1024)
    print(f"[OK] Archivo: {output_unknown}")
    print(f"[OK] Tamaño: {model_size_mb:.2f} MB")
    
    # Resumen final
    print("\n" + "="*70)
    print("[✓] MODELOS ENTRENADOS EXITOSAMENTE")
    print("="*70)
    print(f"[*] Modelo CONOCIDOS: {len(set(y_train))} personas identificables")
    print(f"[*] Modelo DESCONOCIDOS: Detector de anomalías entrenado")
    print(f"[*] Total de muestras usadas: {len(X_train)}")
    print("="*70)
    print()
    
    return True


def main():
    """Función principal"""
    
    # Argumentos de línea de comandos
    dataset = sys.argv[1] if len(sys.argv) > 1 else "dataset/raw"
    output_known = sys.argv[2] if len(sys.argv) > 2 else "models/faces_model_known.pkl"
    output_unknown = sys.argv[3] if len(sys.argv) > 3 else "models/faces_model_unknown.pkl"
    
    success = train_dual_model(dataset, output_known, output_unknown)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
