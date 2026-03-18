import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import dotenv_values

def get_db_conn():
    """Get a database connection."""
    # Load DATABASE_URL from assistant_config.env
    config_path = os.path.join(os.path.dirname(__file__), 'assistant_config.env')
    config = dotenv_values(config_path)
    database_url = config.get('DATABASE_URL')
    if database_url:
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
    raise Exception('DATABASE_URL not found in assistant_config.env')

def test_db_connection():
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute('SELECT 1 AS test')
            result = cur.fetchone()
        conn.close()
        return result['test'] == 1
    except Exception as e:
        print(f"DB connection test failed: {e}")
        return False 