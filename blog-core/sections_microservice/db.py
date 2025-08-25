import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from dotenv import load_dotenv, dotenv_values

logger = logging.getLogger(__name__)

def get_db_conn():
    """Get a database connection for the sections microservice."""
    try:
        # Load DATABASE_URL from assistant_config.env in the parent blog-core directory
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assistant_config.env')
        config = dotenv_values(config_path)
        
        # Parse DATABASE_URL if present
        database_url = config.get('DATABASE_URL')
        if database_url:
            # Parse the DATABASE_URL
            import re
            match = re.match(r"postgres(?:ql)?://([^:]+)(?::([^@]+))?@([^:/]+)(?::(\d+))?/([^\s]+)", database_url)
            if match:
                user = match.group(1)
                password = match.group(2)
                host = match.group(3)
                port = match.group(4) or '5432'
                dbname = match.group(5)
                
                conn = psycopg2.connect(
                    dbname=dbname,
                    user=user,
                    password=password,
                    host=host,
                    port=port,
                    cursor_factory=RealDictCursor
                )
                return conn
        
        # Fallback to environment variables
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'blog'),
            user=os.getenv('DB_USER', 'nickfiddes'),
            password=os.getenv('DB_PASSWORD', ''),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise 