import json
import datetime

from backend.extensions import db


class BiometricProfile(db.Model):
    __tablename__ = 'biometric_profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    profile_data = db.Column(db.Text, nullable=False)
    sample_count = db.Column(db.Integer, default=0)
    threshold = db.Column(db.Float, nullable=False, default=30.0)
    is_trained = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    last_updated_by_login = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'profile_data': self.get_profile_data(),
            'sample_count': self.sample_count,
            'threshold': self.threshold,
            'is_trained': self.is_trained,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_updated_by_login': self.last_updated_by_login.isoformat() if self.last_updated_by_login else None,
        }

    def set_profile_data(self, profile_dict):
        self.profile_data = json.dumps(profile_dict)

    def get_profile_data(self):
        if not self.profile_data:
            return {}

        return json.loads(self.profile_data)