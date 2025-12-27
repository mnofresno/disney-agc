"""Audio history management."""

from collections import deque
from typing import Optional

import numpy as np

from ..audio.classifier import AudioTypeResult
from ..config.settings import Settings


class HistoryManager:
    """Manages history of audio levels and types."""

    def __init__(self, settings: Settings):
        """Initialize history manager."""
        self.smoothing_window = settings.smoothing_window
        self.audio_levels = deque(maxlen=settings.smoothing_window)
        self.audio_types = deque(maxlen=settings.smoothing_window)

    def add_audio_level(self, db: float) -> None:
        """Add audio level to history."""
        self.audio_levels.append(db)

    def add_audio_type(self, type_result: AudioTypeResult) -> None:
        """Add classification result to history."""
        self.audio_types.append(type_result)

    def get_avg_audio_level(self) -> float:
        """Get average of audio levels."""
        if not self.audio_levels:
            return 0.0
        return float(np.mean(list(self.audio_levels)))

    def get_recent_avg_audio_level(self, n: int = 2) -> float:
        """Get average of last n levels."""
        if len(self.audio_levels) < n:
            return self.get_avg_audio_level()
        recent = list(self.audio_levels)[-n:]
        return float(np.mean(recent))

    def get_predominant_audio_type(self) -> Optional[AudioTypeResult]:
        """
        Get predominant audio type from history.

        Returns:
            AudioTypeResult with predominant type, or None if insufficient history
        """
        if len(self.audio_types) < 2:
            if len(self.audio_types) == 1:
                result = self.audio_types[0]
                if result.confidence > 0.3:
                    return result
            return None

        type_counts = {"dialogue": 0, "music": 0, "unknown": 0}
        total_confidence = {"dialogue": 0.0, "music": 0.0}

        for type_result in list(self.audio_types):
            audio_type = type_result.type
            confidence = type_result.confidence
            type_counts[audio_type] += 1
            if audio_type in ["dialogue", "music"]:
                total_confidence[audio_type] += confidence

        if type_counts["dialogue"] > 0 and type_counts["dialogue"] >= type_counts["music"]:
            avg_confidence = total_confidence["dialogue"] / type_counts["dialogue"] if type_counts["dialogue"] > 0 else 0.0
            return AudioTypeResult(
                type="dialogue",
                confidence=avg_confidence,
                features=None,
                scores={"dialogue": avg_confidence, "music": 0.0},
            )
        elif type_counts["music"] > 0 and type_counts["music"] >= type_counts["dialogue"]:
            avg_confidence = total_confidence["music"] / type_counts["music"] if type_counts["music"] > 0 else 0.0
            return AudioTypeResult(
                type="music",
                confidence=avg_confidence,
                features=None,
                scores={"dialogue": 0.0, "music": avg_confidence},
            )
        else:
            return None

    def clear(self) -> None:
        """Clear history."""
        self.audio_levels.clear()
        self.audio_types.clear()
