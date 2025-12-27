"""Tests for Chromecast controller interface."""

import pytest

from chromecast_agc.chromecast.controller import ChromecastController


def test_controller_is_abstract():
    """Test that ChromecastController is abstract."""
    with pytest.raises(TypeError):
        ChromecastController()  # noqa
