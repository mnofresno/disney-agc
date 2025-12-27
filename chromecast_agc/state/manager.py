"""Centralized application state management."""

import threading
import time
from dataclasses import dataclass
from typing import Optional

from ..audio.classifier import AudioTypeResult
from ..config.settings import Settings


@dataclass
class ApplicationState:
    """Current application state."""

    current_volume: Optional[int] = None
    audio_level_db: float = 0.0
    audio_type: str = "unknown"
    audio_confidence: float = 0.0
    is_manual_mode: bool = False
    manual_pause_remaining: float = 0.0
    target_db: float = -25.0
    volume_baseline_max: int = 75


class StateManager:
    """Manages application state in a thread-safe manner."""

    def __init__(self, settings: Settings):
        """Initialize state manager."""
        self.settings = settings
        self._lock = threading.Lock()

        self._current_volume: Optional[int] = None
        self._audio_level_db: float = 0.0
        self._audio_type: str = "unknown"
        self._audio_confidence: float = 0.0
        self._manual_adjustment_time: float = 0.0
        self._target_db: float = settings.target_db

    def update_volume(self, volume: int) -> None:
        """Update current volume."""
        with self._lock:
            self._current_volume = volume

    def update_audio_level(self, db: float) -> None:
        """Update current audio level."""
        with self._lock:
            self._audio_level_db = db

    def update_audio_type(self, type_result: AudioTypeResult) -> None:
        """Update detected audio type."""
        with self._lock:
            self._audio_type = type_result.type
            self._audio_confidence = type_result.confidence

    def record_manual_adjustment(self) -> None:
        """Record that a manual adjustment was made."""
        with self._lock:
            self._manual_adjustment_time = time.time()

    def adjust_baseline(self, delta: float) -> None:
        """Adjust audio baseline."""
        with self._lock:
            self._target_db += delta

    def get_state(self) -> ApplicationState:
        """Get current application state."""
        with self._lock:
            manual_pause_remaining = max(
                0.0,
                self.settings.manual_pause_duration - (time.time() - self._manual_adjustment_time),
            )
            is_manual_mode = manual_pause_remaining > 0

            return ApplicationState(
                current_volume=self._current_volume,
                audio_level_db=self._audio_level_db,
                audio_type=self._audio_type,
                audio_confidence=self._audio_confidence,
                is_manual_mode=is_manual_mode,
                manual_pause_remaining=manual_pause_remaining,
                target_db=self._target_db,
                volume_baseline_max=self.settings.volume_baseline_max,
            )

    def get_current_volume(self) -> Optional[int]:
        """Get current volume."""
        with self._lock:
            return self._current_volume

    def get_target_db(self) -> float:
        """Get current target dB."""
        with self._lock:
            return self._target_db
