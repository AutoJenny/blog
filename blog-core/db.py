import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
import logging
import os
from dotenv import load_dotenv, dotenv_values

logger = logging.getLogger(__name__)

def get_db_conn():
    """Get a database connection."""
    try:
        # Load DATABASE_URL from assistant_config.env
        config_path = os.path.join(os.path.dirname(__file__), 'assistant_config.env')
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
        
        # If DATABASE_URL not found, raise an error
        raise Exception("DATABASE_URL not found in assistant_config.env")
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise 