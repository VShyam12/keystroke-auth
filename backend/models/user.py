import datetime

from sqlalchemy.orm import relationship

from backend.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    enrollment_samples = relationship("EnrollmentSample")
    biometric_profile = relationship("BiometricProfile", uselist=False)
    devices = relationship("Device")
    login_logs = relationship("LoginLog")
    session_events = relationship("SessionEvent")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_locked(self):
        return self.locked_until is not None and self.locked_until > datetime.datetime.now(datetime.timezone.utc)

    def increment_failed_attempts(self):
        self.failed_attempts = (self.failed_attempts or 0) + 1
        if self.failed_attempts >= 5:
            self.locked_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)

    def reset_failed_attempts(self):
        self.failed_attempts = 0
        self.locked_until = None