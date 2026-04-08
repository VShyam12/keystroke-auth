import json
from typing import Dict, List, Optional

import numpy as np


FEATURE_VECTOR_LENGTH = 50
MAX_DWELL_MS = 1000
MAX_FLIGHT_MS = 2000
MIN_SAMPLES = 3


class FeatureExtractor:
    """Extracts normalized fixed-length feature vectors from raw keystroke metrics."""

    def validate(self, raw_features: dict) -> tuple[bool, str]:
        """Validate raw feature payload structure and required numeric constraints."""
        if not isinstance(raw_features, dict):
            return False, "raw_features must be a dictionary"

        required_keys = [
            "dwell",
            "flight",
            "digraph",
            "mean_dwell",
            "std_dwell",
            "mean_flight",
            "mean_digraph",
            "typing_speed",
        ]

        for key in required_keys:
            if key not in raw_features:
                return False, f"missing required key: {key}"

        dwell = raw_features.get("dwell")
        flight = raw_features.get("flight")
        digraph = raw_features.get("digraph")

        if not isinstance(dwell, list) or not isinstance(flight, list) or not isinstance(digraph, list):
            return False, "dwell, flight, and digraph must be lists"

        if len(dwell) < MIN_SAMPLES:
            return False, f"dwell must contain at least {MIN_SAMPLES} samples"

        if raw_features.get("typing_speed", 0) <= 0:
            return False, "typing_speed must be greater than 0"

        for list_name in ("dwell", "flight", "digraph"):
            values = raw_features.get(list_name, [])
            if any(v is None for v in values):
                return False, f"{list_name} contains None values"

        return True, "ok"

    def clip_outliers(self, values: list, min_val: float, max_val: float) -> np.ndarray:
        """Convert values to a numpy array and clip them into an allowed range."""
        array = np.asarray(values, dtype=np.float32)
        return np.clip(array, min_val, max_val)

    def normalize(self, values: np.ndarray) -> np.ndarray:
        """Apply z-score normalization using epsilon to prevent divide-by-zero."""
        epsilon = 1e-6
        mean = np.mean(values) if values.size > 0 else 0.0
        std = np.std(values) if values.size > 0 else 0.0
        return (values - mean) / (std + epsilon)

    def pad_or_truncate(self, values: np.ndarray, target_length: int) -> np.ndarray:
        """Return a float32 vector of exact target_length by truncating or zero-padding."""
        values = np.asarray(values, dtype=np.float32)
        if values.size > target_length:
            return values[:target_length].astype(np.float32)

        if values.size < target_length:
            pad_width = target_length - values.size
            values = np.pad(values, (0, pad_width), mode="constant", constant_values=0.0)

        return values.astype(np.float32)

    def extract(self, raw_features: dict) -> Optional[np.ndarray]:
        """Validate, normalize, and assemble a fixed-length feature vector."""
        is_valid, _ = self.validate(raw_features)
        if not is_valid:
            return None

        dwell = self.clip_outliers(raw_features["dwell"], 0, MAX_DWELL_MS)
        flight = self.clip_outliers(raw_features["flight"], -500, MAX_FLIGHT_MS)
        digraph = self.clip_outliers(raw_features["digraph"], 0, MAX_DWELL_MS + MAX_FLIGHT_MS)

        dwell_normalized = self.normalize(dwell)
        flight_normalized = self.normalize(flight)
        digraph_normalized = self.normalize(digraph)

        base_features = np.asarray(
            [
                raw_features["mean_dwell"],
                raw_features["std_dwell"],
                raw_features["mean_flight"],
                raw_features["mean_digraph"],
                raw_features["typing_speed"],
            ],
            dtype=np.float32,
        )

        vector_48 = np.concatenate(
            [
                base_features,
                self.pad_or_truncate(dwell_normalized, 15),
                self.pad_or_truncate(flight_normalized, 14),
                self.pad_or_truncate(digraph_normalized, 14),
            ]
        )

        return self.pad_or_truncate(vector_48, FEATURE_VECTOR_LENGTH)

    def extract_from_json(self, json_string: str) -> Optional[np.ndarray]:
        """Parse raw features from JSON and extract a feature vector if valid."""
        try:
            raw_features = json.loads(json_string)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

        return self.extract(raw_features)