import pytest
from flask import Flask, jsonify
from app.api.base import APIBlueprint
from marshmallow import Schema, fields
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    return app

@pytest.fixture
def bp(app):
    bp = APIBlueprint("test", __name__)
    bp.init_app(app)
    return bp

@pytest.fixture
def client(app, bp):
    app.register_blueprint(bp)
    return app.test_client()

def test_route_decorator(client):
    """Test that the route decorator adds common functionality."""
    @bp.route("/test")
    def test_route():
        return {"message": "test"}
        
    response = client.get("/test")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["message"] == "test"

def test_validation_decorator(client):
    """Test that the validation decorator validates request data."""
    class TestSchema(Schema):
        name = fields.String(required=True)
        
    @bp.route("/test", methods=["POST"])
    @bp.validate_request(TestSchema)
    def test_route(validated_data):
        return validated_data
        
    # Test valid data
    response = client.post("/test", json={"name": "test"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["name"] == "test"
    
    # Test invalid data
    response = client.post("/test", json={})
    assert response.status_code == 422
    data = response.get_json()
    assert data["status"] == "error"
    assert "name" in data["errors"]

def test_auth_decorator(app, client):
    """Test that the auth decorator requires JWT authentication."""
    @bp.route("/test")
    @bp.require_auth
    def test_route(user_id):
        return {"user_id": user_id}
        
    # Test without token
    response = client.get("/test")
    assert response.status_code == 401
    
    # Test with token
    with app.app_context():
        access_token = create_access_token(identity=1)
        response = client.get("/test", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["user_id"] == 1

def test_version_decorator(client):
    """Test that the version decorator adds version to response."""
    @bp.route("/test")
    @bp.version("v1")
    def test_route():
        return {"message": "test"}
        
    response = client.get("/test")
    assert response.status_code == 200
    data = response.get_json()
    assert data["version"] == "v1"

def test_error_handlers(client):
    """Test that error handlers return proper responses."""
    @bp.route("/400")
    def test_400():
        return "Bad request", 400
        
    @bp.route("/401")
    def test_401():
        return "Unauthorized", 401
        
    @bp.route("/403")
    def test_403():
        return "Forbidden", 403
        
    @bp.route("/404")
    def test_404():
        return "Not found", 404
        
    @bp.route("/405")
    def test_405():
        return "Method not allowed", 405
        
    @bp.route("/500")
    def test_500():
        return "Internal server error", 500
        
    # Test 400
    response = client.get("/400")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert data["message"] == "Bad request"
    
    # Test 401
    response = client.get("/401")
    assert response.status_code == 401
    data = response.get_json()
    assert data["status"] == "error"
    assert data["message"] == "Unauthorized"
    
    # Test 403
    response = client.get("/403")
    assert response.status_code == 403
    data = response.get_json()
    assert data["status"] == "error"
    assert data["message"] == "Forbidden"
    
    # Test 404
    response = client.get("/404")
    assert response.status_code == 404
    data = response.get_json()
    assert data["status"] == "error"
    assert data["message"] == "Not found"
    
    # Test 405
    response = client.get("/405")
    assert response.status_code == 405
    data = response.get_json()
    assert data["status"] == "error"
    assert data["message"] == "Method not allowed"
    
    # Test 500
    response = client.get("/500")
    assert response.status_code == 500
    data = response.get_json()
    assert data["status"] == "error"
    assert data["message"] == "Internal server error" 