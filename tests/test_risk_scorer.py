import pytest

from backend.app import create_app, db
from backend.models.user import User
from backend.risk.scorer import RiskScorer


@pytest.fixture
def app():
    app_instance = create_app('testing')
    with app_instance.app_context():
        db.create_all()
    yield app_instance
    with app_instance.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def scorer():
    return RiskScorer()


@pytest.fixture
def sample_fingerprint():
    return {
        'device_id': 'test' * 16,
        'user_agent': 'Test Browser',
        'platform': 'Win32',
        'screen_resolution': '1920x1080',
        'timezone_offset': -330,
        'color_depth': 24,
        'pixel_ratio': 1.0,
    }


def _create_test_user(user_id: int = 1):
    user = User(
        id=user_id,
        username=f'testuser{user_id}',
        email=f'test{user_id}@example.com',
        password_hash='fakehash123'
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_low_biometric_score_contributes_low_risk(app, scorer, sample_fingerprint):
    with app.app_context():
        risk = scorer.normalize_biometric_score(5.0, 30.0)
        assert risk < 0.3


def test_high_biometric_score_contributes_high_risk(app, scorer, sample_fingerprint):
    with app.app_context():
        risk = scorer.normalize_biometric_score(200.0, 30.0)
        assert risk == 1.0


def test_calculate_risk_returns_dict(app, scorer, sample_fingerprint):
    with app.app_context():
        _create_test_user(user_id=1)

        result = scorer.calculate_risk(1, 25.0, 30.0, sample_fingerprint)

        assert isinstance(result, dict)
        assert 'risk_level' in result
        assert 'final_score' in result
        assert 'biometric_risk' in result
        assert 'device_risk' in result
        assert 'context_risk' in result
        assert 'recommendation' in result


def test_genuine_user_gets_low_or_medium_risk(app, scorer, sample_fingerprint):
    with app.app_context():
        _create_test_user(user_id=1)

        result = scorer.calculate_risk(1, 15.0, 30.0, sample_fingerprint)

        assert result['risk_level'] in ('LOW', 'MEDIUM')


def test_attacker_gets_high_risk(app, scorer, sample_fingerprint):
    with app.app_context():
        _create_test_user(user_id=1)

        result = scorer.calculate_risk(1, 500.0, 30.0, sample_fingerprint)

        assert result['risk_level'] == 'HIGH'


def test_recommendation_matches_risk_level(app, scorer, sample_fingerprint):
    with app.app_context():
        _create_test_user(user_id=1)
        _create_test_user(user_id=2)

        high_risk_fingerprint = {
            'device_id': 'uniquehighrisktestdevice' + '0' * 39,
            'user_agent': 'Test Browser',
            'platform': 'Win32',
            'screen_resolution': '1920x1080',
            'timezone_offset': -330,
            'color_depth': 24,
            'pixel_ratio': 1.0,
        }

        low_result = scorer.calculate_risk(1, 1.0, 30.0, sample_fingerprint)
        high_result = scorer.calculate_risk(2, 500.0, 30.0, high_risk_fingerprint)

        if low_result['risk_level'] == 'LOW':
            assert low_result['recommendation'] == 'grant_access'

        assert high_result['risk_level'] == 'HIGH'
        assert high_result['recommendation'] == 'deny_access'


def test_get_risk_summary_returns_string(app, scorer, sample_fingerprint):
    with app.app_context():
        _create_test_user(user_id=1)

        result = scorer.calculate_risk(1, 25.0, 30.0, sample_fingerprint)
        summary = scorer.get_risk_summary(result)

        assert isinstance(summary, str)
        assert summary.strip() != ''