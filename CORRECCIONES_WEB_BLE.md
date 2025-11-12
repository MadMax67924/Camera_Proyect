# ✅ CORRECCIÓN: ENDPOINTS BLE EN LA WEB

## Problema
La interfaz web mostraba "No conectado" para BLE y no había forma de conectar manualmente desde el navegador. Los botones llamaban a rutas incorrectas `/arduino/` en lugar de `/ble/`.

## Solución Aplicada

### Rutas Corregidas en templates/index.html

| Anterior | Nuevo | Función |
|----------|-------|---------|
| `/arduino/connect` | `/ble/connect` | Conectar dispositivo BLE |
| `/arduino/toggle` | `/ble/toggle` | Activar/desactivar control |
| `/arduino/unlock` | `/ble/open_door` | Abrir puerta (envía 'A') |
| `/arduino/lock` | `/ble/close_door` | Cerrar puerta (envía 'C') |
| `/arduino/status` | `/ble/status` | Obtener estado BLE |

## Cómo Usar en la Web

### Paso 1: Acceder a la interfaz
```
http://192.168.43.159:5000
```

### Paso 2: Buscar botón "🔌 Conectar Arduino"
En la sección **Control Arduino** (que es realmente BLE)

### Paso 3: Presionar botón
- **Botón**: "🔌 Conectar Arduino"
- **Acción**: Busca el dispositivo `NanoDoorBLE` y se conecta
- **Resultado**: 
  - ✅ Si conecta: "✅ Arduino Conectado" y se habilita "⚙️ Activar Control"
  - ❌ Si falla: "❌ Error de Conexión" + mensaje

### Paso 4: Activar Control (opcional)
Presionar "⚙️ Activar Control" para:
- Permitir que abra/cierre puerta automáticamente al reconocer rostros
- Habilitar botones "🔓 Abrir Puerta" y "🔒 Cerrar Puerta"

### Paso 5: Pruebas Manuales
- **🔓 Abrir Puerta**: Envía 'A' al Arduino (abre puerta)
- **🔒 Cerrar Puerta**: Envía 'C' al Arduino (cierra/alarma)

## Estado de Conexión

La página muestra:
```
✅ Conectado (verde) → BLE activo
❌ No conectado (rojo) → Presiona "🔌 Conectar Arduino"
```

## Comandos Enviados al Arduino

### Al Abrir Puerta (botón 🔓)
```
Comando: 'A'
Arduino debe:
  digitalWrite(RELAY_PIN, HIGH);  // Relay ON
  delay(3000);                    // 3 segundos
  digitalWrite(RELAY_PIN, LOW);   // Relay OFF
```

### Al Cerrar Puerta (botón 🔒)
```
Comando: 'C'
Arduino debe:
  digitalWrite(ALARM_PIN, HIGH);  // Alarma ON
  delay(5000);                    // 5 segundos
  digitalWrite(ALARM_PIN, LOW);   // Alarma OFF
```

### Con Reconocimiento Facial
- Persona CONOCIDA detectada → Envía 'A' automáticamente
- Persona DESCONOCIDA detectada → Envía 'C' automáticamente

## Verificación

En los logs del servidor verás:

```
[BLE] ✓ Acceso concedido: Lucho (confianza: 95%)
[BLE] Enviando comando: A (ABRIR)

o

[BLE] ⚠️  DESCONOCIDO detectado: Unknown (confianza: 35%)
[BLE] Enviando comando: C (CERRAR/ALARMA)
```

## Archivos Modificados

✅ `templates/index.html` - Rutas BLE corregidas

## ¡LISTO!

Ya puedes:
1. Conectar desde la web
2. Abrir/cerrar puerta manualmente
3. Activar reconocimiento automático
