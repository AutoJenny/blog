import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def get_db_conn():
    """Get a database connection."""
    try:
        conn = psycopg2.connect(
            dbname=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise 