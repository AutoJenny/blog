import pytest
from flask import Flask
from flask_migrate import Migrate
from app.api.base import APIBlueprint
from app.api.llm import bp as llm_bp
from app.api.llm.models import Action, ActionRun
from app.api.llm.schemas import ActionSchema, ActionRunSchema
from app.api.llm.services import execute_action
from app.extensions import db

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://test:test@localhost:5432/test_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app

@pytest.fixture
def client(app):
    app.register_blueprint(llm_bp)
    db.init_app(app)
    Migrate(app, db)
    return app.test_client()

def test_migration_creation():
    """Test that migrations can be created."""
    from flask_migrate import upgrade, downgrade
    
    # Test upgrade
    try:
        upgrade()
        assert True
    except Exception as e:
        pytest.fail(f"Migration upgrade failed: {str(e)}")
    
    # Test downgrade
    try:
        downgrade()
        assert True
    except Exception as e:
        pytest.fail(f"Migration downgrade failed: {str(e)}")

def test_migration_rollback():
    """Test that migrations can be rolled back."""
    from flask_migrate import upgrade, downgrade
    
    # Upgrade to latest version
    upgrade()
    
    # Create test data
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    db.session.add(action)
    db.session.commit()
    
    # Rollback one version
    downgrade()
    
    # Verify data is gone
    assert Action.query.count() == 0

def test_migration_data_preservation():
    """Test that data is preserved during migrations."""
    from flask_migrate import upgrade, downgrade
    
    # Upgrade to latest version
    upgrade()
    
    # Create test data
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    db.session.add(action)
    db.session.commit()
    
    # Store data for comparison
    action_data = {
        "name": action.name,
        "description": action.description,
        "input_field": action.input_field,
        "output_field": action.output_field,
        "model": action.model,
        "status": action.status
    }
    
    # Downgrade and upgrade
    downgrade()
    upgrade()
    
    # Verify data is preserved
    action = Action.query.first()
    assert action is not None
    assert action.name == action_data["name"]
    assert action.description == action_data["description"]
    assert action.input_field == action_data["input_field"]
    assert action.output_field == action_data["output_field"]
    assert action.model == action_data["model"]
    assert action.status == action_data["status"]

def test_migration_constraints():
    """Test that database constraints are properly enforced."""
    from flask_migrate import upgrade
    
    # Upgrade to latest version
    upgrade()
    
    # Test unique constraint
    action1 = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    db.session.add(action1)
    db.session.commit()
    
    action2 = Action(
        name="Test Action",  # Same name as action1
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    db.session.add(action2)
    
    with pytest.raises(Exception):
        db.session.commit()
    
    db.session.rollback()

def test_migration_indexes():
    """Test that database indexes are properly created."""
    from flask_migrate import upgrade
    from sqlalchemy import inspect
    
    # Upgrade to latest version
    upgrade()
    
    # Get inspector
    inspector = inspect(db.engine)
    
    # Check indexes on actions table
    indexes = inspector.get_indexes("actions")
    assert any(index["name"] == "ix_actions_name" for index in indexes)
    assert any(index["name"] == "ix_actions_status" for index in indexes)
    
    # Check indexes on action_runs table
    indexes = inspector.get_indexes("action_runs")
    assert any(index["name"] == "ix_action_runs_action_id" for index in indexes)
    assert any(index["name"] == "ix_action_runs_status" for index in indexes)

def test_migration_foreign_keys():
    """Test that foreign keys are properly created."""
    from flask_migrate import upgrade
    from sqlalchemy import inspect
    
    # Upgrade to latest version
    upgrade()
    
    # Get inspector
    inspector = inspect(db.engine)
    
    # Check foreign keys on action_runs table
    foreign_keys = inspector.get_foreign_keys("action_runs")
    assert any(fk["referred_table"] == "actions" for fk in foreign_keys)
    assert any(fk["constrained_columns"] == ["action_id"] for fk in foreign_keys)

def test_migration_defaults():
    """Test that default values are properly set."""
    from flask_migrate import upgrade
    
    # Upgrade to latest version
    upgrade()
    
    # Create action without status
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4"
    )
    db.session.add(action)
    db.session.commit()
    
    # Verify default status
    assert action.status == "active"
    
    # Create action run without status
    action_run = ActionRun(
        action_id=action.id,
        input_data={"idea_seed": "Test idea"},
        output_data={"summary": "Test summary"}
    )
    db.session.add(action_run)
    db.session.commit()
    
    # Verify default status
    assert action_run.status == "pending" 