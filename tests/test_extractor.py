import numpy as np

from backend.features.extractor import FeatureExtractor, MAX_DWELL_MS


def make_raw_features(n_keys=8):
    rng = np.random.default_rng(42)
    dwell = rng.uniform(60, 150, size=n_keys).tolist()
    flight = rng.uniform(10, 100, size=max(n_keys - 1, 0)).tolist()
    digraph = rng.uniform(80, 200, size=max(n_keys - 1, 0)).tolist()

    return {
        "dwell": dwell,
        "flight": flight,
        "digraph": digraph,
        "mean_dwell": 95.0,
        "std_dwell": 15.0,
        "mean_flight": 45.0,
        "mean_digraph": 130.0,
        "typing_speed": 5.0,
    }


def test_valid_input_returns_array():
    extractor = FeatureExtractor()
    result = extractor.extract(make_raw_features())

    assert result is not None
    assert result.shape == (50,)
    assert result.dtype == np.float32


def test_output_is_always_length_50():
    extractor = FeatureExtractor()

    result_3 = extractor.extract(make_raw_features(3))
    result_8 = extractor.extract(make_raw_features(8))
    result_20 = extractor.extract(make_raw_features(20))

    assert result_3 is not None and result_3.shape == (50,)
    assert result_8 is not None and result_8.shape == (50,)
    assert result_20 is not None and result_20.shape == (50,)


def test_invalid_input_returns_none():
    extractor = FeatureExtractor()

    missing_keys = {"dwell": [100.0, 110.0, 120.0]}
    assert extractor.extract(missing_keys) is None

    empty_dwell = make_raw_features(8)
    empty_dwell["dwell"] = []
    assert extractor.extract(empty_dwell) is None

    zero_typing_speed = make_raw_features(8)
    zero_typing_speed["typing_speed"] = 0
    assert extractor.extract(zero_typing_speed) is None


def test_clip_outliers_works():
    extractor = FeatureExtractor()
    dwell_values = [80.0, 95.0, 120.0, 5000.0]

    clipped = extractor.clip_outliers(dwell_values, 0, MAX_DWELL_MS)

    assert np.all(clipped <= MAX_DWELL_MS)


def test_normalization_output_range():
    extractor = FeatureExtractor()
    raw_features = make_raw_features(8)

    dwell = extractor.clip_outliers(raw_features["dwell"], 0, MAX_DWELL_MS)
    normalized = extractor.normalize(dwell)

    assert np.all(normalized >= -5)
    assert np.all(normalized <= 5)


def test_negative_flight_values_allowed():
    extractor = FeatureExtractor()
    raw_features = make_raw_features(8)
    raw_features["flight"] = [-20.0, -5.0, 10.0, 30.0, 50.0, 70.0, 90.0]

    result = extractor.extract(raw_features)

    assert result is not None
    assert result.shape == (50,)