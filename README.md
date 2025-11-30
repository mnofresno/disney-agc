# Chromecast Automatic Gain Control (AGC)

An intelligent Python script that automatically adjusts Chromecast volume based on real-time audio analysis from your microphone. The system uses spectral analysis to distinguish between dialogue and music, ensuring optimal listening experience without manual intervention.

## Overview

This project solves a common problem: when watching content on Chromecast, dialogue can be too quiet while background music or action scenes are too loud. The script continuously monitors the audio output (captured via microphone), analyzes its spectral characteristics, and automatically adjusts the Chromecast volume accordingly.

### Key Features

- **Intelligent Audio Classification**: Uses FFT-based spectral analysis to distinguish between:
  - **Dialogue**: Automatically increases volume when human speech is detected
  - **Music**: Automatically decreases volume when music is detected
  - **Unknown**: Maintains current volume when classification is uncertain

- **Persistent Connection**: Uses `pychromecast` for fast, persistent connection to Chromecast devices (no HTTP delays)

- **Manual Override**: 
  - Arrow keys (↑↓) for manual volume adjustment
  - Manual adjustments pause automatic adjustments for 10 seconds
  - Manual volume can exceed automatic baseline limits

- **Adaptive Thresholds**: Automatically adjusts sensitivity based on your manual volume preferences

- **Real-time Status Display**: Shows current volume, audio level (dB), detected audio type, and manual/auto mode

- **Cross-platform Support**: Works on macOS, Linux, and Windows with appropriate keyboard input handling

## How It Works

1. **Audio Capture**: Continuously captures audio from your microphone at 44.1 kHz
2. **Spectral Analysis**: Performs FFT analysis to extract frequency characteristics:
   - Voice formants (500-2000 Hz) - key indicator of dialogue
   - Bass frequencies (20-200 Hz) - more present in music
   - High frequencies (8000+ Hz) - instruments and brightness
   - Background music ratio - distinguishes sung songs from pure dialogue
3. **Classification**: Scores audio samples to determine if they're dialogue or music based on:
   - Energy distribution across frequency bands
   - Spectral variation
   - Presence of background music
4. **Volume Adjustment**: 
   - Aggressively increases volume for dialogue (priority: ensure dialogue is audible)
   - Moderately decreases volume for music
   - Respects baseline maximum volume limits for automatic adjustments

## Installation

### Prerequisites

- Python 3.7 or higher
- A Chromecast device on your network
- A microphone (built-in or external)

### Dependencies

The script will attempt to auto-install dependencies, but you can also install them manually:

**macOS:**
```bash
pip3 install --user numpy sounddevice pychromecast pynput
```

**Linux/Windows:**
```bash
pip3 install --user numpy sounddevice pychromecast keyboard
```

### macOS Permissions

On macOS, you'll need to grant microphone permissions:
1. Go to **System Preferences > Security & Privacy > Microphone**
2. Enable access for **Terminal** (or your IDE if running from one)

For keyboard input in non-terminal environments, you may also need:
- **System Preferences > Security & Privacy > Accessibility**
- Enable access for Terminal/Python

## Usage

### Basic Usage

```bash
python3 chromecast-agc.py
```

This will:
- Search for a Chromecast device named "AceituTele" (default)
- Start capturing audio from the default microphone
- Begin automatic volume adjustment

### Specify Chromecast Device

```bash
python3 chromecast-agc.py -d "Living Room TV"
```

### List Available Audio Devices

```bash
python3 chromecast-agc.py --list-devices
```

### Advanced Configuration

```bash
python3 chromecast-agc.py \
  --device "My Chromecast" \
  --volume-min 20 \
  --volume-max 80 \
  --volume-baseline-max 70 \
  --threshold-loud -15 \
  --threshold-quiet -35 \
  --target-db -20 \
  --step 5
```

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `-d, --device` | `AceituTele` | Chromecast device name |
| `--volume-min` | `20` | Minimum volume (0-100) |
| `--volume-max` | `80` | Maximum volume (0-100) |
| `--volume-baseline-max` | `70` | Maximum baseline volume for automatic adjustments (manual can exceed this) |
| `--threshold-loud` | `-15` | dB threshold for "too loud" |
| `--threshold-quiet` | `-35` | dB threshold for "too quiet" |
| `--target-db` | `-20` | Target audio level in dB (adjustable baseline) |
| `--step` | `5` | Volume adjustment step size (1-10) |
| `--list-devices` | - | List available audio input devices and exit |
| `--device-index` | `None` | Use specific audio device by index |

