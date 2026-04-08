import datetime
import json
from typing import Dict, List, Optional

import numpy as np


class GaussianKeystrokeProfile:
    """Gaussian profile model for keystroke feature vectors."""

    EPSILON = 1e-6

    def __init__(self):
        """Initialize an empty untrained profile with metadata timestamps."""
        self.mean = None
        self.std = None
        self.threshold = 30.0
        self.sample_count = 0
        self.is_trained = False
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def fit(self, samples: List[np.ndarray]) -> dict:
        """Fit profile parameters from enrollment samples and auto-calibrate threshold."""
        if len(samples) < 5:
            raise ValueError("At least 5 samples are required to fit the profile")

        lengths = [len(sample) for sample in samples]
        if len(set(lengths)) != 1:
            raise ValueError("All samples must have the same length")

        sample_array = np.asarray(samples, dtype=np.float32)

        self.mean = np.mean(sample_array, axis=0)
        self.std = np.std(sample_array, axis=0) + self.EPSILON
        self.sample_count = len(samples)
        self.is_trained = True

        scores = np.asarray([self.score(sample) for sample in sample_array], dtype=np.float32)
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores))
        calibrated_threshold = mean_score + (1.5 * std_score)
        self.threshold = float(np.clip(calibrated_threshold, 10.0, 100.0))

        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return {
            "mean_score": mean_score,
            "std_score": std_score,
            "threshold": self.threshold,
            "sample_count": self.sample_count,
        }

    def score(self, sample: np.ndarray) -> float:
        """Compute scaled Manhattan distance from sample to the trained profile."""
        if not self.is_trained or self.mean is None or self.std is None:
            raise RuntimeError("Model is not trained yet")

        sample_array = np.asarray(sample, dtype=np.float32)
        if sample_array.shape != self.mean.shape:
            raise ValueError("Sample length does not match profile length")

        distance = np.sum(np.abs(sample_array - self.mean) / self.std)
        return float(distance)

    def is_authentic(self, sample: np.ndarray, threshold: Optional[float] = None) -> bool:
        """Return whether a sample is accepted under the active threshold."""
        active_threshold = self.threshold if threshold is None else threshold
        return self.score(sample) <= active_threshold

    def update(self, sample: np.ndarray, alpha: float = 0.05):
        """Adapt profile mean toward a verified sample using exponential smoothing."""
        if not self.is_trained or self.mean is None:
            raise RuntimeError("Model is not trained yet")

        sample_array = np.asarray(sample, dtype=np.float32)
        if sample_array.shape != self.mean.shape:
            raise ValueError("Sample length does not match profile length")

        self.mean = ((1 - alpha) * self.mean) + (alpha * sample_array)
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Serialize the current profile into a JSON-compatible dictionary."""
        data = {
            "mean": self.mean.tolist() if self.mean is not None else None,
            "std": self.std.tolist() if self.std is not None else None,
            "threshold": self.threshold,
            "sample_count": self.sample_count,
            "is_trained": self.is_trained,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        json.dumps(data)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GaussianKeystrokeProfile":
        """Create a profile instance from a serialized dictionary representation."""
        profile = cls()
        profile.mean = np.asarray(data.get("mean"), dtype=np.float32) if data.get("mean") is not None else None
        profile.std = np.asarray(data.get("std"), dtype=np.float32) if data.get("std") is not None else None
        profile.threshold = float(data.get("threshold", 30.0))
        profile.sample_count = int(data.get("sample_count", 0))
        profile.is_trained = bool(data.get("is_trained", False))
        profile.created_at = data.get("created_at", profile.created_at)
        profile.updated_at = data.get("updated_at", profile.updated_at)
        return profile