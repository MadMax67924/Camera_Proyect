// ==================== STATE MANAGEMENT ====================
const AppState = {
    startTime: Date.now(),
    frameCount: 0,
    lastFrameTime: Date.now(),
    elements: {}
};

// ==================== DOM ELEMENTS ====================
function initElements() {
    AppState.elements = {
        videoStream: document.getElementById('videoStream'),
        loadingOverlay: document.getElementById('loadingOverlay'),
        statusIndicator: document.querySelector('.status-dot'),
        statusText: document.getElementById('statusText'),
        fpsValue: document.getElementById('fpsValue'),
        uptimeValue: document.getElementById('uptimeValue'),
        frameValue: document.getElementById('frameValue'),
        toggleDetectionBtn: document.getElementById('toggleDetectionBtn'),
        toggleRecognitionBtn: document.getElementById('toggleRecognitionBtn'),
        detectionInfo: document.getElementById('detectionInfo'),
        recognitionInfo: document.getElementById('recognitionInfo'),
        cameraSelector: document.getElementById('cameraSelector'),
        cameraList: document.getElementById('cameraList'),
        recognizedFaces: document.getElementById('recognizedFaces'),
        recognizedList: document.getElementById('recognizedList'),
        arduinoConnectBtn: document.getElementById('arduinoConnectBtn'),
        arduinoToggleBtn: document.getElementById('arduinoToggleBtn'),
        arduinoUnlockBtn: document.getElementById('arduinoUnlockBtn'),
        arduinoLockBtn: document.getElementById('arduinoLockBtn'),
        arduinoStatusText: document.getElementById('arduinoStatusText')
    };
    // Allowed list elements
    AppState.elements.allowedInput = document.getElementById('allowedInput');
    AppState.elements.allowedList = document.getElementById('allowedList');
}

// ==================== VIDEO STREAM HANDLERS ====================
function handleVideoLoad() {
    const { loadingOverlay, statusIndicator, statusText, fpsValue } = AppState.elements;

    loadingOverlay.classList.add('hidden');
    statusIndicator.classList.remove('error');
    statusText.textContent = 'Transmitiendo en vivo';
    AppState.frameCount++;

    const now = Date.now();
    const timeDiff = (now - AppState.lastFrameTime) / 1000;
    if (timeDiff > 0) {
        const fps = Math.round(1 / timeDiff);
        fpsValue.textContent = fps;
    }
    AppState.lastFrameTime = now;
}

function handleVideoError() {
    const { loadingOverlay, statusIndicator, statusText } = AppState.elements;

    loadingOverlay.classList.remove('hidden');
    loadingOverlay.querySelector('p').textContent = 'Error al cargar el stream';
    statusIndicator.classList.add('error');
    statusText.textContent = 'Error de conexi�n';

    setTimeout(refreshStream, 3000);
}

