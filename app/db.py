import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def get_db_conn():
    """Get a database connection."""
    try:
        # Parse the DATABASE_URL
        db_url = urlparse(current_app.config['DATABASE_URL'])
        db_params = {
            'dbname': db_url.path[1:],  # Remove leading slash
            'user': db_url.username,
            'password': db_url.password,
            'host': db_url.hostname,
            'port': db_url.port or 5432,
            'cursor_factory': RealDictCursor
        }
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise 