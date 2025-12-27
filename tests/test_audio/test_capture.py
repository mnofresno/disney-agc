"""Tests for audio capture."""

from unittest.mock import MagicMock, patch

from chromecast_agc.audio.capture import AudioCapture


def test_capture_initialization(test_settings):
    """Test audio capture initialization."""
    capture = AudioCapture(test_settings)

    assert capture.settings == test_settings
    assert capture.sample_rate == test_settings.sample_rate
    assert capture.chunk_size == int(test_settings.sample_rate * test_settings.chunk_duration)
    assert capture.stream is None
    assert capture.running is False


def test_capture_with_callback(test_settings):
    """Test audio capture with callback."""
    callback = MagicMock()
    capture = AudioCapture(test_settings, callback)

    assert capture.callback == callback


@patch("chromecast_agc.audio.capture.sd")
def test_capture_start(mock_sd, test_settings):
    """Test starting audio capture."""
    capture = AudioCapture(test_settings)
    mock_stream = MagicMock()
    mock_sd.InputStream.return_value = mock_stream

    capture.start()

    assert capture.running is True
    mock_sd.InputStream.assert_called_once()
    mock_stream.start.assert_called_once()


def test_capture_start_already_running(test_settings):
    """Test starting capture when already running."""
    capture = AudioCapture(test_settings)
    capture.running = True

    capture.start()

    assert capture.running is True


def test_capture_stop(test_settings):
    """Test stopping audio capture."""
    capture = AudioCapture(test_settings)
    mock_stream = MagicMock()
    capture.stream = mock_stream
    capture.running = True

    capture.stop()

    assert capture.running is False
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()
    assert capture.stream is None


def test_capture_stop_no_stream(test_settings):
    """Test stopping when no stream exists."""
    capture = AudioCapture(test_settings)
    capture.running = True

    capture.stop()

    assert capture.running is False


def test_audio_callback(test_settings):
    """Test audio callback."""
    callback = MagicMock()
    capture = AudioCapture(test_settings, callback)
    capture.running = True

    mock_indata = MagicMock()
    mock_indata.__getitem__.return_value = [0.1, 0.2, 0.3]

    capture._audio_callback(mock_indata, 100, None, None)

    callback.assert_called_once()


def test_audio_callback_not_running(test_settings):
    """Test callback when not running."""
    callback = MagicMock()
    capture = AudioCapture(test_settings, callback)
    capture.running = False

    capture._audio_callback(None, 100, None, None)

    callback.assert_not_called()
