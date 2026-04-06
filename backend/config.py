import os
from datetime import timedelta


class BaseConfig:
	SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
	SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///keystroke_auth.db")
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-prod")
	JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
	BCRYPT_LOG_ROUNDS = 12


class DevelopmentConfig(BaseConfig):
	DEBUG = True
	BCRYPT_LOG_ROUNDS = 4


class ProductionConfig(BaseConfig):
	DEBUG = False


class TestingConfig(BaseConfig):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
	BCRYPT_LOG_ROUNDS = 4


config_map = {
	"development": DevelopmentConfig,
	"production": ProductionConfig,
	"testing": TestingConfig,
}
