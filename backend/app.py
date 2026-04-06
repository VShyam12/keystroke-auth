from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv


db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_name='development'):
	load_dotenv()

	from backend.config import config_map
	from backend.routes import api

	app = Flask(__name__)
	app.config.from_object(config_map[config_name])

	db.init_app(app)
	bcrypt.init_app(app)
	jwt.init_app(app)
	CORS(app, resources={r"/*": {"origins": "*"}})

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
		db.create_all()

	return app


if __name__ == '__main__':
	app = create_app()
	app.run(debug=True, port=5000)
