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
                 rota_year: int, rota_week: int, angle_id: Optional[int] = None) -> Dict:
        """
        Generate a DEPTH_LONG post.
        
        Phase 3.5: Now supports angle-aware generation.
        
        Args:
            topic_id: KB topic ID (from kb_topics)
            source_page_id: KB article ID (from clan_kb_articles) - optional if angle_id provided
            rota_year: Year of rota week
            rota_week: ISO week number
            angle_id: Optional angle ID (Phase 3)
        
        Returns:
            Dictionary with:
            - success: bool
            - content: Generated post text (if success)
            - error: Error message (if not success)
            - word_count: Word count of generated content
            - validation_issues: List of validation issues
            - angle_id: Angle ID used (if any)
        """
        # Phase 2.2: Enforce topic requirement
        if not topic_id:
            return {
                'success': False,
                'error': 'topic_id is required for DEPTH_LONG posts'
            }
        
        try:
            # Step 1: Get topic metadata
            topic = self._get_topic(topic_id)
            if not topic:
                return {
                    'success': False,
                    'error': f'Topic {topic_id} not found'
                }
            
            # Step 2: Handle angle-aware vs. topic-only generation
            angle = None
            source_text = None
            
            if angle_id:
                # Phase 3.5: Angle-aware generation
                angle = self._get_angle(angle_id)
                if not angle:
                    return {
                        'success': False,
                        'error': f'Angle {angle_id} not found'
                    }
                
                # Use angle's source articles for aggregation
                source_article_ids = angle.get('source_article_ids', [])
                if not source_article_ids:
                    # Fallback to source_page_id if provided
                    if source_page_id:
                        source_text = self._fetch_source_text(source_page_id)
                    else:
                        return {
                            'success': False,
                            'error': f'Angle {angle_id} has no source articles and no source_page_id provided'
                        }
                else:
                    # Aggregate source text from angle's articles
                    source_text = self._aggregate_angle_sources(source_article_ids)
                    if not source_text:
                        # Fallback to source_page_id if provided
                        if source_page_id:
                            source_text = self._fetch_source_text(source_page_id)
                        else:
                            return {
                                'success': False,
                                'error': f'Could not aggregate source text from angle {angle_id} articles'
                            }
            else:
                # Fallback: Topic-only generation (current behavior)
                if not source_page_id:
                    return {
                        'success': False,
                        'error': 'source_page_id is required when no angle_id is provided'
                    }
                
                source_text = self._fetch_source_text(source_page_id)
                if not source_text:
                    return {
                        'success': False,
                        'error': f'Could not retrieve source text from KB article {source_page_id}'
                    }
            
            # Step 3: Call LLM with role-specific prompts (and angle prompt if provided)
            generated_content = self._call_llm(source_text, topic, angle)
            
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
            
            result = {
                'success': True,
                'content': generated_content,
                'word_count': word_count,
                'validation_issues': validation_issues,
                'topic_id': topic_id,
                'source_page_id': source_page_id,
                'rota_year': rota_year,
                'rota_week': rota_week
            }
            
            if angle_id:
                result['angle_id'] = angle_id
            
            return result
        
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
    
    def _get_angle(self, angle_id: int) -> Optional[Dict]:
        """Get angle from database."""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, angle_name, narrative_intent, topic_id, source_article_ids
                    FROM content_angles
                    WHERE id = %s AND is_active = TRUE
                """, (angle_id,))
                
                angle = cursor.fetchone()
                if angle:
                    return dict(angle)
        except Exception as e:
            logger.error(f"Error getting angle {angle_id}: {e}")
        
        return None
    
    def _aggregate_angle_sources(self, article_ids: List[int]) -> Optional[str]:
        """
        Aggregate source text from multiple articles (angle's source bundle).
        
        Phase 3.5: Uses TopicContentAggregator logic to combine articles.
        
        Args:
            article_ids: List of KB article IDs
        
        Returns:
            Aggregated text (bounded to ~2000 words), or None
        """
        try:
            from utils.kb_topic_discovery.content_aggregator import TopicContentAggregator
            
            # For angle sources, we'll fetch and combine articles directly
            # (simpler than full aggregation - just combine article texts)
            aggregated_sections = []
            total_words = 0
            
            for article_id in article_ids[:5]:  # Limit to 5 articles
                article_text = self._fetch_source_text(article_id)
                if article_text:
                    words = article_text.split()
                    if total_words + len(words) > self.max_source_words:
                        # Add partial text to stay within limit
                        remaining = self.max_source_words - total_words
                        if remaining > 100:  # Only add if meaningful amount
                            article_text = ' '.join(words[:remaining])
                            aggregated_sections.append(article_text)
                        break
                    else:
                        aggregated_sections.append(article_text)
                        total_words += len(words)
            
            if aggregated_sections:
                # Join with clear separators
                aggregated = '\n\n---\n\n'.join(aggregated_sections)
                return aggregated
            
            return None
        
        except Exception as e:
            logger.error(f"Error aggregating angle sources: {e}")
            return None
    
    def _call_llm(self, source_text: str, topic: Dict, angle: Optional[Dict] = None) -> Optional[str]:
        """
        Call LLM with role-specific prompts for DEPTH_LONG.
        
        Phase 3.5: Now supports angle-aware prompt composition.
        
        Prompt structure:
        1. Global system prompt (role separation rule)
        2. Role system prompt (DEPTH_LONG constraints)
        3. Angle prompt (if angle provided) - NEW
        4. Source text
        5. Task instruction
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
        
        # Phase 3.5: Angle prompt (if angle provided)
        angle_prompt = None
        if angle:
            angle_prompt = f"""You are writing a Facebook post that tells a specific story about this topic.

The story you are telling is: {angle.get('narrative_intent', '')}

This means:
- Focus on: {angle.get('angle_name', '')}
- Tell the story: {angle.get('narrative_intent', '')}
- Use the source material to support this narrative

The role constraints (DEPTH_LONG) still apply:
- 120-220 words
- No selling, no service mentions
- Explanatory, not summarising
- Reflective close

Combine the narrative intent with the role constraints to write the post."""
        
        # Task instruction
        if angle:
            task_instruction = f"""Write a Facebook Sunday post (120-220 words) about: {topic.get('topic_name', 'this topic')} from the angle: {angle.get('angle_name', '')}.

The angle you are telling is: {angle.get('narrative_intent', '')}

Use the source material below to write an explanatory, reflective post that tells this specific story. 
Use short paragraphs with white space. End with a reflective observation, not a conclusion or CTA.

Source Material:
{source_text}

Output ONLY the post text - no explanations, no meta-commentary."""
        else:
            task_instruction = f"""Write a Facebook Sunday post (120-220 words) about: {topic.get('topic_name', 'this topic')}.

Use the source material below to write an explanatory, reflective post that demonstrates knowledge. 
Use short paragraphs with white space. End with a reflective observation, not a conclusion or CTA.

Source Material:
{source_text}

Output ONLY the post text - no explanations, no meta-commentary."""
        
        # Prepare messages
        messages = [
            {'role': 'system', 'content': global_prompt},
            {'role': 'user', 'content': role_prompt}
        ]
        
        # Add angle prompt if provided
        if angle_prompt:
            messages.append({'role': 'user', 'content': angle_prompt})
        
        messages.append({'role': 'user', 'content': task_instruction})
        
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
