import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app

def get_db_conn():
    """Get a PostgreSQL database connection."""
    try:
        # Try to get database URL from environment or config
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            # Fallback to individual environment variables
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'blog')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', '')
            
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # Create connection with dictionary cursor for easier data access
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
        
    except Exception as e:
        current_app.logger.error(f"Database connection error: {e}")
        return None 