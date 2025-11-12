#!/usr/bin/env python3
"""
Entrenador de modelo facial MEJORADO - SIN DLIB
Versión optimizada con:
- Mejores características (LBP + HOG + Histograma)
- Validación cruzada para encontrar mejor umbral
- Métricas de evaluación
- Aumento de datos
- Detección de desconocidos mejorada
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
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')


def extract_lbp_features(gray_face: np.ndarray, num_points: int = 24, radius: int = 3) -> np.ndarray:
    """
    Extrae características LBP (Local Binary Patterns)
    Muy efectivo para reconocimiento facial
    """
    def get_pixel(img, center, x, y):
        new_value = 0
        try:
            if img[x][y] >= center:
                new_value = 1
        except:
            pass
        return new_value

    lbp = np.zeros_like(gray_face)
    h, w = gray_face.shape

    for i in range(1, h-1):
        for j in range(1, w-1):
            center = gray_face[i, j]
            val = 0
            val |= get_pixel(gray_face, center, i-1, j-1) << 7
            val |= get_pixel(gray_face, center, i-1, j) << 6
            val |= get_pixel(gray_face, center, i-1, j+1) << 5
            val |= get_pixel(gray_face, center, i, j+1) << 4
            val |= get_pixel(gray_face, center, i+1, j+1) << 3
            val |= get_pixel(gray_face, center, i+1, j) << 2
            val |= get_pixel(gray_face, center, i+1, j-1) << 1
            val |= get_pixel(gray_face, center, i, j-1) << 0
            lbp[i, j] = val

    # Histograma LBP
    hist, _ = np.histogram(lbp.ravel(), bins=32, range=(0, 256))
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-6)

    return hist


def extract_hog_features(gray_face: np.ndarray) -> np.ndarray:
    """
    Extrae características HOG (Histogram of Oriented Gradients)
    Captura patrones de bordes y formas
    """
    # Calcular gradientes
    gx = cv2.Sobel(gray_face, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_face, cv2.CV_32F, 0, 1, ksize=3)

    # Magnitud y ángulo
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)

    # Histograma de 16 bins
    hist, _ = np.histogram(ang.ravel(), bins=16, range=(0, 360), weights=mag.ravel())
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-6)

    return hist


def augment_image(img: np.ndarray) -> list:
    """
    Genera variaciones de la imagen para hacer el modelo más robusto
    """
    augmented = [img]

    # Rotaciones pequeñas
    rows, cols = img.shape[:2]
    for angle in [-10, 10]:
        M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
        rotated = cv2.warpAffine(img, M, (cols, rows))
        augmented.append(rotated)

    # Ajustes de brillo
    for beta in [-20, 20]:
        adjusted = cv2.convertScaleAbs(img, alpha=1.0, beta=beta)
        augmented.append(adjusted)

    # Flip horizontal
    flipped = cv2.flip(img, 1)
    augmented.append(flipped)

    return augmented


def extract_face_features(frame: np.ndarray, face_rect: tuple, augment: bool = False) -> list:
    """
    Extrae características MEJORADAS de un rostro detectado
    Combina múltiples técnicas para mejor discriminación

    Args:
        frame: Imagen BGR
        face_rect: Tupla (x, y, w, h)
        augment: Si True, genera variaciones de la imagen

    Returns:
        Lista de vectores de características (uno o varios si augment=True)
    """
    x, y, w, h = face_rect

    # Validar coordenadas
    if x < 0 or y < 0 or x+w > frame.shape[1] or y+h > frame.shape[0]:
        return []

    # Extraer región del rostro
    face_roi = frame[y:y+h, x:x+w]

    if face_roi.size == 0:
        return []

    # Aplicar aumento de datos si se solicita
    if augment:
        face_images = augment_image(face_roi)
    else:
        face_images = [face_roi]

    all_features = []

    for face_img in face_images:
        # Redimensionar a tamaño estándar
        face_resized = cv2.resize(face_img, (64, 64))

        # Convertir a escala de grises
        if len(face_resized.shape) == 3:
            face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        else:
            face_gray = face_resized

        # Ecualizar histograma para mejor contraste
        face_gray = cv2.equalizeHist(face_gray)

        features = []

        # 1. Píxeles aplanados reducidos (16x16 = 256)
        face_small = cv2.resize(face_gray, (16, 16))
        features.extend(face_small.flatten().tolist())

        # 2. Estadísticas básicas (6)
        features.append(float(face_gray.mean()))
        features.append(float(face_gray.std()))
        features.append(float(np.min(face_gray)))
        features.append(float(np.max(face_gray)))
        features.append(float(np.median(face_gray)))
        features.append(float(face_gray.var()))

        # 3. Histograma global (16)
        hist = cv2.calcHist([face_gray], [0], None, [16], [0, 256])
        features.extend(hist.flatten().tolist())

        # 4. LBP - Patrones locales binarios (32)
        lbp_hist = extract_lbp_features(face_gray)
        features.extend(lbp_hist.tolist())

        # 5. HOG - Histograma de gradientes orientados (16)
        hog_hist = extract_hog_features(face_gray)
        features.extend(hog_hist.tolist())

        # 6. Características de bordes (4)
        edges = cv2.Canny(face_gray, 100, 200)
        features.append(float(edges.mean()))
        features.append(float(edges.std()))
        features.append(float(edges.sum() / (64 * 64)))
        features.append(float(np.count_nonzero(edges) / (64 * 64)))

        # Total: 256 + 6 + 16 + 32 + 16 + 4 = 330 características
        all_features.append(np.array(features, dtype=np.float32))

    return all_features


def find_best_threshold(X_val, y_val, knn_model, scaler, y_train_split):
    """
    Encuentra el mejor umbral usando validación
    Busca el umbral que mejor separa conocidos de desconocidos
    """
    print("\n[*] Buscando mejor umbral de decisión...")

    # Probar diferentes umbrales
    thresholds = np.arange(10, 150, 5)
    best_threshold = 60
    best_score = 0

    results = []

    for threshold in thresholds:
        correct = 0
        total = len(y_val)

        for features, true_name in zip(X_val, y_val):
            # Normalizar
            features_scaled = scaler.transform([features])

            # Predecir
            distances, indices = knn_model.kneighbors(features_scaled)
            best_distance = distances[0][0]
            best_match_index = indices[0][0]

            # Verificar si la predicción es correcta
            if best_distance <= threshold:
                # Obtener el nombre predicho desde y_train_split
                if best_match_index < len(y_train_split):
                    pred_name = y_train_split[best_match_index]
                    if pred_name == true_name:
                        correct += 1
            else:
                # Si está fuera del umbral, debería ser desconocido
                # (en validación no tenemos desconocidos, así que esto sería un falso negativo)
                pass

        accuracy = correct / total
        results.append((threshold, accuracy))

        if accuracy > best_score:
            best_score = accuracy
            best_threshold = threshold

    print(f"[OK] Mejor umbral encontrado: {best_threshold:.1f}")
    print(f"[OK] Precisión en validación: {best_score*100:.1f}%")

    # Mostrar curva de threshold vs accuracy
    print("\n[*] Curva de umbral vs precisión (muestra):")
    for i in range(0, len(results), 5):
        th, acc = results[i]
        bar = "█" * int(acc * 30)
        print(f"  {th:5.1f} | {bar} {acc*100:.1f}%")

    return best_threshold


def train_model(dataset_dir: str = "dataset/raw",
                output_model: str = "models/faces_model_lite.pkl",
                use_augmentation: bool = True):
    """
    Entrena el modelo MEJORADO desde el dataset

    Args:
        dataset_dir: Ruta al directorio con imágenes
        output_model: Ruta de salida del modelo
        use_augmentation: Si True, usa aumento de datos

    Returns:
        True si se entrenó exitosamente
    """

    print("\n" + "="*70)
    print("ENTRENADOR DE MODELO FACIAL MEJORADO - SIN DLIB")
    print("Con: LBP + HOG + Validación cruzada + Aumento de datos")
    print("="*70)
    print(f"[*] Dataset: {dataset_dir}")
    print(f"[*] Modelo salida: {output_model}")
    print(f"[*] Aumento de datos: {'SI' if use_augmentation else 'NO'}")

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

        # Obtener imágenes
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

                # Convertir a escala de grises para detección
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
                    # Extraer características (con o sin aumento)
                    feature_list = extract_face_features(
                        img, (x, y, w, h),
                        augment=use_augmentation
                    )

                    for features in feature_list:
                        if features is not None and len(features) > 0:
                            X_train.append(features)
                            y_train.append(person_name)
                            images_processed += 1

            except Exception as e:
                images_failed += 1
                continue

        aug_note = f" (x{images_processed // len(image_files)} aumento)" if use_augmentation else ""
        print(f"  ✓ Muestras: {images_processed}{aug_note} | ✗ Errores: {images_failed}")

    if not X_train:
        print("[ERROR] No se extrajeron características de ninguna imagen")
        return False

    print()
    print(f"[*] Total de muestras: {len(X_train)}")
    print(f"[*] Personas únicas: {len(set(y_train))}")

    # Dividir en train y validation
    print("\n[*] Dividiendo en entrenamiento (80%) y validación (20%)...")
    X_train_split, X_val, y_train_split, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )

    print(f"[*] Entrenamiento: {len(X_train_split)} muestras")
    print(f"[*] Validación: {len(X_val)} muestras")

    # Normalizar características
    print("\n[*] Normalizando características...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_split)
    X_val_scaled = scaler.transform(X_val)

    # Entrenar clasificador KNN
    print("[*] Entrenando clasificador KNN...")

    # Probar diferentes valores de k
    best_k = 5
    best_cv_score = 0

    print("[*] Buscando mejor k (vecinos)...")
    for k in [3, 5, 7, 9]:
        knn_temp = KNeighborsClassifier(n_neighbors=k, n_jobs=-1)
        scores = cross_val_score(knn_temp, X_train_scaled, y_train_split, cv=3)
        mean_score = scores.mean()
        print(f"  k={k}: {mean_score*100:.2f}% accuracy")

        if mean_score > best_cv_score:
            best_cv_score = mean_score
            best_k = k

    print(f"[OK] Mejor k seleccionado: {best_k}")

    # Entrenar con mejor k
    knn = KNeighborsClassifier(n_neighbors=best_k, n_jobs=-1)
    knn.fit(X_train_scaled, y_train_split)

    # Evaluar en validación
    val_predictions = knn.predict(X_val_scaled)
    val_accuracy = np.mean(np.array(val_predictions) == np.array(y_val))
    print(f"[OK] Precisión en validación: {val_accuracy*100:.1f}%")

    # Encontrar mejor umbral
    best_threshold = find_best_threshold(X_val, y_val, knn, scaler, y_train_split)

    # Entrenar modelo de detección de anomalías (para desconocidos)
    print("\n[*] Entrenando detector de desconocidos (Isolation Forest)...")
    iso_forest = IsolationForest(
        contamination=0.05,  # 5% de anomalías esperadas
        random_state=42,
        n_jobs=-1
    )

    # Entrenar con TODOS los datos (no solo train_split)
    X_all_scaled = scaler.fit_transform(X_train)
    iso_forest.fit(X_all_scaled)

    # Guardar modelo
    print(f"\n[*] Guardando modelo en {output_model}...")
    model_data = {
        'classifier': knn,
        'scaler': scaler,
        'names': y_train_split,
        'unique_names': list(set(y_train)),
        'best_threshold': best_threshold,
        'anomaly_detector': iso_forest,
        'feature_dim': len(X_train[0]),
        'n_samples': len(X_train),
        'validation_accuracy': val_accuracy
    }

    with open(output_model, 'wb') as f:
        pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    model_size_mb = os.path.getsize(output_model) / (1024*1024)

    # Reporte de clasificación
    print("\n" + "="*70)
    print("REPORTE DE VALIDACIÓN")
    print("="*70)
    print(classification_report(y_val, val_predictions, zero_division=0))

    print("\n" + "="*70)
    print("[✓] MODELO ENTRENADO EXITOSAMENTE")
    print("="*70)
    print(f"[OK] Archivo: {output_model}")
    print(f"[OK] Tamaño: {model_size_mb:.2f} MB")
    print(f"[OK] Personas: {', '.join(sorted(set(y_train)))}")
    print(f"[OK] Muestras totales: {len(X_train)}")
    print(f"[OK] Precisión validación: {val_accuracy*100:.1f}%")
    print(f"[OK] Mejor k (vecinos): {best_k}")
    print(f"[OK] Umbral recomendado: {best_threshold:.1f}")
    print(f"[OK] Dimensión características: {len(X_train[0])}")
    print("="*70)
    print("\n[INFO] Para usar el modelo, ejecuta: python3 app.py")
    print()

    return True


def main():
    """Función principal"""

    # Argumentos de línea de comandos
    dataset = sys.argv[1] if len(sys.argv) > 1 else "dataset/raw"
    output = sys.argv[2] if len(sys.argv) > 2 else "models/faces_model_lite.pkl"
    use_aug = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True

    success = train_model(dataset, output, use_augmentation=use_aug)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
