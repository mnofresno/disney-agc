#!/usr/bin/env python3
"""
Script to automatically adjust Chromecast volume
based on audio analysis captured from the microphone.

Intelligent detection:
- Detects dialogue and automatically increases volume
- Detects music and automatically decreases volume
- Uses spectral analysis to distinguish between audio types

Enhanced features:
- Persistent connection to Chromecast using pychromecast (faster)
- Spectral analysis to distinguish dialogue from music
- Interactive baseline control with up/down arrows
- Manual volume override (pauses automatic adjustment for 10 seconds)
"""

import subprocess
import time
import sys
import signal
import argparse
import threading
import os
from collections import deque

def install_dependencies():
    """Installs necessary dependencies using different methods."""
    import os
    import tempfile
    import platform
    
    print("Installing necessary dependencies...")
    
    # On macOS, use pynput instead of keyboard (more compatible)
    is_macos = platform.system() == "Darwin"
    if is_macos:
        dependencies = ["numpy", "sounddevice", "pychromecast", "pynput"]
    else:
        dependencies = ["numpy", "sounddevice", "pychromecast", "keyboard"]
    
    # Try with pipx if available
    if subprocess.run(["which", "pipx"], capture_output=True).returncode == 0:
        print("Using pipx to install dependencies...")
        try:
            # pipx doesn't install packages directly, we need to use pip in a venv
            venv_path = os.path.join(os.path.expanduser("~"), ".local", "chromecast_venv")
            if not os.path.exists(venv_path):
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
            pip_path = os.path.join(venv_path, "bin", "pip")
            subprocess.run([pip_path, "install"] + dependencies, check=True)
            # Update sys.path to use the venv
            site_packages = os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
            if os.path.exists(site_packages):
                sys.path.insert(0, site_packages)
        except subprocess.CalledProcessError:
            pass
    
    # Try with pip --user
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user"] + dependencies, 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # Last resort: use --break-system-packages (with warning)
        print("⚠️  Using --break-system-packages (may require permissions)")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + dependencies, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            print("\nPlease install manually:")
            print(f"  pip3 install --user {' '.join(dependencies)}")
            sys.exit(1)

try:
    import numpy as np
    import sounddevice as sd
    import pychromecast
    import platform
    is_macos = platform.system() == "Darwin"
    if is_macos:
        import pynput
        from pynput import keyboard as pynput_keyboard
        keyboard_module = None
    else:
        import keyboard
        keyboard_module = keyboard
        pynput = None
except ImportError:
    install_dependencies()
    import numpy as np
    import sounddevice as sd
    import pychromecast
    import platform
    is_macos = platform.system() == "Darwin"
    if is_macos:
        import pynput
        from pynput import keyboard as pynput_keyboard
        keyboard_module = None
    else:
        import keyboard
        keyboard_module = keyboard
        pynput = None


