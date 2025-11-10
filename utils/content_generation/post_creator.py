"""
Post Creator

Handles creation of post records and sections from generated content.
"""

import logging
import re
from typing import Dict, List, Optional
from config.database import db_manager

logger = logging.getLogger(__name__)


class PostCreator:
    """Creates blog posts and sections from generated content."""
    
    def __init__(self):
        pass
    
    def generate_slug(self, title: str) -> str:
        """
        Generate URL-friendly slug from title.
        
        Args:
            title: Post title
            
        Returns:
            URL-friendly slug
        """
        # Convert to lowercase
        slug = title.lower()
        
        # Replace spaces and special characters with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Ensure uniqueness by adding timestamp if needed
        # (This is a simple version - in production you'd check DB)
        import time
        if not slug:
            slug = f"post-{int(time.time())}"
        else:
            slug = f"{slug}-{int(time.time())}"
        
        return slug
    
    def create_post(self, title: str, standfirst: str, 
                    idea_seed: str, expanded_idea: Optional[str] = None) -> int:
        """
        Create a new post record.
        
        Args:
            title: Post title
            standfirst: Post summary/standfirst
            idea_seed: Idea seed text
            expanded_idea: Optional expanded idea/outline
            
        Returns:
            Post ID
        """
        slug = self.generate_slug(title)
        
        with db_manager.get_cursor() as cursor:
            # Create post record
            cursor.execute("""
                INSERT INTO post (title, slug, summary, status, created_at, updated_at)
                VALUES (%s, %s, %s, 'draft', NOW(), NOW())
                RETURNING id
            """, (title, slug, standfirst))
            
            post_id = cursor.fetchone()['id']
            
            # Create post_development record
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed, expanded_idea)
                VALUES (%s, %s, %s)
            """, (post_id, idea_seed, expanded_idea or ''))
            
            logger.info(f"Created post {post_id}: {title}")
            
            return post_id
    
    def create_section(self, post_id: int, heading: str, content: str,
                      section_type: str = 'body', section_order: int = 1) -> int:
        """
        Create a post section.
        
        Args:
            post_id: Post ID
            heading: Section heading
            content: Section content (HTML)
            section_type: Section type (default: 'body')
            section_order: Section order (default: 1)
            
        Returns:
            Section ID
        """
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO post_section 
                (post_id, section_type, section_heading, polished, section_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (post_id, section_type, heading, content, section_order))
            
            section_id = cursor.fetchone()['id']
            
            logger.info(f"Created section {section_id} for post {post_id}: {heading}")
            
            return section_id
    
    def create_sections_from_generated(self, post_id: int, sections: List[Dict],
                                       start_order: int = 1) -> List[int]:
        """
        Create multiple sections from generated content.
        
        Args:
            post_id: Post ID
            sections: List of section dictionaries with 'heading' and 'content'
            start_order: Starting section order
            
        Returns:
            List of section IDs
        """
        section_ids = []
        
        for i, section in enumerate(sections):
            heading = section.get('heading', f'Section {i + 1}')
            content = section.get('content', '')
            
            if not content:
                continue
            
            section_id = self.create_section(
                post_id=post_id,
                heading=heading,
                content=content,
                section_type='body',
                section_order=start_order + i
            )
            
            section_ids.append(section_id)
        
        return section_ids
    
    def add_product_image(self, post_id: int, product_id: int, 
                         section_id: Optional[int] = None) -> Optional[int]:
        """
        Add product image as header image.
        
        Args:
            post_id: Post ID
            product_id: Product ID
            section_id: Optional section ID to link image to
            
        Returns:
            Image record ID or None
        """
        with db_manager.get_cursor() as cursor:
            # Get product image URL
            cursor.execute("""
                SELECT image_url FROM clan_products
                WHERE id = %s
            """, (product_id,))
            
            product = cursor.fetchone()
            if not product or not product.get('image_url'):
                logger.warning(f"No image URL for product {product_id}")
                return None
            
            image_url = product['image_url']
            
            # Get first section if section_id not provided
            if not section_id:
                cursor.execute("""
                    SELECT id FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                    LIMIT 1
                """, (post_id,))
                
                section_result = cursor.fetchone()
                if section_result:
                    section_id = section_result['id']
                else:
                    logger.warning(f"No sections found for post {post_id}")
                    return None
            
            # Create image record
            cursor.execute("""
                INSERT INTO post_images 
                (post_id, section_id, image_url, is_header_image, created_at)
                VALUES (%s, %s, %s, true, NOW())
                RETURNING id
            """, (post_id, section_id, image_url))
            
            image_id = cursor.fetchone()['id']
            
            logger.info(f"Added product image {image_id} for post {post_id}")
            
            return image_id

