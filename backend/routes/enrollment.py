import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.user import User
from backend.models.enrollment_sample import EnrollmentSample
from backend.models.biometric_profile import BiometricProfile
from backend.features.extractor import FeatureExtractor
from backend.ml.gaussian import GaussianKeystrokeProfile


enrollment_bp = Blueprint('enrollment_bp', __name__)
extractor = FeatureExtractor()


@enrollment_bp.route('/sample', methods=['POST'])
@jwt_required()
def enroll_sample():
    data = request.get_json(silent=True) or {}
    keystroke_features = data.get('keystroke_features')
    user_id = get_jwt_identity()

    feature_array = extractor.extract(keystroke_features)
    if feature_array is None:
        return jsonify({'error': 'invalid features'}), 400

    existing_count = EnrollmentSample.query.filter_by(user_id=user_id).count()
    if existing_count >= 15:
        return jsonify({'error': 'already enrolled', 'message': 'call /finalize'}), 400

    sample = EnrollmentSample(user_id=user_id, sample_index=existing_count + 1)
    sample.set_feature_vector(feature_array)
    sample.raw_features = json.dumps(keystroke_features)

    db.session.add(sample)
    db.session.commit()

    samples_collected = existing_count + 1
    return jsonify({
        'sample_index': sample.sample_index,
        'samples_collected': samples_collected,
        'samples_needed': 15,
        'ready_to_finalize': samples_collected >= 15,
    }), 200


@enrollment_bp.route('/finalize', methods=['POST'])
@jwt_required()
def finalize():
    user_id = get_jwt_identity()
    samples = EnrollmentSample.query.filter_by(user_id=user_id).order_by(EnrollmentSample.sample_index.asc()).all()

    if len(samples) < 5:
        return jsonify({'error': 'not enough samples'}), 400

    vectors = [sample.get_feature_vector() for sample in samples]

    model = GaussianKeystrokeProfile()
    model.fit(vectors)

    profile = BiometricProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        profile = BiometricProfile(user_id=user_id)
        db.session.add(profile)

    profile.is_trained = True
    profile.sample_count = len(samples)
    profile.set_profile_data(model.to_dict())
    profile.threshold = model.threshold

    db.session.commit()

    return jsonify({
        'message': 'profile trained',
        'threshold': profile.threshold,
        'sample_count': profile.sample_count,
        'is_trained': True,
    }), 200


@enrollment_bp.route('/status/<int:user_id>', methods=['GET'])
@jwt_required()
def status(user_id):
    samples_collected = EnrollmentSample.query.filter_by(user_id=user_id).count()
    profile = BiometricProfile.query.filter_by(user_id=user_id).first()

    is_enrolled = bool(profile and profile.is_trained)
    threshold = float(profile.threshold) if is_enrolled and profile.threshold is not None else None

    return jsonify({
        'samples_collected': samples_collected,
        'samples_needed': 15,
        'is_enrolled': is_enrolled,
        'threshold': threshold,
    }), 200