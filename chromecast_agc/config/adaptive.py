"""Adaptive threshold management based on user adjustments."""

from typing import Optional

from .settings import Settings


class AdaptiveThresholds:
    """Manages adaptive thresholds that learn from manual adjustments."""

    def __init__(self, settings: Settings):
        """Initialize adaptive thresholds."""
        self.settings = settings
        self.threshold_loud = settings.threshold_loud
        self.threshold_quiet = settings.threshold_quiet
        self.user_set_volume: Optional[int] = None

    def adjust_for_volume(
        self,
        volume: int,
        current_db: float,
        previous_volume: Optional[int] = None,
    ) -> None:
        """
        Adjust thresholds based on user-set volume.

        Args:
            volume: Volume set by user
            current_db: Current audio level in dB
            previous_volume: Previous volume (if exists)
        """
        self.user_set_volume = volume

        if previous_volume is None:
            previous_volume = volume

        if current_db != 0.0 and previous_volume is not None:
            volume_change = volume - previous_volume

            if volume_change > 0 and current_db < self.threshold_quiet:
                adjustment = min(5, (self.threshold_quiet - current_db) / 2)
                self.threshold_quiet = min(-20, self.threshold_quiet + adjustment)
            elif volume_change < 0 and current_db > self.threshold_loud:
                adjustment = min(5, (current_db - self.threshold_loud) / 2)
                self.threshold_loud = max(-25, self.threshold_loud - adjustment)

        if volume > 70:
            self.threshold_quiet = min(-25, self.threshold_quiet + 1)
        elif volume < 40:
            self.threshold_loud = max(-20, self.threshold_loud - 1)

    def get_threshold_loud(self) -> float:
        """Get current loud threshold."""
        return self.threshold_loud

    def get_threshold_quiet(self) -> float:
        """Get current quiet threshold."""
        return self.threshold_quiet

    def reset(self) -> None:
        """Reset thresholds to initial values."""
        self.threshold_loud = self.settings.threshold_loud
        self.threshold_quiet = self.settings.threshold_quiet
        self.user_set_volume = None
