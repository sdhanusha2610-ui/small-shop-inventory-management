import os
import pytest
from decimal import Decimal
from app import create_app
from app.models import db, User, Product, Sale, StockHistory


@pytest.fixture(scope='session')
def app():
    """Create application configured for automated testing with in-memory SQLite."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['ENABLE_SNS_ALERTS'] = 'false'
    _app = create_app('testing')

    with _app.app_context():
        db.create_all()
        yield _app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Test client for simulating HTTP requests."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Provides a clean database state for each test function."""
    with app.app_context():
        # Clean existing tables
        StockHistory.query.delete()
        Sale.query.delete()
        Product.query.delete()
        User.query.delete()
        db.session.commit()

        # Seed standard test admin user
        admin = User(
            username='admin',
            full_name='Test Administrator',
            role='Admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Seed standard test product
        milk = Product(
            sku='TEST-MILK',
            name='Test Whole Milk 1L',
            category='Dairy',
            price=Decimal('3.50'),
            cost_price=Decimal('2.00'),
            quantity=10,
            min_stock_level=5,
            is_low_stock_notified=False
        )
        db.session.add(milk)
        db.session.commit()

        yield db.session

        db.session.rollback()


@pytest.fixture(scope='function')
def auth_client(client, db_session):
    """Test client that is pre-authenticated as admin."""
    with client.session_transaction() as sess:
        admin_user = User.query.filter_by(username='admin').first()
        sess['user_id'] = admin_user.id
        sess['username'] = admin_user.username
        sess['role'] = admin_user.role
    return client
