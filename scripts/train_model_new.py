#!/usr/bin/env python3
"""
Entrenador de modelo facial SIN DLIB
Versión optimizada para Raspberry Pi
Usa OpenCV + Scikit-learn
Entrena en 2-5 minutos (vs 10-15 con dlib)
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
from sklearn.model_selection import train_test_split, cross_val_score


def extract_face_features(frame: np.ndarray, face_rect: tuple) -> np.ndarray:
    """
    Extrae características de un rostro detectado - VERSIÓN OPTIMIZADA
    Reduce características de 4132 a ~530 para mejor velocidad
    
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
    
    # Redimensionar a tamaño más pequeño (32x32 en lugar de 64x64)
    face_resized = cv2.resize(face_roi, (32, 32))
    
    # Convertir a escala de grises
    face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
    
    # Extraer características optimizadas
    features = []
    
    # 1. Píxeles aplanados (32*32 = 1024, reducido a 512 con redimensión)
    face_small = cv2.resize(face_gray, (16, 16))
    features.extend(face_small.flatten().tolist())
    
    # 2. Estadísticas básicas (4)
    features.append(float(face_gray.mean()))
    features.append(float(face_gray.std()))
    features.append(float(np.min(face_gray)))
    features.append(float(np.max(face_gray)))
    
    # 3. Histograma reducido (16 bins en lugar de 32)
    hist = cv2.calcHist([face_gray], [0], None, [16], [0, 256])
    features.extend(hist.flatten().tolist())
    
    # 4. Características de bordes (HOG simplificado)
    edges = cv2.Canny(face_gray, 100, 200)
    features.append(float(edges.mean()))
    features.append(float(edges.sum() / (32 * 32)))
    
    # Total: 256 + 4 + 16 + 2 = 278 características (mucho más rápido que 4132)
    return np.array(features, dtype=np.float32)


