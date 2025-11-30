# Research & Fine-Tuning Guide for Chromecast AGC

## 📚 Research Summary

### Key Standards & References

1. **EBU R 128 Standard**
   - **Target Loudness**: -23 LUFS (integrated loudness)
   - **Maximum True Peak**: -1 dBTP
   - **Loudness Range (LRA)**: 7-20 LU for TV content
   - **Application**: Use LUFS for consistent volume normalization

2. **Human Voice Characteristics**
   - **Fundamental Frequency (F0)**: 
     - Male: 85-180 Hz
     - Female: 165-255 Hz
     - Children: 250-300 Hz
   - **Formants (Critical for Speech Recognition)**:
     - **F1 (First Formant)**: 300-1000 Hz (vowel quality)
     - **F2 (Second Formant)**: 800-3000 Hz (vowel quality, most important)
     - **F3 (Third Formant)**: 2000-4000 Hz (vowel quality, voice timbre)
   - **Telephone Band**: 300-3400 Hz (standard for speech)
   - **Optimal Speech Range**: 500-2000 Hz (formants region)

3. **Distance Attenuation (6 meters)**
   - **Inverse Square Law**: Sound intensity decreases by 6 dB per doubling of distance
   - **At 6 meters from source**: Approximately -15.5 dB attenuation (vs 1 meter)
   - **Practical consideration**: Signal will be significantly weaker
   - **MacBook Pro microphone sensitivity**: Typically -38 to -42 dBV (needs amplification)

4. **FFT & Spectral Analysis Parameters**
   - **Window Size**: 0.5 seconds (current) = 22,050 samples at 44.1 kHz
   - **Frequency Resolution**: ~2 Hz (44,100 / 22,050)
   - **Time Resolution**: 0.5 seconds (good for stability, may need faster response)
   - **Window Function**: Consider Hamming or Hanning for better spectral leakage control

## 🎯 Recommended Parameter Tuning for Your Setup

### Current Configuration Analysis

**Your Setup:**
- MacBook Pro microphone at 6 meters from 32" TV
- Weak signal capture (distance attenuation)
- Need: Dialogue UP, Music DOWN

### 1. Frequency Band Adjustments

```python
# Current bands (good, but can be optimized):
idx_bass = (freqs >= 20) & (freqs < 200)        # ✅ Good
idx_voice_fundamental = (freqs >= 200) & (freqs < 500)  # ✅ Good
idx_voice_formants = (freqs >= 500) & (freqs < 2000)    # ✅ Optimal
idx_voice_harmonics = (freqs >= 2000) & (freqs < 4000)  # ✅ Good

# Recommended adjustments for weak signals:
# - Increase sensitivity to voice formants (500-2000 Hz)
# - Reduce bass threshold (music detection)
# - Add emphasis on F2 formant region (800-2000 Hz)
```

**Recommended Changes:**
- **Voice Formants**: Keep 500-2000 Hz (most critical)
- **F2 Emphasis**: Add sub-band 800-2000 Hz with higher weight
- **Bass Detection**: Lower threshold from 0.4 to 0.3 for music detection

### 2. Classification Thresholds

**Current Values:**
```python
dialogue_threshold = 0.20  # Very low - good for weak signals
music_threshold = 0.40     # Reduced for sung songs
```

**Recommended Adjustments for 6m Distance:**
```python
# More aggressive dialogue detection (weak signals)
dialogue_threshold = 0.15  # Even lower for weak signals
music_threshold = 0.35     # Slightly lower for better music detection

# Voice formants ratio thresholds (key for dialogue)
voice_formants_ratio_threshold = 0.08  # Lower from 0.10 (more sensitive)
background_music_ratio_threshold = 0.20  # Lower from 0.25 (detect music earlier)
```

### 3. Volume Adjustment Parameters

**Current Values:**
```python
adjustment_step = 5
min_adjustment_interval = 0.5  # seconds
volume_baseline_max = 70
```

**Recommended for 6m Distance:**
```python
# More aggressive dialogue boost (weak signals need more help)
dialogue_multiplier_base = 2.0  # Increase from 1.5 (more aggressive)
dialogue_multiplier_max = 3.5   # Increase from 3.0 (more headroom)

# Faster response for weak signals
min_adjustment_interval = 0.3   # Reduce from 0.5 (faster response)
adjustment_step = 6             # Increase from 5 (bigger steps for weak signals)

# Baseline volume limits
volume_baseline_max = 75        # Increase from 70 (allow higher for weak signals)
```

