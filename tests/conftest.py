"""Test configuration and fixtures."""

import os
import tempfile
import pytest
from datetime import datetime, UTC
from app import create_app, db
from tests.test_config import TestConfig
from sqlalchemy import text


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        # Patch: Drop all tables with CASCADE to avoid FK constraint errors
        engine = db.get_engine()
        with engine.connect() as conn:
            conn.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
        # db.drop_all()  # Removed: schema drop already removes all tables


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def setup_and_teardown_db(app):
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        # Patch: Drop all tables with CASCADE to avoid FK constraint errors
        engine = db.get_engine()
        with engine.connect() as conn:
            conn.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
        # db.drop_all()  # Removed: schema drop already removes all tables
