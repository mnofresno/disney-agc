# Plan de Refactorización - Chromecast AGC

## 📋 Resumen Ejecutivo

Este documento describe un plan completo para refactorizar el proyecto `chromecast-agc.py` de un script monolítico a una arquitectura modular, mantenible y extensible.

## 🎯 Objetivos del Refactor

1. **Separación de responsabilidades**: Cada módulo tiene una única responsabilidad clara
2. **Testabilidad**: Componentes aislados y fácilmente testeables
3. **Mantenibilidad**: Código más fácil de entender y modificar
4. **Extensibilidad**: Fácil agregar nuevas funcionalidades
5. **Reutilización**: Componentes reutilizables en otros proyectos

## 🏗️ Estructura Propuesta

```
disney-agc/
├── chromecast_agc/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── parser.py          # Argument parsing
│   │   └── commands.py         # CLI commands (list-devices, etc.)
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── status_display.py   # Status line management
│   │   └── formatter.py        # Status message formatting
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── capture.py          # Audio capture (sounddevice wrapper)
│   │   ├── analyzer.py         # Audio analysis (FFT, dB calculation)
│   │   ├── normalizer.py       # Audio normalization
│   │   └── classifier.py       # Audio type classification (dialogue/music)
│   ├── chromecast/
│   │   ├── __init__.py
│   │   ├── connection.py       # Chromecast connection management
│   │   ├── controller.py        # Volume control interface
│   │   └── adapters.py         # pychromecast and catt adapters
│   ├── input/
│   │   ├── __init__.py
│   │   ├── keyboard.py         # Keyboard input handler
│   │   ├── ansi_handler.py     # ANSI sequence handler (terminal)
│   │   └── platform_handler.py # Platform-specific handlers (pynput/keyboard)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Configuration dataclass
│   │   ├── defaults.py         # Default values
│   │   └── adaptive.py         # Adaptive threshold management
│   ├── volume/
│   │   ├── __init__.py
│   │   ├── controller.py       # Volume adjustment logic
│   │   ├── strategy.py         # Volume adjustment strategies
│   │   └── limits.py            # Volume limits management
│   ├── state/
│   │   ├── __init__.py
│   │   ├── manager.py          # State management (audio levels, types, etc.)
│   │   └── history.py          # History tracking (deque management)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── dependencies.py    # Dependency installation
│   │   ├── platform.py         # Platform detection utilities
│   │   └── signals.py          # Signal handling
│   └── core/
│       ├── __init__.py
│       └── controller.py      # Main orchestrator (replaces ChromecastVolumeController)
├── tests/
│   ├── __init__.py
│   ├── test_audio/
│   ├── test_classifier/
│   ├── test_chromecast/
│   ├── test_volume/
│   └── test_integration/
├── chromecast-agc.py           # Entry point (thin wrapper)
├── setup.py                     # Package setup
├── requirements.txt             # Dependencies
└── README.md
```

## 📦 Componentes Detallados

### 1. CLI (`cli/`)

**Responsabilidad**: Parsear argumentos de línea de comandos y ejecutar comandos.

**Archivos**:
- `parser.py`: Define y parsea argumentos CLI
- `commands.py`: Implementa comandos como `list-devices`

**Interfaces**:
```python
# cli/parser.py
def create_parser() -> argparse.ArgumentParser
def parse_args() -> Namespace

# cli/commands.py
def list_audio_devices(device_index: Optional[int] = None) -> None
```

**Beneficios**:
- Separación clara de CLI del core
- Fácil agregar nuevos comandos
- Testeable independientemente

---

### 2. TUI (`tui/`)

**Responsabilidad**: Gestión de la interfaz de usuario en terminal.

**Archivos**:
- `status_display.py`: Maneja la línea de estado única
- `formatter.py`: Formatea mensajes de estado

