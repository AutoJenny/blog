"""
DEPTH_LONG Content Generator

Phase 2.3: Generates Facebook Sunday DEPTH_LONG posts from KB topics.

This is the core proof of concept for the Content Roles Framework.
"""

import logging
from typing import Dict, Optional
from datetime import date
from bs4 import BeautifulSoup
import re
from config.database import db_manager
from blueprints.llm_actions import LLMService

logger = logging.getLogger(__name__)


class DepthLongGenerator:
    """
    Generates DEPTH_LONG posts from KB topics and articles.
    
    Requirements:
    - topic_id (weekly topic from kb_topic_rota)
    - source_page_id (specific KB article)
    - role = DEPTH_LONG
    - channel = Facebook
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.max_source_words = 2000  # Bound source text
    
    def generate(self, topic_id: int, source_page_id: int, 
                 rota_year: int, rota_week: int) -> Dict:
        """
        Generate a DEPTH_LONG post.
        
        Args:
            topic_id: KB topic ID (from kb_topics)
            source_page_id: KB article ID (from clan_kb_articles)
            rota_year: Year of rota week
            rota_week: ISO week number
        
        Returns:
            Dictionary with:
            - success: bool
            - content: Generated post text (if success)
            - error: Error message (if not success)
            - word_count: Word count of generated content
            - validation_issues: List of validation issues
        """
        # Phase 2.2: Enforce topic and source requirements
        if not topic_id:
            return {
                'success': False,
                'error': 'topic_id is required for DEPTH_LONG posts'
            }
        
        if not source_page_id:
            return {
                'success': False,
                'error': 'source_page_id is required for DEPTH_LONG posts'
            }
        
        try:
            # Step 1: Fetch source text from KB page
            source_text = self._fetch_source_text(source_page_id)
            if not source_text:
                return {
                    'success': False,
                    'error': f'Could not retrieve source text from KB article {source_page_id}'
                }
            
            # Step 2: Get topic metadata
            topic = self._get_topic(topic_id)
            if not topic:
                return {
                    'success': False,
                    'error': f'Topic {topic_id} not found'
                }
            
            # Step 3: Call LLM with role-specific prompts
            generated_content = self._call_llm(source_text, topic)
            
            if not generated_content:
                return {
                    'success': False,
                    'error': 'LLM generation failed'
                }
            
            # Step 4: Basic validation (full validation in Phase 2.4)
            word_count = len(generated_content.split())
            validation_issues = []
            
            if word_count < 120:
                validation_issues.append(f'Word count too low: {word_count} (minimum: 120)')
            elif word_count > 220:
                validation_issues.append(f'Word count too high: {word_count} (maximum: 220)')
            
            return {
                'success': True,
                'content': generated_content,
                'word_count': word_count,
                'validation_issues': validation_issues,
                'topic_id': topic_id,
                'source_page_id': source_page_id,
                'rota_year': rota_year,
                'rota_week': rota_week
            }
        
        except Exception as e:
            logger.error(f"Error generating DEPTH_LONG post: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Generation error: {str(e)}'
            }
    
    def _fetch_source_text(self, article_id: int) -> Optional[str]:
        """
        Fetch and clean source text from KB article.
        
        Args:
            article_id: KB article ID
        
        Returns:
            Cleaned text (bounded to ~2000 words), or None
        """
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT text, name
                    FROM clan_kb_articles
                    WHERE id = %s AND is_active = TRUE
                """, (article_id,))
                
                article = cursor.fetchone()
            
            if not article:
                return None
            
            # Extract text from HTML
            html_text = article['text'] or ''
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Remove script, style, nav elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Bound to max_source_words
            words = text.split()
            if len(words) > self.max_source_words:
                text = ' '.join(words[:self.max_source_words])
            
            return text
        
        except Exception as e:
            logger.error(f"Error fetching source text for article {article_id}: {e}")
            return None
    
    def _get_topic(self, topic_id: int) -> Optional[Dict]:
        """Get topic metadata."""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, topic_name, topic_description, topic_type
                    FROM kb_topics
                    WHERE id = %s AND is_active = TRUE
                """, (topic_id,))
                
                topic = cursor.fetchone()
            
            if topic:
                return dict(topic)
            return None
        
        except Exception as e:
            logger.error(f"Error getting topic {topic_id}: {e}")
            return None
    
    def _call_llm(self, source_text: str, topic: Dict) -> Optional[str]:
        """
        Call LLM with role-specific prompts for DEPTH_LONG.
        
        Prompt structure:
        1. Global system prompt (role separation rule)
        2. Role system prompt (DEPTH_LONG constraints)
        3. Source text
        4. Task instruction
        """
        # Global system prompt
        global_prompt = """You are a content writer for CLAN.com, a Scottish heritage and culture website. 
Every piece of content must perform one job only. This post's job is DEPTH_LONG: to demonstrate embedded knowledge and judgement.
You must never mix roles. This post must not sell, reassure, or provide culture/texture."""
        
        # Role-specific system prompt (DEPTH_LONG)
        role_prompt = """DEPTH_LONG Content Role:
- Purpose: Demonstrate embedded knowledge and judgement
- Characteristics: Narrow scope, explanatory (not summarising), structured with white space, reflective close (not a conclusion)
- Hard Constraints:
  * NO selling language (buy, purchase, order, etc.)
  * NO service mentions (contact us, visit, call, etc.)
  * NO product mentions
  * Must be grounded in the source material provided
  * Must not introduce facts beyond the source
- Length: 120-220 words
- Structure: Short paragraphs with white space between them"""
        
        # Task instruction
        task_instruction = f"""Write a Facebook Sunday post (120-220 words) about: {topic.get('topic_name', 'this topic')}.

Use the source material below to write an explanatory, reflective post that demonstrates knowledge. 
Use short paragraphs with white space. End with a reflective observation, not a conclusion or CTA.

Source Material:
{source_text}

Output ONLY the post text - no explanations, no meta-commentary."""
        
        # Prepare messages
        messages = [
            {'role': 'system', 'content': global_prompt},
            {'role': 'user', 'content': role_prompt},
            {'role': 'user', 'content': task_instruction}
        ]
        
        try:
            # Call LLM (Ollama, llama3.2)
            response = self.llm_service.execute_llm_request(
                provider='ollama',
                model='llama3.2:latest',
                messages=messages
            )
            
            if 'error' in response:
                logger.error(f"LLM error: {response['error']}")
                return None
            
            content = response.get('content', '').strip()
            
            # Basic cleanup
            content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 newlines
            content = content.strip()
            
            return content
        
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return None
