from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.monitoring.session_monitor import SessionMonitor


session_bp = Blueprint('session_bp', __name__)
monitor = SessionMonitor()


@session_bp.route('/event', methods=['POST'])
@jwt_required()
def event():
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    event_type = data.get('event_type')
    event_detail = data.get('event_detail')
    user_id = get_jwt_identity()

    if not session_id or not event_type:
        return jsonify({'error': 'session_id and event_type are required'}), 400

    monitor.log_event(user_id, session_id, event_type, event_detail)
    analysis = monitor.analyze_session(user_id, session_id)

    is_suspicious = bool(analysis.get('is_suspicious', False))
    anomaly_score = float(analysis.get('anomaly_score', 0.0))

    if is_suspicious:
        monitor.flag_suspicious_session(user_id, session_id, 'automated detection')

    return jsonify({
        'event_logged': True,
        'is_suspicious': is_suspicious,
        'anomaly_score': anomaly_score,
    }), 200


@session_bp.route('/analyze/<int:user_id>', methods=['GET'])
@jwt_required()
def analyze(user_id):
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'session_id query parameter is required'}), 400

    analysis = monitor.analyze_session(user_id, session_id)
    return jsonify(analysis), 200


@session_bp.route('/alerts/<int:user_id>', methods=['GET'])
@jwt_required()
def alerts(user_id):
    alerts_data = monitor.get_session_alerts(user_id)
    return jsonify({'alerts': alerts_data, 'count': len(alerts_data)}), 200