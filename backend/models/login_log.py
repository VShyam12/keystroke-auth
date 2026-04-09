import datetime

from backend.extensions import db


class LoginLog(db.Model):
    __tablename__ = 'login_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    device_id = db.Column(db.String(64), nullable=True)
    password_correct = db.Column(db.Boolean, nullable=False)
    biometric_score = db.Column(db.Float, nullable=True)
    device_risk = db.Column(db.Float, nullable=True)
    context_risk = db.Column(db.Float, nullable=True)
    final_risk_score = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(10), nullable=True)
    outcome = db.Column(db.String(20), nullable=False)
    otp_verified = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'device_id': self.device_id,
            'password_correct': self.password_correct,
            'biometric_score': self.biometric_score,
            'device_risk': self.device_risk,
            'context_risk': self.context_risk,
            'final_risk_score': self.final_risk_score,
            'risk_level': self.risk_level,
            'outcome': self.outcome,
            'otp_verified': self.otp_verified,
            'failure_reason': self.failure_reason,
        }