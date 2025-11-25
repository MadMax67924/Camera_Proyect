import argparse
import io
import os
from pathlib import Path

import cv2
import mysql.connector
import numpy as np
from dotenv import load_dotenv


def load_models(detector_path: Path, recognizer_path: Path, input_size, score_threshold: float):
    """Cargar YuNet (deteccion) y SFace (embedding)."""
    detector = cv2.FaceDetectorYN.create(
        model=detector_path.as_posix(),
        config="",
        input_size=input_size,
        score_threshold=score_threshold,
        nms_threshold=0.3,
        top_k=5000,
    )
    recognizer = cv2.FaceRecognizerSF.create(
        model=recognizer_path.as_posix(),
        config="",
    )
    return detector, recognizer


def connect_db():
    """Conectar a MySQL usando variables de entorno."""
    load_dotenv()
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "embeddingsOpenCV"),
        autocommit=True,
    )
    return conn


def get_or_create_person(cur, name: str) -> int:
    cur.execute("SELECT id FROM person WHERE nombre=%s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO person (nombre) VALUES (%s)", (name,))
    return cur.lastrowid


def embedding_exists(cur, image_path: str) -> bool:
    cur.execute("SELECT id FROM embedding WHERE image_path=%s LIMIT 1", (image_path,))
    return cur.fetchone() is not None


def insert_embedding(cur, person_id: int, embedding: np.ndarray, image_path: str):
    buf = io.BytesIO()
    np.save(buf, embedding.astype(np.float32))
    payload = buf.getvalue()
    cur.execute(
        "INSERT INTO embedding (person_id, vector, image_path) VALUES (%s, %s, %s)",
        (person_id, payload, image_path),
    )


def extract_embedding(img_path: Path, detector, recognizer, min_side: int = 0, upscale_factor: float = 1.0) -> np.ndarray | None:
    """Detectar rostro principal y devolver embedding SFace."""
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"[WARN] No se pudo leer {img_path}")
        return None

    # Subir resolución si la imagen es muy pequeña
    if min(img.shape[:2]) < min_side:
        img = cv2.resize(img, None, fx=upscale_factor, fy=upscale_factor, interpolation=cv2.INTER_CUBIC)

    h, w = img.shape[:2]
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    if faces is None or len(faces) == 0:
        print(f"[WARN] Sin rostros en {img_path}")
        return None

    # Tomar el rostro con mayor score
    faces = sorted(faces, key=lambda f: f[4], reverse=True)
    best_face = faces[0]

    aligned = recognizer.alignCrop(img, best_face)
    feat = recognizer.feature(aligned)
    return feat


def process_dataset(dataset_dir: Path, conn, score_threshold: float, min_side: int, upscale_factor: float):
    base_dir = Path(__file__).resolve().parent
    detector_path = base_dir / "Yunet+SFace" / "face_detection_yunet_2023mar.onnx"
    recognizer_path = base_dir / "Yunet+SFace" / "face_recognition_sface_2021dec.onnx"

    detector, recognizer = load_models(
        detector_path,
        recognizer_path,
        input_size=(320, 320),
        score_threshold=score_threshold,
    )

    cur = conn.cursor()
    total = 0
    stored = 0
    skipped = 0
    duplicates = 0

    for person_dir in dataset_dir.iterdir():
        if not person_dir.is_dir():
            continue
        person_name = person_dir.name
        person_id = get_or_create_person(cur, person_name)

        for img_path in person_dir.glob("**/*"):
            if img_path.is_dir():
                continue
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue

            total += 1

            # Evitar recalcular/insertar si ya existe
            if embedding_exists(cur, str(img_path)):
                duplicates += 1
                continue

            embedding = extract_embedding(
                img_path,
                detector,
                recognizer,
                min_side=min_side,
                upscale_factor=upscale_factor,
            )
            if embedding is None:
                skipped += 1
                continue

            insert_embedding(cur, person_id, embedding, str(img_path))
            stored += 1

    cur.close()
    print(
        f"Procesadas {total} imagenes. Embeddings almacenados: {stored}. "
        f"Saltadas (sin rostro): {skipped}. Duplicadas (ya estaban): {duplicates}."
    )


def main():
    parser = argparse.ArgumentParser(description="Generar embeddings con SFace y guardarlos en MySQL.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "dataset" / "raw",
        help="Ruta al directorio con subcarpetas por persona.",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.6,
        help="Umbral de confianza de YuNet (0-1). Baja el valor si no detecta rostros (ej. 0.5 o 0.3).",
    )
    parser.add_argument(
        "--min-side-upscale",
        type=int,
        default=120,
        help="Si el lado menor de la imagen es menor a este valor, se reescala hacia arriba.",
    )
    parser.add_argument(
        "--upscale-factor",
        type=float,
        default=2.0,
        help="Factor de reescalado para imagenes pequeñas.",
    )
    args = parser.parse_args()

    conn = connect_db()
    try:
        process_dataset(
            args.dataset,
            conn,
            score_threshold=args.score_threshold,
            min_side=args.min_side_upscale,
            upscale_factor=args.upscale_factor,
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
