"""Volume control based on audio type."""

from .controller import VolumeController
from .limits import VolumeLimits
from .strategy import DialogueStrategy, MusicStrategy, VolumeStrategy

__all__ = [
    "DialogueStrategy",
    "MusicStrategy",
    "VolumeController",
    "VolumeLimits",
    "VolumeStrategy",
]
