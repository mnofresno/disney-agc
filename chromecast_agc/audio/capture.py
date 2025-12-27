"""Audio capture from microphone."""

from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from ..config.settings import Settings


class AudioCapture:
    """Captures audio from microphone using sounddevice."""

    def __init__(
        self,
        settings: Settings,
        callback: Optional[Callable[[np.ndarray], None]] = None,
    ):
        """Initialize audio capture."""
        self.settings = settings
        self.callback = callback
        self.sample_rate = settings.sample_rate
        self.chunk_duration = settings.chunk_duration
        self.chunk_size = int(settings.sample_rate * settings.chunk_duration)
        self.stream: Optional[sd.InputStream] = None
        self.running = False

    def _audio_callback(self, indata, frames, time_info, status):
        """Internal callback to process audio chunks."""
        if not self.running:
            return

        if self.callback:
            self.callback(indata[:, 0])

    def start(self, device_index: Optional[int] = None) -> None:
        """
        Start audio capture.

        Args:
            device_index: Audio device index to use (None = default)
        """
        if self.running:
            return

        self.running = True
        self.stream = sd.InputStream(
            device=device_index,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            callback=self._audio_callback,
            dtype=np.float32,
        )
        self.stream.start()

    def stop(self) -> None:
        """Stop audio capture."""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    @staticmethod
    def list_devices() -> None:
        """List available audio devices."""
        import platform

        is_macos = platform.system() == "Darwin"

        print("\nAvailable audio devices:")
        print(sd.query_devices())

        if is_macos:
            print("\n💡 Note for macOS:")
            print("   - Make sure you've granted microphone permissions to Terminal/Python")
            print("   - Go to: System Preferences > Security & Privacy > Microphone")
            print("   - If using an IDE, it may also need permissions")
