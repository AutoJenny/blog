"""
Content Process Database Models
Handles content process registry and configuration management
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ContentProcess:
    """Model for content process management"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
    
    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def get_all_processes(self) -> List[Dict[str, Any]]:
        """Get all active content processes with platform information"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            cp.id, cp.process_name, cp.display_name, cp.platform_id,
                            cp.content_type, cp.description, cp.is_active, cp.priority,
                            cp.development_status, cp.created_at, cp.updated_at,
                            smp.platform_name, smp.display_name as platform_display_name
                        FROM social_media_content_processes cp
                        JOIN social_media_platforms smp ON cp.platform_id = smp.id
                        WHERE cp.is_active = true
                        ORDER BY cp.platform_id, cp.priority, cp.display_name
                    """)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching all processes: {e}")
            return []
    
    def get_processes_by_platform(self, platform_id: int) -> List[Dict[str, Any]]:
        """Get all processes for a specific platform"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            cp.id, cp.process_name, cp.display_name, cp.platform_id,
                            cp.content_type, cp.description, cp.is_active, cp.priority,
                            cp.development_status, cp.created_at, cp.updated_at,
                            smp.platform_name, smp.display_name as platform_display_name
                        FROM social_media_content_processes cp
                        JOIN social_media_platforms smp ON cp.platform_id = smp.id
                        WHERE cp.platform_id = %s AND cp.is_active = true
                        ORDER BY cp.priority, cp.display_name
                    """, (platform_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching processes for platform {platform_id}: {e}")
            return []
    
    def get_processes_by_development_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all processes with a specific development status"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            cp.id, cp.process_name, cp.display_name, cp.platform_id,
                            cp.content_type, cp.description, cp.is_active, cp.priority,
                            cp.development_status, cp.created_at, cp.updated_at,
                            smp.platform_name, smp.display_name as platform_display_name
                        FROM social_media_content_processes cp
                        JOIN social_media_platforms smp ON cp.platform_id = smp.id
                        WHERE cp.development_status = %s AND cp.is_active = true
                        ORDER BY cp.platform_id, cp.priority, cp.display_name
                    """, (status,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching processes by status {status}: {e}")
            return []
    
    def get_process_by_name(self, process_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific process by name"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            cp.id, cp.process_name, cp.display_name, cp.platform_id,
                            cp.content_type, cp.description, cp.is_active, cp.priority,
                            cp.development_status, cp.created_at, cp.updated_at,
                            smp.platform_name, smp.display_name as platform_display_name
                        FROM social_media_content_processes cp
                        JOIN social_media_platforms smp ON cp.platform_id = smp.id
                        WHERE cp.process_name = %s AND cp.is_active = true
                    """, (process_name,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error fetching process {process_name}: {e}")
            return None
    
    def get_process_configs(self, process_id: int) -> List[Dict[str, Any]]:
        """Get all configurations for a specific process"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, process_id, config_category, config_key, config_value,
                               config_type, is_required, display_order
                        FROM social_media_process_configs
                        WHERE process_id = %s
                        ORDER BY config_category, display_order
                    """, (process_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching configs for process {process_id}: {e}")
            return []
    
    def get_process_configs_by_category(self, process_id: int, category: str) -> List[Dict[str, Any]]:
        """Get configurations for a specific process and category"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, process_id, config_category, config_key, config_value,
                               config_type, is_required, display_order
                        FROM social_media_process_configs
                        WHERE process_id = %s AND config_category = %s
                        ORDER BY display_order
                    """, (process_id, category))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching configs for process {process_id}, category {category}: {e}")
            return []
    
    def create_process_execution(self, process_id: int, post_id: int, section_id: int, 
                               status: str = 'pending') -> Optional[int]:
        """Create a new process execution record"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO social_media_process_executions
                        (process_id, post_id, section_id, status, started_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        RETURNING id
                    """, (process_id, post_id, section_id, status))
                    execution_id = cur.fetchone()[0]
                    conn.commit()
                    return execution_id
        except Exception as e:
            logger.error(f"Error creating process execution: {e}")
            return None
    
    def update_execution_status(self, execution_id: int, status: str, 
                              result_data: Optional[str] = None) -> bool:
        """Update the status of a process execution"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE social_media_process_executions
                        SET status = %s, result_data = %s, completed_at = NOW()
                        WHERE id = %s
                    """, (status, result_data, execution_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating execution status: {e}")
            return False
    
    def get_execution_history(self, process_id: Optional[int] = None, 
                            post_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history with optional filters"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                        SELECT 
                            e.id, e.process_id, e.post_id, e.section_id, e.status,
                            e.started_at, e.completed_at, e.result_data,
                            cp.process_name, cp.display_name
                        FROM social_media_process_executions e
                        JOIN social_media_content_processes cp ON e.process_id = cp.id
                        WHERE 1=1
                    """
                    params = []
                    
                    if process_id:
                        query += " AND e.process_id = %s"
                        params.append(process_id)
                    
                    if post_id:
                        query += " AND e.post_id = %s"
                        params.append(post_id)
                    
                    query += " ORDER BY e.started_at DESC LIMIT %s"
                    params.append(limit)
                    
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as e:
                    logger.error(f"Error fetching execution history: {e}")
        return []
    
    def update_config_value(self, config_id: int, new_value: str) -> bool:
        """Update a specific configuration value."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE social_media_process_configs
                        SET config_value = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_value, config_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating config value: {e}")
            return False
    
    def update_development_status(self, process_id: int, new_status: str) -> bool:
        """Update the development status of a content process."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE social_media_content_processes
                        SET development_status = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_status, process_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating development status: {e}")
            return False
