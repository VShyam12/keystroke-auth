import datetime

from backend.app import db


class Device(db.Model):
    __tablename__ = 'devices'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'device_id', name='uq_devices_user_id_device_id'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    device_id = db.Column(db.String(64), nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    platform = db.Column(db.String(100), nullable=True)
    screen_resolution = db.Column(db.String(20), nullable=True)
    timezone_offset = db.Column(db.Integer, nullable=True)
    is_trusted = db.Column(db.Boolean, default=False)
    first_seen = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    trust_granted_at = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'user_agent': self.user_agent,
            'platform': self.platform,
            'screen_resolution': self.screen_resolution,
            'timezone_offset': self.timezone_offset,
            'is_trusted': self.is_trusted,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'trust_granted_at': self.trust_granted_at.isoformat() if self.trust_granted_at else None,
            'login_count': self.login_count,
        }

    def mark_trusted(self):
        self.is_trusted = True
        self.trust_granted_at = datetime.datetime.now(datetime.timezone.utc)

    def update_last_seen(self):
        self.last_seen = datetime.datetime.now(datetime.timezone.utc)
        self.login_count = (self.login_count or 0) + 1