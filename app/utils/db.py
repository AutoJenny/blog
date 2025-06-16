import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection pool
connection_pool = None

def init_db_pool():
    """Initialize the database connection pool."""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname=os.getenv('POSTGRES_DB', 'blog'),
            user=os.getenv('POSTGRES_USER', 'nickfiddes'),
            password=os.getenv('POSTGRES_PASSWORD', ''),
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {str(e)}")
        raise

@contextmanager
def get_db_conn():
    """Get a database connection from the pool with automatic cleanup."""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute a read-only query safely."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(query, params or {})
                return cur.fetchall()
            except Exception as e:
                logger.error(f"Query execution error: {str(e)}")
                raise

def execute_transaction(queries: List[tuple]) -> None:
    """Execute multiple queries in a transaction."""
    with get_db_conn() as conn:
        try:
            with conn.cursor() as cur:
                for query, params in queries:
                    cur.execute(query, params or {})
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction error: {str(e)}")
            raise

def verify_workflow_tables() -> bool:
    """Verify that all required workflow tables exist and are accessible."""
    required_tables = [
        'workflow_stage_entity',
        'workflow_sub_stage_entity',
        'workflow_step_entity',
        'post_workflow_stage',
        'post_workflow_step_action'
    ]
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                for table in required_tables:
                    cur.execute(f"SELECT 1 FROM {table} LIMIT 1")
        return True
    except Exception as e:
        logger.error(f"Workflow table verification failed: {str(e)}")
        return False

def get_workflow_stages() -> List[Dict[str, Any]]:
    """Get all workflow stages with their sub-stages and steps."""
    query = """
    SELECT 
        wse.id as stage_id,
        wse.name as stage_name,
        wse.stage_order,
        wsse.id as sub_stage_id,
        wsse.name as sub_stage_name,
        wsse.sub_stage_order,
        wste.id as step_id,
        wste.name as step_name,
        wste.step_order
    FROM workflow_stage_entity wse
    LEFT JOIN workflow_sub_stage_entity wsse ON wse.id = wsse.stage_id
    LEFT JOIN workflow_step_entity wste ON wsse.id = wste.sub_stage_id
    ORDER BY wse.stage_order, wsse.sub_stage_order, wste.step_order
    """
    return execute_query(query)

def get_post_workflow_status(post_id: int) -> List[Dict[str, Any]]:
    """Get the workflow status for a specific post."""
    query = """
    SELECT 
        pws.*,
        wse.name as stage_name,
        wsse.name as sub_stage_name,
        wste.name as step_name
    FROM post_workflow_stage pws
    JOIN workflow_stage_entity wse ON pws.stage_id = wse.id
    LEFT JOIN workflow_sub_stage_entity wsse ON wse.id = wsse.stage_id
    LEFT JOIN workflow_step_entity wste ON wsse.id = wste.sub_stage_id
    WHERE pws.post_id = %(post_id)s
    ORDER BY wse.stage_order, wsse.sub_stage_order, wste.step_order
    """
    return execute_query(query, {'post_id': post_id})

def update_post_workflow_status(post_id: int, stage_id: int, status: str) -> None:
    """Update the workflow status for a post."""
    query = """
    UPDATE post_workflow_stage
    SET status = %(status)s
    WHERE post_id = %(post_id)s
    AND stage_id = %(stage_id)s
    """
    execute_transaction([(query, {'post_id': post_id, 'stage_id': stage_id, 'status': status})])

def get_workflow_step_actions(step_id: int) -> List[Dict[str, Any]]:
    """Get all LLM actions configured for a workflow step."""
    query = """
    SELECT 
        la.*,
        pwsa.button_label,
        pwsa.button_order
    FROM llm_action la
    LEFT JOIN post_workflow_step_action pwsa ON la.id = pwsa.action_id
    WHERE pwsa.step_id = %(step_id)s
    ORDER BY pwsa.button_order
    """
    return execute_query(query, {'step_id': step_id})

# Initialize the connection pool when the module is imported
init_db_pool() 