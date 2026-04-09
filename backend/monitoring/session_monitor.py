import datetime
import warnings

from backend.extensions import db
from backend.models.login_log import LoginLog
from backend.models.session_event import SessionEvent


class SessionMonitor:
    """Tracks session behavior and identifies suspicious usage patterns."""

    def log_event(self, user_id: int, session_id: str, event_type: str, event_detail: str = None) -> dict:
        """Persist a session event and return key event metadata."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            now_utc = datetime.datetime.utcnow()

        event = SessionEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            event_detail=event_detail,
            timestamp=now_utc,
            is_flagged=False,
        )
        db.session.add(event)
        db.session.commit()

        return {
            'event_id': event.id,
            'timestamp': event.timestamp.isoformat() if event.timestamp else None,
            'event_type': event.event_type,
        }

    def get_user_baseline(self, user_id: int, exclude_session_id: str = None) -> dict:
        """Compute user behavior baseline from the last 30 days of session activity."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            now_utc = datetime.datetime.utcnow()
        window_start = now_utc - datetime.timedelta(days=30)

        query = SessionEvent.query.filter(
            SessionEvent.user_id == user_id,
            SessionEvent.timestamp >= window_start,
        )
        if exclude_session_id is not None:
            query = query.filter(SessionEvent.session_id != exclude_session_id)

        events = query.order_by(SessionEvent.timestamp.asc()).all()

        if len(events) < 10:
            return {
                'avg_events_per_session': 20,
                'avg_session_duration_minutes': 30,
                'common_hours': list(range(0, 24)),
                'avg_actions_per_minute': 2.0,
                'is_default': True,
            }

        sessions = {}
        for event in events:
            sessions.setdefault(event.session_id, []).append(event)

        event_counts = []
        durations = []
        actions_per_minute = []
        session_hour_presence = {hour: 0 for hour in range(24)}

        for session_events in sessions.values():
            event_count = len(session_events)
            event_counts.append(event_count)

            timestamps = [evt.timestamp for evt in session_events if evt.timestamp is not None]
            if timestamps:
                duration_minutes = (max(timestamps) - min(timestamps)).total_seconds() / 60.0
            else:
                duration_minutes = 0.0
            durations.append(duration_minutes)

            if duration_minutes > 0:
                apm = event_count / duration_minutes
            else:
                apm = float(event_count)
            actions_per_minute.append(apm)

            unique_hours = {ts.hour for ts in timestamps}
            for hour in unique_hours:
                session_hour_presence[hour] += 1

        total_sessions = len(sessions)
        common_hours = [
            hour
            for hour, count in session_hour_presence.items()
            if total_sessions > 0 and (count / total_sessions) > 0.20
        ]

        return {
            'avg_events_per_session': float(sum(event_counts) / len(event_counts)) if event_counts else 20.0,
            'avg_session_duration_minutes': float(sum(durations) / len(durations)) if durations else 30.0,
            'common_hours': common_hours,
            'avg_actions_per_minute': float(sum(actions_per_minute) / len(actions_per_minute)) if actions_per_minute else 2.0,
            'is_default': False,
        }

    def analyze_session(self, user_id: int, session_id: str) -> dict:
        """Analyze the current session against baseline behavior and return anomaly indicators."""
        session_events = (
            SessionEvent.query.filter_by(user_id=user_id, session_id=session_id)
            .order_by(SessionEvent.timestamp.asc())
            .all()
        )

        if len(session_events) < 3:
            return {'status': 'insufficient_data'}

        baseline = self.get_user_baseline(
            user_id, exclude_session_id=session_id
        )

        timestamps = [evt.timestamp for evt in session_events if evt.timestamp is not None]
        current_event_count = len(session_events)
        if timestamps:
            current_duration_minutes = (max(timestamps) - min(timestamps)).total_seconds() / 60.0
        else:
            current_duration_minutes = 0.0

        if current_duration_minutes <= 0.1:
            current_duration_minutes = 0.1

        current_actions_per_minute = current_event_count / max(current_duration_minutes, 0.1)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            current_hour = datetime.datetime.utcnow().hour

        high_frequency = current_actions_per_minute > (baseline['avg_actions_per_minute'] * 3)
        excessive_events = current_event_count > (baseline['avg_events_per_session'] * 3)
        unusual_hour = current_hour not in baseline['common_hours']
        long_session = current_duration_minutes > (baseline['avg_session_duration_minutes'] * 3)

        anomaly_score = (
            (0.35 * (1.0 if high_frequency else 0.0))
            + (0.35 * (1.0 if excessive_events else 0.0))
            + (0.20 * (1.0 if unusual_hour else 0.0))
            + (0.10 * (1.0 if long_session else 0.0))
        )

        is_suspicious = anomaly_score >= 0.35

        return {
            'current_event_count': current_event_count,
            'current_duration_minutes': float(current_duration_minutes),
            'current_actions_per_minute': float(current_actions_per_minute),
            'current_hour': current_hour,
            'high_frequency': high_frequency,
            'excessive_events': excessive_events,
            'unusual_hour': unusual_hour,
            'long_session': long_session,
            'anomaly_score': float(anomaly_score),
            'is_suspicious': is_suspicious,
            'baseline_used': 'default' if baseline.get('is_default') else 'computed',
            'baseline': baseline,
        }

    def flag_suspicious_session(self, user_id: int, session_id: str, reason: str) -> int:
        """Flag all unflagged events in a session and return the number of flagged rows."""
        events = SessionEvent.query.filter_by(user_id=user_id, session_id=session_id, is_flagged=False).all()

        for event in events:
            event.is_flagged = True
            event.flag_reason = reason

        db.session.commit()
        return len(events)

    def get_session_alerts(self, user_id: int, limit: int = 10) -> list:
        """Return the latest flagged session events for a user in descending time order."""
        events = (
            SessionEvent.query.filter_by(user_id=user_id, is_flagged=True)
            .order_by(SessionEvent.timestamp.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                'id': event.id,
                'user_id': event.user_id,
                'session_id': event.session_id,
                'event_type': event.event_type,
                'event_detail': event.event_detail,
                'timestamp': event.timestamp.isoformat() if event.timestamp else None,
                'is_flagged': event.is_flagged,
                'flag_reason': event.flag_reason,
            }
            for event in events
        ]