### 4. Audio Level Thresholds

**Current Values:**
```python
threshold_loud = -15 dB
threshold_quiet = -35 dB
target_db = -20 dB
silence_threshold = -60 dB
```

**Recommended for 6m Distance:**
```python
# Adjust for distance attenuation (~15.5 dB loss)
threshold_loud = -20 dB      # Lower from -15 (account for distance)
threshold_quiet = -45 dB     # Lower from -35 (account for distance)
target_db = -25 dB           # Lower from -20 (account for distance)
silence_threshold = -65 dB    # Lower from -60 (more permissive for weak signals)

# Normalization factor for weak signals
normalization_target_rms = 0.15  # Increase from 0.1 (more amplification)
max_normalization_factor = 15.0  # Increase from 10.0 (allow more gain)
```

### 5. Smoothing & Response Time

**Current Values:**
```python
smoothing_window = 7
chunk_duration = 0.5  # seconds
```

**Recommended Adjustments:**
```python
# Balance between stability and responsiveness
smoothing_window = 5          # Reduce from 7 (faster response)
chunk_duration = 0.4          # Reduce from 0.5 (faster analysis)

# For dialogue detection with weak signals
min_samples_for_dialogue = 2   # Keep (already optimized)
min_samples_for_music = 3     # Increase from 2 (more stable music detection)
```

## 🔬 Advanced Tuning Strategies

### 1. Adaptive Normalization

For weak signals at 6m, implement adaptive normalization based on signal strength:

```python
def adaptive_normalization(audio_data, distance_meters=6):
    """
    Adaptive normalization based on distance and signal strength.
    
    At 6 meters: ~15.5 dB attenuation
    MacBook mic sensitivity: ~-40 dBV
    Expected signal range: -50 to -30 dB
    """
    audio_rms = np.sqrt(np.mean(audio_data**2))
    
    # Distance compensation factor
    distance_attenuation_db = 20 * np.log10(distance_meters)
    compensation_factor = 10 ** (distance_attenuation_db / 20)
    
    # Adaptive normalization
    if audio_rms > 0:
        # Target RMS for analysis (compensated for distance)
        target_rms = 0.15 * compensation_factor
        normalization_factor = target_rms / audio_rms
        # Limit to prevent over-amplification
        max_factor = 20.0  # Increased for 6m distance
        normalization_factor = min(normalization_factor, max_factor)
        
        return audio_data * normalization_factor
    return audio_data
```

### 2. Formant-Based Dialogue Detection

Enhance dialogue detection using formant characteristics:

```python
def enhanced_formant_detection(magnitude, freqs):
    """
    Enhanced formant detection for weak signals.
    
    Focus on F1 (300-1000 Hz) and F2 (800-2000 Hz) regions.
    """
    # F1 region (first formant - vowel quality)
    idx_f1 = (freqs >= 300) & (freqs < 1000)
    energy_f1 = np.sum(magnitude[idx_f1]) if np.any(idx_f1) else 0
    
    # F2 region (second formant - most important for speech)
    idx_f2 = (freqs >= 800) & (freqs < 2000)
    energy_f2 = np.sum(magnitude[idx_f2]) if np.any(idx_f2) else 0
    
    # Combined formant energy (weighted)
    formant_energy = energy_f1 * 0.3 + energy_f2 * 0.7  # F2 more important
    
    return formant_energy, energy_f1, energy_f2
```

### 3. EBU R 128 Integration

Implement LUFS-based loudness measurement:

```python
def calculate_lufs(audio_data, sample_rate=44100):
    """
    Calculate LUFS (Loudness Units relative to Full Scale) per EBU R 128.
    
    Target: -23 LUFS for TV content
    """
    # Simplified LUFS calculation (full implementation requires K-weighting filter)
    # For now, use RMS-based approximation
    rms = np.sqrt(np.mean(audio_data**2))
    lufs = 20 * np.log10(rms) + 23  # Approximate LUFS
    return lufs

# Use in volume adjustment:
target_lufs = -23  # EBU R 128 standard
current_lufs = calculate_lufs(audio_data)
lufs_difference = current_lufs - target_lufs

# Adjust volume based on LUFS difference
if lufs_difference < -5:  # Too quiet
    volume_adjustment = +adjustment_step
elif lufs_difference > 5:  # Too loud
    volume_adjustment = -adjustment_step
```

