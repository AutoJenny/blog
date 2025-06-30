from flask import Blueprint, jsonify, request, current_app
from functools import wraps
import time
import logging
from typing import Callable, Any, Dict, List, Optional, Union
from marshmallow import Schema, ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS
from flasgger import swag_from

class APIBlueprint(Blueprint):
    """Base blueprint class for all API endpoints with common functionality."""
    
    def __init__(self, name: str, import_name: str, url_prefix: str = None):
        super().__init__(name, import_name, url_prefix=url_prefix)
        self.logger = logging.getLogger(f"api.{name}")
        
    def init_app(self, app):
        """Initialize the blueprint with the application."""
        # Initialize CORS
        CORS(self)
        
        # Register error handlers
        @self.errorhandler(400)
        def handle_400(e):
            return jsonify({
                "status": "error",
                "message": "Bad request",
                "errors": [{"message": str(e)}]
            }), 400
            
        @self.errorhandler(401)
        def handle_401(e):
            return jsonify({
                "status": "error",
                "message": "Unauthorized",
                "errors": [{"message": str(e)}]
            }), 401
            
        @self.errorhandler(403)
        def handle_403(e):
            return jsonify({
                "status": "error",
                "message": "Forbidden",
                "errors": [{"message": str(e)}]
            }), 403
            
        @self.errorhandler(404)
        def handle_404(e):
            return jsonify({
                "status": "error",
                "message": "Not found",
                "errors": [{"message": str(e)}]
            }), 404
            
        @self.errorhandler(405)
        def handle_405(e):
            return jsonify({
                "status": "error",
                "message": "Method not allowed",
                "errors": [{"message": str(e)}]
            }), 405
            
        @self.errorhandler(500)
        def handle_500(e):
            return jsonify({
                "status": "error",
                "message": "Internal server error",
                "errors": [{"message": str(e)}]
            }), 500
        
    def route(self, rule: str, **options) -> Callable:
        """Enhanced route decorator that adds common functionality."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapped(*args, **kwargs) -> Any:
                # Start timing
                start_time = time.time()
                
                # Log request
                self.logger.info(f"Request: {request.method} {request.path}")
                
                try:
                    # Execute route handler
                    response = f(*args, **kwargs)
                    
                    # Format response
                    if isinstance(response, tuple):
                        data, status_code = response
                    else:
                        data, status_code = response, 200
                        
                    if not isinstance(data, dict):
                        data = {"data": data}
                        
                    if "status" not in data:
                        data["status"] = "success"
                        
                    # Log response time
                    duration = time.time() - start_time
                    self.logger.info(f"Response: {status_code} ({duration:.2f}s)")
                    
                    return jsonify(data), status_code
                    
                except ValidationError as e:
                    self.logger.error(f"Validation error: {str(e)}")
                    return jsonify({
                        "status": "error",
                        "message": "Validation failed",
                        "errors": e.messages
                    }), 422
                    
                except Exception as e:
                    self.logger.error(f"Error: {str(e)}", exc_info=True)
                    return jsonify({
                        "status": "error",
                        "message": "Internal server error",
                        "errors": [{"message": str(e)}]
                    }), 500
                    
            # Add route to blueprint using correct parent reference
            return Blueprint.route(self, rule, **options)(wrapped)
        return decorator
        
    def validate_request(self, schema: Schema) -> Callable:
        """Decorator to validate request data against a schema."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapped(*args, **kwargs) -> Any:
                try:
                    # Get request data
                    if request.is_json:
                        data = request.get_json()
                    else:
                        data = request.form.to_dict()
                        
                    # Validate data
                    validated_data = schema.load(data)
                    
                    # Add validated data to kwargs
                    kwargs["validated_data"] = validated_data
                    
                    return f(*args, **kwargs)
                    
                except ValidationError as e:
                    return jsonify({
                        "status": "error",
                        "message": "Validation failed",
                        "errors": e.messages
                    }), 422
                    
            return wrapped
        return decorator
        
    def require_auth(self, f: Callable) -> Callable:
        """Decorator to require JWT authentication."""
        @wraps(f)
        @jwt_required()
        def wrapped(*args, **kwargs) -> Any:
            # Add user ID to kwargs
            kwargs["user_id"] = get_jwt_identity()
            return f(*args, **kwargs)
        return wrapped
        
    def rate_limit(self, limit: int, period: int = 60) -> Callable:
        """Decorator to implement rate limiting."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapped(*args, **kwargs) -> Any:
                # TODO: Implement rate limiting
                return f(*args, **kwargs)
            return wrapped
        return decorator
        
    def version(self, version: str) -> Callable:
        """Decorator to specify API version."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapped(*args, **kwargs) -> Any:
                # Add version to response
                response = f(*args, **kwargs)
                if isinstance(response, tuple):
                    data, status_code = response
                else:
                    data, status_code = response, 200
                    
                if isinstance(data, dict):
                    data["version"] = version
                    
                return data, status_code
            return wrapped
        return decorator

    def document(self, spec: Dict[str, Any]) -> Callable:
        """Decorator to document API endpoints using Flasgger."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            @swag_from(spec)
            def wrapped(*args, **kwargs) -> Any:
                return f(*args, **kwargs)
            return wrapped
        return decorator 