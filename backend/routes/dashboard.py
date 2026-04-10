import datetime
import warnings

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.login_log import LoginLog
from backend.models.biometric_profile import BiometricProfile
from backend.models.device import Device
from backend.models.session_event import SessionEvent
from backend.features.device_fingerprint import DeviceFingerprintAnalyzer


dashboard_bp = Blueprint('dashboard_bp', __name__)
device_analyzer = DeviceFingerprintAnalyzer()


@dashboard_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def dashboard(user_id):
    _ = get_jwt_identity()

    last_10_logins = (
        LoginLog.query.filter_by(user_id=user_id)
        .order_by(LoginLog.timestamp.desc())
        .limit(10)
        .all()
    )

    profile = BiometricProfile.query.filter_by(user_id=user_id).first()
    is_enrolled = bool(profile and profile.is_trained)
    current_threshold = float(profile.threshold) if profile and profile.threshold is not None else None

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        now_utc = datetime.datetime.utcnow()
    seven_days_ago = now_utc - datetime.timedelta(days=7)

    denied_count = (
        LoginLog.query.filter(
            LoginLog.user_id == user_id,
            LoginLog.outcome == 'denied',
            LoginLog.timestamp >= seven_days_ago,
        )
        .count()
    )

    recent_logs = (
        LoginLog.query.filter(
            LoginLog.user_id == user_id,
            LoginLog.timestamp >= seven_days_ago,
        )
        .all()
    )
    recent_scores = [log.final_risk_score for log in recent_logs if log.final_risk_score is not None]
    avg_score_last_7_days = (sum(recent_scores) / len(recent_scores)) if recent_scores else 0.0

    total_logins = LoginLog.query.filter_by(user_id=user_id).count()

    return jsonify({
        'last_10_logins': [log.to_dict() for log in last_10_logins],
        'current_threshold': current_threshold,
        'is_enrolled': is_enrolled,
        'anomaly_count_7days': denied_count,
        'avg_score_last_7_days': float(avg_score_last_7_days),
        'total_logins': total_logins,
    }), 200


@dashboard_bp.route('/devices/<int:user_id>', methods=['GET'])
@jwt_required()
def devices(user_id):
    _ = get_jwt_identity()
    devices_data = device_analyzer.get_user_devices(user_id)
    return jsonify({'devices': devices_data, 'count': len(devices_data)}), 200


@dashboard_bp.route('/devices/trust', methods=['POST'])
@jwt_required()
def trust_device():
    _ = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    device_id = data.get('device_id')

    if not user_id or not device_id:
        return jsonify({'error': 'user_id and device_id are required'}), 400

    trusted = device_analyzer.trust_device(user_id, device_id)
    if trusted:
        return jsonify({'message': 'device trusted'}), 200

    return jsonify({'error': 'device not found'}), 404