**Interfaces**:
```python
# tui/status_display.py
class StatusDisplay:
    def update(message: str) -> None
    def update_immediate(state: ApplicationState) -> None
    def clear() -> None

# tui/formatter.py
def format_status(state: ApplicationState) -> str
```

**Beneficios**:
- Separación de presentación y lógica
- Fácil cambiar formato de salida
- Permite futuras interfaces (GUI, web, etc.)

---

### 3. Audio (`audio/`)

**Responsabilidad**: Captura, análisis y clasificación de audio.

#### 3.1 `audio/capture.py`
- Wrapper alrededor de `sounddevice`
- Maneja callbacks de audio
- Gestión de dispositivos

**Interfaces**:
```python
class AudioCapture:
    def start(callback: Callable, device_index: Optional[int] = None) -> None
    def stop() -> None
    def list_devices() -> List[DeviceInfo]
```

#### 3.2 `audio/analyzer.py`
- Cálculo de dB (RMS)
- Análisis FFT
- Extracción de características espectrales

**Interfaces**:
```python
class AudioAnalyzer:
    def calculate_db(audio_data: np.ndarray) -> float
    def analyze_spectrum(audio_data: np.ndarray, sample_rate: int) -> SpectrumFeatures
```

#### 3.3 `audio/normalizer.py`
- Normalización de audio para señales débiles
- Compensación por distancia

**Interfaces**:
```python
class AudioNormalizer:
    def normalize(audio_data: np.ndarray, target_rms: float = 0.15) -> np.ndarray
```

#### 3.4 `audio/classifier.py`
- Clasificación diálogo/música/desconocido
- Sistema de scoring
- Detección de canciones cantadas

**Interfaces**:
```python
class AudioClassifier:
    def classify(features: SpectrumFeatures) -> AudioTypeResult
    
@dataclass
class AudioTypeResult:
    type: str  # 'dialogue', 'music', 'unknown'
    confidence: float
    features: Dict[str, float]
    scores: Dict[str, float]
```

**Beneficios**:
- Lógica de audio completamente aislada
- Fácil testear algoritmos de clasificación
- Permite experimentar con diferentes algoritmos

---

### 4. Chromecast (`chromecast/`)

**Responsabilidad**: Conexión y control de dispositivos Chromecast.

#### 4.1 `chromecast/connection.py`
- Descubrimiento de dispositivos
- Gestión de conexión persistente
- Reconexión automática

**Interfaces**:
```python
class ChromecastConnection:
    def connect(device_name: str) -> bool
    def disconnect() -> None
    def is_connected() -> bool
    @property
    def cast() -> Optional[Cast]
```

#### 4.2 `chromecast/controller.py`
- Interfaz unificada para control de volumen
- Abstracción sobre diferentes backends

**Interfaces**:
```python
class ChromecastController:
    def get_volume() -> Optional[int]
    def set_volume(volume: int) -> bool
    def connect(device_name: str) -> bool
```

#### 4.3 `chromecast/adapters.py`
- Implementaciones específicas: pychromecast, catt
- Patrón Adapter para diferentes backends

**Interfaces**:
```python
class PyChromecastAdapter(ChromecastController):
    # Implementación con pychromecast
    
class CattAdapter(ChromecastController):
    # Implementación con catt (fallback)
```

**Beneficios**:
- Fácil cambiar backend de Chromecast
- Testeable con mocks
- Soporte para múltiples dispositivos en el futuro

---

### 5. Input (`input/`)

**Responsabilidad**: Captura de entrada de teclado multiplataforma.

#### 5.1 `input/keyboard.py`
- Interfaz unificada para entrada de teclado
- Coordinación entre diferentes handlers

**Interfaces**:
```python
class KeyboardInput:
    def start(callbacks: KeyboardCallbacks) -> None
    def stop() -> None
    def is_active() -> bool
```

#### 5.2 `input/ansi_handler.py`
- Manejo de secuencias ANSI en terminal
- Lectura no bloqueante de stdin