## 📊 Recommended Configuration File

Create a configuration optimized for your setup:

```python
# config_6m_macbook.py

CONFIG_6M_MACBOOK = {
    # Audio capture
    'sample_rate': 44100,
    'chunk_duration': 0.4,  # Faster response
    'smoothing_window': 5,   # Faster response
    
    # Distance compensation
    'distance_meters': 6,
    'distance_attenuation_db': -15.5,
    'normalization_target_rms': 0.15,
    'max_normalization_factor': 20.0,
    
    # Frequency bands (optimized for voice)
    'voice_formants_low': 500,
    'voice_formants_high': 2000,
    'f2_emphasis_low': 800,   # F2 formant region
    'f2_emphasis_high': 2000,
    'bass_cutoff': 200,
    
    # Classification thresholds (more sensitive for weak signals)
    'dialogue_threshold': 0.15,
    'music_threshold': 0.35,
    'voice_formants_ratio_min': 0.08,  # Lower threshold
    'background_music_ratio_max': 0.20,  # Detect music earlier
    
    # Volume adjustment
    'adjustment_step': 6,
    'min_adjustment_interval': 0.3,
    'dialogue_multiplier_base': 2.0,
    'dialogue_multiplier_max': 3.5,
    'music_multiplier_base': 0.8,
    'music_multiplier_max': 1.2,
    
    # Volume limits
    'volume_min': 20,
    'volume_max': 85,  # Increased for weak signals
    'volume_baseline_max': 75,  # Increased for weak signals
    
    # Audio level thresholds (adjusted for distance)
    'threshold_loud': -20,
    'threshold_quiet': -45,
    'target_db': -25,
    'silence_threshold': -65,
    
    # Response timing
    'min_samples_for_dialogue': 2,
    'min_samples_for_music': 3,
    'confidence_threshold_dialogue': 0.25,
    'confidence_threshold_music': 0.5,
}
```

## 🧪 Testing & Calibration Procedure

### Step 1: Baseline Measurement
1. Play dialogue-only content (news, podcast)
2. Measure RMS and dB levels at MacBook mic
3. Note typical values (should be -40 to -30 dB for 6m distance)

### Step 2: Music Measurement
1. Play music-only content
2. Measure RMS and dB levels
3. Compare with dialogue levels

### Step 3: Mixed Content Testing
1. Play Disney movie with dialogue + music
2. Verify dialogue detection works
3. Verify music detection works
4. Adjust thresholds iteratively

### Step 4: Fine-Tuning
1. Start with recommended values above
2. Adjust `dialogue_threshold` if dialogue not detected
3. Adjust `music_threshold` if music not detected
4. Adjust `adjustment_step` for response speed
5. Adjust `volume_baseline_max` for comfort

## 📖 References & Further Reading

1. **EBU R 128**: European Broadcasting Union recommendation for loudness normalization
2. **Formant Frequencies**: "Acoustic Phonetics" by Kenneth N. Stevens
3. **Distance Attenuation**: Inverse square law for sound propagation
4. **FFT Analysis**: "Digital Signal Processing" by Oppenheim & Schafer
5. **Voice Activity Detection**: Various papers on VAD algorithms
6. **Dialogue Enhancement**: "Dialogue Enhancement and Listening Effort in Broadcast Audio" (arXiv:2207.14240)

## 🎯 Quick Start Tuning

For immediate improvement with your 6m MacBook setup, try these changes:

```python
# In chromecast-agc.py __init__:
chunk_duration=0.4,           # Faster (was 0.5)
smoothing_window=5,           # Faster (was 7)
adjustment_step=6,            # Bigger steps (was 5)
volume_baseline_max=75,        # Higher limit (was 70)
threshold_loud=-20,            # Lower (was -15)
threshold_quiet=-45,           # Lower (was -35)
target_db=-25,                 # Lower (was -20)

# In analyze_audio_type:
voice_formants_ratio > 0.08    # More sensitive (was 0.10)
background_music_ratio < 0.20  # Detect music earlier (was 0.25)

# In adjust_volume_based_on_type:
multiplier = 2.0 + (confidence - 0.25) * 3.0  # More aggressive (was 1.5 + ... * 2.0)
```

These changes account for the 6-meter distance and weak signal capture while maintaining system stability.