// ==================== UTILITY FUNCTIONS ====================
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const error = await response.json();
            throw error;
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${url}:`, error);
        throw error;
    }
}

function updateButtonState(button, config) {
    const { text, icon, color, disabled = false } = config;
    if (text) {
        const span = button.querySelector('span');
        if (span) span.textContent = text;
    }
    if (color) button.style.background = color;
    button.disabled = disabled;
}

// ==================== CAMERA CONTROLS ====================
function refreshStream() {
    const { videoStream, loadingOverlay } = AppState.elements;
    const timestamp = new Date().getTime();
    videoStream.src = `/video_feed?t=${timestamp}`;
    loadingOverlay.classList.remove('hidden');
    loadingOverlay.querySelector('p').textContent = 'Cargando stream...';
}

function toggleFullscreen() {
    const wrapper = document.querySelector('.video-container');

    if (!document.fullscreenElement) {
        wrapper.requestFullscreen().catch(err => {
            alert(`No se pudo activar pantalla completa: ${err.message}`);
        });
    } else {
        document.exitFullscreen();
    }
}

function viewStats() {
    window.open('/stats', '_blank');
}

// ==================== DETECTION & RECOGNITION ====================
async function toggleDetection() {
    const { toggleDetectionBtn, detectionInfo, statusText } = AppState.elements;

    try {
        const data = await fetchJSON('/toggle_detection', { method: 'POST' });

        if (data.detection_enabled) {
            updateButtonState(toggleDetectionBtn, {
                text: 'Desactivar Detección',
                color: '#ef4444'
            });
            detectionInfo.textContent = 'Detección facial ACTIVADA - 25-30 FPS';
            statusText.textContent = 'Detección Facial Activa';
        } else {
            updateButtonState(toggleDetectionBtn, {
                text: 'Activar Detección',
                color: '#6366f1'
            });
            detectionInfo.textContent = 'Detección facial DESACTIVADA - Máximo FPS (60+)';
            statusText.textContent = 'Modo Rápido - Sin Detección';
        }
    } catch (err) {
        alert('Error al cambiar modo de detección');
    }
}

async function toggleRecognition() {
    const { toggleRecognitionBtn, recognitionInfo } = AppState.elements;

    try {
        const data = await fetchJSON('/toggle_recognition', { method: 'POST' });

        if (data.recognition_enabled) {
            updateButtonState(toggleRecognitionBtn, {
                text: 'Desactivar Reconocimiento',
                color: '#ef4444'
            });
            recognitionInfo.textContent = 'Reconocimiento facial ACTIVADO - 15-20 FPS';
        } else {
            updateButtonState(toggleRecognitionBtn, {
                text: 'Activar Reconocimiento',
                color: '#6366f1'
            });
            recognitionInfo.textContent = 'Reconocimiento facial DESACTIVADO';
        }
    } catch (err) {
        alert(err.message || 'Error al cambiar modo de reconocimiento');
    }
}

// ==================== CAMERA SELECTION ====================
async function showCameraSelector() {
    const { cameraSelector, cameraList } = AppState.elements;

    try {
        const data = await fetchJSON('/cameras');
        cameraList.innerHTML = '';

        data.cameras.forEach(camId => {
            const btn = document.createElement('button');
            btn.textContent = `/dev/video${camId}`;

            if (camId === data.current) {
                btn.className = 'px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-300';
                btn.textContent += ' ✓ Actual';
            } else {
                btn.className = 'px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-300';
            }

            btn.onclick = () => changeCamera(camId);
            cameraList.appendChild(btn);
        });

        cameraSelector.classList.toggle('hidden');
    } catch (err) {
        alert('Error al obtener lista de cámaras');
    }
}

async function changeCamera(cameraId) {
    if (!confirm(`¿Cambiar a /dev/video${cameraId}?`)) return;

    try {
        const data = await fetchJSON(`/set_camera/${cameraId}`, { method: 'POST' });

        if (data.success) {
            alert(data.message);
            setTimeout(refreshStream, 1000);
            AppState.elements.cameraSelector.classList.add('hidden');
        } else {
            alert(data.message);
        }
    } catch (err) {
        alert('Error al cambiar cámara');
    }
}

// ==================== ARDUINO CONTROLS (BLE) ====================
async function connectArduino() {
    const { arduinoConnectBtn } = AppState.elements;

    updateButtonState(arduinoConnectBtn, {
        text: 'Conectando...',
        disabled: true
    });

    try {
        const data = await fetchJSON('/ble/connect', { method: 'POST' });

        await updateArduinoStatus();

        if (data.success) {
            setTimeout(() => {
                updateButtonState(arduinoConnectBtn, {
                    text: 'Arduino Conectado',
                    color: '#10b981'
                });
                AppState.elements.arduinoToggleBtn.disabled = false;
            }, 500);
        } else {
            throw new Error(data.message);
        }
    } catch (err) {
        updateButtonState(arduinoConnectBtn, {
            text: 'Error de Conexión',
            color: '#ef4444'
        });
        alert(`Error: ${err.message}`);

        setTimeout(() => {
            updateButtonState(arduinoConnectBtn, {
                text: 'Conectar Arduino',
                color: '#10b981',
                disabled: false
            });
        }, 2000);
    }
}

async function toggleArduino() {
    const { arduinoToggleBtn, arduinoUnlockBtn, arduinoLockBtn } = AppState.elements;

    arduinoToggleBtn.disabled = true;

    try {
        const data = await fetchJSON('/ble/toggle', { method: 'POST' });

        if (data.arduino_enabled) {
            updateButtonState(arduinoToggleBtn, { text: 'Control Activo', color: '#10b981' });
            arduinoUnlockBtn.disabled = false;
            arduinoLockBtn.disabled = false;
        } else {
            updateButtonState(arduinoToggleBtn, { text: 'Activar Control', color: '#f59e0b' });
            arduinoUnlockBtn.disabled = true;
            arduinoLockBtn.disabled = true;
        }

        await updateArduinoStatus();
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        arduinoToggleBtn.disabled = false;
    }
}

async function unlockDoor() {
    if (!confirm('¿Abrir la puerta?')) return;

    const { arduinoUnlockBtn } = AppState.elements;

    updateButtonState(arduinoUnlockBtn, {
        text: 'Abriendo...',
        disabled: true
    });

    try {
        const data = await fetchJSON('/ble/open_door', { method: 'POST' });

        if (data.success) {
            updateButtonState(arduinoUnlockBtn, { text: '�Puerta Abierta!' });
            setTimeout(() => {
                updateButtonState(arduinoUnlockBtn, {
                    text: 'Abrir Puerta',
                    disabled: false
                });
            }, 2000);
        } else {
            throw new Error(data.message);
        }

        await updateArduinoStatus();
    } catch (err) {
        updateButtonState(arduinoUnlockBtn, { text: 'Abrir Puerta', disabled: false });
        alert(`Error: ${err.message}`);
    }
}

async function lockDoor() {
    if (!confirm('¿Cerrar la puerta?')) return;

    const { arduinoLockBtn } = AppState.elements;

    updateButtonState(arduinoLockBtn, {
        text: 'Cerrando...',
        disabled: true
    });

    try {
        const data = await fetchJSON('/ble/close_door', { method: 'POST' });

        if (data.success) {
            updateButtonState(arduinoLockBtn, { text: '¡Puerta Cerrada!' });
            setTimeout(() => {
                updateButtonState(arduinoLockBtn, {
                    text: 'Cerrar Puerta',
                    disabled: false
                });
            }, 2000);
        } else {
            throw new Error(data.message);
        }

        await updateArduinoStatus();
    } catch (err) {
        updateButtonState(arduinoLockBtn, { text: 'Cerrar Puerta', disabled: false });
        alert(`Error: ${err.message}`);
    }
}

async function updateArduinoStatus() {
    try {
        const data = await fetchJSON('/ble/status');
        const { arduinoStatusText } = AppState.elements;

        if (data.connected) {
            arduinoStatusText.textContent = 'Conectado';
            arduinoStatusText.style.color = '#10b981';
        } else {
            arduinoStatusText.textContent = 'No conectado';
            arduinoStatusText.style.color = '#ef4444';
        }
    } catch (err) {
        console.log('Error obteniendo estado Arduino:', err);
    }
}

// ==================== ALLOWED USERS CRUD ====================
async function loadAllowed() {
    try {
        const data = await fetchJSON('/allowed');
        const { allowedList } = AppState.elements;
        allowedList.innerHTML = '';
        data.allowed.forEach(name => {
            const li = document.createElement('li');
            li.className = 'flex items-center justify-between px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg';
            li.innerHTML = `<span class="text-sm">${name}</span>`;
            const btn = document.createElement('button');
            btn.className = 'text-red-500 hover:text-red-600 text-sm';
            btn.textContent = 'Eliminar';
            btn.onclick = () => removeAllowed(name);
            li.appendChild(btn);
            allowedList.appendChild(li);
        });
    } catch (err) {
        console.error('Error cargando lista permitidos:', err);
    }
}

async function addAllowed() {
    const { allowedInput } = AppState.elements;
    const name = (allowedInput.value || '').trim();
    if (!name) return;
    try {
        await fetchJSON('/allowed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        allowedInput.value = '';
        loadAllowed();
    } catch (err) {
        alert(err.message || 'Error al agregar permitido');
    }
}

async function removeAllowed(name) {
    if (!confirm(`¿Quitar a "${name}" de permitidos?`)) return;
    try {
        await fetchJSON(`/allowed/${encodeURIComponent(name)}`, { method: 'DELETE' });
        loadAllowed();
    } catch (err) {
        alert(err.message || 'Error al eliminar permitido');
    }
}

// ==================== STATUS UPDATES ====================
async function updateStats() {
    const { uptimeValue, frameValue, fpsValue } = AppState.elements;
    const { toggleDetectionBtn, toggleRecognitionBtn, detectionInfo, recognitionInfo } = AppState.elements;
    const { recognizedFaces, recognizedList } = AppState.elements;

    // Update uptime
    const elapsed = Math.floor((Date.now() - AppState.startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    uptimeValue.textContent =
        String(minutes).padStart(2, '0') + ':' +
        String(seconds).padStart(2, '0');

    // Fetch server status
    try {
        const data = await fetchJSON('/status');

        if (data.total_frames) frameValue.textContent = data.total_frames;
        if (data.fps) fpsValue.textContent = data.fps;

        // Update detection button
        if (data.detection_enabled !== undefined) {
            if (data.detection_enabled) {
                updateButtonState(toggleDetectionBtn, {
                    text: 'Desactivar Detección',
                    color: '#ef4444'
                });
                detectionInfo.textContent = 'Detección facial ACTIVADA - 25-30 FPS';
            } else {
                updateButtonState(toggleDetectionBtn, {
                    text: 'Activar Detección',
                    color: '#6366f1'
                });
                detectionInfo.textContent = 'Detección facial DESACTIVADA - Máximo FPS (60+)';
            }
        }

        // Update recognition button
        if (!data.recognition_available) {
            // Permite intentar activar para forzar carga de embeddings/modelo
            toggleRecognitionBtn.disabled = false;
            updateButtonState(toggleRecognitionBtn, {
                text: 'Activar Reconocimiento',
                color: '#f97316'
            });
            recognitionInfo.textContent = 'Reconocimiento NO DISPONIBLE (intenta activar tras configurar BD/embeddings)';
        } else {
            toggleRecognitionBtn.disabled = false;
            if (data.recognition_enabled) {
                updateButtonState(toggleRecognitionBtn, {
                    text: 'Desactivar Reconocimiento',
                    color: '#ef4444'
                });
                recognitionInfo.textContent = 'Reconocimiento facial ACTIVADO';
            } else {
                updateButtonState(toggleRecognitionBtn, {
                    text: 'Activar Reconocimiento',
                    color: '#6366f1'
                });
                recognitionInfo.textContent = 'Reconocimiento facial DISPONIBLE (SFace)';
            }
        }

        // Show recognized faces
        if (data.recognized_names && data.recognized_names.length > 0) {
            recognizedFaces.classList.remove('hidden');
            recognizedList.innerHTML = data.recognized_names.map(name =>
                `<span class="inline-flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-full font-medium shadow-md">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    ${name}
                </span>`
            ).join('');
        } else {
            recognizedFaces.classList.add('hidden');
        }
    } catch (err) {
        console.log('Error obteniendo status:', err);
    }
}

// ==================== INITIALIZATION ====================
function init() {
    initElements();

    const { videoStream } = AppState.elements;

    // Video stream event listeners
    videoStream.addEventListener('load', handleVideoLoad);
    videoStream.addEventListener('error', handleVideoError);

    // Prevent right-click on video
    videoStream.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        return false;
    });

    // Update stats every second
    setInterval(updateStats, 1000);

    // Update Arduino status every 5 seconds
    setInterval(updateArduinoStatus, 5000);

    // Load allowed users list
    loadAllowed();
}

// Start application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
