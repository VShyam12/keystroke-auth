from flask import Blueprint, jsonify

from backend.routes.auth import auth_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.enrollment import enrollment_bp
from backend.routes.session import session_bp


api = Blueprint('api', __name__)

api.register_blueprint(auth_bp, url_prefix='/auth')
api.register_blueprint(enrollment_bp, url_prefix='/enroll')
api.register_blueprint(session_bp, url_prefix='/session')
api.register_blueprint(dashboard_bp, url_prefix='/dashboard')


@api.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"}), 200