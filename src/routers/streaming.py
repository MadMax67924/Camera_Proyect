import cv2
import time
import io
import os
import json
from pathlib import Path
from typing import List, Tuple, Optional, Set
import asyncio
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse, JSONResponse
import numpy as np
import mysql.connector
from dotenv import load_dotenv
from src.routers.arduino import arduino_config
from pydantic import BaseModel, Field

streaming_router = APIRouter()


class AllowedUser(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre exacto a autorizar")

# ==================== CONFIGURACION ====================
class CameraConfig:
    def __init__(self):
        self.camera = None
        self.current_camera_id = 0
        self.detection_enabled = False
        self.recognition_enabled = False
        self.face_detector = None  # YuNet
        self.face_recognizer = None  # SFace
        self.recognition_available = False
        self.total_frames = 0
        self.start_time = time.time()
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0
        self.recognized_names = []
        self.model_path = (
            Path(__file__).resolve().parent.parent
            / "scripts"
            / "Yunet+SFace"
            / "face_detection_yunet_2023mar.onnx"
        )
        self.sface_path = (
            Path(__file__).resolve().parent.parent
            / "scripts"
            / "Yunet+SFace"
            / "face_recognition_sface_2021dec.onnx"
        )
        self.embeddings: List[Tuple[str, np.ndarray]] = []
        self.recognition_threshold = 0.5
        self.last_ble_command: Optional[str] = None
        self.last_ble_time = 0.0
        self.ble_interval = 2.0  # segundos entre envios automaticos
        self.allowed_file = Path(__file__).resolve().parent.parent / "allowed_users.json"
        self.allowed_users: Set[str] = set()

    def initialize_camera(self, camera_id=0):
        """Inicializar camara"""
        if self.camera is not None:
            self.camera.release()

        self.camera = cv2.VideoCapture(camera_id)
        self.current_camera_id = camera_id

        # Configurar resolucion para mejor rendimiento en Raspberry Pi
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        return self.camera.isOpened()

    def load_yunet(self, input_size=(480, 360)):
        """Cargar detector YuNet."""
        if self.face_detector is not None:
            return True

        if not self.model_path.exists():
            print(f"Error: modelo YuNet no encontrado en {self.model_path}")
            return False

        try:
            self.face_detector = cv2.FaceDetectorYN.create(
                model=self.model_path.as_posix(),
                config="",
                input_size=input_size,
                score_threshold=0.9,
                nms_threshold=0.3,
                top_k=5000
            )
            return self.face_detector is not None
        except Exception as e:
            print(f"Error cargando YuNet: {e}")
            self.face_detector = None
            return False

    def load_sface(self):
        """Cargar modelo SFace para reconocimiento."""
        if self.face_recognizer is not None:
            return True

        if not self.sface_path.exists():
            print(f"Error: modelo SFace no encontrado en {self.sface_path}")
            return False

        try:
            self.face_recognizer = cv2.FaceRecognizerSF.create(
                model=self.sface_path.as_posix(),
                config="",
            )
            return True
        except Exception as e:
            print(f"Error cargando SFace: {e}")
            self.face_recognizer = None
            return False

    def load_embeddings(self):
        """Cargar embeddings desde MySQL."""
        load_dotenv()
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "embeddingsOpenCV"),
            )
        except Exception as exc:
            print(f"Error conectando a MySQL: {exc}")
            self.recognition_available = False
            self.embeddings = []
            return False, 0, str(exc)

        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT p.nombre, e.vector
                FROM embedding e
                JOIN person p ON e.person_id = p.id
                """
            )
            embeddings: List[Tuple[str, np.ndarray]] = []
            for name, blob in cur.fetchall():
                arr = np.load(io.BytesIO(blob), allow_pickle=False).astype(np.float32).reshape(-1)
                norm = np.linalg.norm(arr)
                if norm == 0:
                    continue
                embeddings.append((name, arr / norm))
            cur.close()
            conn.close()

            self.embeddings = embeddings
            self.recognition_available = self.face_recognizer is not None and len(embeddings) > 0
            print(f"Embeddings cargados: {len(self.embeddings)}")
            return True, len(embeddings), None
        except Exception as exc:
            print(f"Error cargando embeddings: {exc}")
            self.embeddings = []
            self.recognition_available = False
            return False, 0, str(exc)

    def load_allowed_users(self):
        """Cargar lista de permitidos desde JSON."""
        try:
            if self.allowed_file.exists():
                data = json.loads(self.allowed_file.read_text(encoding="utf-8") or "[]")
                self.allowed_users = {str(x).strip() for x in data if str(x).strip()}
            else:
                self.allowed_users = set()
        except Exception as exc:
            print(f"Error cargando allowed_users: {exc}")
            self.allowed_users = set()

    def save_allowed_users(self):
        """Persistir lista de permitidos a JSON."""
        try:
            self.allowed_file.write_text(json.dumps(sorted(self.allowed_users), ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as exc:
            print(f"Error guardando allowed_users: {exc}")
            return False

# Instancia global
camera_config = CameraConfig()

# ==================== FUNCIONES DE PROCESAMIENTO ====================
def match_embedding(feat: np.ndarray) -> Tuple[Optional[str], float]:
    """Encontrar el nombre con mayor similitud coseno."""
    if not camera_config.embeddings:
        return None, -1.0
    feat_flat = feat.astype(np.float32).reshape(-1)
    norm = np.linalg.norm(feat_flat) + 1e-8
    feat_norm = feat_flat / norm
    best_name = None
    best_score = -1.0
    for name, emb in camera_config.embeddings:
        score = float(np.dot(feat_norm, emb))
        if score > best_score:
            best_score = score
            best_name = name
    if best_score >= camera_config.recognition_threshold:
        return best_name, best_score
    return None, best_score


def detect_and_recognize(frame):
    """Detectar rostros y opcionalmente reconocerlos."""
    # Reset de reconocidos en cada ciclo
    camera_config.recognized_names = []
    if camera_config.face_detector is None:
        return frame, 0

    h, w = frame.shape[:2]
    try:
        camera_config.face_detector.setInputSize((w, h))
        _, faces = camera_config.face_detector.detect(frame)
    except Exception:
        return frame, 0

    if faces is None:
        camera_config.recognized_names = []
        return frame, 0

    faces_detected = 0
    recognized = []

    for face in faces:
        x, y, fw, fh = face[:4].astype(int)
        score = float(face[4])
        label = f"Face {score:.2f}"

        if camera_config.recognition_enabled and camera_config.face_recognizer is not None and camera_config.embeddings:
            try:
                aligned = camera_config.face_recognizer.alignCrop(frame, face)
                feat = camera_config.face_recognizer.feature(aligned)
                name, sim = match_embedding(feat)
                if name:
                    label = f"{name} ({sim:.2f})"
                    recognized.append(name)
                else:
                    label = f"Desconocido ({sim:.2f})"
            except Exception as exc:
                print(f"Error en reconocimiento SFace: {exc}")

        cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
        cv2.putText(
            frame,
            label,
            (x, max(0, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )
        faces_detected += 1

    # Evitar duplicados
    camera_config.recognized_names = list(dict.fromkeys(recognized))
    return frame, faces_detected


def send_ble_command(command: str):
    """Enviar comando BLE de forma no bloqueante si procede."""
    # Requiere que el control este habilitado desde el UI (/ble/toggle)
    if not arduino_config.connected or not arduino_config.enabled:
        return

    now = time.time()
    if camera_config.last_ble_command == command and (now - camera_config.last_ble_time) < camera_config.ble_interval:
        return

    camera_config.last_ble_command = command
    camera_config.last_ble_time = now

    async def _send():
        try:
            await arduino_config.send_command("UNLOCK" if command == "A" else "LOCK")
        except Exception as exc:
            print(f"Error enviando comando BLE {command}: {exc}")

    # Ejecutar en el loop si existe, de lo contrario lanzar uno simple
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_send())
        else:
            loop.run_until_complete(_send())
    except RuntimeError:
        asyncio.run(_send())

def add_overlay_info(frame, fps, faces_detected=0):
    """Agregar informacion sobre el frame de manera eficiente"""
    # Usar rectangulo simple sin transparencia para mejor rendimiento
    cv2.rectangle(frame, (5, 5), (200, 70), (0, 0, 0), -1)

    # Informacion minima para reducir overhead
    cv2.putText(frame, f'FPS: {fps:.0f}', (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    if camera_config.detection_enabled:
        cv2.putText(frame, f'Rostros: {faces_detected}', (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    return frame


def generate_frames():
    """Generador de frames para streaming"""
    while True:
        if camera_config.camera is None or not camera_config.camera.isOpened():
            # Intentar reinicializar la cOmara
            if not camera_config.initialize_camera(camera_config.current_camera_id):
                # Si falla, generar frame de error
                error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    error_frame,
                    'Error: Camara no disponible',
                    (100, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )
                _, buffer = cv2.imencode('.jpg', error_frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(1)
                continue

        success, frame = camera_config.camera.read()

        if not success:
            continue

        # Actualizar contadores
        camera_config.total_frames += 1
        camera_config.frame_count += 1

        # Calcular FPS
        current_time = time.time()
        elapsed = current_time - camera_config.last_fps_time
        if elapsed > 1.0:
            camera_config.fps = camera_config.frame_count / elapsed
            camera_config.frame_count = 0
            camera_config.last_fps_time = current_time

        faces_detected = 0

        # Aplicar deteccion/reconocimiento si estO habilitado
        if camera_config.detection_enabled or camera_config.recognition_enabled:
            try:
                frame, faces_detected = detect_and_recognize(frame)
            except Exception as exc:
                # Fallback si algo falla en el detector/reconocedor
                print(f"Error en detect_and_recognize: {exc}")
                faces_detected = 0
                camera_config.recognized_names = []
        else:
            camera_config.recognized_names = []

        # Enviar comando BLE asincrono segun reconocimiento
        if camera_config.recognition_enabled:
            # Abrir solo si algun reconocido esta en la lista de permitidos
            allowed_match = any(name in camera_config.allowed_users for name in camera_config.recognized_names)
            if allowed_match:
                send_ble_command("A")
            else:
                send_ble_command("C")

        # Agregar informacion overlay
        frame = add_overlay_info(frame, camera_config.fps, faces_detected)

        # Codificar frame a JPEG con calidad optimizada para streaming
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])

        # Yield frame en formato multipart
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# ==================== RUTAS ====================


@streaming_router.get("/video_feed")
async def video_feed():
    """Stream de video en tiempo real"""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@streaming_router.get("/status")
async def get_status():
    """Obtener estado del sistema"""
    uptime = int(time.time() - camera_config.start_time)

    return JSONResponse({
        "fps": round(camera_config.fps, 1),
        "total_frames": camera_config.total_frames,
        "uptime": uptime,
        "detection_enabled": camera_config.detection_enabled,
        "recognition_enabled": camera_config.recognition_enabled,
        "recognition_available": camera_config.recognition_available,
        "model_loaded": camera_config.recognition_available,
        "recognized_names": camera_config.recognized_names,
        "camera_id": camera_config.current_camera_id,
        "allowed_users": sorted(camera_config.allowed_users)
    })


@streaming_router.post("/toggle_detection")
async def toggle_detection():
    """Activar/desactivar detecciOn facial"""
    camera_config.detection_enabled = not camera_config.detection_enabled

    # Cargar YuNet si se activa por primera vez
    if camera_config.detection_enabled and camera_config.face_detector is None:
        if not camera_config.load_yunet():
            camera_config.detection_enabled = False
            return JSONResponse({
                "success": False,
                "message": "Error al cargar YuNet",
                "detection_enabled": False
            })

    return JSONResponse({
        "success": True,
        "message": f"DetecciOn {'activada' if camera_config.detection_enabled else 'desactivada'}",
        "detection_enabled": camera_config.detection_enabled
    })


@streaming_router.post("/toggle_recognition")
async def toggle_recognition():
    """Activar/desactivar reconocimiento facial (SFace)."""
    # Asegurar carga de modelos y embeddings
    if camera_config.face_detector is None:
        if not camera_config.load_yunet():
            return JSONResponse({
                "success": False,
                "message": "No se pudo cargar YuNet",
                "recognition_enabled": False
            }, status_code=500)

    if camera_config.face_recognizer is None:
        if not camera_config.load_sface():
            return JSONResponse({
                "success": False,
                "message": "No se pudo cargar SFace",
                "recognition_enabled": False
            }, status_code=500)

    if not camera_config.recognition_available:
        ok, count, err = camera_config.load_embeddings()
        if not ok:
            return JSONResponse({
                "success": False,
                "message": f"No hay embeddings cargados o conexion a BD fallida: {err}",
                "recognition_enabled": False
            }, status_code=400)
        if count == 0:
            return JSONResponse({
                "success": False,
                "message": "No hay embeddings en la base de datos",
                "recognition_enabled": False
            }, status_code=400)

    if not camera_config.recognition_available:
        return JSONResponse({
            "success": False,
            "message": "No hay embeddings cargados o conexion a BD fallida",
            "recognition_enabled": False
        }, status_code=400)

    # Reconocimiento depende de deteccion
    camera_config.recognition_enabled = not camera_config.recognition_enabled
    if camera_config.recognition_enabled:
        camera_config.detection_enabled = True

    return JSONResponse({
        "success": True,
        "message": f"Reconocimiento {'activado' if camera_config.recognition_enabled else 'desactivado'}",
        "recognition_enabled": camera_config.recognition_enabled,
        "detection_enabled": camera_config.detection_enabled
    })


@streaming_router.get("/cameras")
async def list_cameras():
    """Listar cOmaras disponibles"""
    available_cameras = []

    # Probar las primeras 5 cOmaras
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()

    return JSONResponse({
        "cameras": available_cameras,
        "current": camera_config.current_camera_id
    })


@streaming_router.post("/set_camera/{camera_id}")
async def set_camera(camera_id: int):
    """Cambiar cámara activa"""
    if camera_config.initialize_camera(camera_id):
        return JSONResponse({
            "success": True,
            "message": f"Cambiado a cámara /dev/video{camera_id}",
            "camera_id": camera_id
        })
    else:
        return JSONResponse({
            "success": False,
            "message": f"No se pudo acceder a la cámara /dev/video{camera_id}",
            "camera_id": camera_config.current_camera_id
        })


@streaming_router.get("/stats")
async def stats_page():
    """POgina de estadOsticas detalladas"""
    uptime = int(time.time() - camera_config.start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60

    stats_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EstadOsticas - Camera Stream</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="5">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
            }}
            .stats-container {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 30px;
                max-width: 600px;
                margin: 0 auto;
            }}
            h1 {{ text-align: center; }}
            .stat {{
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
            }}
            .stat-label {{ font-weight: bold; }}
            .stat-value {{ color: #90EE90; }}
        </style>
    </head>
    <body>
        <div class="stats-container">
            <h1>=O EstadOsticas del Sistema</h1>
            <div class="stat">
                <span class="stat-label">FPS:</span>
                <span class="stat-value">{camera_config.fps:.2f}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Frames Totales:</span>
                <span class="stat-value">{camera_config.total_frames}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Tiempo Activo:</span>
                <span class="stat-value">{hours:02d}:{minutes:02d}:{seconds:02d}</span>
            </div>
            <div class="stat">
                <span class="stat-label">COmara Activa:</span>
                <span class="stat-value">/dev/video{camera_config.current_camera_id}</span>
            </div>
            <div class="stat">
                <span class="stat-label">DetecciOn Facial:</span>
                <span class="stat-value">{"ACTIVADA" if camera_config.detection_enabled else "DESACTIVADA"}</span>
            </div>
            <div class="stat">
                <span class="stat-label">MOtodo:</span>
                <span class="stat-value">YuNet + SFace</span>
            </div>
        </div>
    </body>
    </html>
    """

    return Response(content=stats_html, media_type="text/html")


