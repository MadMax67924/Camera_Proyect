# 🎥 Sistema de Reconocimiento Facial - Guía Rápida

**Sistema completo**: Entrenamiento en laptop → Ejecución en Raspberry Pi

## ⚡ Instalación (Laptop)

```bash
# 1. Instalación inicial (solo una vez)
python3 setup_initial.py

# 2. Usar interfaz interactiva (recomendado)
python3 master.py
```

## 🎯 Workflow Completo

### Fase 1: Capturar Imágenes (Laptop)

```bash
# Capturar rostros para una persona
python3 scripts/capture_faces.py "Tu Nombre"

# Instrucciones en pantalla:
# - Se abrirá cámara
# - Presiona ESPACIO para capturar
# - Presiona 'q' para terminar

# Repetir para cada persona
python3 scripts/capture_faces.py "Otra Persona"
```

**Resultado**: Imágenes guardadas en `dataset/raw/Tu Nombre/`

### Fase 2: Entrenar Modelo (Laptop)

```bash
# Opción A: Entrenar modelo básico
python3 scripts/train_model_new.py

# Opción B: Entrenar detectando desconocidos (más preciso)
python3 scripts/train_model_with_unknowns.py
```

**Resultado**: Modelo guardado en `models/faces_model_lite.pkl`

### Fase 3: Usar el Sistema (Laptop o Raspberry)

```bash
# Iniciar servidor web
python3 app.py

# Accesible en: http://localhost:5000
# (o http://<IP_RASPBERRY>:5000 si está en Raspberry)
```

## 📋 Estructura del Proyecto

```
.
├── app.py                          # Servidor web principal
├── master.py                       # Interfaz interactiva
├── test_system.py                  # Verificación del sistema
├── requirements.txt                # Dependencias Python
│
├── scripts/
│   ├── capture_faces.py            # Capturar rostros
│   ├── train_model_new.py          # Entrenar modelo
│   └── train_model_with_unknowns.py # Entrenar avanzado
│
├── core/
│   ├── face_recognition_lite.py    # Motor de reconocimiento
│   ├── ble_door_integration.py     # Control BLE de puerta
│   └── arduino_control.py          # Control Arduino
│
├── dataset/
│   ├── raw/                        # Imágenes de entrenamiento
│   ├── unknown/                    # Imágenes de desconocidos
│   └── processed/                  # Imágenes procesadas
│
└── models/
    └── faces_model_lite.pkl        # Modelo entrenado
```

## 🔧 Verificación

```bash
# Verificar que todo funciona
python3 test_system.py

# Diagnóstico completo
python3 diagnose_system.py
```

## 🚀 Transferir a Raspberry Pi

```bash
# En laptop: copiar archivos
scp -r models/ pi@192.168.1.100:/home/pi/camaraproject/

# En Raspberry Pi:
cd camaraproject
python3 app.py
```

## 📱 Interfaz Web

- **Streaming en vivo**: 30 FPS en tiempo real
- **Detección facial**: Detecta rostros automáticamente  
- **Reconocimiento**: Identifica personas entrenadas
- **Control BLE**: Abre puerta por reconocimiento
- **Control Arduino**: Controla relés y actuadores

## ⚙️ Configuración

### Archivo: `config/authorized_users.json`

```json
{
  "authorized_users": ["Lucho", "Maxi", "Nacho"],
  "door_open_duration": 3,
  "cooldown_time": 5
}
```

## 🐛 Solución de Problemas

### "No se detectan rostros"
- Aumentar iluminación
- Acercarse a la cámara
- Usar `diagnose_camera.py`

### "Reconocimiento muy lento"
- Desactivar detección si solo necesitas streaming
- Reducir resolución en app.py
- Usar versión lite del modelo

### "Modelo pequeño/impreciso"
- Capturar más imágenes (20+ por persona)
- Usar diferentes ángulos y iluminación
- Entrenar con desconocidos: `train_model_with_unknowns.py`

## 📊 Rendimiento

| Operación | FPS | CPU | RAM |
|-----------|-----|-----|-----|
| Streaming solo | 30-60 | 20% | 100MB |
| + Detección | 20-30 | 60% | 150MB |
| + Reconocimiento | 10-15 | 80% | 200MB |

*Valores en Raspberry Pi 3*

## 📚 Comandos Útiles

```bash
# Limpiar pycache
find . -type d -name __pycache__ -exec rm -r {} +

# Ver logs
tail -f logs/*.log

# Entrenar con argumentos personalizados
python3 scripts/train_model_new.py --dataset dataset/raw --output models/custom.pkl

# Diagnosticar cámara
python3 diagnose_camera.py
```

## 🔐 Seguridad

- Modelos almacenados localmente (sin nubes)
- Autenticación por reconocimiento facial
- Control de acceso por usuario
- Log completo de accesos

## 📝 Notas Importantes

1. **Entrenamiento**: Realiza en laptop (más rápido)
2. **Ejecución**: Funciona en laptop o Raspberry Pi
3. **Modelos**: Se pueden copiar entre dispositivos
4. **Dataset**: No es necesario después del entrenamiento
5. **BLE/Arduino**: Opcionales, funcionan sin ellos

## 🤝 Soporte

Para problemas específicos:
- `test_system.py` - Verificación integral
- `diagnose_system.py` - Diagnóstico detallado
- `INTEGRACION_BLE.md` - Control BLE
- `QUICKSTART_BLE.md` - Inicio rápido BLE

---

**¡Creemos que esto funcionará! 🚀**

Actualizado: 12 de noviembre de 2025
