"""Platform detection utilities."""

import platform
from typing import Any, Optional


def is_macos() -> bool:
    """Check if system is macOS."""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if system is Linux."""
    return platform.system() == "Linux"


def is_windows() -> bool:
    """Check if system is Windows."""
    return platform.system() == "Windows"


def get_keyboard_module() -> Optional[Any]:
    """Get appropriate keyboard module for platform."""
    if is_macos():
        try:
            import pynput

            return pynput
        except ImportError:
            return None
    else:
        try:
            import keyboard

            return keyboard
        except ImportError:
            return None


def get_pynput_keyboard() -> Optional[Any]:
    """Get pynput.keyboard module if available."""
    if is_macos():
        try:
            from pynput import keyboard as pynput_keyboard

            return pynput_keyboard
        except ImportError:
            return None
    return None
