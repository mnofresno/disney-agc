"""Chromecast connection management."""

from typing import Callable, Optional

from .controller import ChromecastController


class ChromecastConnection:
    """Manages connection to a Chromecast device."""

    def __init__(
        self,
        controller: ChromecastController,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize connection."""
        self.controller = controller
        self.status_callback = status_callback
        self.device_name: Optional[str] = None

    def connect(self, device_name: str) -> bool:
        """
        Connect to specified Chromecast device.

        Args:
            device_name: Chromecast device name

        Returns:
            True if connection was successful
        """
        self.device_name = device_name

        if self.status_callback:
            self.status_callback(f"Searching for Chromecast '{device_name}'...")

        success = self.controller.connect(device_name)

        if success:
            if self.status_callback:
                self.status_callback(f"Connected to {device_name}")
        else:
            if self.status_callback:
                self.status_callback(f"Error: Chromecast '{device_name}' not found")

        return success

    def disconnect(self) -> None:
        """Disconnect from device."""
        self.controller.disconnect()
        if self.status_callback:
            self.status_callback("Disconnected from Chromecast")

    def is_connected(self) -> bool:
        """Check if connected."""
        return self.controller.is_connected()
