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
    print("🚀 Iniciando aplicación...")
    streaming.startup()
    print("📹 Cámara inicializada")
    print("✅ Aplicación lista")

    yield

    # Shutdown
    print("🛑 Cerrando aplicación...")
    streaming.shutdown()
    arduino.shutdown()
    print("✅ Recursos liberados")


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


