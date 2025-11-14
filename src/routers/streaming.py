import cv2
import time
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse, JSONResponse
import numpy as np

router = APIRouter()

# ==================== CONFIGURACION ====================
class CameraConfig:
    def __init__(self):
        self.camera = None
        self.current_camera_id = 0
        self.detection_enabled = False
        self.recognition_enabled = False
        self.face_cascade = None
        self.total_frames = 0
        self.start_time = time.time()
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0
        self.recognized_names = []

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

    def load_haar_cascade(self):
        """Cargar clasificador Haar Cascade para detecciOn facial"""
        try:
            # Intentar cargar desde la instalaciOn de OpenCV
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            if self.face_cascade.empty():
                print("Error: No se pudo cargar Haar Cascade")
                return False
            return True
        except Exception as e:
            print(f"Error cargando Haar Cascade: {e}")
            return False

# Instancia global
camera_config = CameraConfig()

# ==================== FUNCIONES DE PROCESAMIENTO ====================
def detect_faces(frame):
    """Detectar rostros usando Haar Cascade"""
    if camera_config.face_cascade is None:
        return frame, 0

    # Convertir a escala de grises para mejor rendimiento
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detectar rostros con parametros optimizados para velocidad
    faces = camera_config.face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=4,
        minSize=(40, 40),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    # Dibujar rectOngulos alrededor de los rostros
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(
            frame,
            'Rostro detectado',
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    return frame, len(faces)

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

        # Aplicar detecciOn facial si estO habilitada
        if camera_config.detection_enabled:
            frame, faces_detected = detect_faces(frame)

        # Agregar informacion overlay
        frame = add_overlay_info(frame, camera_config.fps, faces_detected)

        # Codificar frame a JPEG con calidad optimizada para streaming
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])

        # Yield frame en formato multipart
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# ==================== RUTAS ====================

@router.get("/video_feed")
async def video_feed():
    """Stream de video en tiempo real"""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/status")
async def get_status():
    """Obtener estado del sistema"""
    uptime = int(time.time() - camera_config.start_time)

    return JSONResponse({
        "fps": round(camera_config.fps, 1),
        "total_frames": camera_config.total_frames,
        "uptime": uptime,
        "detection_enabled": camera_config.detection_enabled,
        "recognition_enabled": camera_config.recognition_enabled,
        "recognition_available": False,  # Haar Cascade no hace reconocimiento
        "model_loaded": False,
        "recognized_names": camera_config.recognized_names,
        "camera_id": camera_config.current_camera_id
    })

@router.post("/toggle_detection")
async def toggle_detection():
    """Activar/desactivar detecciOn facial"""
    camera_config.detection_enabled = not camera_config.detection_enabled

    # Cargar Haar Cascade si se activa por primera vez
    if camera_config.detection_enabled and camera_config.face_cascade is None:
        if not camera_config.load_haar_cascade():
            camera_config.detection_enabled = False
            return JSONResponse({
                "success": False,
                "message": "Error al cargar Haar Cascade",
                "detection_enabled": False
            })

    return JSONResponse({
        "success": True,
        "message": f"DetecciOn {'activada' if camera_config.detection_enabled else 'desactivada'}",
        "detection_enabled": camera_config.detection_enabled
    })

@router.post("/toggle_recognition")
async def toggle_recognition():
    """Activar/desactivar reconocimiento facial (no disponible con Haar Cascade)"""
    return JSONResponse({
        "success": False,
        "message": "Reconocimiento no disponible con Haar Cascade. Solo detecciOn.",
        "recognition_enabled": False
    }, status_code=400)

@router.get("/cameras")
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

@router.post("/set_camera/{camera_id}")
async def set_camera(camera_id: int):
    """Cambiar cOmara activa"""
    if camera_config.initialize_camera(camera_id):
        return JSONResponse({
            "success": True,
            "message": f"Cambiado a cOmara /dev/video{camera_id}",
            "camera_id": camera_id
        })
    else:
        return JSONResponse({
            "success": False,
            "message": f"No se pudo acceder a la cOmara /dev/video{camera_id}",
            "camera_id": camera_config.current_camera_id
        })

@router.get("/stats")
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
                <span class="stat-value">{camera_config.fps:.1f}</span>
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
                <span class="stat-value">Haar Cascade</span>
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
    camera_config.load_haar_cascade()

def shutdown():
    """Limpiar recursos al cerrar"""
    if camera_config.camera is not None:
        camera_config.camera.release()
