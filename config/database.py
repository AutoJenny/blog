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
        # Always create a new connection to avoid transaction state issues
        try:
            connection = psycopg.connect(
                self.config.DATABASE_URL,
                row_factory=dict_row
            )
            logger.info("Database connection established")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_cursor(self):
        """Get database cursor with proper context management."""
        return self.get_connection().cursor()
    
    def __enter__(self):
        """Context manager entry."""
        return self.get_cursor()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure proper cleanup."""
        if exc_type is not None:
            # If there was an exception, rollback the transaction
            try:
                if hasattr(self, '_connection') and self._connection and not self._connection.closed:
                    self._connection.rollback()
                    logger.info("Transaction rolled back due to exception")
            except Exception as e:
                logger.error(f"Error during rollback: {e}")
    
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
