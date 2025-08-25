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
            
            # Handle tuple responses (response, status_code)
            if isinstance(response, tuple) and len(response) == 2:
                response_obj, status_code = response
                if isinstance(response_obj, Response):
                    response_obj.headers['Warning'] = (
                        message or 
                        'This endpoint is deprecated and will be removed in a future version.'
                    )
                    return response_obj, status_code
                else:
                    response_obj = jsonify(response_obj)
                    response_obj.headers['Warning'] = (
                        message or 
                        'This endpoint is deprecated and will be removed in a future version.'
                    )
                    return response_obj, status_code
            
            # Handle single Response objects
            elif isinstance(response, Response):
                response.headers['Warning'] = (
                    message or 
                    'This endpoint is deprecated and will be removed in a future version.'
                )
                return response
            
            # Handle other objects (dict, list, etc.)
            else:
                response = jsonify(response)
                response.headers['Warning'] = (
                    message or 
                    'This endpoint is deprecated and will be removed in a future version.'
                )
                return response
        return decorated_function
    return decorator 