## Interactive Controls

While the script is running:

- **↑ (Up Arrow)**: Increase volume manually (+2%)
- **↓ (Down Arrow)**: Decrease volume manually (-2%)
- **+ or =**: Increase audio baseline threshold (+1 dB)
- **-**: Decrease audio baseline threshold (-1 dB)
- **Ctrl+C**: Exit gracefully

Manual volume adjustments pause automatic adjustments for 10 seconds to respect your preferences.

## Status Display

The script displays a real-time status line showing:

```
Volumen: 45% (max: 70%) | Audio: -28.3 dB | Tipo: Dialogue (85%) | Auto | ↑↓ Volumen | +/- Baseline
```

- **Volumen**: Current Chromecast volume percentage
- **max**: Maximum baseline volume (automatic adjustments won't exceed this)
- **Audio**: Current audio level in decibels
- **Tipo**: Detected audio type (Dialogue/Music/Unknown) with confidence percentage
- **Manual/Auto**: Current mode (Manual shows remaining pause time)

## Technical Details

### Audio Analysis

The script uses Fast Fourier Transform (FFT) to analyze audio in the following frequency bands:

- **Bass (20-200 Hz)**: More prominent in music
- **Voice Fundamental (200-500 Hz)**: Fundamental frequency of human voice
- **Voice Formants (500-2000 Hz)**: Primary voice formants (critical for dialogue detection)
- **Voice Harmonics (2000-4000 Hz)**: Upper voice harmonics
- **High Mid (4000-8000 Hz)**: Brightness and some harmonics
- **High (8000+ Hz)**: Brightness and high percussion

### Classification Algorithm

The classification uses a scoring system based on:

1. **Voice formants ratio**: High ratio with low background music → dialogue
2. **Voice energy ratio**: Total voice energy (200-4000 Hz) vs total energy
3. **Bass to voice ratio**: Low ratio → dialogue, high ratio → music
4. **Background music ratio**: Presence of bass + high frequencies
5. **Spectral variation**: Lower variation → dialogue, higher → music

The algorithm prioritizes dialogue detection to ensure speech is always audible, even with weak signals captured from distance (optimized for ~6 meters).

### Connection Management

- Uses persistent `pychromecast` connection for fast volume adjustments
- Falls back to `catt` command-line tool if persistent connection fails
- Automatic reconnection on connection loss

## Limitations

- Requires microphone access to capture audio output
- Works best when microphone is positioned to capture TV/Chromecast audio
- Classification accuracy depends on audio quality and signal strength
- May require fine-tuning of thresholds for your specific environment

## Troubleshooting

### Chromecast Not Found

- Ensure Chromecast and computer are on the same network
- Check the device name matches exactly (case-sensitive)
- Try listing devices with `pychromecast` or Google Home app

### No Audio Detection

- Check microphone permissions (especially on macOS)
- Verify microphone is working: `python3 chromecast-agc.py --list-devices`
- Try specifying device index: `--device-index 1`

### Keyboard Controls Not Working

**macOS:**
- If running in Terminal, should work without additional permissions
- If running in IDE, may need Accessibility permissions
- Try running from Terminal directly

**Linux:**
- May require root permissions for global keyboard hooks
- Consider using terminal-based input (ANSI sequences)

### Volume Adjustments Too Aggressive

- Increase `--step` value for smaller adjustments
- Adjust `--volume-baseline-max` to limit maximum automatic volume
- Use manual adjustments to train the adaptive thresholds

## License

This project is provided as-is for personal use.

## Contributing

Contributions are welcome! Areas for improvement:
- Machine learning-based classification
- Support for multiple Chromecast devices
- Web interface for configuration
- Better handling of mixed audio (dialogue + music)
- Calibration mode for environment-specific tuning

