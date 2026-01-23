"""
Topic Content Aggregation Module

Aggregates relevant content from multiple KB articles for a topic.
"""

import logging
import hashlib
import numpy as np
from typing import List, Dict, Optional
from config.database import db_manager
from utils.vector_search.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
    similarity = np.dot(vec1_norm, vec2_norm)
    return max(0.0, min(1.0, similarity))


class TopicContentAggregator:
    """
    Aggregates relevant content from multiple KB articles for a topic.
    """
    
    def __init__(self, embedding_model: str = 'intfloat/e5-large-v2'):
        """
        Initialize content aggregator.
        
        Args:
            embedding_model: HuggingFace model name for embeddings
        """
        self.embedding_generator = EmbeddingGenerator(embedding_model)
    
    def aggregate_content(self, topic_id: int, limit: int = 5) -> Dict:
        """
        Aggregate content from articles belonging to this topic.
        
        Args:
            topic_id: Topic ID
            limit: Maximum number of chunks to include
        
        Returns:
            Dictionary with:
            - aggregated_text: Combined content
            - source_article_ids: Which articles were used
            - source_chunk_ids: Specific chunks used
            - word_count
        """
        logger.info(f"Aggregating content for topic {topic_id}")
        
        # Get topic
        topic = self._get_topic(topic_id)
        if not topic:
            logger.error(f"Topic {topic_id} not found")
            return {}
        
        # Get articles for this topic
        article_ids = topic.get('article_ids', [])
        if not article_ids:
            logger.warning(f"Topic {topic_id} has no articles")
            return {}
        
        # Retrieve chunks for these articles
        chunks = self._get_article_chunks(article_ids)
        
        if not chunks:
            logger.warning(f"No chunks found for articles {article_ids}")
            return {}
        
        # Get topic centroid embedding
        topic_embedding = np.array(topic.get('centroid_embedding', []))
        if len(topic_embedding) == 0:
            logger.warning(f"Topic {topic_id} has no centroid embedding")
            return {}
        
        # Rank chunks by relevance to topic centroid
        ranked_chunks = self._rank_chunks_by_relevance(chunks, topic_embedding)
        
        # Select top N chunks
        selected_chunks = ranked_chunks[:limit]
        
        # Aggregate content
        aggregated_text = self._combine_chunks(selected_chunks)
        
        # Get source article IDs
        source_article_ids = list(set(chunk['article_id'] for chunk in selected_chunks))
        source_chunk_ids = [chunk.get('chunk_id') or chunk.get('id') for chunk in selected_chunks]
        
        return {
            'aggregated_text': aggregated_text,
            'source_article_ids': source_article_ids,
            'source_chunk_ids': source_chunk_ids,
            'word_count': len(aggregated_text.split())
        }
    
    def _get_topic(self, topic_id: int) -> Optional[Dict]:
        """Get topic from database."""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, topic_name, article_ids, embedding_vector
                    FROM kb_topics
                    WHERE id = %s
                """, (topic_id,))
                
                topic = cursor.fetchone()
                if topic:
                    topic_dict = dict(topic)
                    # Parse embedding vector
                    if isinstance(topic_dict.get('embedding_vector'), list):
                        topic_dict['centroid_embedding'] = topic_dict['embedding_vector']
                    elif topic_dict.get('embedding_vector') is not None:
                        topic_dict['centroid_embedding'] = np.array(topic_dict['embedding_vector']).tolist()
                    return topic_dict
        except Exception as e:
            logger.error(f"Error getting topic {topic_id}: {e}")
        
        return None
    
    def _get_article_chunks(self, article_ids: List[int]) -> List[Dict]:
        """Retrieve chunks for articles."""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, source_id as article_id, chunk_text, chunk_index
                    FROM content_chunks
                    WHERE chunk_type = 'kb'
                    AND source_id = ANY(%s)
                    ORDER BY source_id, chunk_index
                """, (article_ids,))
                
                chunks = cursor.fetchall()
                return [dict(chunk) for chunk in chunks]
        except Exception as e:
            logger.error(f"Error getting article chunks: {e}")
            return []
    
    def _rank_chunks_by_relevance(self, chunks: List[Dict],
                                  topic_embedding: np.ndarray) -> List[Dict]:
        """
        Rank chunks by similarity to topic centroid.
        
        Args:
            chunks: List of chunk dictionaries
            topic_embedding: Topic centroid embedding
        
        Returns:
            List of chunks sorted by relevance (highest first)
        """
        ranked = []
        
        # Generate embeddings for chunks in batches
        batch_size = 32
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            chunk_texts = [chunk['chunk_text'] for chunk in batch]
            
            try:
                # Generate embeddings
                embeddings = self.embedding_generator.generate_embeddings_batch(
                    chunk_texts,
                    batch_size=batch_size
                )
                
                # Calculate similarity to topic centroid
                for j, chunk in enumerate(batch):
                    chunk_embedding = np.array(embeddings[j])
                    similarity = cosine_similarity(topic_embedding, chunk_embedding)
                    
                    ranked.append({
                        **chunk,
                        'relevance_score': similarity
                    })
            except Exception as e:
                logger.warning(f"Error ranking batch {i//batch_size + 1}: {e}")
                continue
        
        # Sort by relevance score (highest first)
        ranked.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return ranked
    
    def _combine_chunks(self, chunks: List[Dict]) -> str:
        """
        Combine chunks into aggregated text.
        
        Args:
            chunks: List of chunk dictionaries
        
        Returns:
            Combined text
        """
        # Group by article to maintain some structure
        articles = {}
        for chunk in chunks:
            article_id = chunk['article_id']
            if article_id not in articles:
                articles[article_id] = []
            articles[article_id].append(chunk)
        
        # Combine chunks from each article
        sections = []
        for article_id, article_chunks in articles.items():
            # Sort chunks by chunk_index
            article_chunks.sort(key=lambda x: x.get('chunk_index', 0))
            
            # Combine chunks from this article
            article_text = '\n\n'.join(chunk['chunk_text'] for chunk in article_chunks)
            sections.append(article_text)
        
        # Join sections with clear separators
        aggregated = '\n\n---\n\n'.join(sections)
        
        return aggregated
    
    def save_aggregated_content(self, topic_id: int, rota_id: Optional[int],
                               aggregated_data: Dict) -> bool:
        """
        Save aggregated content to database.
        
        Args:
            topic_id: Topic ID
            rota_id: Optional rota ID
            aggregated_data: Aggregated content data
        
        Returns:
            True if successful
        """
        try:
            # Calculate content hash
            content_hash = hashlib.md5(
                aggregated_data['aggregated_text'].encode('utf-8')
            ).hexdigest()
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO kb_topic_content
                        (topic_id, rota_id, aggregated_text, source_article_ids,
                         source_chunk_ids, content_hash, word_count,
                         created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (topic_id, rota_id)
                    DO UPDATE SET
                        aggregated_text = EXCLUDED.aggregated_text,
                        source_article_ids = EXCLUDED.source_article_ids,
                        source_chunk_ids = EXCLUDED.source_chunk_ids,
                        content_hash = EXCLUDED.content_hash,
                        word_count = EXCLUDED.word_count,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    topic_id,
                    rota_id,
                    aggregated_data['aggregated_text'],
                    aggregated_data['source_article_ids'],
                    aggregated_data['source_chunk_ids'],
                    content_hash,
                    aggregated_data['word_count']
                ))
            
            logger.info(f"Saved aggregated content for topic {topic_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving aggregated content: {e}")
            return False
