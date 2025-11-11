# Modelos Entrenados

Este directorio contiene los modelos de reconocimiento facial entrenados.

## Archivos

- `faces_model.pkl`: Modelo principal con encodings faciales de todas las personas registradas

## Estructura del Modelo

El archivo `.pkl` contiene:

```python
{
    'encodings': [
        array([...]),  # Encoding de 128 dimensiones
        ...
    ],
    'names': [
        'persona1',
        'persona2',
        ...
    ]
}
```

## Generar Modelo

```bash
# Asegúrate de tener fotos en dataset/raw/
python3 scripts/train_model.py
```

## Información del Modelo

Para ver información sobre el modelo actual:

```python
import pickle

with open('models/faces_model.pkl', 'rb') as f:
    data = pickle.load(f)
    print(f"Personas: {set(data['names'])}")
    print(f"Total de muestras: {len(data['encodings'])}")

    # Muestras por persona
    from collections import Counter
    counts = Counter(data['names'])
    for name, count in counts.items():
        print(f"  {name}: {count} muestras")
```

## Backup

Es recomendable hacer backup del modelo:

```bash
cp models/faces_model.pkl models/faces_model_backup_$(date +%Y%m%d).pkl
```

## Actualizar Modelo

Si agregas nuevas personas o más fotos:

1. Captura fotos nuevas
2. Re-entrena: `python3 scripts/train_model.py`
3. El modelo se sobrescribirá automáticamente
4. Reinicia la aplicación: `python3 app.py`