class ChromecastVolumeController:
    def __init__(self, device_name="AceituTele", 
                 sample_rate=44100, 
                 chunk_duration=0.5,  # Increased from 0.3 for more spectral information
                 volume_min=20,
                 volume_max=80,
                 volume_baseline_max=70,  # Maximum baseline volume that will never be exceeded
                 target_db=-20,
                 threshold_loud=-15,
                 threshold_quiet=-35,
                 adjustment_step=5,
                 smoothing_window=7):  # Increased from 5 for better averaging with weak signals
        """
        Initializes the Chromecast volume controller.
        
        Args:
            device_name: Chromecast device name
            sample_rate: Audio sampling rate (Hz)
            chunk_duration: Duration of each audio chunk to analyze (seconds)
            volume_min: Minimum allowed volume (0-100)
            volume_max: Maximum allowed volume (0-100)
            volume_baseline_max: Maximum baseline volume that will never be exceeded (0-100)
            target_db: Target decibel level (adjustable baseline)
            threshold_loud: Decibel threshold to consider "too loud"
            threshold_quiet: Decibel threshold to consider "too quiet"
            adjustment_step: Volume adjustment step size (1-10)
            smoothing_window: Smoothing window for averaging levels
        """
        self.device_name = device_name
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.volume_min = volume_min
        self.volume_max = volume_max
        self.volume_baseline_max = volume_baseline_max  # Maximum baseline volume (never exceeded)
        self.target_db = target_db  # Dynamically adjustable baseline
        self.threshold_loud = threshold_loud
        self.threshold_quiet = threshold_quiet
        self.adjustment_step = adjustment_step
        self.smoothing_window = smoothing_window
        
        # History of audio levels for smoothing
        self.audio_levels = deque(maxlen=smoothing_window)
        
        # History of detected audio types for stability
        self.audio_types = deque(maxlen=smoothing_window)
        self.current_audio_type = 'unknown'
        self.audio_type_confidence = 0.0
        
        # Current state
        self.current_volume = None
        self.running = True
        self.last_adjustment_time = 0
        self.min_adjustment_interval = 0.5  # Wait at least 0.5 seconds between adjustments (faster)
        
        # Manual volume control (override)
        self.manual_adjustment_time = 0
        self.manual_pause_duration = 10.0  # Pause automatic adjustment for 10 seconds after manual adjustment
        self.user_set_volume = None  # Volume set by user (reference)
        
        # Persistent connection to Chromecast
        self.cast = None
        self.cast_connected = False
        self.browser = None
        
        # Lock for thread-safe access to target_db and volume
        self.target_db_lock = threading.Lock()
        self.volume_lock = threading.Lock()
        
        # Current status line state
        self.status_line = ""
        self.last_message = ""  # Last keyboard message for clean rendering
        
        # Signal handling for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handles interrupt signals for clean exit."""
        self.running = False
        if self.cast:
            try:
                self.cast.disconnect()
            except:
                pass
        if self.browser:
            try:
                self.browser.stop_discovery()
            except:
                pass
    
    def _update_status_line(self, message):
        """Updates the single status line without creating new lines."""
        # Clear the previous line and any pending messages
        clear_length = max(len(self.status_line), len(self.last_message))
        sys.stdout.write('\r' + ' ' * clear_length + '\r')
        # Write the new message
        sys.stdout.write(message)
        sys.stdout.flush()
        self.status_line = message
        self.last_message = ""
    
    def _update_status_line_immediate(self):
        """Updates the status line immediately with current information."""
        with self.target_db_lock:
            current_target = self.target_db
        current_db = self._get_avg_audio_level()
        with self.volume_lock:
            current_vol = self.current_volume if self.current_volume is not None else 0
        
        # Calculate remaining manual pause time
        manual_pause_remaining = max(0, self.manual_pause_duration - (time.time() - self.manual_adjustment_time))
        manual_status = f"Manual: {manual_pause_remaining:.0f}s" if manual_pause_remaining > 0 else "Auto"
        
        # Show detected audio type
        audio_type_display = self.current_audio_type.capitalize()
        if self.current_audio_type != 'unknown':
            audio_type_display += f" ({self.audio_type_confidence:.0%})"
        
        # Build status message (includes maximum baseline volume)
        status_msg = (f"Volume: {current_vol}% (max: {self.volume_baseline_max}%) | "
                    f"Audio: {current_db:.1f} dB | Type: {audio_type_display} | "
                    f"{manual_status} | ↑↓ Volume | +/- Baseline")
        
        # Update the status line
        self._update_status_line(status_msg)
    
    def _adjust_thresholds_for_volume(self, volume):
        """Adjusts audio thresholds based on the volume set by the user."""
        # User set a specific volume, use this as reference
        # Get current audio level to understand context
        current_db = self._get_avg_audio_level()
        
        # Save previous volume for comparison
        previous_volume = self.user_set_volume if self.user_set_volume is not None else self.current_volume
        
        # Save user volume as reference
        self.user_set_volume = volume
        
        # Dynamically adjust thresholds based on user volume and current audio
        # If user increases volume when audio is low, they need more sensitivity to low audio
        # If user decreases volume when audio is high, they need more sensitivity to high audio
        
        # Smarter adjustment: consider both volume and current audio level
        if current_db != 0.0 and previous_volume is not None:  # Only if we have valid reading and previous volume
            volume_change = volume - previous_volume
            
            # If user increases volume and audio is low, increase sensitivity to low audio
            if volume_change > 0 and current_db < self.threshold_quiet:
                # User increased volume: adjust threshold_quiet upward
                # Adjustment is proportional to how low current audio is
                adjustment = min(5, (self.threshold_quiet - current_db) / 2)
                self.threshold_quiet = min(-20, self.threshold_quiet + adjustment)
            
            # If user decreases volume and audio is high, increase sensitivity to high audio
            elif volume_change < 0 and current_db > self.threshold_loud:
                # User decreased volume: adjust threshold_loud downward
                # Adjustment is proportional to how high current audio is
                adjustment = min(5, (current_db - self.threshold_loud) / 2)
                self.threshold_loud = max(-25, self.threshold_loud - adjustment)
        
        # Also adjust based on absolute volume as fallback
        if volume > 70:
            # High volume: be more sensitive to low audio
            self.threshold_quiet = min(-25, self.threshold_quiet + 1)
        elif volume < 40:
            # Low volume: be more sensitive to high audio
            self.threshold_loud = max(-20, self.threshold_loud - 1)
    
    def _connect_to_chromecast(self):
        """Connects to Chromecast using pychromecast (persistent connection)."""
        try:
            self._update_status_line(f"Searching for Chromecast '{self.device_name}'...")
            
            # Try method with name filter
            try:
                chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[self.device_name])
                self.browser = browser
            except Exception as e:
                # If it fails, try general discovery and filter manually
                chromecasts, browser = pychromecast.get_chromecasts()
                self.browser = browser
                # Filter by name
                chromecasts = [cc for cc in chromecasts if cc.name == self.device_name or 
                              (hasattr(cc, 'cast_info') and cc.cast_info.friendly_name == self.device_name)]
            
            if not chromecasts:
                self._update_status_line(f"Error: Chromecast '{self.device_name}' not found")
                if self.browser:
                    self.browser.stop_discovery()
                return False
            
            self.cast = chromecasts[0]
            # Get cast name safely
            cast_name = self.device_name
            if hasattr(self.cast, 'name'):
                cast_name = self.cast.name
            elif hasattr(self.cast, 'cast_info') and hasattr(self.cast.cast_info, 'friendly_name'):
                cast_name = self.cast.cast_info.friendly_name
            
            self._update_status_line(f"Connecting to {cast_name}...")
            self.cast.wait()
            self.cast_connected = True
            
            return True
        except Exception as e:
            self._update_status_line(f"Error connecting to Chromecast: {e}")
            try:
                if self.browser:
                    self.browser.stop_discovery()
            except:
                pass
            return False
    
    def get_current_volume(self):
        """Gets the current Chromecast volume using persistent connection."""
        if self.cast_connected and self.cast:
            try:
                # Use persistent connection (very fast)
                # Wait for status to be available
                if not self.cast.status:
                    self.cast.wait()
                
                volume = self.cast.status.volume_level
                if volume is not None:
                    return int(volume * 100)  # Convert from 0.0-1.0 to 0-100
            except AttributeError:
                # If status is not available, try to get it another way
                try:
                    volume = self.cast.volume_level
                    if volume is not None:
                        return int(volume * 100)
                except:
                    pass
            except Exception as e:
                pass
        
        # Fallback to catt if persistent connection fails
        try:
            result = subprocess.run(
                ["catt", "-d", self.device_name, "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Volume:'):
                        volume_str = line.split(':')[1].strip()
                        return int(volume_str)
            return None
        except FileNotFoundError:
            # catt is not installed, not critical if we have persistent connection
            return None
        except Exception as e:
            return None
    
    def set_volume(self, volume):
        """Sets the Chromecast volume using persistent connection."""
        # Apply limits: never exceed volume_baseline_max (except manual adjustments)
        volume = max(self.volume_min, min(self.volume_max, volume))
        # Maximum baseline volume is applied in adjust_volume_based_on_type, not here
        # to allow manual adjustments that may exceed it
        
        if self.cast_connected and self.cast:
            try:
                # Use persistent connection (very fast, no HTTP delay)
                volume_normalized = volume / 100.0  # Convert from 0-100 to 0.0-1.0
                # Make sure cast is connected before setting volume
                if not self.cast.socket_client or not self.cast.socket_client.is_connected:
                    self.cast.wait()
                self.cast.set_volume(volume_normalized)
                self.current_volume = volume
                return True
            except Exception as e:
                # Try to reconnect
                try:
                    self.cast.wait()
                    volume_normalized = volume / 100.0
                    self.cast.set_volume(volume_normalized)
                    self.current_volume = volume
                    return True
                except:
                    self.cast_connected = False
        
        # Fallback to catt if persistent connection fails
        try:
            subprocess.run(
                ["catt", "-d", self.device_name, "volume", str(volume)],
                capture_output=True,
                timeout=5
            )
            self.current_volume = volume
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            return False
    
    def calculate_db_level(self, audio_data):
        """Calculates the decibel level of the audio."""
        # Calculate RMS (Root Mean Square)
        rms = np.sqrt(np.mean(audio_data**2))
        
        # Convert to decibels (avoid log(0))
        if rms > 0:
            db = 20 * np.log10(rms)
        else:
            db = -np.inf
        
        return db
    
    def analyze_audio_type(self, audio_data):
        """
        Analyzes the audio type to distinguish between dialogue and music.
        Optimized to work with weak signals captured from distance.
        
        Returns:
            dict with:
                - 'type': 'dialogue', 'music', or 'unknown'
                - 'confidence': 0.0 to 1.0
                - 'features': dict with audio characteristics
        """
        # Normalize audio to compensate for weak signals (useful when far away)
        # This helps maintain relative spectral characteristics even with weak signal
        audio_rms = np.sqrt(np.mean(audio_data**2))
        if audio_rms > 0:
            # Normalize to a standard level for more stable spectral analysis
            normalization_factor = 0.1 / audio_rms  # Normalize to ~0.1 RMS
            audio_data_normalized = audio_data * min(normalization_factor, 10.0)  # Limit amplification
        else:
            audio_data_normalized = audio_data
        
        # Calculate FFT for spectral analysis
        fft = np.fft.rfft(audio_data_normalized)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio_data_normalized), 1.0 / self.sample_rate)
        
        # Important frequency bands:
        # - Bass (20-200 Hz): more present in music (bass, low percussion)
        # - Voice fundamental (200-500 Hz): fundamental frequency of human voice
        # - Voice formants (500-2000 Hz): main voice formants (very important for dialogue)
        # - Voice harmonics (2000-4000 Hz): upper voice harmonics
        # - High mid (4000-8000 Hz): brightness, some harmonics
        # - High (8000+ Hz): brightness, high percussion
        
        # Frequency indices (adjusted for better voice detection)
        idx_bass = (freqs >= 20) & (freqs < 200)  # Reduced from 250 to exclude voice fundamental
        idx_voice_fundamental = (freqs >= 200) & (freqs < 500)  # New band for voice fundamental
        idx_voice_formants = (freqs >= 500) & (freqs < 2000)  # Main formants (very important)
        idx_voice_harmonics = (freqs >= 2000) & (freqs < 4000)  # Voice harmonics
        idx_high_mid = (freqs >= 4000) & (freqs < 8000)
        idx_high = freqs >= 8000
        
        # Energy in each band
        energy_bass = np.sum(magnitude[idx_bass]) if np.any(idx_bass) else 0
        energy_voice_fundamental = np.sum(magnitude[idx_voice_fundamental]) if np.any(idx_voice_fundamental) else 0
        energy_voice_formants = np.sum(magnitude[idx_voice_formants]) if np.any(idx_voice_formants) else 0
        energy_voice_harmonics = np.sum(magnitude[idx_voice_harmonics]) if np.any(idx_voice_harmonics) else 0
        energy_high_mid = np.sum(magnitude[idx_high_mid]) if np.any(idx_high_mid) else 0
        energy_high = np.sum(magnitude[idx_high]) if np.any(idx_high) else 0
        
        total_energy = energy_bass + energy_voice_fundamental + energy_voice_formants + energy_voice_harmonics + energy_high_mid + energy_high
        
        if total_energy == 0:
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'features': {}
            }
        
        # Normalized energy ratios
        ratio_bass = energy_bass / total_energy
        ratio_voice_fundamental = energy_voice_fundamental / total_energy
        ratio_voice_formants = energy_voice_formants / total_energy
        ratio_voice_harmonics = energy_voice_harmonics / total_energy
        ratio_high_mid = energy_high_mid / total_energy
        ratio_high = energy_high / total_energy
        
        # Characteristics to distinguish dialogue vs music:
        # 1. Dialogue has more energy in voice frequencies (200-4000 Hz)
        # 2. Music has more energy in bass and highs
        # 3. Music has more spectral variation
        # 4. Dialogue has energy more concentrated in voice band
        
        # Calculate spectral variation (standard deviation of magnitude)
        spectral_variance = np.std(magnitude)
        spectral_mean = np.mean(magnitude)
        spectral_coefficient_variation = spectral_variance / spectral_mean if spectral_mean > 0 else 0
        
        # Full voice energy ratio (200-4000 Hz) vs total - broader to better capture voice
        voice_energy = energy_voice_fundamental + energy_voice_formants + energy_voice_harmonics
        voice_ratio = voice_energy / total_energy
        
        # Voice formants energy ratio (500-2000 Hz) - very specific for dialogue
        voice_formants_ratio = energy_voice_formants / total_energy
        
        # Total voice energy (for comparisons)
        voice_total_energy = energy_voice_fundamental + energy_voice_formants + energy_voice_harmonics
        
        # Bass to voice energy ratio (higher in music)
        bass_to_voice_ratio = energy_bass / voice_total_energy if voice_total_energy > 0 else 0
        
        # High to voice energy ratio (higher in music)
        high_to_voice_ratio = (energy_high_mid + energy_high) / voice_total_energy if voice_total_energy > 0 else 0
        
        # Calculate total background music energy (bass + highs)
        # This is key to distinguish sung songs (voice + music) from pure dialogue (voice only)
        background_music_energy = energy_bass + energy_high_mid + energy_high
        background_music_ratio = background_music_energy / total_energy if total_energy > 0 else 0
        
        # Características combinadas
        features = {
            'voice_ratio': voice_ratio,
            'voice_formants_ratio': voice_formants_ratio,
            'bass_to_voice_ratio': bass_to_voice_ratio,
            'high_to_voice_ratio': high_to_voice_ratio,
            'spectral_variation': spectral_coefficient_variation,
            'ratio_voice_formants': ratio_voice_formants,
            'ratio_bass': ratio_bass,
            'ratio_high': ratio_high,
            'background_music_ratio': background_music_ratio
        }
        
        # Classification based on characteristics
        # Dialogue: high voice_ratio, high voice_formants_ratio, low bass_to_voice_ratio, low spectral_variation
        # Music: low voice_ratio, low voice_formants_ratio, high bass_to_voice_ratio, high spectral_variation
        # SUNG SONGS: voice (formants) + background music (bass + highs)
        
        dialogue_score = 0.0
        music_score = 0.0
        
        # Scoring for dialogue (VERY SENSITIVE - maximum priority)
        # Based on known spectral characteristics of human voice:
        # - Human voice: 300-3400 Hz (telephone band)
        # - Main formants: 500-2000 Hz (very specific)
        # - Low energy in bass (<200 Hz) and highs (>4000 Hz)
        # - WITHOUT significant background music
        
        # Voice formants (500-2000 Hz) are VERY specific to dialogue
        # BUT only if there is NOT much background music (if there is background music, it's a sung song)
        if voice_formants_ratio > 0.10 and background_music_ratio < 0.25:  # Voice without background music
            dialogue_score += 0.8  # Very high weight - most important characteristic
        elif voice_formants_ratio > 0.10:  # There is voice but also background music
            dialogue_score += 0.3  # Reduced weight - probably a sung song
        if voice_formants_ratio > 0.15 and background_music_ratio < 0.20:
            dialogue_score += 0.5
        if voice_formants_ratio > 0.20 and background_music_ratio < 0.15:
            dialogue_score += 0.3
        if voice_formants_ratio > 0.25 and background_music_ratio < 0.10:
            dialogue_score += 0.2
        
        # Dialogue has more energy in voice frequencies (200-4000 Hz)
        if voice_ratio > 0.15:  # Very sensitive - any voice detected
            dialogue_score += 0.6
        if voice_ratio > 0.25:
            dialogue_score += 0.4
        if voice_ratio > 0.35:
            dialogue_score += 0.3
        
        # Dialogue has little bass compared to voice (key characteristic)
        if bass_to_voice_ratio < 1.5:  # Less restrictive for weak signals
            dialogue_score += 0.3
        if bass_to_voice_ratio < 0.8:
            dialogue_score += 0.3
        if bass_to_voice_ratio < 0.5:
            dialogue_score += 0.2
        
        # Dialogue has less spectral variation than music
        if spectral_coefficient_variation < 2.0:  # Less restrictive
            dialogue_score += 0.2
        if spectral_coefficient_variation < 1.2:
            dialogue_score += 0.3
        if spectral_coefficient_variation < 0.8:
            dialogue_score += 0.2
        
        # High energy in voice formants (very specific to dialogue)
        if ratio_voice_formants > 0.12:  # Very sensitive
            dialogue_score += 0.4
        if ratio_voice_formants > 0.18:
            dialogue_score += 0.3
        
        # Dialogue has less energy in highs than music
        if ratio_high < 0.35:  # More permissive
            dialogue_score += 0.2
        if ratio_high < 0.25:
            dialogue_score += 0.1
        
        # Scoring for music (adjusted to detect sung songs)
        # Sung songs have voice BUT also have background music
        
        # If there is voice BUT also much background music, it's a sung song
        # This is the key to distinguish sung songs from pure dialogue
        if voice_formants_ratio > 0.10 and background_music_ratio > 0.25:
            # There is voice AND background music = sung song
            music_score += 0.8  # Very high weight - key characteristic
        if voice_formants_ratio > 0.10 and background_music_ratio > 0.35:
            music_score += 0.5
        if voice_formants_ratio > 0.15 and background_music_ratio > 0.30:
            music_score += 0.4
        
        # Much bass compared to voice (background music)
        if bass_to_voice_ratio > 0.4:  # Reduced to be more sensitive
            music_score += 0.4
        if bass_to_voice_ratio > 0.6:
            music_score += 0.3
        if bass_to_voice_ratio > 0.8:
            music_score += 0.2
        
        # High energy in highs compared to voice (instruments, brightness)
        if high_to_voice_ratio > 0.6:  # Reduced to be more sensitive
            music_score += 0.3
        if high_to_voice_ratio > 0.9:
            music_score += 0.3
        if high_to_voice_ratio > 1.2:
            music_score += 0.2
        
        # High spectral variation (music has more variation than dialogue)
        if spectral_coefficient_variation > 0.8:  # Reduced to be more sensitive
            music_score += 0.3
        if spectral_coefficient_variation > 1.2:
            music_score += 0.3
        if spectral_coefficient_variation > 1.8:
            music_score += 0.2
        
        # Background music present (bass + highs)
        if background_music_ratio > 0.20:  # Background music detected
            music_score += 0.4
        if background_music_ratio > 0.30:
            music_score += 0.3
        if background_music_ratio > 0.40:
            music_score += 0.2
        
        # If there is little energy in voice band (instrumental music)
        if voice_ratio < 0.3:
            music_score += 0.2
        if voice_ratio < 0.2:
            music_score += 0.2
        
        # Music has little in voice formants (pure instrumental music)
        if voice_formants_ratio < 0.15:
            music_score += 0.2
        if voice_formants_ratio < 0.10:
            music_score += 0.2
        
        # Normalize scores
        total_score = dialogue_score + music_score
        if total_score > 0:
            dialogue_score /= total_score
            music_score /= total_score
        
        # Determine type and confidence
        # Priority: pure dialogue (without background music) vs sung songs (voice + music)
        dialogue_threshold = 0.20  # VERY low - maximum priority on pure dialogue
        music_threshold = 0.40  # Reduced to better detect sung songs
        
        # If there is voice BUT also significant background music, prioritize music
        # (it's a sung song, not pure dialogue)
        if voice_formants_ratio > 0.10 and background_music_ratio > 0.25:
            # There is voice AND background music = sung song
            if music_score > 0.30:  # Low threshold for sung songs
                audio_type = 'music'
                confidence = music_score
            elif dialogue_score > music_score and dialogue_score > dialogue_threshold:
                audio_type = 'dialogue'
                confidence = dialogue_score
            else:
                audio_type = 'music'  # By default, if there is background music, it's music
                confidence = music_score if music_score > 0 else 0.5
        # If there is voice WITHOUT significant background music, prioritize dialogue
        elif dialogue_score > music_score and dialogue_score > dialogue_threshold:
            audio_type = 'dialogue'
            confidence = dialogue_score
        elif music_score > dialogue_score and music_score > music_threshold:
            audio_type = 'music'
            confidence = music_score
        else:
            # If neither exceeds threshold but there is a clear preference, use that
            # Priority to dialogue if there is NO background music, music if there IS background music
            if background_music_ratio > 0.25 and music_score > 0.25:
                # There is background music, prioritize music
                audio_type = 'music'
                confidence = music_score
            elif dialogue_score > music_score and dialogue_score > 0.15:
                audio_type = 'dialogue'
                confidence = dialogue_score
            elif music_score > dialogue_score and music_score > 0.30:
                audio_type = 'music'
                confidence = music_score
            else:
                audio_type = 'unknown'
                confidence = max(dialogue_score, music_score)
        
        return {
            'type': audio_type,
            'confidence': confidence,
            'features': features,
            'scores': {
                'dialogue': dialogue_score,
                'music': music_score
            }
        }
    
    def adjust_volume_based_on_type(self, db_level, audio_type_info):
        """
        Adjusts volume based on detected audio type (dialogue vs music).
        Only adjusts when dialogue or music is detected. Respects user's manual volume.
        
        Args:
            db_level: Audio decibel level
            audio_type_info: Dict with audio type information (from analyze_audio_type)
        """
        current_time = time.time()
        
        # Detect total silence (very low audio level)
        # Adjusted for weak signals captured from distance (6 meters)
        is_silence = db_level < -60 or db_level == -np.inf  # More permissive: -60 dB instead of -50
        
        audio_type = audio_type_info.get('type', 'unknown')
        confidence = audio_type_info.get('confidence', 0.0)
        
        # If type is unknown, do NOT adjust automatically
        # Respect the volume that user set manually
        if audio_type == 'unknown' and not is_silence:
            return
        
        # If user adjusted volume manually recently, pause automatic adjustment
        # Only when dialogue or music is detected (to avoid immediate adjustments after manual adjustment)
        if audio_type in ['dialogue', 'music']:
            if current_time - self.manual_adjustment_time < self.manual_pause_duration:
                return
        
        # For silence, reduce minimum interval for faster response
        min_interval = 0.3 if is_silence else self.min_adjustment_interval
        
        # Avoid very frequent adjustments (except in silence)
        if current_time - self.last_adjustment_time < min_interval:
            return
        
        if self.current_volume is None:
            self.current_volume = self.get_current_volume()
            if self.current_volume is None:
                return
        
        adjustment = 0
        
        # If there is silence, increase volume quickly (so it's audible when audio returns)
        if is_silence:
            adjustment = int(self.adjustment_step * 2)
        
        # PRIORITY: If we detect dialogue, increase volume aggressively
        # Very low threshold (0.25) to work with weak signals from distance
        # Maximum priority: ensure dialogue is audible
        elif audio_type == 'dialogue' and confidence > 0.25:
            # Increase volume for dialogue - VERY AGGRESSIVE
            # Maximum priority: dialogue must be heard well
            base_threshold = 0.25
            # More aggressive multiplier: up to 3x when confidence = 1.0
            multiplier = 1.5 + (confidence - base_threshold) * 2.0  # 1.5 to 3.0 when confidence = 1.0
            adjustment = int(self.adjustment_step * multiplier)
        
        # If we detect music, decrease volume moderately
        # Less aggressive since it's not critical if lyrics are heard
        elif audio_type == 'music' and confidence > 0.5:
            # Decrease volume for music - MODERATE
            # Not critical if lyrics aren't heard well
            base_threshold = 0.5
            multiplier = 0.8 + (confidence - base_threshold) * 0.8  # 0.8 to 1.2 when confidence = 1.0
            adjustment = -int(self.adjustment_step * multiplier)
        
        if adjustment != 0:
            new_volume = self.current_volume + adjustment
            
            # APPLY LIMIT: Never exceed volume_baseline_max in automatic adjustments
            # (Manual adjustments can exceed it)
            if new_volume > self.volume_baseline_max:
                new_volume = self.volume_baseline_max
            
            if self.set_volume(new_volume):
                self.last_adjustment_time = current_time
                # Adjustment log (optional, for debugging)
                # print(f"  [Adjustment] Type: {audio_type} ({confidence:.2f}) | Change: {adjustment:+d} | New: {new_volume}%")
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback to process audio chunks."""
        if not self.running:
            return
        
        # Calculate decibel level
        db_level = self.calculate_db_level(indata[:, 0])
        
        # Detect silence immediately (without waiting for average)
        # Adjusted for weak signals captured from distance
        is_silence = db_level < -60 or db_level == -np.inf  # More permissive: -60 dB
        
        # Add to history for smoothing
        self.audio_levels.append(db_level)
        
        # Analyze audio type (dialogue vs music)
        if not is_silence:
            audio_type_info = self.analyze_audio_type(indata[:, 0])
            self.audio_types.append(audio_type_info)
            
            # Determine predominant audio type from history
            # Reduced from 3 to 2 samples to respond faster with weak signals
            if len(self.audio_types) >= 2:
                # Count types in recent history
                type_counts = {'dialogue': 0, 'music': 0, 'unknown': 0}
                total_confidence = {'dialogue': 0.0, 'music': 0.0}
                
                for at_info in list(self.audio_types):
                    at_type = at_info.get('type', 'unknown')
                    confidence = at_info.get('confidence', 0.0)
                    type_counts[at_type] += 1
                    if at_type in ['dialogue', 'music']:
                        total_confidence[at_type] += confidence
                
                # Determine predominant type (more permissive for weak signals)
                # If there is at least one clear detection, use it even if there is 'unknown'
                if type_counts['dialogue'] > 0 and type_counts['dialogue'] >= type_counts['music']:
                    self.current_audio_type = 'dialogue'
                    self.audio_type_confidence = total_confidence['dialogue'] / type_counts['dialogue'] if type_counts['dialogue'] > 0 else 0.0
                elif type_counts['music'] > 0 and type_counts['music'] >= type_counts['dialogue']:
                    self.current_audio_type = 'music'
                    self.audio_type_confidence = total_confidence['music'] / type_counts['music'] if type_counts['music'] > 0 else 0.0
                else:
                    self.current_audio_type = 'unknown'
                    self.audio_type_confidence = 0.0
            else:
                # Use last analysis if there isn't enough history (more permissive)
                # If it has reasonable confidence, use it directly
                if audio_type_info.get('confidence', 0.0) > 0.3:
                    self.current_audio_type = audio_type_info.get('type', 'unknown')
                    self.audio_type_confidence = audio_type_info.get('confidence', 0.0)
                else:
                    self.current_audio_type = 'unknown'
                    self.audio_type_confidence = 0.0
        else:
            # For silence, use unknown type
            self.current_audio_type = 'unknown'
            self.audio_type_confidence = 0.0
        
        # Create audio type info for adjustment
        audio_type_info = {
            'type': self.current_audio_type,
            'confidence': self.audio_type_confidence
        }
        
        # For weak signals from distance, be more permissive with number of samples
        # If we detect something with reasonable confidence, act faster
        
        # For silence, respond immediately without waiting for average
        if is_silence and len(self.audio_levels) >= 1:
            self.adjust_volume_based_on_type(db_level, audio_type_info)
        # If we detect dialogue or music with reasonable confidence, act with fewer samples
        elif (self.current_audio_type in ['dialogue', 'music'] and 
              self.audio_type_confidence > 0.4 and 
              len(self.audio_levels) >= 2):
            # With 2 samples and good confidence, act fast
            recent_avg = np.mean(list(self.audio_levels)[-2:])
            self.adjust_volume_based_on_type(recent_avg, audio_type_info)
        # For normal audio, use history average for more stable decisions
        elif len(self.audio_levels) >= 3:
            avg_db = np.mean(list(self.audio_levels))
            self.adjust_volume_based_on_type(avg_db, audio_type_info)
        # For very loud audio or detected music, respond faster (with fewer samples)
        elif len(self.audio_levels) >= 2:
            recent_avg = np.mean(list(self.audio_levels)[-2:])
            # Respond fast if it's music or if audio is very loud
            if recent_avg > self.threshold_loud or self.current_audio_type == 'music':
                self.adjust_volume_based_on_type(recent_avg, audio_type_info)
    
    def list_audio_devices(self):
        """Lists available audio devices."""
        import platform
        is_macos = platform.system() == "Darwin"
        
        print("\nAvailable audio devices:")
        print(sd.query_devices())
        
        if is_macos:
            print("\n💡 Note for macOS:")
            print("   - Make sure you've granted microphone permissions to Terminal/Python")
            print("   - Go to: System Preferences > Security & Privacy > Microphone")
            print("   - If using an IDE, it may also need permissions")
    
    def _get_avg_audio_level(self):
        """Gets the audio average safely."""
        if self.audio_levels:
            return np.mean(list(self.audio_levels))
        return 0.0
    
    def _keyboard_listener(self):
        """Listens for arrow keys to adjust volume and baseline."""
        import platform
        import select
        import termios
        import tty
        is_macos = platform.system() == "Darwin"
        
        # Check if stdin is an interactive terminal
        is_tty = sys.stdin.isatty()
        
        try:
            # If we're in an interactive terminal, use direct stdin reading
            # This captures ANSI sequences of arrow keys without needing permissions
            if is_tty:
                # Save original terminal configuration
                old_settings = termios.tcgetattr(sys.stdin)
                
                try:
                    # Configure terminal in raw mode to capture individual keys
                    tty.setraw(sys.stdin.fileno())
                    
                    # Configure stdin in non-blocking mode
                    import fcntl
                    flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
                    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
                    
                    # Buffer to accumulate escape sequences
                    buffer = b''
                    last_char_time = time.time()
                    waiting_for_ansi = False
                    
                    while self.running:
                        try:
                            # Try to read a character (non-blocking)
                            char = sys.stdin.buffer.read(1)
                            
                            if char:
                                last_char_time = time.time()
                                buffer += char
                                waiting_for_ansi = False
                                
                                # Process simple keys immediately
                                if len(buffer) == 1:
                                    if buffer == b'+' or buffer == b'=':
                                        with self.target_db_lock:
                                            self.target_db += 1.0
                                        self._update_status_line_immediate()
                                        buffer = b''
                                    elif buffer == b'-':
                                        with self.target_db_lock:
                                            self.target_db -= 1.0
                                        self._update_status_line_immediate()
                                        buffer = b''
                                    elif buffer == b'\x03':  # Ctrl+C
                                        self.running = False
                                        break
                                    elif buffer == b'\x1b':  # ESC - start of ANSI sequence
                                        # Wait for more characters for complete sequence
                                        waiting_for_ansi = True
                                        continue
                                    else:
                                        # Normal characters we're not interested in
                                        buffer = b''
                                
                                # Process ANSI sequences for arrow keys
                                # Format: ESC [ A (up), ESC [ B (down)
                                elif len(buffer) >= 3:
                                    if buffer[:2] == b'\x1b[':
                                        if buffer[2:3] == b'A':  # Up arrow
                                            with self.volume_lock:
                                                if self.current_volume is not None:
                                                    new_vol = min(self.volume_max, self.current_volume + 2)
                                                    if self.set_volume(new_vol):
                                                        self.manual_adjustment_time = time.time()
                                                        self._adjust_thresholds_for_volume(new_vol)
                                                        self._update_status_line_immediate()
                                            buffer = b''
                                        elif buffer[2:3] == b'B':  # Down arrow
                                            with self.volume_lock:
                                                if self.current_volume is not None:
                                                    new_vol = max(self.volume_min, self.current_volume - 2)
                                                    if self.set_volume(new_vol):
                                                        self.manual_adjustment_time = time.time()
                                                        self._adjust_thresholds_for_volume(new_vol)
                                                        self._update_status_line_immediate()
                                            buffer = b''
                                        elif buffer[2:3] == b'C':  # Right arrow (not used but clear buffer)
                                            buffer = b''
                                        elif buffer[2:3] == b'D':  # Left arrow (not used but clear buffer)
                                            buffer = b''
                                        else:
                                            # Unknown sequence, clear buffer after a while
                                            if len(buffer) > 10:
                                                buffer = b''
                                    else:
                                        # Not a sequence we're interested in, clear
                                        buffer = b''
                                
                                # Clear buffer if it accumulates too much (invalid sequence)
                                if len(buffer) > 10:
                                    buffer = b''
                            else:
                                # No data available
                                if waiting_for_ansi:
                                    # If we're waiting for an ANSI sequence, give more time
                                    if time.time() - last_char_time > 0.05:
                                        # If enough time has passed, process what we have
                                        if len(buffer) >= 3 and buffer[:2] == b'\x1b[':
                                            # We have a complete ANSI sequence
                                            if buffer[2:3] == b'A':  # Up arrow
                                                with self.volume_lock:
                                                    if self.current_volume is not None:
                                                        new_vol = min(self.volume_max, self.current_volume + 2)
                                                        if self.set_volume(new_vol):
                                                            self.manual_adjustment_time = time.time()
                                                            self._adjust_thresholds_for_volume(new_vol)
                                                            self._update_status_line_immediate()
                                                buffer = b''
                                                waiting_for_ansi = False
                                            elif buffer[2:3] == b'B':  # Down arrow
                                                with self.volume_lock:
                                                    if self.current_volume is not None:
                                                        new_vol = max(self.volume_min, self.current_volume - 2)
                                                        if self.set_volume(new_vol):
                                                            self.manual_adjustment_time = time.time()
                                                            self._adjust_thresholds_for_volume(new_vol)
                                                            self._update_status_line_immediate()
                                                buffer = b''
                                                waiting_for_ansi = False
                                            else:
                                                # Unknown sequence, clear
                                                buffer = b''
                                                waiting_for_ansi = False
                                        elif len(buffer) == 1 and buffer == b'\x1b':
                                            # We only have ESC, wait a bit more
                                            if time.time() - last_char_time > 0.1:
                                                # Timeout, clear
                                                buffer = b''
                                                waiting_for_ansi = False
                                elif buffer and time.time() - last_char_time > 0.1:
                                    # If too much time passed without new characters, clear buffer
                                    buffer = b''
                                
                        except BlockingIOError:
                            # No data available, continue
                            if waiting_for_ansi:
                                if time.time() - last_char_time > 0.05:
                                    # Process ANSI sequence if we have enough
                                    if len(buffer) >= 3 and buffer[:2] == b'\x1b[':
                                        if buffer[2:3] == b'A':  # Up arrow
                                            with self.volume_lock:
                                                if self.current_volume is not None:
                                                    new_vol = min(self.volume_max, self.current_volume + 2)
                                                    if self.set_volume(new_vol):
                                                        self.manual_adjustment_time = time.time()
                                                        self._adjust_thresholds_for_volume(new_vol)
                                                        self._update_status_line_immediate()
                                            buffer = b''
                                            waiting_for_ansi = False
                                        elif buffer[2:3] == b'B':  # Down arrow
                                            with self.volume_lock:
                                                if self.current_volume is not None:
                                                    new_vol = max(self.volume_min, self.current_volume - 2)
                                                    if self.set_volume(new_vol):
                                                        self.manual_adjustment_time = time.time()
                                                        self._adjust_thresholds_for_volume(new_vol)
                                                        self._update_status_line_immediate()
                                            buffer = b''
                                            waiting_for_ansi = False
                                    elif len(buffer) == 1 and buffer == b'\x1b':
                                        if time.time() - last_char_time > 0.1:
                                            buffer = b''
                                            waiting_for_ansi = False
                            elif buffer and time.time() - last_char_time > 0.1:
                                buffer = b''
                        
                        # Small pause to not consume CPU
                        time.sleep(0.01)
                
                finally:
                    # Restore original terminal configuration
                    try:
                        fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags)
                    except:
                        pass
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            # Fallback: use pynput if we're not in a terminal or if direct reading fails
            elif is_macos and pynput:
                # Use pynput on macOS when not in interactive terminal
                listener = None
                
                def on_press(key):
                    try:
                        if key == pynput_keyboard.Key.up:
                            # Up arrow: increase volume
                            with self.volume_lock:
                                if self.current_volume is not None:
                                    new_vol = min(self.volume_max, self.current_volume + 2)
                                    if self.set_volume(new_vol):
                                        self.manual_adjustment_time = time.time()
                                        self._adjust_thresholds_for_volume(new_vol)
                                        self._update_status_line_immediate()
                        elif key == pynput_keyboard.Key.down:
                            # Down arrow: decrease volume
                            with self.volume_lock:
                                if self.current_volume is not None:
                                    new_vol = max(self.volume_min, self.current_volume - 2)
                                    if self.set_volume(new_vol):
                                        self.manual_adjustment_time = time.time()
                                        self._adjust_thresholds_for_volume(new_vol)
                                        self._update_status_line_immediate()
                        elif hasattr(key, 'char') and key.char:
                            # Modifier keys for baseline
                            if key.char == '+' or key.char == '=':
                                with self.target_db_lock:
                                    self.target_db += 1.0
                                self._update_status_line_immediate()
                            elif key.char == '-':
                                with self.target_db_lock:
                                    self.target_db -= 1.0
                                self._update_status_line_immediate()
                    except AttributeError:
                        pass
                    except Exception as e:
                        pass
                
                try:
                    listener = pynput_keyboard.Listener(on_press=on_press, suppress=False)
                    listener.start()
                    time.sleep(0.2)
                    
                    while self.running:
                        if listener and not listener.running:
                            try:
                                listener.stop()
                                time.sleep(0.1)
                                listener = pynput_keyboard.Listener(on_press=on_press, suppress=False)
                                listener.start()
                                time.sleep(0.2)
                            except Exception:
                                pass
                        time.sleep(0.1)
                    
                    if listener:
                        try:
                            listener.stop()
                        except:
                            pass
                except Exception as e:
                    print(f"\n❌ Error starting keyboard listener: {e}")
                    while self.running:
                        time.sleep(0.1)
                        
            elif keyboard_module:
                # Use keyboard on Linux/Windows
                def on_key_event(event):
                    try:
                        if event.event_type == keyboard_module.KEY_DOWN:
                            if event.name == 'up':
                                # Up arrow: increase volume
                                with self.volume_lock:
                                    if self.current_volume is not None:
                                        new_vol = min(self.volume_max, self.current_volume + 2)
                                        if self.set_volume(new_vol):
                                            self.manual_adjustment_time = time.time()
                                            self._adjust_thresholds_for_volume(new_vol)
                                            self._update_status_line_immediate()
                            elif event.name == 'down':
                                # Down arrow: decrease volume
                                with self.volume_lock:
                                    if self.current_volume is not None:
                                        new_vol = max(self.volume_min, self.current_volume - 2)
                                        if self.set_volume(new_vol):
                                            self.manual_adjustment_time = time.time()
                                            self._adjust_thresholds_for_volume(new_vol)
                                            self._update_status_line_immediate()
                            elif event.name == '+' or event.name == '=':
                                with self.target_db_lock:
                                    self.target_db += 1.0
                                self._update_status_line_immediate()
                            elif event.name == '-':
                                with self.target_db_lock:
                                    self.target_db -= 1.0
                                self._update_status_line_immediate()
                    except Exception as e:
                        pass
                
                # Hook to capture keys without blocking
                try:
                    keyboard_module.hook(on_key_event)
                    
                    # Keep listener active while script runs
                    while self.running:
                        time.sleep(0.1)
                except Exception as e:
                    print(f"\n❌ Error starting keyboard listener: {e}")
                    while self.running:
                        time.sleep(0.1)
            else:
                print("\n⚠️  No keyboard module found.")
                print("   Arrow keys will not work.")
                while self.running:
                    time.sleep(0.1)
        except Exception as e:
            print(f"\n❌ Critical error in keyboard listener: {e}")
            while self.running:
                time.sleep(0.1)
    
    def run(self, device_index=None):
        """Runs the volume controller."""
        import platform
        is_macos = platform.system() == "Darwin"
        
        # Informative message about keyboard control
        if is_macos:
            print("\n💡 Keyboard control:")
            print("   - Arrows ↑↓: Manually adjust volume")
            print("   - Keys +/-: Adjust audio baseline")
            if sys.stdin.isatty():
                print("   - Works directly from Terminal (no additional permissions needed)\n")
            else:
                print("   - If it doesn't work, it may need accessibility permissions")
                print("   - Go to: System Preferences > Security & Privacy > Accessibility")
                print("   - And enable Terminal or Python as appropriate\n")
        
        # Connect to Chromecast using persistent connection
        if not self._connect_to_chromecast():
            self._update_status_line("Error: Could not connect to Chromecast")
            return
        
        # Get initial volume
        self.current_volume = self.get_current_volume()
        if self.current_volume is None:
            self._update_status_line("Error: Could not get initial volume")
            return
        
        # Start keyboard listener in a separate thread
        keyboard_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
        keyboard_thread.start()
        
        # Give time for listener to start
        time.sleep(0.5)
        
        # Verify thread is alive
        if not keyboard_thread.is_alive():
            print("\n⚠️  Warning: Keyboard listener thread is not active.")
            if is_macos:
                print("   This may indicate missing accessibility permissions.")
        
        try:
            # Start audio capture
            with sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=self.audio_callback,
                dtype=np.float32
            ):
                last_status_time = time.time()
                
                while self.running:
                    # Update status line periodically
                    if time.time() - last_status_time > 0.5:
                        with self.target_db_lock:
                            current_target = self.target_db
                        current_db = self._get_avg_audio_level()
                        with self.volume_lock:
                            current_vol = self.current_volume if self.current_volume is not None else 0
                        
                        # Calculate remaining manual pause time
                        manual_pause_remaining = max(0, self.manual_pause_duration - (time.time() - self.manual_adjustment_time))
                        manual_status = f"Manual: {manual_pause_remaining:.0f}s" if manual_pause_remaining > 0 else "Auto"
                        
                        # Show detected audio type
                        audio_type_display = self.current_audio_type.capitalize()
                        if self.current_audio_type != 'unknown':
                            audio_type_display += f" ({self.audio_type_confidence:.0%})"
                        
                        # Show status (includes maximum baseline volume)
                        status_msg = (f"Volume: {current_vol}% (max: {self.volume_baseline_max}%) | "
                                    f"Audio: {current_db:.1f} dB | Type: {audio_type_display} | "
                                    f"{manual_status} | ↑↓ Volume | +/- Baseline")
                        self._update_status_line(status_msg)
                        last_status_time = time.time()
                    
                    time.sleep(0.1)
        except KeyboardInterrupt:
            self.running = False
        except Exception as e:
            self._update_status_line(f"Error capturing audio: {e}")
            time.sleep(2)
        finally:
            # Clean up connection
            sys.stdout.write('\r' + ' ' * len(self.status_line) + '\r')
            sys.stdout.flush()
            if self.cast:
                try:
                    self.cast.disconnect()
                except:
                    pass
            if self.browser:
                try:
                    self.browser.stop_discovery()
                except:
                    pass
            try:
                if keyboard_module:
                    keyboard_module.unhook_all()
                elif pynput:
                    # pynput doesn't require explicit unhook, listener stops automatically
                    pass
            except:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Automatically adjusts Chromecast volume based on microphone audio"
    )
    parser.add_argument(
        "-d", "--device",
        default="AceituTele",
        help="Chromecast device name (default: AceituTele)"
    )
    parser.add_argument(
        "--volume-min",
        type=int,
        default=20,
        help="Minimum allowed volume (default: 20)"
    )
    parser.add_argument(
        "--volume-max",
        type=int,
        default=80,
        help="Maximum allowed volume (default: 80)"
    )
    parser.add_argument(
        "--volume-baseline-max",
        type=int,
        default=70,
        help="Maximum baseline volume that will never be exceeded in automatic adjustments (default: 70)"
    )
    parser.add_argument(
        "--threshold-loud",
        type=float,
        default=-15,
        help="Decibel threshold to consider 'too loud' (default: -15)"
    )
    parser.add_argument(
        "--threshold-quiet",
        type=float,
        default=-35,
        help="Decibel threshold to consider 'too quiet' (default: -35)"
    )
    parser.add_argument(
        "--target-db",
        type=float,
        default=-20,
        help="Target decibel level (default: -20)"
    )
    parser.add_argument(
        "--step",
        type=int,
        default=5,
        help="Volume adjustment step size (default: 5)"
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit"
    )
    parser.add_argument(
        "--device-index",
        type=int,
        default=None,
        help="Audio device index to use (see --list-devices)"
    )
    
    args = parser.parse_args()
    
    controller = ChromecastVolumeController(
        device_name=args.device,
        volume_min=args.volume_min,
        volume_max=args.volume_max,
        volume_baseline_max=args.volume_baseline_max,
        threshold_loud=args.threshold_loud,
        threshold_quiet=args.threshold_quiet,
        target_db=args.target_db,
        adjustment_step=args.step
    )
    
    if args.list_devices:
        controller.list_audio_devices()
        return
    
    controller.run(device_index=args.device_index)


if __name__ == "__main__":
    main()
