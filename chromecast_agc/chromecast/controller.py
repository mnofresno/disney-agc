"""Abstract interface for Chromecast control."""

from abc import ABC, abstractmethod
from typing import Optional


class ChromecastController(ABC):
    """Abstract interface for Chromecast control."""

    @abstractmethod
    def connect(self, device_name: str) -> bool:
        """Connect to Chromecast device."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from device."""
        pass

    @abstractmethod
    def get_volume(self) -> Optional[int]:
        """Get current volume (0-100)."""
        pass

    @abstractmethod
    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        pass
