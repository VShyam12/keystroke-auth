import datetime

import pytest

from backend.app import create_app, db
from backend.models.otp import OTPRecord
from backend.models.user import User
from backend.otp.generator import OTPService


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
def otp_service():
    return OTPService()


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            id=1,
            username='testuser',
            email='test@example.com',
            password_hash='fakehash'
        )
        db.session.add(user)
        db.session.commit()
    return user


def test_generate_otp_returns_dict(app, otp_service, test_user):
    with app.app_context():
        result = otp_service.generate_otp(user_id=1)

        assert isinstance(result, dict)
        assert 'code' in result
        assert len(result['code']) == 6
        assert result['code'].isdigit()


def test_otp_expires_in_5_minutes(app, otp_service, test_user):
    with app.app_context():
        result = otp_service.generate_otp(user_id=1)

        assert 290 <= result['expires_in_seconds'] <= 300


def test_verify_correct_otp(app, otp_service, test_user):
    with app.app_context():
        gen_result = otp_service.generate_otp(user_id=1)
        code = gen_result['code']

        verify_result = otp_service.verify_otp(user_id=1, submitted_code=code)

        assert verify_result['success'] is True
        assert verify_result['reason'] == 'verified'


def test_verify_wrong_otp(app, otp_service, test_user):
    with app.app_context():
        otp_service.generate_otp(user_id=1)

        verify_result = otp_service.verify_otp(user_id=1, submitted_code='000000')

        assert verify_result['success'] is False
        assert verify_result['reason'] == 'invalid_code'


def test_otp_cannot_be_reused(app, otp_service, test_user):
    with app.app_context():
        gen_result = otp_service.generate_otp(user_id=1)
        code = gen_result['code']

        first_verify = otp_service.verify_otp(user_id=1, submitted_code=code)
        assert first_verify['success'] is True

        second_verify = otp_service.verify_otp(user_id=1, submitted_code=code)
        assert second_verify['success'] is False


def test_old_otp_invalidated_on_new_generate(app, otp_service, test_user):
    with app.app_context():
        first_result = otp_service.generate_otp(user_id=1)
        first_code = first_result['code']

        otp_service.generate_otp(user_id=1)

        verify_result = otp_service.verify_otp(user_id=1, submitted_code=first_code)
        assert verify_result['success'] is False


def test_too_many_attempts_blocks_verification(app, otp_service, test_user):
    with app.app_context():
        otp_service.generate_otp(user_id=1)

        result = {}
        for i in range(4):
            result = otp_service.verify_otp(user_id=1, submitted_code='000000')

        assert result['reason'] == 'too_many_attempts'


def test_cleanup_removes_used_otps(app, otp_service, test_user):
    with app.app_context():
        gen_result = otp_service.generate_otp(user_id=1)
        code = gen_result['code']

        otp_service.verify_otp(user_id=1, submitted_code=code)

        count = otp_service.cleanup_expired_otps(user_id=1)
        assert count >= 1
