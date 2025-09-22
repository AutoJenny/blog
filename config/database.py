# config/database.py
import psycopg
from psycopg.rows import dict_row
from config.unified_config import get_config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Unified database connection manager."""
    
    def __init__(self, config_name=None):
        self.config = get_config(config_name)
        self._connection = None
    
    def get_connection(self):
        """Get database connection with proper configuration."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg.connect(
                    self.config.DATABASE_URL,
                    row_factory=dict_row
                )
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self._connection
    
    def get_cursor(self):
        """Get database cursor."""
        return self.get_connection().cursor()
    
    def close_connection(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute a query and return results."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_update(self, query, params=None):
        """Execute an update query."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()
