"""Volume controller based on audio type."""

import time
from typing import Optional

import numpy as np

from ..audio.classifier import AudioTypeResult
from ..chromecast.controller import ChromecastController
from ..config.settings import Settings
from ..state.history import HistoryManager
from ..state.manager import StateManager
from .limits import VolumeLimits
from .strategy import DialogueStrategy, MusicStrategy, SilenceStrategy


class VolumeController:
    """Controls volume adjustments based on audio type."""

    def __init__(
        self,
        settings: Settings,
        chromecast: ChromecastController,
        state_manager: StateManager,
        history_manager: HistoryManager,
    ):
        """Initialize volume controller."""
        self.settings = settings
        self.chromecast = chromecast
        self.state = state_manager
        self.history = history_manager

        self.limits = VolumeLimits(settings)
        self.dialogue_strategy = DialogueStrategy()
        self.music_strategy = MusicStrategy()
        self.silence_strategy = SilenceStrategy()

        self.last_adjustment_time = 0.0

    def adjust_based_on_type(
        self,
        db_level: float,
        audio_type_result: AudioTypeResult,
    ) -> Optional[int]:
        """
        Adjust volume based on detected audio type.

        Args:
            db_level: Audio level in dB
            audio_type_result: Classification result

        Returns:
            New volume if adjusted, None if not
        """
        current_time = time.time()

        if not self._can_adjust(current_time, db_level, audio_type_result):
            return None

        current_volume = self.chromecast.get_volume()
        if current_volume is None:
            return None

        adjustment = self._calculate_adjustment(db_level, audio_type_result)

        if adjustment == 0:
            return None

        new_volume = current_volume + adjustment
        new_volume = self.limits.apply_limits(new_volume, is_manual=False)

        if self.chromecast.set_volume(new_volume):
            self.last_adjustment_time = current_time
            self.state.update_volume(new_volume)
            return new_volume

        return None

    def _can_adjust(
        self,
        current_time: float,
        db_level: float,
        audio_type_result: AudioTypeResult,
    ) -> bool:
        """Check if adjustment can be made."""
        is_silence = db_level < self.settings.silence_threshold_db or db_level == -np.inf

        if audio_type_result.type == "unknown" and not is_silence:
            return False

        state = self.state.get_state()
        if audio_type_result.type in ["dialogue", "music"]:
            if state.is_manual_mode:
                return False

        min_interval = 0.3 if is_silence else self.settings.min_adjustment_interval
        if current_time - self.last_adjustment_time < min_interval:
            return False

        return True

    def _calculate_adjustment(
        self,
        db_level: float,
        audio_type_result: AudioTypeResult,
    ) -> int:
        """Calculate volume adjustment."""
        is_silence = db_level < self.settings.silence_threshold_db or db_level == -np.inf

        if is_silence:
            return self.silence_strategy.calculate_adjustment(audio_type_result, db_level, self.settings)

        if audio_type_result.type == "dialogue":
            return self.dialogue_strategy.calculate_adjustment(audio_type_result, db_level, self.settings)

        if audio_type_result.type == "music":
            return self.music_strategy.calculate_adjustment(audio_type_result, db_level, self.settings)

        return 0

    def manual_adjust(self, delta: int) -> bool:
        """
        Manual volume adjustment.

        Args:
            delta: Volume change (+2 or -2 typically)

        Returns:
            True if adjustment was successful
        """
        current_volume = self.chromecast.get_volume()
        if current_volume is None:
            return False

        new_volume = self.limits.apply_limits(current_volume + delta, is_manual=True)

        if self.chromecast.set_volume(new_volume):
            self.state.record_manual_adjustment()
            self.state.update_volume(new_volume)
            return True

        return False
