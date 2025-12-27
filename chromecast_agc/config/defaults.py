"""Default values and predefined configurations."""

from .settings import Settings


def get_default_settings() -> Settings:
    """Get default configuration."""
    return Settings()


def get_settings_for_distance(distance_meters: float = 6.0) -> Settings:
    """
    Get configuration optimized for a specific distance.

    Optimized for 6m distance with ~15.5 dB attenuation.
    Values tuned for weak signals captured from distance.

    Args:
        distance_meters: Distance in meters from microphone to TV

    Returns:
        Settings optimized for the specified distance
    """
    return Settings(
        device_name="AceituTele",
        volume_min=20,
        volume_max=85,
        volume_baseline_max=75,
        target_db=-25.0,
        threshold_loud=-20.0,
        threshold_quiet=-45.0,
        adjustment_step=6,
        min_adjustment_interval=0.3,
        manual_pause_duration=10.0,
        sample_rate=44100,
        chunk_duration=0.4,
        smoothing_window=5,
        normalization_target_rms=0.15,
        normalization_max_factor=20.0,
        silence_threshold_db=-65.0,
    )
