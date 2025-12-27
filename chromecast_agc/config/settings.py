"""Application configuration."""

from dataclasses import dataclass


@dataclass
class Settings:
    """Complete application configuration."""

    device_name: str = "AceituTele"
    volume_min: int = 20
    volume_max: int = 85
    volume_baseline_max: int = 75
    target_db: float = -25.0
    threshold_loud: float = -20.0
    threshold_quiet: float = -45.0
    adjustment_step: int = 6
    min_adjustment_interval: float = 0.3
    manual_pause_duration: float = 10.0
    sample_rate: int = 44100
    chunk_duration: float = 0.4
    smoothing_window: int = 5
    normalization_target_rms: float = 0.15
    normalization_max_factor: float = 20.0
    silence_threshold_db: float = -65.0

    def validate(self) -> None:
        """Validate that values are within acceptable ranges."""
        assert 0 <= self.volume_min < self.volume_max <= 100
        assert 0 <= self.volume_baseline_max <= 100
        assert self.threshold_quiet < self.threshold_loud
        assert 0 < self.adjustment_step <= 10
        assert 0 < self.chunk_duration <= 1.0
        assert self.sample_rate > 0
        assert self.smoothing_window > 0
