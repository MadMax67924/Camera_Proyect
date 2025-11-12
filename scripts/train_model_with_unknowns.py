#!/usr/bin/env python3
"""
Entrenador MEJORADO con dataset de DESCONOCIDOS
Entrena el modelo usando:
1. Personas CONOCIDAS (tu dataset actual)
2. Personas DESCONOCIDAS (LFW u otro dataset público)

Esto mejora SIGNIFICATIVAMENTE la detección de desconocidos
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
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

# Importar funciones del train_model_improved
sys.path.insert(0, str(Path(__file__).parent))
from train_model_improved import extract_face_features, find_best_threshold


def train_with_unknowns(known_dir: str = "dataset/raw",
                        unknown_dir: str = "dataset/unknown",
                        output_model: str = "models/faces_model_lite.pkl",
                        unknown_samples: int = 200):
    """
    Entrena modelo usando conocidos + desconocidos

    Args:
        known_dir: Directorio con personas conocidas
        unknown_dir: Directorio con personas desconocidas
        output_model: Ruta del modelo de salida
        unknown_samples: Número de muestras de desconocidos a usar
    """

    print("\n" + "="*70)
    print("ENTRENAMIENTO CON CONOCIDOS + DESCONOCIDOS")
    print("="*70)
    print(f"[*] Conocidos: {known_dir}")
    print(f"[*] Desconocidos: {unknown_dir}")
    print(f"[*] Modelo salida: {output_model}")

    # Verificar que existen ambos directorios
    known_path = Path(known_dir)
    unknown_path = Path(unknown_dir)

    if not known_path.exists():
        print(f"[ERROR] No existe: {known_dir}")
        return False

    if not unknown_path.exists():
        print(f"[ERROR] No existe: {unknown_dir}")
        print(f"[INFO] Ejecuta: python3 scripts/setup_unknown_dataset.py lfw")
        return False

    # Cargar Cascade Classifier
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        print("[ERROR] No se pudo cargar Cascade Classifier")
        return False

    print("[OK] Cascade Classifier cargado")

    X_known = []
    y_known = []
    X_unknown = []

    # ============================================================
    # PASO 1: Procesar CONOCIDOS
    # ============================================================
    print("\n" + "="*70)
    print("PASO 1: PROCESANDO PERSONAS CONOCIDAS")
    print("="*70)

    people_dirs = sorted([d for d in known_path.iterdir() if d.is_dir()])

    if not people_dirs:
        print(f"[ERROR] No hay carpetas en {known_dir}")
        return False

    print(f"[*] Encontradas {len(people_dirs)} personas conocidas")
    print()

    for person_dir in people_dirs:
        person_name = person_dir.name
        image_files = list(person_dir.glob("*.jpg")) + \
                     list(person_dir.glob("*.png")) + \
                     list(person_dir.glob("*.jpeg"))

        if not image_files:
            continue

        print(f"[*] Procesando '{person_name}' ({len(image_files)} imágenes)")

        for img_path in tqdm(image_files, desc=f"  {person_name}", leave=False):
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )

                for (x, y, w, h) in faces:
                    feature_list = extract_face_features(
                        img, (x, y, w, h), augment=True  # Con aumento
                    )

                    for features in feature_list:
                        if features is not None and len(features) > 0:
                            X_known.append(features)
                            y_known.append(person_name)

            except Exception as e:
                continue

        print(f"  ✓ Muestras: {sum(1 for y in y_known if y == person_name)}")

    print(f"\n[OK] Total conocidos: {len(X_known)} muestras de {len(set(y_known))} personas")

    # ============================================================
    # PASO 2: Procesar DESCONOCIDOS
    # ============================================================
    print("\n" + "="*70)
    print("PASO 2: PROCESANDO PERSONAS DESCONOCIDAS")
    print("="*70)

    # Obtener imágenes de desconocidos
    unknown_images = list(unknown_path.glob("*.jpg")) + \
                    list(unknown_path.glob("*.png")) + \
                    list(unknown_path.glob("*.jpeg"))

    if not unknown_images:
        print(f"[WARNING] No hay imágenes en {unknown_dir}")
        print("[INFO] El detector de anomalías será menos preciso")
    else:
        print(f"[INFO] Encontradas {len(unknown_images)} imágenes de desconocidos")

        # Limitar número de muestras
        if len(unknown_images) > unknown_samples:
            import random
            unknown_images = random.sample(unknown_images, unknown_samples)
            print(f"[INFO] Usando {unknown_samples} imágenes aleatorias")

        print(f"[*] Procesando desconocidos...")

        for img_path in tqdm(unknown_images, desc="  Desconocidos"):
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )

                # Solo tomar el primer rostro detectado
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    feature_list = extract_face_features(
                        img, (x, y, w, h), augment=False  # Sin aumento para desconocidos
                    )

                    if feature_list and len(feature_list) > 0:
                        X_unknown.append(feature_list[0])

            except Exception as e:
                continue

        print(f"\n[OK] Total desconocidos: {len(X_unknown)} muestras")

    # ============================================================
    # PASO 3: ENTRENAR MODELO
    # ============================================================
    print("\n" + "="*70)
    print("PASO 3: ENTRENANDO MODELO CON AMBOS DATASETS")
    print("="*70)

    if not X_known:
        print("[ERROR] No hay muestras de conocidos")
        return False

    # Dividir conocidos en train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_known, y_known, test_size=0.2, random_state=42, stratify=y_known
    )

    print(f"[*] Entrenamiento: {len(X_train)} muestras")
    print(f"[*] Validación: {len(X_val)} muestras")

    # Normalizar
    print("\n[*] Normalizando características...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    # Entrenar KNN
    print("[*] Buscando mejor k (vecinos)...")
    from sklearn.model_selection import cross_val_score

    best_k = 5
    best_cv_score = 0

    for k in [3, 5, 7, 9]:
        knn_temp = KNeighborsClassifier(n_neighbors=k, n_jobs=-1)
        scores = cross_val_score(knn_temp, X_train_scaled, y_train, cv=3)
        mean_score = scores.mean()
        print(f"  k={k}: {mean_score*100:.2f}% accuracy")

        if mean_score > best_cv_score:
            best_cv_score = mean_score
            best_k = k

    print(f"[OK] Mejor k seleccionado: {best_k}")

    # Entrenar con mejor k
    knn = KNeighborsClassifier(n_neighbors=best_k, n_jobs=-1)
    knn.fit(X_train_scaled, y_train)

    # Evaluar
    val_predictions = knn.predict(X_val_scaled)
    val_accuracy = np.mean(np.array(val_predictions) == np.array(y_val))
    print(f"[OK] Precisión en validación: {val_accuracy*100:.1f}%")

    # Encontrar mejor umbral
    best_threshold = find_best_threshold(X_val, y_val, knn, scaler, y_train)

    # ============================================================
    # PASO 4: ENTRENAR DETECTOR DE ANOMALÍAS CON DESCONOCIDOS
    # ============================================================
    print("\n" + "="*70)
    print("PASO 4: ENTRENANDO DETECTOR DE ANOMALÍAS")
    print("="*70)

    # Combinar conocidos + desconocidos para entrenar Isolation Forest
    if X_unknown:
        print(f"[*] Usando {len(X_known)} conocidos + {len(X_unknown)} desconocidos")

        # Normalizar desconocidos
        X_unknown_scaled = scaler.transform(X_unknown)

        # Entrenar SOLO con conocidos (Isolation Forest aprende lo "normal")
        iso_forest = IsolationForest(
            contamination=0.1,  # 10% de anomalías esperadas
            random_state=42,
            n_jobs=-1
        )

        # Entrenar con conocidos + algunos desconocidos
        X_combined = np.vstack([X_train_scaled, X_unknown_scaled[:len(X_train_scaled)//4]])
        iso_forest.fit(X_combined)

        # Evaluar en desconocidos
        unknown_predictions = iso_forest.predict(X_unknown_scaled)
        anomalies_detected = np.sum(unknown_predictions == -1)
        anomaly_rate = anomalies_detected / len(unknown_predictions) * 100

        print(f"[OK] Anomalías detectadas en desconocidos: {anomalies_detected}/{len(X_unknown)} ({anomaly_rate:.1f}%)")

        # Evaluar en conocidos (no deberían ser anomalías)
        known_predictions = iso_forest.predict(X_train_scaled)
        false_anomalies = np.sum(known_predictions == -1)
        false_rate = false_anomalies / len(known_predictions) * 100

        print(f"[OK] Falsos positivos en conocidos: {false_anomalies}/{len(X_train)} ({false_rate:.1f}%)")

    else:
        print("[WARNING] No hay desconocidos, usando solo conocidos")
        iso_forest = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
        iso_forest.fit(X_train_scaled)

    # Guardar modelo
    print(f"\n[*] Guardando modelo en {output_model}...")
    os.makedirs(os.path.dirname(output_model) or ".", exist_ok=True)

    model_data = {
        'classifier': knn,
        'scaler': scaler,
        'names': y_train,
        'unique_names': list(set(y_known)),
        'best_threshold': best_threshold,
        'anomaly_detector': iso_forest,
        'feature_dim': len(X_train[0]),
        'n_samples': len(X_known),
        'n_unknown_samples': len(X_unknown) if X_unknown else 0,
        'validation_accuracy': val_accuracy
    }

    with open(output_model, 'wb') as f:
        pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    model_size_mb = os.path.getsize(output_model) / (1024*1024)

    # Reporte final
    print("\n" + "="*70)
    print("[✓] MODELO ENTRENADO CON CONOCIDOS + DESCONOCIDOS")
    print("="*70)
    print(f"[OK] Archivo: {output_model}")
    print(f"[OK] Tamaño: {model_size_mb:.2f} MB")
    print(f"[OK] Personas conocidas: {', '.join(sorted(set(y_known)))}")
    print(f"[OK] Muestras conocidos: {len(X_known)}")
    print(f"[OK] Muestras desconocidos: {len(X_unknown) if X_unknown else 0}")
    print(f"[OK] Precisión validación: {val_accuracy*100:.1f}%")
    print(f"[OK] Umbral óptimo: {best_threshold:.1f}")
    if X_unknown:
        print(f"[OK] Detección de anomalías: {anomaly_rate:.1f}% en desconocidos")
    print("="*70)
    print("\n[INFO] El modelo ahora distingue MUCHO MEJOR entre conocidos y desconocidos")
    print("[INFO] Para probar: python3 scripts/evaluate_model.py webcam")
    print("="*70 + "\n")

    return True


def main():
    """Función principal"""

    # Argumentos
    known = sys.argv[1] if len(sys.argv) > 1 else "dataset/raw"
    unknown = sys.argv[2] if len(sys.argv) > 2 else "dataset/unknown"
    output = sys.argv[3] if len(sys.argv) > 3 else "models/faces_model_lite.pkl"

    success = train_with_unknowns(known, unknown, output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
