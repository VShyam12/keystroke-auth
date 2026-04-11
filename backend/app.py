import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from backend.extensions import db, bcrypt, jwt, limiter


def create_app(config_name='development'):
	load_dotenv()

	from backend.config import config_map
	from backend.routes import api

	instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance'))
	os.makedirs(instance_path, exist_ok=True)
	app = Flask(__name__, instance_path=instance_path)
	app.config.from_object(config_map[config_name])

	db.init_app(app)
	bcrypt.init_app(app)
	jwt.init_app(app)
	limiter.init_app(app)
	CORS(app,
		 origins=["http://127.0.0.1:5500", 
		           "http://localhost:5500"],
		 allow_headers=["Content-Type", "Authorization"],
		 methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
		 supports_credentials=False)

	@app.after_request
	def add_cors_headers(response):
		origin = request.headers.get('Origin', '')
		if '5500' in origin or '5000' in origin:
			response.headers['Access-Control-Allow-Origin'] = origin
			response.headers['Access-Control-Allow-Headers'] = \
				'Content-Type, Authorization'
			response.headers['Access-Control-Allow-Methods'] = \
				'GET, POST, PUT, DELETE, OPTIONS'
		return response

	app.register_blueprint(api, url_prefix='/api')

	@app.route('/health', methods=['GET'])
	def health_check():
		return jsonify({"status": "ok", "message": "Server is running"}), 200

	with app.app_context():
		from backend.models.user import User
		from backend.models.enrollment_sample import EnrollmentSample
		from backend.models.biometric_profile import BiometricProfile
		from backend.models.device import Device
		from backend.models.login_log import LoginLog
		from backend.models.session_event import SessionEvent
		from backend.models.otp import OTPRecord
		db.create_all()
		with app.app_context():
			from backend.models.user import User
			from backend.models.enrollment_sample import EnrollmentSample
			from backend.models.biometric_profile import BiometricProfile
			from backend.models.device import Device
			from backend.models.login_log import LoginLog
			from backend.models.session_event import SessionEvent
			from backend.models.otp import OTPRecord
			db.create_all()
			from sqlalchemy import inspect
			inspector = inspect(db.engine)
			tables = inspector.get_table_names()

	return app


if __name__ == '__main__':
	app = create_app()
	app.run(debug=True, port=5000)
