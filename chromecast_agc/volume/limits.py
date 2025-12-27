"""Volume limits management."""

from ..config.settings import Settings


class VolumeLimits:
    """Manages volume limits (automatic vs manual)."""

    def __init__(self, settings: Settings):
        """
        Initialize volume limits.

        Args:
            settings: Application configuration
        """
        self.volume_min = settings.volume_min
        self.volume_max = settings.volume_max
        self.volume_baseline_max = settings.volume_baseline_max

    def apply_limits(self, volume: int, is_manual: bool = False) -> int:
        """
        Apply volume limits.

        Args:
            volume: Desired volume
            is_manual: If manual adjustment (can exceed baseline_max)

        Returns:
            Volume with limits applied
        """
        # Apply absolute min and max limits
        volume = max(self.volume_min, volume)
        volume = min(self.volume_max, volume)

        # Baseline limit for automatic adjustments
        # Manual adjustments can exceed this limit
        if not is_manual and volume > self.volume_baseline_max:
            volume = self.volume_baseline_max

        return volume

    def can_exceed_baseline(self, is_manual: bool) -> bool:
        """Check if baseline maximum can be exceeded."""
        return is_manual
