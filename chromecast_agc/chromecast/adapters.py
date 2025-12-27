"""Adapters for different Chromecast backends."""

import subprocess
from typing import Optional

from .controller import ChromecastController


class PyChromecastAdapter(ChromecastController):
    """Implementation using pychromecast (persistent connection)."""

    def __init__(self):
        """Initialize adapter."""
        self.cast = None
        self.browser = None
        self._connected = False

    def connect(self, device_name: str) -> bool:
        """Connect using pychromecast."""
        try:
            import pychromecast

            # Try method with name filter
            try:
                chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[device_name])
                self.browser = browser
            except Exception:
                # If fails, try general discovery and filter manually
                chromecasts, browser = pychromecast.get_chromecasts()
                self.browser = browser
                # Filter by name
                chromecasts = [
                    cc
                    for cc in chromecasts
                    if (cc.name == device_name or (hasattr(cc, "cast_info") and cc.cast_info.friendly_name == device_name))
                ]

            if not chromecasts:
                if self.browser:
                    self.browser.stop_discovery()
                return False

            self.cast = chromecasts[0]
            self.cast.wait()
            self._connected = True
            return True
        except Exception:
            try:
                if self.browser:
                    self.browser.stop_discovery()
            except Exception:
                pass
            return False

    def disconnect(self) -> None:
        """Disconnect."""
        if self.cast:
            try:
                self.cast.disconnect()
            except Exception:
                pass
        if self.browser:
            try:
                self.browser.stop_discovery()
            except Exception:
                pass
        self._connected = False

    def get_volume(self) -> Optional[int]:
        """Get volume from pychromecast."""
        if not self._connected or not self.cast:
            return None

        try:
            # Use persistent connection (very fast)
            # Wait for status to be available
            if not self.cast.status:
                self.cast.wait()

            volume = self.cast.status.volume_level
            if volume is not None:
                return int(volume * 100)  # Convert from 0.0-1.0 to 0-100
        except AttributeError:
            # If status not available, try another way
            try:
                volume = self.cast.volume_level
                if volume is not None:
                    return int(volume * 100)
            except Exception:
                pass
        except Exception:
            pass

        return None

    def set_volume(self, volume: int) -> bool:
        """Set volume using pychromecast."""
        if not self._connected or not self.cast:
            return False

        try:
            # Use persistent connection (very fast, no HTTP delay)
            volume_normalized = volume / 100.0  # Convert from 0-100 to 0.0-1.0
            # Ensure cast is connected before setting volume
            if not self.cast.socket_client or not self.cast.socket_client.is_connected:
                self.cast.wait()
            self.cast.set_volume(volume_normalized)
            return True
        except Exception:
            # Try reconnecting
            try:
                self.cast.wait()
                volume_normalized = volume / 100.0
                self.cast.set_volume(volume_normalized)
                return True
            except Exception:
                self._connected = False
                return False

    def is_connected(self) -> bool:
        """Check connection."""
        return self._connected


class CattAdapter(ChromecastController):
    """Implementation using catt as fallback."""

    def __init__(self, device_name: str):
        """
        Initialize catt adapter.

        Args:
            device_name: Chromecast device name
        """
        self.device_name = device_name
        self._connected = False

    def connect(self, device_name: str) -> bool:
        """Connect using catt (only verifies availability)."""
        # catt doesn't require explicit connection
        try:
            result = subprocess.run(
                ["catt", "-d", device_name, "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self._connected = result.returncode == 0
            return self._connected
        except FileNotFoundError:
            # catt not installed
            return False
        except Exception:
            return False

    def disconnect(self) -> None:
        """Disconnect (no-op for catt)."""
        self._connected = False

    def get_volume(self) -> Optional[int]:
        """Get volume using catt."""
        try:
            result = subprocess.run(
                ["catt", "-d", self.device_name, "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Volume:"):
                        volume_str = line.split(":")[1].strip()
                        return int(volume_str)
            return None
        except FileNotFoundError:
            return None
        except Exception:
            return None

    def set_volume(self, volume: int) -> bool:
        """Set volume using catt."""
        try:
            subprocess.run(
                ["catt", "-d", self.device_name, "volume", str(volume)],
                capture_output=True,
                timeout=5,
            )
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def is_connected(self) -> bool:
        """Check connection."""
        return self._connected
