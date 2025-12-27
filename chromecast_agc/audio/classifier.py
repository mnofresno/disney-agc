"""Audio classification: distinguishes between dialogue, music and unknown."""

from dataclasses import dataclass
from typing import Dict, Optional

from ..config.settings import Settings
from .analyzer import SpectrumFeatures


@dataclass
class AudioTypeResult:
    """Audio classification result."""

    type: str
    confidence: float
    features: Optional[SpectrumFeatures]
    scores: Dict[str, float]


class AudioClassifier:
    """Classifies audio into dialogue, music, or unknown."""

    def __init__(self, settings: Settings):
        """Initialize audio classifier."""
        self.settings = settings
        self.dialogue_threshold = 0.15
        self.music_threshold = 0.35

    def classify(self, features: SpectrumFeatures) -> AudioTypeResult:
        """
        Classify audio based on spectral features.

        Args:
            features: Extracted spectral features

        Returns:
            AudioTypeResult with type, confidence and scores
        """
        dialogue_score = self._score_dialogue(features)
        music_score = self._score_music(features)

        total_score = dialogue_score + music_score
        if total_score > 0:
            dialogue_score /= total_score
            music_score /= total_score

        audio_type, confidence = self._determine_type(dialogue_score, music_score, features)

        return AudioTypeResult(
            type=audio_type,
            confidence=confidence,
            features=features,
            scores={"dialogue": dialogue_score, "music": music_score},
        )

    def _score_dialogue(self, features: SpectrumFeatures) -> float:
        """Calculate dialogue score."""
        score = 0.0

        if features.voice_formants_ratio > 0.08 and features.background_music_ratio < 0.20:
            score += 0.8
        elif features.voice_formants_ratio > 0.08:
            score += 0.3

        if features.voice_formants_ratio > 0.12 and features.background_music_ratio < 0.18:
            score += 0.5
        if features.voice_formants_ratio > 0.18 and features.background_music_ratio < 0.12:
            score += 0.3
        if features.voice_formants_ratio > 0.22 and features.background_music_ratio < 0.08:
            score += 0.2

        if features.voice_ratio > 0.15:
            score += 0.6
        if features.voice_ratio > 0.25:
            score += 0.4
        if features.voice_ratio > 0.35:
            score += 0.3

        if features.bass_to_voice_ratio < 1.5:
            score += 0.3
        if features.bass_to_voice_ratio < 0.8:
            score += 0.3
        if features.bass_to_voice_ratio < 0.5:
            score += 0.2

        if features.spectral_variation < 2.0:
            score += 0.2
        if features.spectral_variation < 1.2:
            score += 0.3
        if features.spectral_variation < 0.8:
            score += 0.2

        if features.ratio_voice_formants > 0.12:
            score += 0.4
        if features.ratio_voice_formants > 0.18:
            score += 0.3

        if features.ratio_high < 0.35:
            score += 0.2
        if features.ratio_high < 0.25:
            score += 0.1

        return score

    def _score_music(self, features: SpectrumFeatures) -> float:
        """Calculate music score."""
        score = 0.0

        if features.voice_formants_ratio > 0.08 and features.background_music_ratio > 0.20:
            score += 0.8
        if features.voice_formants_ratio > 0.08 and features.background_music_ratio > 0.30:
            score += 0.5
        if features.voice_formants_ratio > 0.12 and features.background_music_ratio > 0.25:
            score += 0.4

        if features.bass_to_voice_ratio > 0.4:
            score += 0.4
        if features.bass_to_voice_ratio > 0.6:
            score += 0.3
        if features.bass_to_voice_ratio > 0.8:
            score += 0.2

        if features.high_to_voice_ratio > 0.6:
            score += 0.3
        if features.high_to_voice_ratio > 0.9:
            score += 0.3
        if features.high_to_voice_ratio > 1.2:
            score += 0.2

        if features.spectral_variation > 0.8:
            score += 0.3
        if features.spectral_variation > 1.2:
            score += 0.3
        if features.spectral_variation > 1.8:
            score += 0.2

        if features.background_music_ratio > 0.20:
            score += 0.4
        if features.background_music_ratio > 0.30:
            score += 0.3
        if features.background_music_ratio > 0.40:
            score += 0.2

        if features.voice_ratio < 0.3:
            score += 0.2
        if features.voice_ratio < 0.2:
            score += 0.2

        if features.voice_formants_ratio < 0.15:
            score += 0.2
        if features.voice_formants_ratio < 0.10:
            score += 0.2

        return score

    def _determine_type(
        self,
        dialogue_score: float,
        music_score: float,
        features: SpectrumFeatures,
    ) -> tuple[str, float]:
        """
        Determine final type and confidence.

        Args:
            dialogue_score: Normalized dialogue score
            music_score: Normalized music score
            features: Spectral features

        Returns:
            Tuple (type, confidence)
        """
        if features.voice_formants_ratio > 0.08 and features.background_music_ratio > 0.20:
            if music_score > 0.30:
                return ("music", music_score)
            elif dialogue_score > music_score and dialogue_score > self.dialogue_threshold:
                return ("dialogue", dialogue_score)
            else:
                return ("music", music_score if music_score > 0 else 0.5)
        elif dialogue_score > music_score and dialogue_score > self.dialogue_threshold:
            return ("dialogue", dialogue_score)
        elif music_score > dialogue_score and music_score > self.music_threshold:
            return ("music", music_score)
        else:
            if features.background_music_ratio > 0.20 and music_score > 0.25:
                return ("music", music_score)
            elif dialogue_score > music_score and dialogue_score > 0.15:
                return ("dialogue", dialogue_score)
            elif music_score > dialogue_score and music_score > 0.30:
                return ("music", music_score)
            else:
                return ("unknown", max(dialogue_score, music_score))
