"""Tests for Chromecast connection."""

from unittest.mock import MagicMock

from chromecast_agc.chromecast.adapters import PyChromecastAdapter
from chromecast_agc.chromecast.connection import ChromecastConnection


def test_connection_initialization():
    """Test connection initialization."""
    controller = PyChromecastAdapter()
    conn = ChromecastConnection(controller)

    assert conn.controller == controller
    assert conn.device_name is None
    assert conn.status_callback is None


def test_connection_with_callback():
    """Test connection with status callback."""
    controller = PyChromecastAdapter()
    callback = MagicMock()
    conn = ChromecastConnection(controller, callback)

    assert conn.status_callback == callback


def test_connect_success():
    """Test successful connection."""
    controller = PyChromecastAdapter()
    controller.connect = MagicMock(return_value=True)
    callback = MagicMock()
    conn = ChromecastConnection(controller, callback)

    result = conn.connect("TestDevice")

    assert result is True
    assert conn.device_name == "TestDevice"
    callback.assert_any_call("Searching for Chromecast 'TestDevice'...")
    callback.assert_any_call("Connected to TestDevice")


def test_connect_failure():
    """Test failed connection."""
    controller = PyChromecastAdapter()
    controller.connect = MagicMock(return_value=False)
    callback = MagicMock()
    conn = ChromecastConnection(controller, callback)

    result = conn.connect("TestDevice")

    assert result is False
    callback.assert_any_call("Error: Chromecast 'TestDevice' not found")


def test_disconnect():
    """Test disconnection."""
    controller = PyChromecastAdapter()
    controller.disconnect = MagicMock()
    callback = MagicMock()
    conn = ChromecastConnection(controller, callback)

    conn.disconnect()

    controller.disconnect.assert_called_once()
    callback.assert_called_with("Disconnected from Chromecast")


def test_is_connected():
    """Test connection status check."""
    controller = PyChromecastAdapter()
    controller.is_connected = MagicMock(return_value=True)
    conn = ChromecastConnection(controller)

    assert conn.is_connected() is True
    controller.is_connected.assert_called_once()
