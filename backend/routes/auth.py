import datetime
import warnings

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.extensions import db, bcrypt
from backend.models.user import User
from backend.models.login_log import LoginLog
from backend.features.extractor import FeatureExtractor
from backend.features.device_fingerprint import DeviceFingerprintAnalyzer
from backend.ml.gaussian import GaussianKeystrokeProfile
from backend.models.biometric_profile import BiometricProfile
from backend.risk.scorer import RiskScorer
from backend.otp.generator import OTPService


auth_bp = Blueprint('auth_bp', __name__)
limiter = Limiter(key_func=get_remote_address)
extractor = FeatureExtractor()
device_analyzer = DeviceFingerprintAnalyzer()
risk_scorer = RiskScorer()
otp_service = OTPService()


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'username, email, and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'username already exists'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'email already exists'}), 409

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'user registered successfully', 'user_id': user.id, 'username': user.username}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    keystroke_features = data.get('keystroke_features')
    fingerprint_data = data.get('fingerprint_data')

    if not username or not password:
        return jsonify({'status': 'denied', 'reason': 'missing_credentials'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'status': 'denied', 'reason': 'invalid_credentials'}), 401

    if user.is_locked():
        return jsonify({'status': 'denied', 'reason': 'account_locked', 'locked_until': user.locked_until.isoformat() if user.locked_until else None}), 423

    if not bcrypt.check_password_hash(user.password_hash, password):
        user.increment_failed_attempts()
        db.session.commit()
        return jsonify({'status': 'denied', 'reason': 'invalid_password'}), 401

    user.reset_failed_attempts()

    biometric_score = 999.0
    biometric_threshold = 30.0

    profile = BiometricProfile.query.filter_by(user_id=user.id).first()
    if profile and profile.threshold is not None:
        biometric_threshold = float(profile.threshold)

    if keystroke_features:
        extracted = extractor.extract(keystroke_features)
        if extracted is not None and profile and profile.is_trained:
            model_data = profile.get_profile_data()
            model = GaussianKeystrokeProfile.from_dict(model_data)
            try:
                biometric_score = float(model.score(extracted))
            except (RuntimeError, ValueError):
                biometric_score = 999.0

    resolved_fingerprint = fingerprint_data if isinstance(fingerprint_data, dict) else {}
    if 'device_id' not in resolved_fingerprint:
        resolved_fingerprint = {
            'device_id': 'unknown',
            **resolved_fingerprint,
        }

    risk_result = risk_scorer.calculate_risk(
        user_id=user.id,
        biometric_score=biometric_score,
        biometric_threshold=biometric_threshold,
        fingerprint_data=resolved_fingerprint,
    )

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        login_time = datetime.datetime.utcnow()

    outcome = 'denied'
    if risk_result['risk_level'] == 'LOW':
        outcome = 'granted'
    elif risk_result['risk_level'] == 'MEDIUM':
        outcome = 'otp_required'

    log_entry = LoginLog(
        user_id=user.id,
        timestamp=login_time,
        ip_address=request.remote_addr,
        device_id=resolved_fingerprint.get('device_id'),
        password_correct=True,
        biometric_score=biometric_score,
        device_risk=risk_result.get('device_risk'),
        context_risk=risk_result.get('context_risk'),
        final_risk_score=risk_result.get('final_score'),
        risk_level=risk_result.get('risk_level'),
        outcome=outcome,
        otp_verified=False,
        failure_reason='high_risk' if risk_result['risk_level'] == 'HIGH' else None,
    )
    db.session.add(log_entry)
    db.session.commit()

    if risk_result['risk_level'] == 'LOW':
        token = create_access_token(identity=str(user.id))
        return jsonify({
            'status': 'granted',
            'token': token,
            'user_id': user.id,
            'risk_score': risk_result.get('final_score'),
            'risk_level': risk_result.get('risk_level'),
        }), 200

    if risk_result['risk_level'] == 'MEDIUM':
        otp_result = otp_service.generate_otp(user.id)
        return jsonify({
            'status': 'otp_required',
            'otp_code': otp_result.get('code'),
            'expires_in_seconds': otp_result.get('expires_in_seconds'),
            'user_id': user.id,
            'risk_level': risk_result.get('risk_level'),
        }), 202

    return jsonify({
        'status': 'denied',
        'reason': 'high_risk',
        'risk_score': risk_result.get('final_score'),
        'risk_level': risk_result.get('risk_level'),
    }), 401


@auth_bp.route('/otp/verify', methods=['POST'])
def verify_otp():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    otp_code = data.get('otp_code')

    if not user_id or not otp_code:
        return jsonify({'status': 'denied', 'reason': 'missing_otp_fields'}), 400

    result = otp_service.verify_otp(user_id, otp_code)
    if not result.get('success'):
        return jsonify({'status': 'denied', 'reason': result.get('reason')}), 401

    latest_otp_log = (
        LoginLog.query.filter_by(user_id=user_id, outcome='otp_required')
        .order_by(LoginLog.timestamp.desc())
        .first()
    )
    if latest_otp_log:
        latest_otp_log.otp_verified = True
        db.session.commit()

    token = create_access_token(identity=str(user_id))
    return jsonify({'status': 'granted', 'token': token, 'user_id': user_id}), 200


@auth_bp.route('/test-token', methods=['POST'])
def test_token():
    # REMOVE BEFORE PRODUCTION
    if not current_app.config.get('DEBUG', False):
        return jsonify({'error': 'not available'}), 404

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    username = data.get('username')

    if user_id is None or not username:
        return jsonify({'error': 'user_id and username are required'}), 400

    token = create_access_token(identity=str(user_id))
    return jsonify({'token': token, 'user_id': user_id}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'user not found'}), 404

    return jsonify({'user_id': user.id, 'username': user.username, 'email': user.email}), 200