# Dataset de Entrenamiento

Este directorio contiene las fotos para entrenar el modelo de reconocimiento facial.

## Estructura

Cada subdirectorio representa una persona:

```
dataset/raw/
├── juan/
│   ├── juan_001_20250110_143022.jpg
│   ├── juan_002_20250110_143025.jpg
│   └── ...
├── maria/
│   ├── maria_001_20250110_143122.jpg
│   └── ...
└── pedro/
    └── ...
```

## Cómo Agregar Personas

### Opción 1: Usar script de captura (RECOMENDADO)

```bash
python3 scripts/capture_faces.py
```

### Opción 2: Manualmente

1. Crea un subdirectorio con el nombre de la persona (sin espacios):
   ```bash
   mkdir dataset/raw/nombre_persona
   ```

2. Coloca 10-20 fotos de la persona en ese directorio
   - Formato: JPG, JPEG o PNG
   - Requisitos:
     * Un solo rostro visible
     * Buena iluminación
     * Diferentes ángulos
     * Resolución mínima: 200x200 px

3. Entrena el modelo:
   ```bash
   python3 scripts/train_model.py
   ```

## Mejores Prácticas

- **Cantidad**: 15-20 fotos por persona
- **Variedad**: Diferentes ángulos y expresiones
- **Iluminación**: Buena luz, evitar sombras fuertes
- **Calidad**: Rostro nítido y bien enfocado
- **Tamaño**: Rostro ocupa al menos 30% de la imagen

## Eliminar Personas

Para eliminar una persona del sistema:

1. Elimina su carpeta:
   ```bash
   rm -rf dataset/raw/nombre_persona
   ```

2. Re-entrena el modelo:
   ```bash
   python3 scripts/train_model.py
   ```

3. Reinicia la aplicación:
   ```bash
   python3 app.py
   ```
