"""Decorators for workflow API endpoints."""

from functools import wraps
import warnings
from flask import request, current_app, redirect, url_for, jsonify
import psycopg2
from app.db import get_db_conn

def deprecated_endpoint(redirect_endpoint=None, message=None):
    """
    Decorator to mark an endpoint as deprecated.
    
    Args:
        redirect_endpoint (str, optional): The endpoint to redirect to. If provided,
            will redirect instead of executing the decorated function.
        message (str, optional): Custom deprecation message. If not provided,
            a default message will be used.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warning_message = message or (
                f"Endpoint {request.path} is deprecated. "
                f"Use /api/v1/workflow/run_llm/ instead."
            )
            
            # Log the deprecation
            current_app.logger.warning(
                f"Deprecated endpoint {request.path} called from {request.remote_addr}"
            )
            warnings.warn(warning_message, DeprecationWarning, stacklevel=2)
            
            # If redirect endpoint is provided, redirect instead of executing
            if redirect_endpoint:
                return redirect(url_for(redirect_endpoint))
            
            # Add deprecation notice to response headers
            response = func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['Warning'] = '299 - "This endpoint is deprecated"'
            
            return response
        return wrapper
    return decorator 

def handle_workflow_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except psycopg2.Error as e:
            return jsonify({
                'error': 'Database error',
                'message': str(e)
            }), 500
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    return decorated_function

def validate_post_id(f):
    """Validate that the post_id exists in the database."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        post_id = kwargs.get('post_id')
        if not post_id:
            return jsonify({'error': 'Missing post_id parameter'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
                if not cur.fetchone():
                    return jsonify({'error': 'Post not found'}), 404
        return f(*args, **kwargs)
    return decorated_function

def validate_step_id(f):
    """Validate that the step_id exists in the database."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        step_id = kwargs.get('step_id')
        if not step_id:
            return jsonify({'error': 'Missing step_id parameter'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM workflow_step_entity WHERE id = %s", (step_id,))
                if not cur.fetchone():
                    return jsonify({'error': 'Step not found'}), 404
        return f(*args, **kwargs)
    return decorated_function