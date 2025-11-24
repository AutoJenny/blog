"""
Post Content Extractor

Extracts and combines post content from post_development for embedding generation.
"""

import logging
from config.database import db_manager

logger = logging.getLogger(__name__)


def extract_post_content(post_id: int) -> str:
    """
    Extract and combine post content from post_development for embedding.
    
    Priority order:
    1. expanded_idea (most comprehensive)
    2. idea_seed (core concept)
    3. summary (condensed version)
    4. intro_blurb (introduction)
    5. basic_idea (fallback)
    
    Args:
        post_id: Post ID
        
    Returns:
        Combined text content for embedding
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT expanded_idea, idea_seed, summary, intro_blurb, basic_idea
            FROM post_development
            WHERE post_id = %s
        """, (post_id,))
        
        data = cursor.fetchone()
        if not data:
            logger.warning(f"No post_development data found for post_id {post_id}")
            return ""
        
        # Combine fields with priority
        parts = []
        
        if data.get('expanded_idea'):
            parts.append(data['expanded_idea'])
        
        if data.get('idea_seed'):
            parts.append(f"\n\nCore Concept: {data['idea_seed']}")
        
        if data.get('summary'):
            parts.append(f"\n\nSummary: {data['summary']}")
        
        if data.get('intro_blurb'):
            parts.append(f"\n\nIntroduction: {data['intro_blurb']}")
        
        # Fallback to basic_idea if nothing else available
        if not parts and data.get('basic_idea'):
            parts.append(data['basic_idea'])
        
        combined_text = "\n".join(parts).strip()
        
        if not combined_text:
            logger.warning(f"No content found for post_id {post_id}")
        
        return combined_text