# ==================== INICIALIZACION ====================
def startup():
    """Inicializar al arranque"""
    camera_config.initialize_camera(0)
    # Cargar modelos al inicio para evitar latencia en el primer uso
    camera_config.load_yunet((480, 360))
    camera_config.load_sface()
    camera_config.load_embeddings()
    camera_config.load_allowed_users()


def shutdown():
    """Limpiar recursos al cerrar"""
    if camera_config.camera is not None:
        camera_config.camera.release()


# ==================== ALLOWED USERS CRUD ====================
@streaming_router.get("/allowed")
async def list_allowed():
    """Listar nombres permitidos para autoapertura."""
    return JSONResponse({"allowed": sorted(camera_config.allowed_users)})


@streaming_router.post("/allowed")
async def add_allowed(user: AllowedUser):
    """Agregar un nombre permitido."""
    name = user.name.strip()
    if not name:
        return JSONResponse({"success": False, "message": "Nombre vacio"}, status_code=400)
    camera_config.allowed_users.add(name)
    camera_config.save_allowed_users()
    return JSONResponse({"success": True, "allowed": sorted(camera_config.allowed_users)})


@streaming_router.delete("/allowed/{name}")
async def delete_allowed(name: str):
    """Eliminar un nombre permitido."""
    cleaned = name.strip()
    if cleaned in camera_config.allowed_users:
        camera_config.allowed_users.remove(cleaned)
        camera_config.save_allowed_users()
        return JSONResponse({"success": True, "allowed": sorted(camera_config.allowed_users)})
    return JSONResponse({"success": False, "message": "Nombre no encontrado"}, status_code=404)