**Interfaces**:
```python
class ANSIHandler:
    def read_key() -> Optional[Key]
    def setup_terminal() -> None
    def restore_terminal() -> None
```

#### 5.3 `input/platform_handler.py`
- Handlers específicos por plataforma (pynput, keyboard)
- Detección automática de plataforma

**Interfaces**:
```python
class PlatformKeyboardHandler:
    def start(callbacks: KeyboardCallbacks) -> None
    def stop() -> None
```

**Beneficios**:
- Lógica de entrada aislada
- Fácil agregar nuevos métodos de entrada
- Mejor manejo de errores por plataforma

---

### 6. Config (`config/`)

**Responsabilidad**: Gestión de configuración y thresholds adaptativos.

#### 6.1 `config/settings.py`
- Dataclass para toda la configuración
- Validación de valores

**Interfaces**:
```python
@dataclass
class Settings:
    device_name: str
    volume_min: int
    volume_max: int
    volume_baseline_max: int
    target_db: float
    threshold_loud: float
    threshold_quiet: float
    adjustment_step: int
    sample_rate: int
    chunk_duration: float
    smoothing_window: int
    # ... más configuraciones
```

#### 6.2 `config/defaults.py`
- Valores por defecto
- Configuraciones optimizadas por distancia

**Interfaces**:
```python
def get_default_settings() -> Settings
def get_settings_for_distance(distance_meters: float) -> Settings
```

#### 6.3 `config/adaptive.py`
- Ajuste adaptativo de thresholds
- Aprendizaje de ajustes manuales del usuario

**Interfaces**:
```python
class AdaptiveThresholds:
    def adjust_for_volume(volume: int, current_db: float, previous_volume: Optional[int]) -> None
    def get_threshold_loud() -> float
    def get_threshold_quiet() -> float
```

**Beneficios**:
- Configuración centralizada y tipada
- Fácil serializar/deserializar (JSON, YAML)
- Lógica adaptativa aislada

---

### 7. Volume (`volume/`)

**Responsabilidad**: Lógica de ajuste de volumen.

#### 7.1 `volume/controller.py`
- Coordinación de ajustes de volumen
- Respeto a límites y pausas manuales

**Interfaces**:
```python
class VolumeController:
    def adjust_based_on_type(db_level: float, audio_type: AudioTypeResult) -> Optional[int]
    def can_adjust() -> bool
    def pause_automatic(duration: float) -> None
```

#### 7.2 `volume/strategy.py`
- Estrategias de ajuste por tipo de audio
- Cálculo de incrementos/decrementos

**Interfaces**:
```python
class VolumeStrategy:
    def calculate_adjustment(audio_type: str, confidence: float, current_db: float) -> int

class DialogueStrategy(VolumeStrategy):
    # Ajuste agresivo para diálogo
    
class MusicStrategy(VolumeStrategy):
    # Ajuste moderado para música
```

#### 7.3 `volume/limits.py`
- Gestión de límites de volumen
- Diferencia entre límites automáticos y manuales

**Interfaces**:
```python
class VolumeLimits:
    def apply_limits(volume: int, is_manual: bool) -> int
    def can_exceed_baseline(is_manual: bool) -> bool
```

**Beneficios**:
- Lógica de volumen clara y testeable
- Fácil agregar nuevas estrategias
- Separación de límites y ajustes

---

### 8. State (`state/`)

**Responsabilidad**: Gestión de estado de la aplicación.

#### 8.1 `state/manager.py`
- Estado centralizado de la aplicación
- Thread-safe access

**Interfaces**:
```python
@dataclass
class ApplicationState:
    current_volume: Optional[int]
    audio_level_db: float
    audio_type: str
    audio_confidence: float
    is_manual_mode: bool
    manual_pause_remaining: float
    target_db: float
    
class StateManager:
    def update_audio_level(db: float) -> None
    def update_audio_type(type_result: AudioTypeResult) -> None
    def update_volume(volume: int) -> None
    def get_state() -> ApplicationState
```

