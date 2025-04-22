"""Test configuration and fixtures."""

import os
import tempfile
import pytest
from datetime import datetime, UTC
from flask_login import LoginManager
from app import create_app, db
from app.models import User
from tests.config import TestConfig

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.from_object(TestConfig)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create the database and the database tables
    with app.app_context():
        db.create_all()
        
        # Create a test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            created_at=datetime.now(UTC)
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
    
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def auth(client):
    """Authentication helper for tests."""
    class AuthActions:
        def __init__(self, client):
            self._client = client
            self._config = TestConfig

        def login(self, email=None, password=None):
            return self._client.post(
                '/auth/login',
                data={
                    'email': email or self._config.TEST_USER_EMAIL,
                    'password': password or self._config.TEST_USER_PASSWORD
                }
            )

        def logout(self):
            return self._client.get('/auth/logout')

    return AuthActions(client)

@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            email=TestConfig.TEST_USER_EMAIL,
            name='Test User',
            is_admin=True
        )
        user.set_password(TestConfig.TEST_USER_PASSWORD)
        db.session.add(user)
        db.session.commit()
        return user 