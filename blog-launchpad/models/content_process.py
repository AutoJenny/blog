"""
Content Process Registry Database Models
Handles LLM-based content conversion processes for social media syndication
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
        """Get all content processes"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cp.*, p.platform_name, p.display_name as platform_display_name
                        FROM social_media_content_processes cp
                        JOIN social_media_platforms p ON cp.platform_id = p.id
                        WHERE cp.is_active = true
                        ORDER BY cp.priority, cp.display_name
                    """)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching content processes: {e}")
            return []
    
    def get_processes_by_platform(self, platform_id: int) -> List[Dict[str, Any]]:
        """Get all processes for a specific platform"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cp.*, p.platform_name, p.display_name as platform_display_name
                        FROM social_media_content_processes cp
                        JOIN social_media_platforms p ON cp.platform_id = p.id
                        WHERE cp.platform_id = %s AND cp.is_active = true
                        ORDER BY cp.priority, cp.display_name
                    """, (platform_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching processes for platform {platform_id}: {e}")
            return []
    
    def get_process_by_name(self, process_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific process by name"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT cp.*, p.platform_name, p.display_name as platform_display_name
                        FROM social_media_content_processes cp
                        JOIN social_media_platforms p ON cp.platform_id = p.id
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
                        SELECT config_category, config_key, config_value, config_type, is_required, display_order
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
                        SELECT config_key, config_value, config_type, is_required
                        FROM social_media_process_configs
                        WHERE process_id = %s AND config_category = %s
                        ORDER BY display_order
                    """, (process_id, category))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching configs for process {process_id}, category {category}: {e}")
            return []
    
    def create_process_execution(self, process_id: int, post_id: int, section_id: int, 
                                input_content: str, status: str = 'pending') -> Optional[int]:
        """Create a new process execution record"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO social_media_process_executions 
                        (process_id, post_id, section_id, input_content, execution_status)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (process_id, post_id, section_id, input_content, status))
                    execution_id = cur.fetchone()[0]
                    conn.commit()
                    return execution_id
        except Exception as e:
            logger.error(f"Error creating process execution: {e}")
            return None
    
    def update_execution_status(self, execution_id: int, status: str, 
                               output_content: str = None, error_message: str = None,
                               processing_time_ms: int = None) -> bool:
        """Update the status of a process execution"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    update_fields = ["execution_status = %s"]
                    params = [status]
                    
                    if output_content is not None:
                        update_fields.append("output_content = %s")
                        params.append(output_content)
                    
                    if error_message is not None:
                        update_fields.append("error_message = %s")
                        params.append(error_message)
                    
                    if processing_time_ms is not None:
                        update_fields.append("processing_time_ms = %s")
                        params.append(processing_time_ms)
                    
                    params.append(execution_id)
                    
                    cur.execute(f"""
                        UPDATE social_media_process_executions 
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                    """, params)
                    
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating execution status: {e}")
            return False
    
    def get_execution_history(self, process_id: int = None, post_id: int = None, 
                             limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history with optional filtering"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                        SELECT e.*, cp.process_name, cp.display_name as process_display_name
                        FROM social_media_process_executions e
                        JOIN social_media_content_processes cp ON e.process_id = cp.id
                    """
                    params = []
                    conditions = []
                    
                    if process_id:
                        conditions.append("e.process_id = %s")
                        params.append(process_id)
                    
                    if post_id:
                        conditions.append("e.post_id = %s")
                        params.append(post_id)
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                    
                    query += " ORDER BY e.created_at DESC LIMIT %s"
                    params.append(limit)
                    
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching execution history: {e}")
            return []