#### 8.2 `state/history.py`
- Gestión de historial (deque)
- Promedios y agregaciones

**Interfaces**:
```python
class HistoryManager:
    def add_audio_level(db: float) -> None
    def add_audio_type(type_result: AudioTypeResult) -> None
    def get_avg_audio_level() -> float
    def get_predominant_audio_type() -> AudioTypeResult
```

**Beneficios**:
- Estado centralizado y observable
- Fácil debugging
- Thread-safe por diseño

---

### 9. Utils (`utils/`)

**Responsabilidad**: Utilidades generales.

#### 9.1 `utils/dependencies.py`
- Auto-instalación de dependencias
- Detección de plataforma para dependencias

**Interfaces**:
```python
def install_dependencies() -> None
def check_dependencies() -> bool
def get_platform_dependencies() -> List[str]
```

#### 9.2 `utils/platform.py`
- Detección de plataforma
- Utilidades específicas por plataforma

**Interfaces**:
```python
def is_macos() -> bool
def is_linux() -> bool
def is_windows() -> bool
def get_keyboard_module() -> Optional[ModuleType]
```

#### 9.3 `utils/signals.py`
- Manejo de señales (SIGINT, SIGTERM)
- Cleanup graceful

**Interfaces**:
```python
def setup_signal_handlers(cleanup_callback: Callable) -> None
```

**Beneficios**:
- Utilidades reutilizables
- Mejor organización
- Fácil testear

---

### 10. Core (`core/`)

**Responsabilidad**: Orquestación principal de la aplicación.

#### 10.1 `core/controller.py`
- Coordina todos los componentes
- Reemplaza `ChromecastVolumeController` monolítico

**Interfaces**:
```python
class AGCController:
    def __init__(self, settings: Settings) -> None
    def start(device_index: Optional[int] = None) -> None
    def stop() -> None
    def is_running() -> bool
    
    # Event handlers
    def on_audio_chunk(audio_data: np.ndarray) -> None
    def on_keyboard_input(key: Key) -> None
```

**Flujo principal**:
1. Inicializar componentes (chromecast, audio, keyboard, etc.)
2. Configurar callbacks
3. Iniciar captura de audio
4. Procesar chunks de audio:
   - Analizar → Clasificar → Ajustar volumen
5. Manejar entrada de teclado
6. Actualizar TUI periódicamente
7. Cleanup al salir

**Beneficios**:
- Orquestación clara
- Fácil entender flujo completo
- Componentes desacoplados

---

## 🔄 Flujo de Datos Refactorizado

```
CLI (parser.py)
  ↓
Core Controller (core/controller.py)
  ├─→ Chromecast Connection (chromecast/connection.py)
  ├─→ Audio Capture (audio/capture.py)
  │     └─→ Audio Callback
  │           ├─→ Audio Analyzer (audio/analyzer.py)
  │           ├─→ Audio Normalizer (audio/normalizer.py)
  │           ├─→ Audio Classifier (audio/classifier.py)
  │           └─→ Volume Controller (volume/controller.py)
  │                 └─→ Chromecast Controller (chromecast/controller.py)
  ├─→ Keyboard Input (input/keyboard.py)
  │     └─→ Volume Controller (volume/controller.py)
  ├─→ State Manager (state/manager.py)
  └─→ TUI Display (tui/status_display.py)
        └─→ State Manager (state/manager.py)
```

## 📝 Plan de Implementación

### Fase 1: Estructura Base (Semana 1)
1. ✅ Crear estructura de directorios
2. ✅ Crear `__init__.py` files
3. ✅ Mover `utils/` (dependencies, platform, signals)
4. ✅ Crear `config/` (settings, defaults)
5. ✅ Crear `state/` (manager, history)

