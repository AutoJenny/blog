"""
Angle Proposer

Phase 3.2: Proposes multiple angle candidates for a topic using vector search and LLM.

This is a read-only operation - candidates are not persisted until explicitly selected.
"""

import logging
from typing import List, Dict, Optional
from config.database import db_manager
from utils.vector_search.embeddings import EmbeddingGenerator
from blueprints.llm_actions import LLMService

logger = logging.getLogger(__name__)


class AngleProposer:
    """
    Proposes angle candidates for a topic.
    
    Uses:
    - Vector search on topic articles to find relevant sources
    - LLM to generate angle names and narrative intents
    - Similarity checking to avoid duplicate angles
    """
    
    def __init__(self, embedding_model: str = 'intfloat/e5-large-v2'):
        """
        Initialize angle proposer.
        
        Args:
            embedding_model: HuggingFace model name for embeddings
        """
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.llm_service = LLMService()
    
    def propose_angles(self, topic_id: int, num_candidates: int = 5) -> Dict:
        """
        Propose angle candidates for a topic.
        
        Args:
            topic_id: KB topic ID
            num_candidates: Number of candidates to generate (default: 5)
        
        Returns:
            Dictionary with:
            - success: bool
            - topic_id: int
            - topic_name: str
            - candidates: List of angle candidate dicts
            - error: str (if not success)
        """
        try:
            # Step 1: Get topic metadata
            topic = self._get_topic(topic_id)
            if not topic:
                return {
                    'success': False,
                    'error': f'Topic {topic_id} not found',
                    'error_code': 'TOPIC_NOT_FOUND'
                }
            
            if not topic.get('is_active'):
                return {
                    'success': False,
                    'error': f'Topic {topic_id} is inactive',
                    'error_code': 'TOPIC_INACTIVE'
                }
            
            # Step 2: Get topic articles
            article_ids = topic.get('article_ids', [])
            if not article_ids:
                return {
                    'success': False,
                    'error': f'Topic {topic_id} has no associated KB articles',
                    'error_code': 'NO_SOURCE_ARTICLES'
                }
            
            # Step 3: Get article details for context
            articles = self._get_article_details(article_ids)
            if not articles:
                return {
                    'success': False,
                    'error': f'Could not retrieve article details for topic {topic_id}',
                    'error_code': 'NO_SOURCE_ARTICLES'
                }
            
            # Step 4: Generate angle candidates using LLM
            candidates = self._generate_candidates(
                topic=topic,
                articles=articles,
                num_candidates=num_candidates
            )
            
            if not candidates:
                return {
                    'success': False,
                    'error': 'Failed to generate angle candidates',
                    'error_code': 'GENERATION_FAILED'
                }
            
            return {
                'success': True,
                'topic_id': topic_id,
                'topic_name': topic.get('topic_name', ''),
                'candidates': candidates
            }
        
        except Exception as e:
            logger.error(f"Error proposing angles for topic {topic_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Angle proposal failed: {str(e)}',
                'error_code': 'GENERATION_FAILED'
            }
    
    def _get_topic(self, topic_id: int) -> Optional[Dict]:
        """Get topic from database."""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, topic_name, topic_description, article_ids, 
                           embedding_vector, is_active
                    FROM kb_topics
                    WHERE id = %s
                """, (topic_id,))
                
                topic = cursor.fetchone()
                if topic:
                    return dict(topic)
        except Exception as e:
            logger.error(f"Error getting topic {topic_id}: {e}")
        
        return None
    
    def _get_article_details(self, article_ids: List[int]) -> List[Dict]:
        """Get article details for context."""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, text, short_text
                    FROM clan_kb_articles
                    WHERE id = ANY(%s) AND is_active = TRUE
                    ORDER BY id
                """, (article_ids,))
                
                articles = cursor.fetchall()
                return [dict(article) for article in articles]
        except Exception as e:
            logger.error(f"Error getting article details: {e}")
            return []
    
    def _generate_candidates(self, topic: Dict, articles: List[Dict], 
                            num_candidates: int) -> List[Dict]:
        """
        Generate angle candidates using LLM.
        
        Args:
            topic: Topic dictionary
            articles: List of article dictionaries
            num_candidates: Number of candidates to generate
        
        Returns:
            List of candidate dictionaries
        """
        # Prepare article context
        article_context = []
        for article in articles[:10]:  # Limit to top 10 articles
            name = article.get('name', '')
            text_preview = (article.get('short_text') or article.get('text') or '')[:500]
            if name:
                article_context.append(f"Article: {name}\n{text_preview}")
        
        context_text = "\n\n".join(article_context)
        
        # Prepare topic context
        topic_name = topic.get('topic_name', '')
        topic_description = topic.get('topic_description', '')
        
        # LLM prompt for angle generation
        system_prompt = """You are an expert at identifying editorial storylines and narrative angles from factual content.

Your task is to analyze a topic and its source articles, then propose multiple distinct editorial angles (storylines) that could be used to tell different stories about this topic.

Each angle should:
- Be a specific, coherent narrative interpretation
- Answer "What story are we telling about this topic?"
- Be distinct from other angles (different perspectives, not just rewordings)
- Be grounded in the source material provided
- Be suitable for social media content (not academic papers)

Return exactly {num_candidates} distinct angles, each with:
1. A clear, concise angle name (2-8 words)
2. A narrative intent (1-2 sentences explaining what story this angle tells)
3. Which source articles are most relevant to this angle

Format your response as a JSON array of objects with keys: angle_name, narrative_intent, source_article_indices (array of 0-based indices into the articles list)."""

        user_prompt = f"""Analyze this topic and propose {num_candidates} distinct editorial angles:

Topic: {topic_name}
Description: {topic_description or 'No description'}

Source Articles:
{context_text}

Propose {num_candidates} distinct angles. Each angle should tell a different story about this topic. Return ONLY a valid JSON array, no other text."""

        try:
            messages = [
                {'role': 'system', 'content': system_prompt.format(num_candidates=num_candidates)},
                {'role': 'user', 'content': user_prompt}
            ]
            
            response = self.llm_service.execute_llm_request(
                provider='ollama',
                model='llama3.2:latest',
                messages=messages,
                max_tokens=2000
            )
            
            if 'error' in response:
                logger.error(f"LLM error: {response['error']}")
                return []
            
            content = response.get('content', '').strip()
            
            # Parse JSON response
            import json
            # Try to extract JSON from response (handle markdown code blocks)
            if '```' in content:
                # Extract JSON from code block
                start = content.find('```')
                end = content.find('```', start + 3)
                if end > start:
                    content = content[start + 3:end].strip()
                    if content.startswith('json'):
                        content = content[4:].strip()
            
            candidates_data = json.loads(content)
            
            # Convert to candidate format
            candidates = []
            for i, candidate in enumerate(candidates_data[:num_candidates]):
                # Get source article IDs from indices
                source_indices = candidate.get('source_article_indices', [])
                source_article_ids = []
                for idx in source_indices:
                    if 0 <= idx < len(articles):
                        source_article_ids.append(articles[idx]['id'])
                
                # If no indices provided, use all articles
                if not source_article_ids and articles:
                    source_article_ids = [a['id'] for a in articles[:3]]  # Default to first 3
                
                candidates.append({
                    'angle_name': candidate.get('angle_name', f'Angle {i+1}'),
                    'narrative_intent': candidate.get('narrative_intent', ''),
                    'source_article_ids': source_article_ids,
                    'confidence_score': 0.8  # Default confidence (could be enhanced)
                })
            
            return candidates
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response content: {content[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error generating candidates: {e}", exc_info=True)
            return []
