"""Test fixtures for workflow navigation module."""

import pytest
from flask import Flask
from modules.nav import bp as nav_bp

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'DATABASE_URL': 'postgresql://localhost/blog_test'
    })
    
    # Register the nav blueprint
    app.register_blueprint(nav_bp, url_prefix='/workflow_nav')
    
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner() 