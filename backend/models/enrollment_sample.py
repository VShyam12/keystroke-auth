import json
from datetime import datetime

import numpy as np

from backend.app import db


class EnrollmentSample(db.Model):
    __tablename__ = 'enrollment_samples'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    feature_vector = db.Column(db.Text, nullable=False)
    raw_features = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sample_index = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'feature_vector': self.get_feature_vector().tolist() if self.feature_vector else [],
            'raw_features': json.loads(self.raw_features) if self.raw_features else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sample_index': self.sample_index,
        }

    def set_feature_vector(self, numpy_array):
        array = np.asarray(numpy_array, dtype=np.float32)
        self.feature_vector = json.dumps(array.tolist())

    def get_feature_vector(self):
        if not self.feature_vector:
            return np.array([], dtype=np.float32)

        return np.asarray(json.loads(self.feature_vector), dtype=np.float32)