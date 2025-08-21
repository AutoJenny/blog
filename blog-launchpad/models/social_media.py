"""
Social Media Platform Database Models
Handles social media platform data and specifications
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SocialMediaPlatform:
    """Model for social media platform management"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
    
    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def get_all_platforms(self) -> List[Dict[str, Any]]:
        """Get all social media platforms with their status"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, platform_name, display_name, status, priority, icon_url
                        FROM social_media_platforms
                        ORDER BY priority, display_name
                    """)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching platforms: {e}")
            return []
    
    def get_platform_by_name(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific platform by name"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, platform_name, display_name, status, priority, icon_url
                        FROM social_media_platforms
                        ORDER BY priority, display_name
                    """, (platform_name,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error fetching platform {platform_name}: {e}")
            return None
    
    def get_platform_specifications(self, platform_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get all specifications for a platform, organized by category"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, spec_category, spec_key, spec_value, spec_type, 
                               is_required, display_order
                        FROM social_media_platform_specs
                        WHERE platform_id = %s
                        ORDER BY spec_category, display_order
                    """, (platform_id,))
                    
                    specs = cur.fetchall()
                    
                    # Organize by category
                    organized_specs = {}
                    for spec in specs:
                        category = spec['spec_category']
                        if category not in organized_specs:
                            organized_specs[category] = []
                        organized_specs[category].append(spec)
                    
                    return organized_specs
        except Exception as e:
            logger.error(f"Error fetching specifications for platform {platform_id}: {e}")
            return {}
    
    def get_platform_with_specs(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get platform with all its specifications"""
        platform = self.get_platform_by_name(platform_name)
        if not platform:
            return None
        
        specs = self.get_platform_specifications(platform['id'])
        platform['specifications'] = specs
        return platform
    
    def update_platform_status(self, platform_name: str, new_status: str) -> bool:
        """Update platform status (undeveloped, developed, active)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE social_media_platforms
                        SET status = %s
                        WHERE platform_name = %s
                    """, (new_status, platform_name))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating platform status: {e}")
            return False
    
    def get_platforms_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all platforms with a specific status"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, platform_name, display_name, status, priority, icon_url
                        FROM social_media_platforms
                        ORDER BY priority, display_name
                    """, (status,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching platforms by status {status}: {e}")
            return []

class SocialMediaSpecification:
    """Model for managing platform specifications"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
    
    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def update_specification(self, platform_id: int, category: str, key: str, 
                           new_value: str) -> bool:
        """Update a specific specification value"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE social_media_platform_specs
                        SET spec_value = %s
                        WHERE platform_id = %s AND spec_category = %s AND spec_key = %s
                    """, (new_value, platform_id, category, key))
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating specification: {e}")
            return False
    
    def add_specification(self, platform_id: int, category: str, key: str, 
                         value: str, spec_type: str = 'text', 
                         is_required: bool = False, display_order: int = 0) -> bool:
        """Add a new specification"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO social_media_platform_specs
                        (platform_id, spec_category, spec_key, spec_value, spec_type, 
                         is_required, display_order)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (platform_id, spec_category, spec_key)
                        DO UPDATE SET spec_value = EXCLUDED.spec_value,
                                    spec_type = EXCLUDED.spec_type,
                                    is_required = EXCLUDED.is_required,
                                    display_order = EXCLUDED.display_order
                    """, (platform_id, category, key, value, spec_type, is_required, display_order))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding specification: {e}")
            return False
    
    def delete_specification(self, spec_id: int) -> bool:
        """Delete a specification by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM social_media_platform_specs
                        WHERE id = %s
                    """, (spec_id,))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting specification: {e}")
            return False
    
    def update_specification_by_id(self, spec_id: int, new_value: str) -> bool:
        """Update a specification by its ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE social_media_platform_specs
                        SET spec_value = %s
                        WHERE id = %s
                    """, (new_value, spec_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating specification by ID: {e}")
            return False
