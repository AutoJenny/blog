import psycopg
from psycopg.rows import dict_row
from flask import current_app
import logging
import os
from dotenv import load_dotenv, dotenv_values

logger = logging.getLogger(__name__)

def get_db_conn():
    """Get a database connection."""
    try:
        # Load DATABASE_URL from assistant_config.env
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
                
                conn = psycopg.connect(
                    dbname=dbname,
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
                return conn
        
        # Fallback to Flask config if DATABASE_URL not available
        conn = psycopg.connect(
            dbname=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise 