import os
import logging
from flask import Flask
from dotenv import load_dotenv
from app.config import config_by_name
from app.models import db, User

# Load environment variables from .env if present
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('inventory_app')


def create_app(config_name: str = None) -> Flask:
    """Application factory for Flask.
    
    Args:
        config_name: 'development', 'testing', or 'production'
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development').lower()

    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_obj)

    logger.info(f"Starting Shop Inventory System in [{config_name.upper()}] environment.")

    # Initialize SQLAlchemy
    db.init_app(app)

    # Initialize Prometheus Metrics (optional, graceful fallback)
    try:
        from prometheus_flask_exporter import PrometheusMetrics
        metrics = PrometheusMetrics(app, path='/metrics')
        logger.info("Prometheus metrics initialized on /metrics")
    except ImportError:
        logger.warning("prometheus_flask_exporter not installed. /metrics endpoint disabled.")

    # Register Blueprints
    from app.routes import routes
    app.register_blueprint(routes)

    # Auto-initialize database tables and default admin user for local development
    with app.app_context():
        try:
            db.create_all()
            # Seed default admin user if user table is empty
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    full_name='Store Administrator',
                    role='Admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Default administrator account created: admin / admin123")
        except Exception as e:
            logger.warning(f"Database table verification deferred: {e}")

    return app
