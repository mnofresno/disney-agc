"""Tests for signal handling."""

import signal
from unittest.mock import MagicMock, patch

from chromecast_agc.utils.signals import setup_signal_handlers


def test_setup_signal_handlers():
    """Test setting up signal handlers."""
    callback = MagicMock()

    with patch("signal.signal") as mock_signal:
        setup_signal_handlers(callback)

        assert mock_signal.call_count == 2
        calls = [call[0][0] for call in mock_signal.call_args_list]
        assert signal.SIGINT in calls
        assert signal.SIGTERM in calls
