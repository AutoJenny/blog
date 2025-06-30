"""Decorators for the application."""

from functools import wraps
from flask import jsonify, Response


def deprecated_endpoint(message=None):
    """Mark an endpoint as deprecated.
    
    Args:
        message (str, optional): Custom deprecation message. If not provided,
            a default message will be used.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Add deprecation warning to response headers
            response = f(*args, **kwargs)
            if not isinstance(response, Response):
                response = jsonify(response)
            
            response.headers['Warning'] = (
                message or 
                'This endpoint is deprecated and will be removed in a future version.'
            )
            return response
        return decorated_function
    return decorator 