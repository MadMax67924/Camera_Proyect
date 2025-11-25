# Manual del Sistema (Cámara + Reconocimiento + Arduino BLE)

## 1. Estructura general
- Backend: FastAPI en `src/routers/streaming.py` (cámara, detección/reconocimiento) y `src/routers/arduino.py` (BLE).
- Frontend: `src/templates/index.html` + `src/templates/javascript/index.js`.
- Scripts: `src/scripts/build_embeddings.py` (genera embeddings con SFace).
- Modelos: `src/scripts/Yunet+SFace/face_detection_yunet_2023mar.onnx` (YuNet) y `face_recognition_sface_2021dec.onnx` (SFace).
- Persistencia:
  - Embeddings en MySQL (`embedding`/`person`).
  - Lista de permitidos en `src/allowed_users.json`.
  - Config DB en `.env`.

## 2. Configuración previa
- Instalación: `pip install -r requirements.txt` (incluye OpenCV contrib, Bleak, MySQL connector).
- `.env` esperado:
  ```
  DB_HOST=localhost
  DB_PORT=3306
  DB_USER=usuario
  DB_PASSWORD=clave
  DB_NAME=embeddingsOpenCV
  ```
- Base de datos (ya creada): tablas `person(id,nombre)` y `embedding(id,person_id,vector,image_path,created_at)`.
- Dataset: imágenes por persona en subcarpetas bajo `dataset/raw/PersonaX/...`.

## 3. Generar embeddings (SFace)
- Script: `python src/scripts/build_embeddings.py --dataset dataset/raw --score-threshold 0.9 --min-side-upscale 120 --upscale-factor 2.0`
  - Ajustar `--score-threshold` (sensibilidad YuNet), `--min-side-upscale` y `--upscale-factor` para imágenes pequeñas.
  - Inserta en MySQL (evita duplicados por `image_path`).

## 4. Endpoints principales (cámara)
- `GET /video_feed` – stream MJPEG.
- `GET /status` – estado general (FPS, frames, flags de detección/reconocimiento, cámara activa, lista de permitidos).
- `POST /toggle_detection` – activa/desactiva detección (YuNet).
- `POST /toggle_recognition` – activa/desactiva reconocimiento (carga YuNet, SFace, embeddings; requiere BD operativa).
- `GET /cameras` – lista cámaras disponibles.
- `POST /set_camera/{id}` – cambia cámara activa.
- `GET /stats` – página simple con estadísticas.
- Lista de permitidos (auto-abrir con reconocimiento):
  - `GET /allowed`
  - `POST /allowed` body `{ "name": "Nombre" }`
  - `DELETE /allowed/{name}`

## 5. Integración BLE (Arduino)
- Router: `src/routers/arduino.py`, prefijo `/ble`.
- Endpoints:
  - `POST /ble/connect` – conecta al NanoDoorBLE (service/char UUID del sketch).
  - `POST /ble/disconnect` – desconecta.
  - `POST /ble/toggle` – habilita/inhabilita control (permite autoenvíos).
  - `POST /ble/open_door` – envía `A` (UNLOCK).
  - `POST /ble/close_door` – envía `C` (LOCK).
- Autoenvío desde reconocimiento (cuando está activado y BLE habilitado):
  - Regla de negocio: **solo abre cuando detecta una cara permitida**.
    - Si hay un rostro reconocido y el nombre está en `allowed_users.json` → manda `A`.
    - Si no hay coincidencia permitida o no se detecta rostro → manda `C`.
  - Debounce de 2s (`ble_interval` en `CameraConfig`).

## 6. Flujo típico de uso (UI)
1. Conectar BLE (`Conectar Arduino`) y activar control (`Activar Control`).
2. Activar detección o directamente reconocimiento (`Activar Reconocimiento` carga modelos/embeddings).
3. Añadir nombres permitidos en la sección “Personas permitidas (auto-A)” (CRUD llama a `/allowed`).
4. Ver reconocidos en tiempo real; el sistema autoenvía A/C según permitidos.
5. Botones manuales de abrir/cerrar siguen funcionando.

## 7. Notas y ajustes
- Umbral de similitud SFace: `recognition_threshold` en `CameraConfig` (0.5 por defecto). Súbelo para ser más estricto.
- Si el botón de reconocimiento se deshabilita, revisa logs del backend (carga de modelos/BD) y asegúrate de que hay embeddings en la BD.
- `allowed_users.json` se persiste en `src/` y se carga en `startup()`.
- Si cambias dataset/embeddings, reejecuta `build_embeddings.py`.
