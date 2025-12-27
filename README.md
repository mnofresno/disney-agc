# Chromecast Automatic Gain Control (AGC) 🎬🔊

**Because your kid's Disney movie shouldn't make you deaf while you're trying to work** 🎧👨‍💻

An intelligent Python script that automatically adjusts Chromecast volume based on real-time audio analysis from your microphone. The system uses spectral analysis to distinguish between dialogue and music, ensuring your daughter can hear Elsa sing "Let It Go" while you can still hear yourself think (and work) 🧠💼

## Overview

**The Problem:** Your kid is watching Disney movies on the TV, and you're trying to work nearby. The dialogue is too quiet, but when the music kicks in (you know, *that* song), it's loud enough to wake the neighbors. You're constantly reaching for the remote like a volume-control zombie 🧟‍♂️📺

**The Solution:** This script listens to what's playing, uses fancy spectral analysis to tell the difference between dialogue and music, and automatically:
- 🔊 **Turns UP** the volume when there's dialogue (so your kid can follow the story)
- 🔇 **Turns DOWN** the volume when there's music (so you don't go deaf)

No more remote control juggling. No more "CAN YOU TURN IT DOWN?!" interruptions. Just peace, quiet work time, and happy kids watching their movies 🎉

### Key Features 🎯

- **🧠 Intelligent Audio Classification**: Uses FFT-based spectral analysis (fancy math!) to distinguish between:
  - **💬 Dialogue**: Automatically cranks it UP when characters are talking (so your kid doesn't miss the plot)
  - **🎵 Music**: Automatically dials it DOWN when songs start (so you don't lose your hearing)
  - **❓ Unknown**: Keeps things stable when it's not sure (better safe than sorry)

- **⚡ Persistent Connection**: Uses `pychromecast` for lightning-fast volume changes (no annoying delays)

- **🎮 Manual Override**: 
  - Arrow keys (↑↓) for emergency volume control (because sometimes you need to take matters into your own hands)
  - Manual adjustments pause automatic mode for 10 seconds (you're the boss)
  - Manual volume can exceed automatic limits (power user mode activated)

- **🎚️ Adaptive Thresholds**: Learns from your manual adjustments (gets smarter over time, like a good assistant)

- **📊 Real-time Status Display**: Shows what's happening (volume, audio type, confidence level) so you know it's working

- **🌍 Cross-platform Support**: Works on macOS, Linux, and Windows (because work happens everywhere)

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

**Production dependencies:**
```bash
pip3 install --user -r requirements.txt
```

**Development dependencies (for testing/contributing):**
```bash
pip3 install --user -r requirements-dev.txt
```

**Platform-specific keyboard libraries:**
- macOS: `pynput` (included in requirements.txt detection)
- Linux/Windows: `keyboard` (included in requirements.txt detection)

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

## Fine-Tuning & Research

For detailed information on optimizing parameters for your specific setup (e.g., MacBook Pro at 6 meters from TV), see:

- **[TUNING_SUMMARY.md](TUNING_SUMMARY.md)**: Quick reference guide with recommended parameter changes
- **[RESEARCH_AND_TUNING.md](RESEARCH_AND_TUNING.md)**: Complete research findings, technical details, and advanced tuning strategies

### Key Research Areas Covered:
- Human voice formant frequencies (500-2000 Hz)
- Distance attenuation calculations (6 meters = ~15.5 dB loss)
- EBU R 128 loudness standards
- FFT and spectral analysis parameters
- Adaptive normalization for weak signals
- Formant-based dialogue detection

## Contributing

Contributions are welcome! Areas for improvement:
- Machine learning-based classification
- Support for multiple Chromecast devices
- Web interface for configuration
- Better handling of mixed audio (dialogue + music)
- Calibration mode for environment-specific tuning
- Integration of EBU R 128 loudness measurement

