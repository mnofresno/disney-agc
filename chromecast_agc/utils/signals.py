"""System signal handling for graceful cleanup."""

import signal
from typing import Callable, Optional

_cleanup_callback: Optional[Callable[[], None]] = None


def setup_signal_handlers(cleanup_callback: Callable[[], None]) -> None:
    """
    Setup signal handlers for graceful cleanup.

    Args:
        cleanup_callback: Function to call when SIGINT or SIGTERM is received
    """
    global _cleanup_callback
    _cleanup_callback = cleanup_callback

    def _signal_handler(signum, frame):
        if _cleanup_callback:
            _cleanup_callback()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
