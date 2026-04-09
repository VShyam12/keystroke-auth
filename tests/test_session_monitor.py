import datetime

import pytest

from backend.app import create_app
from backend.extensions import db
from backend.models.session_event import SessionEvent
from backend.models.user import User
from backend.monitoring.session_monitor import SessionMonitor


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
def monitor():
    return SessionMonitor()


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            id=1,
            username='testuser',
            email='test@example.com',
            password_hash='fakehash',
        )
        db.session.add(user)
        db.session.commit()
        yield user


def test_log_event_creates_record(app, monitor, test_user):
    with app.app_context():
        result = monitor.log_event(
            user_id=1,
            session_id='sess1',
            event_type='page_view',
            event_detail='/dashboard',
        )

        assert isinstance(result, dict)
        assert 'event_id' in result
        assert SessionEvent.query.count() == 1


def test_log_multiple_events(app, monitor, test_user):
    with app.app_context():
        for i in range(5):
            monitor.log_event(
                user_id=1,
                session_id='sess1',
                event_type='api_call',
                event_detail=f'call_{i}',
            )

        assert SessionEvent.query.count() == 5


def test_get_baseline_returns_default_for_new_user(app, monitor, test_user):
    with app.app_context():
        result = monitor.get_user_baseline(user_id=1)

        assert result['is_default'] is True
        assert result['avg_events_per_session'] == 20


def test_analyze_session_insufficient_data(app, monitor, test_user):
    with app.app_context():
        monitor.log_event(user_id=1, session_id='sess1', event_type='page_view')
        monitor.log_event(user_id=1, session_id='sess1', event_type='button_click')

        result = monitor.analyze_session(1, 'sess1')

        assert result['status'] == 'insufficient_data'


def test_analyze_session_returns_stats(app, monitor, test_user):
    with app.app_context():
        for i in range(10):
            monitor.log_event(user_id=1, session_id='sess1', event_type='api_call', event_detail=str(i))

        result = monitor.analyze_session(1, 'sess1')

        assert 'current_event_count' in result
        assert 'anomaly_score' in result
        assert 'is_suspicious' in result


def test_high_frequency_detected(app, monitor, test_user):
    with app.app_context():
        for i in range(12):
            monitor.log_event(user_id=1, session_id=f'base_{i}', event_type='page_view')

        for i in range(100):
            monitor.log_event(user_id=1, session_id='sess_fast', event_type='api_call', event_detail=str(i))

        result = monitor.analyze_session(1, 'sess_fast')

        assert result['excessive_events'] is True


def test_flag_suspicious_session(app, monitor, test_user):
    with app.app_context():
        for i in range(3):
            monitor.log_event(user_id=1, session_id='sess_flag', event_type='page_view', event_detail=str(i))

        flagged_count = monitor.flag_suspicious_session(1, 'sess_flag', 'test reason')
        flagged_events = SessionEvent.query.filter_by(user_id=1, session_id='sess_flag', is_flagged=True).all()

        assert flagged_count == 3
        assert len(flagged_events) == 3


def test_get_session_alerts_returns_flagged(app, monitor, test_user):
    with app.app_context():
        for i in range(4):
            monitor.log_event(user_id=1, session_id='sess_alert', event_type='api_call', event_detail=str(i))

        monitor.flag_suspicious_session(1, 'sess_alert', 'alert reason')
        alerts = monitor.get_session_alerts(user_id=1)

        assert isinstance(alerts, list)
        assert len(alerts) > 0
