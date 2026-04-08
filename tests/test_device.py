import pytest

from backend.app import create_app, db
from backend.features.device_fingerprint import DeviceFingerprintAnalyzer
from backend.models.user import User


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
def client(app):
    return app.test_client()


@pytest.fixture
def sample_fingerprint():
    return {
        'device_id': 'abc123def456' * 4,
        'user_agent': 'Mozilla/5.0 Test Browser',
        'platform': 'Win32',
        'screen_resolution': '1920x1080',
        'timezone_offset': -330,
        'color_depth': 24,
        'pixel_ratio': 1.0,
    }


def test_new_device_returns_high_risk(app, sample_fingerprint):
    with app.app_context():
        user = User(username='user1', email='user1@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()
        assert user.id == 1

        analyzer = DeviceFingerprintAnalyzer()
        risk = analyzer.calculate_device_risk(user_id=1, fingerprint_data=sample_fingerprint)

        assert risk >= 0.5


def test_same_device_returns_lower_risk(app, sample_fingerprint):
    with app.app_context():
        user = User(username='user2', email='user2@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        analyzer = DeviceFingerprintAnalyzer()
        first_risk = analyzer.calculate_device_risk(user_id=user.id, fingerprint_data=sample_fingerprint)
        second_risk = analyzer.calculate_device_risk(user_id=user.id, fingerprint_data=sample_fingerprint)

        assert second_risk < first_risk


def test_get_user_devices_returns_list(app, sample_fingerprint):
    with app.app_context():
        user = User(username='user3', email='user3@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        analyzer = DeviceFingerprintAnalyzer()
        analyzer.get_or_create_device(user_id=user.id, fingerprint_data=sample_fingerprint)
        devices = analyzer.get_user_devices(user_id=user.id)

        assert isinstance(devices, list)
        assert len(devices) >= 1


def test_trust_device(app, sample_fingerprint):
    with app.app_context():
        user = User(username='user4', email='user4@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        analyzer = DeviceFingerprintAnalyzer()
        device, _ = analyzer.get_or_create_device(user_id=user.id, fingerprint_data=sample_fingerprint)

        trusted = analyzer.trust_device(user_id=user.id, device_id=device.device_id)
        risk = analyzer.calculate_device_risk(user_id=user.id, fingerprint_data=sample_fingerprint)

        assert trusted is True
        assert risk <= 0.2