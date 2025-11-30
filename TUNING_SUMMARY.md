# 🎯 Quick Tuning Summary for 6m MacBook Pro Setup

## The Problem
- **Distance**: 6 meters from TV to MacBook Pro
- **Signal Loss**: ~15.5 dB attenuation (sound gets weaker with distance)
- **Weak Signal**: MacBook mic captures very quiet audio
- **Need**: Detect dialogue (quiet) and music (loud) accurately

## Key Findings from Research

### 1. Human Voice Characteristics
- **Formants (speech markers)**: 500-2000 Hz (most important: 800-2000 Hz)
- **Fundamental frequency**: 200-500 Hz
- **Telephone band**: 300-3400 Hz (standard for speech)

### 2. Distance Attenuation
- **6 meters = ~15.5 dB loss** compared to 1 meter
- Your signals will be **much weaker** than close-range setups
- Need **more aggressive amplification** and **lower thresholds**

### 3. EBU R 128 Standard
- **Target loudness**: -23 LUFS for TV content
- Use for consistent volume normalization

## 🚀 Recommended Changes (Apply These First)

### Priority 1: Distance Compensation

```python
# In __init__ method, change these defaults:
threshold_loud = -20      # Was -15 (account for distance)
threshold_quiet = -45    # Was -35 (account for distance)  
target_db = -25          # Was -20 (account for distance)
silence_threshold = -65  # Was -60 (more permissive)
```

### Priority 2: More Aggressive Dialogue Detection

```python
# In analyze_audio_type method:
voice_formants_ratio > 0.08    # Was 0.10 (more sensitive)
dialogue_threshold = 0.15      # Was 0.20 (detect dialogue easier)

# In adjust_volume_based_on_type:
multiplier = 2.0 + (confidence - 0.25) * 3.0  # Was 1.5 + ... * 2.0
# This makes dialogue volume increases MORE aggressive
```

### Priority 3: Faster Response

```python
# In __init__ method:
chunk_duration = 0.4      # Was 0.5 (faster analysis)
smoothing_window = 5      # Was 7 (faster response)
min_adjustment_interval = 0.3  # Was 0.5 (react faster)
adjustment_step = 6       # Was 5 (bigger steps)
```

### Priority 4: Higher Volume Limits

```python
# In __init__ method:
volume_baseline_max = 75  # Was 70 (allow higher for weak signals)
volume_max = 85          # Was 80 (more headroom)
```

### Priority 5: Better Normalization for Weak Signals

```python
# In analyze_audio_type method, change normalization:
normalization_factor = 0.15 / audio_rms  # Was 0.1
max_normalization = 20.0                 # Was 10.0
```

## 📝 Testing Checklist

1. ✅ **Test with dialogue-only content** (news, podcast)
   - Should detect as "Dialogue" with >50% confidence
   - Volume should increase

2. ✅ **Test with music-only content** (song, instrumental)
   - Should detect as "Music" with >50% confidence  
   - Volume should decrease

3. ✅ **Test with Disney movie** (dialogue + music)
   - Should switch between Dialogue and Music
   - Volume should go UP for dialogue, DOWN for music

4. ✅ **Verify comfort level**
   - Dialogue should be audible but not too loud
   - Music should be quieter but not silent

## 🔧 Fine-Tuning Guide

If dialogue not detected:
- Lower `dialogue_threshold` to 0.12
- Lower `voice_formants_ratio` threshold to 0.06
- Increase `dialogue_multiplier_base` to 2.5

If music not detected:
- Lower `music_threshold` to 0.30
- Lower `background_music_ratio` threshold to 0.15
- Increase `music_multiplier_base` to 1.0

If too aggressive:
- Increase `min_adjustment_interval` to 0.4
- Decrease `adjustment_step` to 4
- Lower `volume_baseline_max` to 70

## 📚 Full Details

See `RESEARCH_AND_TUNING.md` for complete research findings and advanced tuning strategies.