### Fase 2: Componentes de Audio (Semana 1-2)
1. ✅ Extraer `audio/capture.py`
2. ✅ Extraer `audio/analyzer.py`
3. ✅ Extraer `audio/normalizer.py`
4. ✅ Extraer `audio/classifier.py` (más complejo)
5. ✅ Tests unitarios para cada componente

### Fase 3: Chromecast (Semana 2)
1. ✅ Extraer `chromecast/connection.py`
2. ✅ Extraer `chromecast/controller.py`
3. ✅ Crear `chromecast/adapters.py`
4. ✅ Tests con mocks

### Fase 4: Input y TUI (Semana 2-3)
1. ✅ Extraer `input/keyboard.py`
2. ✅ Extraer `input/ansi_handler.py`
3. ✅ Extraer `input/platform_handler.py`
4. ✅ Extraer `tui/status_display.py`
5. ✅ Extraer `tui/formatter.py`

### Fase 5: Volume y Config Adaptativa (Semana 3)
1. ✅ Extraer `volume/controller.py`
2. ✅ Extraer `volume/strategy.py`
3. ✅ Extraer `volume/limits.py`
4. ✅ Extraer `config/adaptive.py`

### Fase 6: CLI y Core (Semana 3-4)
1. ✅ Extraer `cli/parser.py`
2. ✅ Extraer `cli/commands.py`
3. ✅ Crear `core/controller.py` (orquestador)
4. ✅ Refactorizar `chromecast-agc.py` como entry point

### Fase 7: Testing y Refinamiento (Semana 4)
1. ✅ Tests de integración
2. ✅ Tests end-to-end
3. ✅ Documentación de APIs
4. ✅ Optimizaciones de rendimiento

### Fase 8: Migración y Cleanup (Semana 4)
1. ✅ Migrar código existente a nuevos módulos
2. ✅ Eliminar código duplicado
3. ✅ Actualizar imports
4. ✅ Verificar que todo funciona igual

## 🧪 Estrategia de Testing

### Tests Unitarios
- Cada módulo tiene tests independientes
- Mocks para dependencias externas (pychromecast, sounddevice)
- Tests de algoritmos de clasificación con datos sintéticos

### Tests de Integración
- Tests de flujo completo con mocks
- Tests de componentes que interactúan

### Tests End-to-End
- Tests con Chromecast real (opcional, marcados como `@pytest.mark.slow`)
- Tests con audio sintético

## 🔧 Mejoras Adicionales

### 1. Type Hints
- Agregar type hints completos en todos los módulos
- Usar `typing` y `dataclasses` donde corresponda

### 2. Logging
- Reemplazar `print()` con `logging`
- Niveles de log configurables
- Logs estructurados

### 3. Configuración Persistente
- Guardar configuración en archivo (JSON/YAML)
- Cargar configuración al inicio
- Permitir override con CLI

### 4. Event System (Opcional)
- Sistema de eventos para desacoplar componentes
- Permite extensibilidad futura

### 5. Plugin System (Futuro)
- Permitir plugins para nuevos clasificadores
- Plugins para nuevos backends de Chromecast

## 📊 Métricas de Éxito

1. **Cobertura de tests**: >80%
2. **Líneas por módulo**: <500 (excepto classifier que puede ser más complejo)
3. **Acoplamiento**: Bajo (módulos independientes)
4. **Cohesión**: Alta (cada módulo tiene responsabilidad única)
5. **Funcionalidad**: 100% de features originales mantenidas

## 🚀 Próximos Pasos

1. Revisar y aprobar este plan
2. Crear estructura de directorios
3. Comenzar con Fase 1 (estructura base)
4. Implementar módulo por módulo siguiendo el plan
5. Tests continuos durante desarrollo
6. Documentación inline y README actualizado

## 📚 Referencias

- Clean Architecture (Robert C. Martin)
- SOLID Principles
- Python Packaging Best Practices
- Testing Best Practices

---

**Nota**: Este plan es un documento vivo. Se actualizará según se descubran necesidades durante la implementación.

