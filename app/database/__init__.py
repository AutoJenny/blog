import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_db_conn():
    """Get database connection for minimal setup in llm-actions branch"""
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('DB_NAME', 'blog'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', ''),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None 