def train_model(dataset_dir: str = "dataset/raw", 
                output_model: str = "models/faces_model_lite.pkl"):
    """
    Entrena el modelo desde el dataset
    
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
        output_model: Ruta de salida del modelo
        
    Returns:
        True si se entrenó exitosamente
    """
    
    print("\n" + "="*60)
    print("ENTRENADOR DE MODELO FACIAL - SIN DLIB")
    print("="*60)
    print(f"[*] Dataset: {dataset_dir}")
    print(f"[*] Modelo salida: {output_model}")
    
    # Crear carpeta de modelos si no existe
    os.makedirs(os.path.dirname(output_model) or ".", exist_ok=True)
    
    # Cargar Cascade Classifier
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    if face_cascade.empty():
        print("[ERROR] No se pudo cargar Cascade Classifier")
        return False
    
    print("[OK] Cascade Classifier cargado")
    
    X_train = []  # Características
    y_train = []  # Etiquetas (nombres)
    
    # Verificar que existe el dataset
    dataset_path = Path(dataset_dir)
    
    if not dataset_path.exists():
        print(f"[ERROR] Carpeta no existe: {dataset_dir}")
        print(f"[!] Crea primero: {dataset_dir}")
        print("[!] Ejecuta: python3 scripts/capture_faces.py 'tu_nombre'")
        return False
    
    # Obtener carpetas de personas
    people_dirs = sorted([d for d in dataset_path.iterdir() if d.is_dir()])
    
    if not people_dirs:
        print(f"[ERROR] No hay carpetas en {dataset_dir}")
        return False
    
    print(f"[*] Encontradas {len(people_dirs)} personas")
    print()
    
    # Procesar cada persona
    for person_dir in people_dirs:
        person_name = person_dir.name
        
        # Obtener imágenes JPG y PNG
        image_files = list(person_dir.glob("*.jpg")) + \
                     list(person_dir.glob("*.png")) + \
                     list(person_dir.glob("*.jpeg"))
        
        if not image_files:
            print(f"[!] {person_name}: Sin imágenes, saltando...")
            continue
        
        print(f"[*] Procesando '{person_name}' ({len(image_files)} imágenes)")
        
        images_processed = 0
        images_failed = 0
        
        for img_path in tqdm(image_files, desc=f"  {person_name}", leave=False):
            try:
                # Leer imagen
                img = cv2.imread(str(img_path))
                if img is None:
                    images_failed += 1
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
                
            except Exception as e:
                images_failed += 1
                continue
        
        print(f"  ✓ Procesadas: {images_processed} | ✗ Errores: {images_failed}")
    
    if not X_train:
        print("[ERROR] No se extrajeron características de ninguna imagen")
        return False

    print()
    print(f"[*] Total de muestras: {len(X_train)}")
    print(f"[*] Personas únicas: {len(set(y_train))}")

    # Dividir en train y validación para encontrar mejor k
    X_train_split, X_val, y_train_split, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )

    print(f"[*] Entrenamiento: {len(X_train_split)} | Validación: {len(X_val)}")

    # Normalizar características
    print("[*] Normalizando características...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_split)
    X_val_scaled = scaler.transform(X_val)

    # Buscar mejor k
    print("[*] Buscando mejor k (vecinos)...")
    best_k = 5
    best_cv_score = 0

    for k in [3, 5, 7, 9]:
        knn_temp = KNeighborsClassifier(n_neighbors=k, n_jobs=-1)
        scores = cross_val_score(knn_temp, X_train_scaled, y_train_split, cv=3)
        mean_score = scores.mean()
        print(f"  k={k}: {mean_score*100:.2f}% accuracy")

        if mean_score > best_cv_score:
            best_cv_score = mean_score
            best_k = k

    print(f"[OK] Mejor k seleccionado: {best_k}")

    # Entrenar clasificador KNN con mejor k
    print(f"[*] Entrenando clasificador KNN (k={best_k})...")
    knn = KNeighborsClassifier(n_neighbors=best_k, n_jobs=-1)
    knn.fit(X_train_scaled, y_train_split)

    # Evaluar en validación
    val_predictions = knn.predict(X_val_scaled)
    val_accuracy = np.mean(np.array(val_predictions) == np.array(y_val))
    print(f"[OK] Precisión en validación: {val_accuracy*100:.1f}%")

    # Encontrar mejor umbral
    print("[*] Buscando mejor umbral de distancia...")
    distances, indices = knn.kneighbors(X_val_scaled)

    best_threshold = 60.0
    best_accuracy = 0.0

    for threshold in np.arange(30, 120, 5):
        correct = 0
        total = len(X_val)

        for i, (dists, idxs) in enumerate(zip(distances, indices)):
            best_dist = dists[0]
            best_idx = idxs[0]

            if best_dist <= threshold and best_idx < len(y_train_split):
                predicted_name = y_train_split[best_idx]
                if predicted_name == y_val[i]:
                    correct += 1

        accuracy = correct / total

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = threshold

    print(f"[OK] Mejor umbral: {best_threshold:.1f} (precisión: {best_accuracy*100:.1f}%)")

    # Re-entrenar con todos los datos usando mejor k
    print(f"[*] Re-entrenando con todos los datos...")
    X_all_scaled = scaler.fit_transform(X_train)
    knn_final = KNeighborsClassifier(n_neighbors=best_k, n_jobs=-1)
    knn_final.fit(X_all_scaled, y_train)
    
    # Guardar modelo
    print(f"[*] Guardando modelo en {output_model}...")
    model_data = {
        'classifier': knn_final,
        'scaler': scaler,
        'names': y_train,  # Guardar la lista completa con nombres repetidos (debe coincidir con índices del KNN)
        'unique_names': list(set(y_train)),  # También guardar las únicas para referencia
        'best_threshold': best_threshold,  # Umbral óptimo encontrado
        'validation_accuracy': val_accuracy,  # Precisión en validación
        'feature_dim': len(X_train[0]),  # Dimensión de características
        'n_samples': len(X_train)  # Total de muestras
    }

    with open(output_model, 'wb') as f:
        pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    model_size_mb = os.path.getsize(output_model) / (1024*1024)

    print()
    print("="*60)
    print("[✓] MODELO ENTRENADO EXITOSAMENTE")
    print("="*60)
    print(f"[OK] Archivo: {output_model}")
    print(f"[OK] Tamaño: {model_size_mb:.2f} MB")
    print(f"[OK] Personas: {', '.join(sorted(set(y_train)))}")
    print(f"[OK] Muestras: {len(X_train)}")
    print(f"[OK] Features: {len(X_train[0])}")
    print(f"[OK] Mejor k: {best_k}")
    print(f"[OK] Umbral óptimo: {best_threshold:.1f}")
    print(f"[OK] Precisión validación: {val_accuracy*100:.1f}%")
    print("="*60)
    print()
    
    return True


def main():
    """Función principal"""
    
    # Argumentos de línea de comandos
    dataset = sys.argv[1] if len(sys.argv) > 1 else "dataset/raw"
    output = sys.argv[2] if len(sys.argv) > 2 else "models/faces_model_lite.pkl"
    
    success = train_model(dataset, output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
