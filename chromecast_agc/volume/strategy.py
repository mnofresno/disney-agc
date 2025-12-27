"""Volume adjustment strategies by audio type."""

from abc import ABC, abstractmethod

from ..audio.classifier import AudioTypeResult
from ..config.settings import Settings


class VolumeStrategy(ABC):
    """Abstract strategy for volume adjustment."""

    @abstractmethod
    def calculate_adjustment(
        self,
        audio_type_result: AudioTypeResult,
        current_db: float,
        settings: Settings,
    ) -> int:
        """
        Calculate volume adjustment.

        Args:
            audio_type_result: Audio classification result
            current_db: Current audio level in dB
            settings: Application configuration

        Returns:
            Volume adjustment (positive = increase, negative = decrease)
        """
        pass


class DialogueStrategy(VolumeStrategy):
    """Aggressive strategy for dialogue (maximum priority)."""

    def calculate_adjustment(
        self,
        audio_type_result: AudioTypeResult,
        current_db: float,
        settings: Settings,
    ) -> int:
        """Calculate aggressive adjustment for dialogue."""
        confidence = audio_type_result.confidence

        if confidence <= 0.25:
            return 0

        base_threshold = 0.25
        multiplier = 2.0 + (confidence - base_threshold) * 3.0

        return int(settings.adjustment_step * multiplier)


class MusicStrategy(VolumeStrategy):
    """Moderate strategy for music."""

    def calculate_adjustment(
        self,
        audio_type_result: AudioTypeResult,
        current_db: float,
        settings: Settings,
    ) -> int:
        """Calculate moderate adjustment for music."""
        confidence = audio_type_result.confidence

        if confidence <= 0.5:
            return 0

        base_threshold = 0.5
        multiplier = 0.8 + (confidence - base_threshold) * 0.8

        return -int(settings.adjustment_step * multiplier)


class SilenceStrategy(VolumeStrategy):
    """Strategy for silence (fast increase)."""

    def calculate_adjustment(
        self,
        audio_type_result: AudioTypeResult,
        current_db: float,
        settings: Settings,
    ) -> int:
        """Calculate fast adjustment for silence."""
        return int(settings.adjustment_step * 2)
