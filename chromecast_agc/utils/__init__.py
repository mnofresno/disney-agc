"""General utilities."""

from .dependencies import check_dependencies, install_dependencies
from .platform import get_keyboard_module, is_linux, is_macos, is_windows
from .signals import setup_signal_handlers

__all__ = [
    "check_dependencies",
    "get_keyboard_module",
    "install_dependencies",
    "is_linux",
    "is_macos",
    "is_windows",
    "setup_signal_handlers",
]
