import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class Config:
    """Base Configuration with security defaults."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-shop-inventory-2026')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
    ENABLE_SNS_ALERTS = os.environ.get('ENABLE_SNS_ALERTS', 'true').lower() in ('true', '1', 'yes')


class DevelopmentConfig(Config):
    """Local Development Configuration.
    Defaults to SQLite if MySQL environment variables are not provided.
    """
    DEBUG = True
    DB_USER = os.environ.get('DB_USER', '')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', '')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'inventory_db')

    if DB_HOST and DB_USER:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Fallback to local SQLite file for immediate out-of-the-box local testing
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'inventory_dev.sqlite3')}"


class TestingConfig(Config):
    """Testing Configuration for automated Pytest suites."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory database for ultra-fast unit testing
    ENABLE_SNS_ALERTS = False  # Never spam real AWS SNS during automated unit tests


class ProductionConfig(Config):
    """Production Configuration for AWS EC2 & RDS deployment."""
    DEBUG = False
    DB_USER = os.environ.get('DB_USER', 'admin')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', '')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'inventory_db')

    if not DB_HOST:
        # Fallback if DB_HOST is not yet configured during initialization
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'inventory_prod_fallback.sqlite3')}"
    else:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
