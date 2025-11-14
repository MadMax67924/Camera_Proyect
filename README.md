# 📹 Raspberry Pi Camera Stream

Sistema de streaming de cámara en tiempo real con detección facial usando Haar Cascade.

## 🚀 Inicio Rápido

```bash
# Ejecutar script de inicio
./run.sh
```

Accede a: http://localhost:5000

## 📋 Requisitos

- Python 3.10+
- Cámara USB o integrada
- OpenCV con Haar Cascade

## 🛠️ Instalación Manual

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

## ✨ Características

- Streaming en tiempo real
- Detección facial con Haar Cascade
- Interfaz web moderna
- Control de múltiples cámaras
- Estadísticas en tiempo real
- Preparado para control Arduino (BLE)
