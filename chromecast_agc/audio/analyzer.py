"""Audio analysis: dB calculation and spectral features extraction."""

from dataclasses import dataclass

import numpy as np

from ..config.settings import Settings


@dataclass
class SpectrumFeatures:
    """Spectral features extracted from audio."""

    voice_ratio: float
    voice_formants_ratio: float
    bass_to_voice_ratio: float
    high_to_voice_ratio: float
    spectral_variation: float
    background_music_ratio: float
    ratio_voice_formants: float
    ratio_bass: float
    ratio_high: float


class AudioAnalyzer:
    """Analyzes audio and extracts spectral features."""

    def __init__(self, settings: Settings):
        """Initialize audio analyzer."""
        self.sample_rate = settings.sample_rate

    def calculate_db(self, audio_data: np.ndarray) -> float:
        """
        Calculate audio decibel level.

        Args:
            audio_data: Audio data (numpy array)

        Returns:
            Level in dB, or -inf if no signal
        """
        rms = np.sqrt(np.mean(audio_data**2))

        if rms > 0:
            db = 20 * np.log10(rms)
        else:
            db = -np.inf

        return float(db)

    def analyze_spectrum(self, audio_data: np.ndarray) -> SpectrumFeatures:
        """
        Analyze audio frequency spectrum.

        Args:
            audio_data: Normalized audio data

        Returns:
            SpectrumFeatures with spectral characteristics
        """
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio_data), 1.0 / self.sample_rate)

        idx_bass = (freqs >= 20) & (freqs < 200)
        idx_voice_fundamental = (freqs >= 200) & (freqs < 500)
        idx_voice_formants = (freqs >= 500) & (freqs < 2000)
        idx_voice_harmonics = (freqs >= 2000) & (freqs < 4000)
        idx_high_mid = (freqs >= 4000) & (freqs < 8000)
        idx_high = freqs >= 8000

        energy_bass = np.sum(magnitude[idx_bass]) if np.any(idx_bass) else 0.0
        energy_voice_fundamental = np.sum(magnitude[idx_voice_fundamental]) if np.any(idx_voice_fundamental) else 0.0
        energy_voice_formants = np.sum(magnitude[idx_voice_formants]) if np.any(idx_voice_formants) else 0.0
        energy_voice_harmonics = np.sum(magnitude[idx_voice_harmonics]) if np.any(idx_voice_harmonics) else 0.0
        energy_high_mid = np.sum(magnitude[idx_high_mid]) if np.any(idx_high_mid) else 0.0
        energy_high = np.sum(magnitude[idx_high]) if np.any(idx_high) else 0.0

        total_energy = (
            energy_bass
            + energy_voice_fundamental
            + energy_voice_formants
            + energy_voice_harmonics
            + energy_high_mid
            + energy_high
        )

        if total_energy == 0:
            return SpectrumFeatures(
                voice_ratio=0.0,
                voice_formants_ratio=0.0,
                bass_to_voice_ratio=0.0,
                high_to_voice_ratio=0.0,
                spectral_variation=0.0,
                background_music_ratio=0.0,
                ratio_voice_formants=0.0,
                ratio_bass=0.0,
                ratio_high=0.0,
            )

        ratio_bass = energy_bass / total_energy
        ratio_voice_formants = energy_voice_formants / total_energy
        ratio_high = energy_high / total_energy

        spectral_variance = np.std(magnitude)
        spectral_mean = np.mean(magnitude)
        spectral_coefficient_variation = spectral_variance / spectral_mean if spectral_mean > 0 else 0.0

        voice_energy = energy_voice_fundamental + energy_voice_formants + energy_voice_harmonics
        voice_ratio = voice_energy / total_energy

        voice_formants_ratio = energy_voice_formants / total_energy

        voice_total_energy = energy_voice_fundamental + energy_voice_formants + energy_voice_harmonics

        bass_to_voice_ratio = energy_bass / voice_total_energy if voice_total_energy > 0 else 0.0

        high_to_voice_ratio = (energy_high_mid + energy_high) / voice_total_energy if voice_total_energy > 0 else 0.0

        background_music_energy = energy_bass + energy_high_mid + energy_high
        background_music_ratio = background_music_energy / total_energy if total_energy > 0 else 0.0

        return SpectrumFeatures(
            voice_ratio=float(voice_ratio),
            voice_formants_ratio=float(voice_formants_ratio),
            bass_to_voice_ratio=float(bass_to_voice_ratio),
            high_to_voice_ratio=float(high_to_voice_ratio),
            spectral_variation=float(spectral_coefficient_variation),
            background_music_ratio=float(background_music_ratio),
            ratio_voice_formants=float(ratio_voice_formants),
            ratio_bass=float(ratio_bass),
            ratio_high=float(ratio_high),
        )
