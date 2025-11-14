import os
import cv2
import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importar routers
from src.routers import streaming, arduino


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    import socket

    print("\n" + "="*60)
    print("🚀 Iniciando aplicación...")
    print("="*60)

    streaming.startup()
    print("📹 Cámara inicializada")

    # Obtener IP local
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "No disponible"

    print("\n" + "="*60)
    print("✅ Aplicación lista")
    print("="*60)
    print("\n📱 URLs de acceso:\n")
    print("   Desde este equipo:")
    print("   └─ http://localhost:8000")
    print("   └─ http://127.0.0.1:8000")
    print("\n   Desde otros equipos en la red:")
    print(f"   └─ http://{local_ip}:8000")
    print("\n💡 Comparte la URL con otros dispositivos en la misma red")
    print("="*60 + "\n")

    yield

    # Shutdown
    print("\n🛑 Cerrando aplicación...")
    streaming.shutdown()
    arduino.shutdown()
    print("✅ Recursos liberados\n")


app = FastAPI(
    title="Raspberry Pi Camera Stream",
    description="Sistema de streaming con detección facial usando Haar Cascade",
    version="1.0.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="src/templates")

# Mount static files for CSS, JS, etc
app.mount("/templates", StaticFiles(directory="src/templates"), name="templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(streaming.router)
app.include_router(arduino.router)


@app.get("/", response_class=HTMLResponse)
async def show_index(request: Request):
    """Página principal"""
    return templates.TemplateResponse("index.html", {"request": request})


