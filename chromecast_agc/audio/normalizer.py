"""Audio normalization to compensate for weak signals."""

import numpy as np

from ..config.settings import Settings


class AudioNormalizer:
    """Normalizes audio to maintain relative spectral characteristics."""

    def __init__(self, settings: Settings):
        """Initialize audio normalizer."""
        self.target_rms = settings.normalization_target_rms
        self.max_factor = settings.normalization_max_factor

    def normalize(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio to a standard level.

        Helps maintain relative spectral characteristics even with weak signals
        captured from distance.

        Args:
            audio_data: Unnormalized audio data

        Returns:
            Normalized audio data
        """
        audio_rms = np.sqrt(np.mean(audio_data**2))

        if audio_rms > 0:
            normalization_factor = self.target_rms / audio_rms
            audio_data_normalized = audio_data * min(normalization_factor, self.max_factor)
        else:
            audio_data_normalized = audio_data

        return audio_data_normalized
