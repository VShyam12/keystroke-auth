import datetime
import random
import string
import warnings

from backend.app import db


class OTPRecord(db.Model):
    """One-time password record for multi-factor authentication."""

    __tablename__ = 'otp_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), nullable=False, default='login')
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    attempts = db.Column(db.Integer, default=0)

    @staticmethod
    def generate_code():
        """Generate a random 6-digit OTP code."""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        """Check whether the OTP has passed its expiration time."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            now = datetime.datetime.utcnow()
        return now > self.expires_at

    def is_valid(self):
        """Check whether the OTP is neither used nor expired."""
        return not self.is_used and not self.is_expired()

    def to_dict(self):
        """Return a dict representation excluding the code for security."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'purpose': self.purpose,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_used': self.is_used,
            'is_expired': self.is_expired(),
            'attempts': self.attempts,
        }
