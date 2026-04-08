import datetime

from sqlalchemy import func

from backend.app import db


class SessionEvent(db.Model):
    __tablename__ = 'session_events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    event_detail = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(200), nullable=True)

    @classmethod
    def get_session_stats(cls, user_id, session_id):
        events = cls.query.filter_by(user_id=user_id, session_id=session_id).order_by(cls.timestamp.asc()).all()

        if not events:
            return {
                'total_events': 0,
                'events_per_minute': 0.0,
                'session_duration_minutes': 0.0,
                'unique_event_types': 0,
            }

        total_events = len(events)
        first_timestamp = events[0].timestamp
        last_timestamp = events[-1].timestamp
        duration_seconds = (last_timestamp - first_timestamp).total_seconds() if first_timestamp and last_timestamp else 0
        session_duration_minutes = duration_seconds / 60 if duration_seconds > 0 else 0.0
        events_per_minute = (total_events / session_duration_minutes) if session_duration_minutes > 0 else float(total_events)
        unique_event_types = len({event.event_type for event in events})

        return {
            'total_events': total_events,
            'events_per_minute': events_per_minute,
            'session_duration_minutes': session_duration_minutes,
            'unique_event_types': unique_event_types,
        }

    @classmethod
    def flag_event(cls, event_id, reason):
        event = cls.query.get(event_id)
        if event is None:
            return None

        event.is_flagged = True
        event.flag_reason = reason
        db.session.commit()
        return event