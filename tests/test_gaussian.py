import numpy as np
import pytest

from backend.ml.gaussian import GaussianKeystrokeProfile


def make_samples(n=15, length=50, center=50.0, noise=5.0):
    rng = np.random.default_rng(42)
    samples = []
    for _ in range(n):
        sample = center + rng.normal(loc=0.0, scale=noise, size=length)
        samples.append(np.asarray(sample, dtype=np.float32))
    return samples


def test_fit_requires_minimum_5_samples():
    model = GaussianKeystrokeProfile()
    samples = make_samples(n=3)

    with pytest.raises(ValueError):
        model.fit(samples)


def test_fit_sets_trained_flag():
    model = GaussianKeystrokeProfile()
    samples = make_samples(n=15)

    model.fit(samples)

    assert model.is_trained is True
    assert model.mean is not None
    assert model.std is not None
    assert model.sample_count == 15


def test_score_returns_float():
    model = GaussianKeystrokeProfile()
    samples = make_samples(n=15)
    model.fit(samples)

    new_sample = make_samples(n=1, center=50.0, noise=3.0)[0]
    score = model.score(new_sample)

    assert isinstance(score, float)
    assert score >= 0


def test_genuine_user_scores_lower_than_attacker():
    model = GaussianKeystrokeProfile()
    enrollment_samples = make_samples(n=15, center=50.0, noise=5.0)
    model.fit(enrollment_samples)

    genuine_sample = make_samples(n=1, center=50.0, noise=3.0)[0]
    attacker_sample = make_samples(n=1, center=80.0, noise=3.0)[0]

    genuine_score = model.score(genuine_sample)
    attacker_score = model.score(attacker_sample)

    assert genuine_score < attacker_score


def test_is_authentic_genuine_user():
    model = GaussianKeystrokeProfile()
    model.fit(make_samples(n=15))

    genuine_sample = make_samples(n=1, center=50.0, noise=3.0)[0]

    assert model.is_authentic(genuine_sample) is True


def test_is_authentic_attacker():
    model = GaussianKeystrokeProfile()
    model.fit(make_samples(n=15, center=50.0, noise=5.0))

    attacker_sample = make_samples(n=1, center=90.0, noise=3.0)[0]

    assert model.is_authentic(attacker_sample) is False


def test_threshold_auto_calibration():
    model = GaussianKeystrokeProfile()
    model.fit(make_samples(n=15))

    assert isinstance(model.threshold, float)
    assert 10.0 <= model.threshold <= 100.0


def test_update_shifts_mean():
    model = GaussianKeystrokeProfile()
    model.fit(make_samples(n=15))
    original_mean = model.mean.copy()

    shifted_sample = make_samples(n=1, center=80.0, noise=3.0)[0]
    model.update(shifted_sample)

    assert not np.allclose(original_mean, model.mean)


def test_to_dict_and_from_dict():
    model = GaussianKeystrokeProfile()
    model.fit(make_samples(n=15))
    data = model.to_dict()

    restored = GaussianKeystrokeProfile.from_dict(data)

    assert restored.threshold == model.threshold
    assert restored.sample_count == model.sample_count
    assert restored.is_trained == model.is_trained

    sample = make_samples(n=1, center=50.0, noise=3.0)[0]
    score = restored.score(sample)
    assert isinstance(score, float)


def test_score_before_fit_raises_error():
    model = GaussianKeystrokeProfile()
    sample = make_samples(n=1)[0]

    with pytest.raises(RuntimeError):
        model.score(sample)