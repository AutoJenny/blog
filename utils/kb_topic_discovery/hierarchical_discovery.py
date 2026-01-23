"""
Hierarchical Topic Discovery Module

Discovers topics at multiple levels of granularity:
- Level 1: Broad themes (e.g., "Tartan Design")
- Level 2: Specific sub-themes (e.g., "Line Widths and Balance in Tartan Design")
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from config.database import db_manager
from .clustering import KBTopicClusterer

logger = logging.getLogger(__name__)


class HierarchicalTopicDiscoverer:
    """
    Discovers topics hierarchically at multiple levels of granularity.
    """
    
    def __init__(self, embedding_model: str = 'intfloat/e5-large-v2'):
        """
        Initialize hierarchical discoverer.
        
        Args:
            embedding_model: HuggingFace model name for embeddings
        """
        self.clusterer = KBTopicClusterer(embedding_model)
    
    def discover_hierarchical_topics(self,
                                     broad_clusters: int = 15,
                                     granular_threshold: float = 0.75,
                                     min_broad_size: int = 10,
                                     min_granular_size: int = 3) -> List[Dict]:
        """
        Discover topics at multiple levels of granularity.
        
        Args:
            broad_clusters: Number of broad theme clusters
            granular_threshold: Similarity threshold for granular sub-clustering (higher = more specific)
            min_broad_size: Minimum articles for broad topics
            min_granular_size: Minimum articles for granular sub-topics
        
        Returns:
            List of topic dictionaries with parent_id for hierarchical structure
        """
        logger.info("Starting hierarchical topic discovery...")
        
        # Step 1: Discover broad themes
        logger.info(f"Step 1: Discovering {broad_clusters} broad themes...")
        broad_topics = self.clusterer.discover_topics(
            method='kmeans',
            n_clusters=broad_clusters,
            min_cluster_size=min_broad_size
        )
        
        logger.info(f"Found {len(broad_topics)} broad themes")
        
        # Step 2: For each broad topic, discover granular sub-topics
        all_topics = []
        topic_id_counter = 1
        
        for broad_topic in broad_topics:
            # Store broad topic (no parent) - use cluster_id as temporary ID
            broad_topic['temp_id'] = topic_id_counter
            broad_topic['parent_id'] = None
            broad_topic['level'] = 1
            broad_topic['is_broad'] = True
            all_topics.append(broad_topic)
            topic_id_counter += 1
            
            # Get articles for this broad topic
            article_ids = broad_topic.get('article_ids', [])
            
            if len(article_ids) >= min_granular_size * 2:  # Need enough articles to sub-cluster
                logger.info(f"  Discovering sub-topics for: {broad_topic['topic_name']} ({len(article_ids)} articles)")
                
                # Discover granular sub-topics within this broad topic
                granular_topics = self._discover_granular_subtopics(
                    article_ids,
                    broad_topic,
                    granular_threshold,
                    min_granular_size
                )
                
                # Store granular topics (with parent reference)
                for granular_topic in granular_topics:
                    granular_topic['temp_id'] = topic_id_counter
                    granular_topic['parent_id'] = broad_topic['temp_id']  # Use temp_id for parent reference
                    granular_topic['level'] = 2
                    granular_topic['is_broad'] = False
                    all_topics.append(granular_topic)
                    topic_id_counter += 1
                
                logger.info(f"    Found {len(granular_topics)} sub-topics")
        
        logger.info(f"Total topics discovered: {len(all_topics)} ({len(broad_topics)} broad, {len(all_topics) - len(broad_topics)} granular)")
        
        return all_topics
    
    def _discover_granular_subtopics(self,
                                    article_ids: List[int],
                                    parent_topic: Dict,
                                    similarity_threshold: float,
                                    min_size: int) -> List[Dict]:
        """
        Discover granular sub-topics within a broad topic.
        
        Args:
            article_ids: Article IDs belonging to the broad topic
            parent_topic: Parent topic dictionary
            similarity_threshold: Similarity threshold for sub-clustering
            min_size: Minimum cluster size
        
        Returns:
            List of granular topic dictionaries
        """
        # Load embeddings for these specific articles
        kb_data = self._load_article_embeddings(article_ids)
        
        if len(kb_data) < min_size * 2:
            return []  # Not enough data for sub-clustering
        
        # Extract embeddings and metadata
        embeddings = np.array([item['embedding'] for item in kb_data])
        article_ids_list = [item['article_id'] for item in kb_data]
        chunk_ids = [item['chunk_id'] for item in kb_data]
        
        # Use hierarchical clustering with tighter threshold for granularity
        from sklearn.cluster import AgglomerativeClustering
        
        # Convert similarity threshold to distance
        distance_threshold = 1.0 - similarity_threshold
        
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            linkage='average',
            metric='cosine'
        )
        
        try:
            labels = clustering.fit_predict(embeddings)
        except Exception as e:
            logger.warning(f"Error in granular clustering: {e}")
            return []
        
        # Group by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = {
                    'article_ids': [],
                    'chunk_ids': [],
                    'embeddings': []
                }
            clusters[label]['article_ids'].append(article_ids_list[i])
            clusters[label]['chunk_ids'].append(chunk_ids[i])
            clusters[label]['embeddings'].append(embeddings[i])
        
        # Extract sub-topics
        granular_topics = []
        for label, cluster_data in clusters.items():
            unique_article_ids = list(set(cluster_data['article_ids']))
            
            if len(unique_article_ids) < min_size:
                continue  # Too small
            
            # Get article texts for this sub-cluster
            article_texts = self._get_cluster_article_texts(unique_article_ids, kb_data)
            
            # Generate semantic topic name (with context of parent)
            topic_name = self._generate_granular_topic_name(article_texts, parent_topic)
            topic_description = self._generate_topic_description(article_texts, topic_name)
            
            # Get category IDs
            category_ids = self.clusterer._get_category_ids(unique_article_ids)
            
            # Classify topic type
            topic_type = self.clusterer._classify_topic_type(article_texts)
            
            granular_topics.append({
                'cluster_id': label,
                'topic_name': topic_name,
                'topic_description': topic_description,
                'keywords': self.clusterer._extract_keywords(article_texts),
                'article_ids': unique_article_ids,
                'category_ids': category_ids,
                'centroid_embedding': np.mean(cluster_data['embeddings'], axis=0).tolist(),
                'topic_type': topic_type,
                'article_count': len(unique_article_ids)
            })
        
        return granular_topics
    
    def _load_article_embeddings(self, article_ids: List[int]) -> List[Dict]:
        """Load embeddings for specific articles."""
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    cc.id as chunk_id,
                    cc.source_id as article_id,
                    cc.chunk_text,
                    cc.metadata,
                    cc.faiss_index_id
                FROM content_chunks cc
                WHERE cc.chunk_type = 'kb'
                AND cc.source_id = ANY(%s)
                ORDER BY cc.source_id, cc.chunk_index
            """, (article_ids,))
            
            chunks = cursor.fetchall()
        
        if not chunks:
            return []
        
        # Generate embeddings
        kb_data = []
        batch_size = 32
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            chunk_texts = [chunk['chunk_text'] for chunk in batch]
            
            try:
                embeddings = self.clusterer.embedding_generator.generate_embeddings_batch(
                    chunk_texts,
                    batch_size=batch_size
                )
                
                for j, chunk in enumerate(batch):
                    kb_data.append({
                        'chunk_id': chunk['chunk_id'],
                        'article_id': chunk['article_id'],
                        'chunk_text': chunk['chunk_text'],
                        'metadata': chunk['metadata'] or {},
                        'embedding': embeddings[j]
                    })
            except Exception as e:
                logger.warning(f"Error generating embeddings for batch: {e}")
                continue
        
        return kb_data
    
    def _get_cluster_article_texts(self, article_ids: List[int], kb_data: List[Dict]) -> List[Dict]:
        """Get article texts for cluster articles."""
        article_texts = []
        seen_articles = set()
        
        for item in kb_data:
            if item['article_id'] in article_ids and item['article_id'] not in seen_articles:
                seen_articles.add(item['article_id'])
                article_texts.append({
                    'article_id': item['article_id'],
                    'text': item['chunk_text'],
                    'metadata': item['metadata']
                })
        
        return article_texts
    
    def _generate_granular_topic_name(self, article_texts: List[Dict], parent_topic: Dict) -> str:
        """
        Generate semantic name for granular sub-topic, contextualized by parent.
        
        Args:
            article_texts: Article text data
            parent_topic: Parent topic for context
        
        Returns:
            Semantic topic name
        """
        try:
            from blueprints.llm_actions import LLMService
            
            # Get article titles and summaries
            article_summaries = []
            for item in article_texts[:8]:
                title = item.get('metadata', {}).get('article_name', '')
                text_preview = item.get('text', '')[:300]
                if title:
                    article_summaries.append(f"Article: {title}\n{text_preview}")
            
            context = "\n\n".join(article_summaries)
            parent_name = parent_topic.get('topic_name', '')
            
            llm_service = LLMService()
            messages = [
                {
                    'role': 'system',
                    'content': """You are an expert at identifying specific, granular themes within broader topics.
Your task is to identify a SPECIFIC sub-theme or aspect within the broader parent topic.
Focus on what makes this sub-theme unique and specific.
Generate a concise, meaningful topic name (3-7 words) that captures the specific aspect.
Examples:
- "Line Widths and Balance in Tartan Design" (specific aspect of tartan design)
- "Using the Online Tartan Designer Tool" (specific tool/process)
- "Choosing Pre-Made Tartans by Pattern" (specific selection criteria)
- "Tartan Color Accuracy and Authenticity" (specific quality aspect)
Return ONLY the topic name, nothing else."""
                },
                {
                    'role': 'user',
                    'content': f"""These articles are part of the broader topic: "{parent_name}"

Within this broader topic, these articles discuss a specific sub-theme or aspect.

Articles:
{context}

What is the SPECIFIC sub-theme or aspect that these articles focus on?
What makes this different from the general "{parent_name}" topic?
What specific knowledge or angle do these articles cover?

Specific sub-topic name (3-7 words, be specific and granular):"""
                }
            ]
            
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'content' in result:
                topic_name = result['content'].strip()
                topic_name = topic_name.split('\n')[0].strip()
                topic_name = topic_name.strip('"\'')
                if topic_name and len(topic_name) > 5:
                    return topic_name
            
        except Exception as e:
            logger.warning(f"LLM granular naming failed: {e}")
        
        # Fallback
        if article_texts:
            titles = [item.get('metadata', {}).get('article_name', '') 
                     for item in article_texts[:3] if item.get('metadata', {}).get('article_name')]
            if titles:
                return f"{parent_topic.get('topic_name', 'Topic')}: {titles[0][:40]}"
        
        return f"{parent_topic.get('topic_name', 'Topic')} Sub-topic"
    
    def _generate_topic_description(self, article_texts: List[Dict], topic_name: str) -> Optional[str]:
        """Generate topic description using LLM."""
        try:
            from blueprints.llm_actions import LLMService
            
            article_titles = [item.get('metadata', {}).get('article_name', '') 
                            for item in article_texts[:6] 
                            if item.get('metadata', {}).get('article_name')]
            
            if not article_titles:
                return None
            
            context = "\n".join([f"- {title}" for title in article_titles])
            
            llm_service = LLMService()
            messages = [
                {
                    'role': 'system',
                    'content': """Generate a brief, meaningful description (1-2 sentences) of what this specific topic covers."""
                },
                {
                    'role': 'user',
                    'content': f"""Topic: {topic_name}

Articles:
{context}

What does this specific topic cover? Brief description (1-2 sentences):"""
                }
            ]
            
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'content' in result:
                description = result['content'].strip()
                description = description.split('\n')[0].strip()
                description = description.strip('"\'')
                if description and len(description) > 10:
                    return description
            
        except Exception as e:
            logger.warning(f"LLM description generation failed: {e}")
        
        return None
