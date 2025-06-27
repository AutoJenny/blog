"""Decorators for workflow API endpoints."""

from functools import wraps
import warnings
from flask import request, current_app, redirect, url_for, jsonify
import psycopg2
from app.db import get_db_conn
import logging

def deprecated_endpoint(new_endpoint=None, message=None):
    """
    Decorator to mark an endpoint as deprecated.
    Logs a warning and redirects to the new endpoint.
    
    Args:
        new_endpoint (str, optional): The new endpoint to redirect to
        message (str, optional): Custom deprecation message
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            warning_msg = message or f"Deprecated endpoint {request.path} accessed. Please use {new_endpoint} instead."
            current_app.logger.warning(warning_msg)
            
            if request.method == 'GET' and new_endpoint:
                return redirect(new_endpoint)
            else:
                # For POST/PUT/etc, return a deprecation notice
                return jsonify({
                    'status': 'error',
                    'message': warning_msg,
                    'new_endpoint': new_endpoint
                }), 410  # 410 Gone
        return decorated_function
    return decorator

def handle_workflow_errors(f):
    """Decorator to handle common workflow errors."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Workflow error: {str(e)}")
            return jsonify({'error': str(e)}), 500
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