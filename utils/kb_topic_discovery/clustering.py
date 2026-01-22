"""
KB Topic Clustering Module

Clusters KB articles by semantic similarity to discover topics.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from config.database import db_manager
from utils.vector_search.embeddings import EmbeddingGenerator
from utils.vector_search.faiss_index import FAISSIndexManager

logger = logging.getLogger(__name__)

# Lazy import for scikit-learn
_sklearn = None


def _import_sklearn():
    """Lazy import of scikit-learn."""
    global _sklearn
    if _sklearn is None:
        try:
            from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
            from sklearn.metrics import silhouette_score
            _sklearn = {
                'KMeans': KMeans,
                'DBSCAN': DBSCAN,
                'AgglomerativeClustering': AgglomerativeClustering,
                'silhouette_score': silhouette_score
            }
        except ImportError:
            raise ImportError(
                "scikit-learn is required. Install with: pip install scikit-learn"
            )
    return _sklearn


class KBTopicClusterer:
    """
    Clusters KB articles by semantic similarity to discover topics.
    """
    
    def __init__(self, embedding_model: str = 'intfloat/e5-large-v2'):
        """
        Initialize KB topic clusterer.
        
        Args:
            embedding_model: HuggingFace model name for embeddings
        """
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.embedding_model = embedding_model
    
    def discover_topics(self,
                       method: str = 'kmeans',
                       n_clusters: Optional[int] = None,
                       min_cluster_size: int = 3,
                       similarity_threshold: float = 0.7) -> List[Dict]:
        """
        Discover topics by clustering KB articles.
        
        Args:
            method: Clustering method ('kmeans', 'dbscan', 'hierarchical')
            n_clusters: Number of clusters (auto-detect if None for kmeans)
            min_cluster_size: Minimum cluster size for DBSCAN
            similarity_threshold: Similarity threshold for hierarchical clustering
        
        Returns:
            List of topic dictionaries with:
            - cluster_id
            - article_ids
            - centroid_embedding
            - keywords
            - suggested_name
        """
        logger.info(f"Starting topic discovery using {method} method")
        
        # 1. Load all KB chunk embeddings
        kb_data = self._load_kb_embeddings()
        
        if not kb_data or len(kb_data) < min_cluster_size:
            logger.warning(f"Not enough KB data for clustering: {len(kb_data) if kb_data else 0} chunks")
            return []
        
        logger.info(f"Loaded {len(kb_data)} KB chunks for clustering")
        
        # Extract embeddings and metadata
        embeddings = np.array([item['embedding'] for item in kb_data])
        article_ids = [item['article_id'] for item in kb_data]
        chunk_ids = [item['chunk_id'] for item in kb_data]
        
        # 2. Apply clustering algorithm
        if method == 'kmeans':
            clusters = self._kmeans_cluster(embeddings, n_clusters, article_ids, chunk_ids, kb_data)
        elif method == 'dbscan':
            clusters = self._dbscan_cluster(embeddings, min_cluster_size, article_ids, chunk_ids, kb_data)
        elif method == 'hierarchical':
            clusters = self._hierarchical_cluster(embeddings, similarity_threshold, article_ids, chunk_ids, kb_data)
        else:
            raise ValueError(f"Unknown clustering method: {method}")
        
        logger.info(f"Found {len(clusters)} clusters")
        
        # 3. Extract topic information from clusters
        topics = []
        for cluster_id, cluster_data in enumerate(clusters):
            if len(cluster_data['article_ids']) < min_cluster_size:
                logger.debug(f"Skipping cluster {cluster_id} - too small ({len(cluster_data['article_ids'])} articles)")
                continue
            
            topic = self._extract_topic_info(cluster_id, cluster_data, kb_data)
            topics.append(topic)
        
        logger.info(f"Extracted {len(topics)} topics from clusters")
        return topics
    
    def _load_kb_embeddings(self) -> List[Dict]:
        """
        Load all KB chunk embeddings from database.
        
        Returns:
            List of dicts with: chunk_id, article_id, embedding, chunk_text, metadata
        """
        with db_manager.get_cursor() as cursor:
            # Get all KB chunks with their embeddings
            cursor.execute("""
                SELECT 
                    cc.id as chunk_id,
                    cc.source_id as article_id,
                    cc.chunk_text,
                    cc.metadata,
                    cc.faiss_index_id
                FROM content_chunks cc
                WHERE cc.chunk_type = 'kb'
                AND cc.faiss_index_id IS NOT NULL
                ORDER BY cc.source_id, cc.chunk_index
            """)
            
            chunks = cursor.fetchall()
        
        if not chunks:
            logger.warning("No KB chunks found in database")
            return []
        
        # Generate embeddings from chunk text
        # This is more reliable than trying to retrieve from FAISS
        logger.info(f"Generating embeddings for {len(chunks)} KB chunks...")
        
        kb_data = []
        batch_size = 32
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            chunk_texts = [chunk['chunk_text'] for chunk in batch]
            
            try:
                # Generate embeddings in batch
                embeddings = self.embedding_generator.generate_embeddings_batch(
                    chunk_texts,
                    batch_size=batch_size
                )
                
                # Store with metadata
                for j, chunk in enumerate(batch):
                    kb_data.append({
                        'chunk_id': chunk['chunk_id'],
                        'article_id': chunk['article_id'],
                        'chunk_text': chunk['chunk_text'],
                        'metadata': chunk['metadata'] or {},
                        'embedding': embeddings[j]
                    })
            except Exception as e:
                logger.warning(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Generated embeddings for {len(kb_data)} chunks")
        return kb_data
    
    def _kmeans_cluster(self, embeddings: np.ndarray, n_clusters: Optional[int],
                       article_ids: List[int], chunk_ids: List[int],
                       kb_data: List[Dict]) -> List[Dict]:
        """Apply K-means clustering."""
        sklearn = _import_sklearn()
        KMeans = sklearn['KMeans']
        silhouette_score = sklearn['silhouette_score']
        
        # Auto-detect optimal number of clusters if not specified
        if n_clusters is None:
            n_clusters = self._auto_detect_clusters(embeddings, silhouette_score)
        
        logger.info(f"Running K-means with {n_clusters} clusters")
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # Group by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = {
                    'article_ids': [],
                    'chunk_ids': [],
                    'embeddings': []
                }
            clusters[label]['article_ids'].append(article_ids[i])
            clusters[label]['chunk_ids'].append(chunk_ids[i])
            clusters[label]['embeddings'].append(embeddings[i])
        
        # Convert to list and calculate centroids
        cluster_list = []
        for label, data in clusters.items():
            # Get unique article IDs
            unique_article_ids = list(set(data['article_ids']))
            cluster_list.append({
                'article_ids': unique_article_ids,
                'chunk_ids': data['chunk_ids'],
                'centroid': np.mean(data['embeddings'], axis=0)
            })
        
        return cluster_list
    
    def _dbscan_cluster(self, embeddings: np.ndarray, min_cluster_size: int,
                       article_ids: List[int], chunk_ids: List[int],
                       kb_data: List[Dict]) -> List[Dict]:
        """Apply DBSCAN clustering."""
        sklearn = _import_sklearn()
        DBSCAN = sklearn['DBSCAN']
        
        # DBSCAN parameters
        # eps: maximum distance between samples in same cluster
        # min_samples: minimum samples in a cluster
        eps = 0.5  # Adjust based on embedding space
        min_samples = min_cluster_size
        
        logger.info(f"Running DBSCAN with eps={eps}, min_samples={min_samples}")
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = dbscan.fit_predict(embeddings)
        
        # Group by cluster (ignore noise points with label -1)
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:  # Noise
                continue
            if label not in clusters:
                clusters[label] = {
                    'article_ids': [],
                    'chunk_ids': [],
                    'embeddings': []
                }
            clusters[label]['article_ids'].append(article_ids[i])
            clusters[label]['chunk_ids'].append(chunk_ids[i])
            clusters[label]['embeddings'].append(embeddings[i])
        
        # Convert to list and calculate centroids
        cluster_list = []
        for label, data in clusters.items():
            unique_article_ids = list(set(data['article_ids']))
            cluster_list.append({
                'article_ids': unique_article_ids,
                'chunk_ids': data['chunk_ids'],
                'centroid': np.mean(data['embeddings'], axis=0)
            })
        
        return cluster_list
    
    def _hierarchical_cluster(self, embeddings: np.ndarray, similarity_threshold: float,
                              article_ids: List[int], chunk_ids: List[int],
                              kb_data: List[Dict]) -> List[Dict]:
        """Apply hierarchical clustering."""
        sklearn = _import_sklearn()
        AgglomerativeClustering = sklearn['AgglomerativeClustering']
        
        # Convert similarity threshold to distance
        # cosine distance = 1 - cosine similarity
        distance_threshold = 1.0 - similarity_threshold
        
        logger.info(f"Running hierarchical clustering with distance_threshold={distance_threshold}")
        
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            linkage='average',
            metric='cosine'
        )
        labels = clustering.fit_predict(embeddings)
        
        # Group by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = {
                    'article_ids': [],
                    'chunk_ids': [],
                    'embeddings': []
                }
            clusters[label]['article_ids'].append(article_ids[i])
            clusters[label]['chunk_ids'].append(chunk_ids[i])
            clusters[label]['embeddings'].append(embeddings[i])
        
        # Convert to list and calculate centroids
        cluster_list = []
        for label, data in clusters.items():
            unique_article_ids = list(set(data['article_ids']))
            cluster_list.append({
                'article_ids': unique_article_ids,
                'chunk_ids': data['chunk_ids'],
                'centroid': np.mean(data['embeddings'], axis=0)
            })
        
        return cluster_list
    
    def _auto_detect_clusters(self, embeddings: np.ndarray, silhouette_score) -> int:
        """
        Auto-detect optimal number of clusters using elbow method and silhouette score.
        
        Args:
            embeddings: Embedding vectors
            silhouette_score: Function to calculate silhouette score
        
        Returns:
            Optimal number of clusters
        """
        KMeans = _import_sklearn()['KMeans']
        
        # Try range of cluster numbers
        min_k = 5
        max_k = min(50, len(embeddings) // 10)  # Don't exceed reasonable limits
        
        best_k = min_k
        best_score = -1
        
        logger.info(f"Auto-detecting optimal cluster count (testing {min_k} to {max_k})")
        
        for k in range(min_k, max_k + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
                
                # Calculate silhouette score
                if len(set(labels)) > 1:  # Need at least 2 clusters
                    score = silhouette_score(embeddings, labels, metric='cosine')
                    if score > best_score:
                        best_score = score
                        best_k = k
            except Exception as e:
                logger.warning(f"Error testing k={k}: {e}")
                continue
        
        logger.info(f"Auto-detected optimal cluster count: {best_k} (silhouette score: {best_score:.3f})")
        return best_k
    
    def _extract_topic_info(self, cluster_id: int, cluster_data: Dict,
                           kb_data: List[Dict]) -> Dict:
        """
        Extract topic name, keywords, and metadata from cluster.
        
        Args:
            cluster_id: Cluster identifier
            cluster_data: Cluster data with article_ids, chunk_ids, centroid
            kb_data: Full KB data for context
        
        Returns:
            Topic dictionary
        """
        # Get article texts from cluster
        article_texts = self._get_cluster_article_texts(cluster_data['article_ids'], kb_data)
        
        # Extract keywords (simple TF-IDF approach)
        keywords = self._extract_keywords(article_texts)
        
        # Generate topic name (simple keyword-based for now, can be enhanced with LLM)
        topic_name = self._generate_topic_name(article_texts, keywords)
        
        # Get category IDs from articles
        category_ids = self._get_category_ids(cluster_data['article_ids'])
        
        # Classify topic type
        topic_type = self._classify_topic_type(article_texts)
        
        return {
            'cluster_id': cluster_id,
            'topic_name': topic_name,
            'topic_description': None,  # Can be enhanced with LLM
            'keywords': keywords,
            'article_ids': cluster_data['article_ids'],
            'category_ids': category_ids,
            'centroid_embedding': cluster_data['centroid'].tolist(),  # Convert numpy to list
            'topic_type': topic_type,
            'article_count': len(cluster_data['article_ids'])
        }
    
    def _get_cluster_article_texts(self, article_ids: List[int],
                                   kb_data: List[Dict]) -> List[Dict]:
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
    
    def _extract_keywords(self, article_texts: List[Dict], top_n: int = 10) -> List[str]:
        """
        Extract keywords from article texts using simple frequency analysis.
        
        Args:
            article_texts: List of article text dictionaries
            top_n: Number of top keywords to return
        
        Returns:
            List of keywords
        """
        # Simple word frequency approach
        # In production, could use TF-IDF or LLM-based extraction
        import re
        from collections import Counter
        
        # Common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                     'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
                     'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                     'what', 'which', 'who', 'where', 'when', 'why', 'how', 'about'}
        
        # Combine all texts
        all_text = ' '.join([item['text'] for item in article_texts])
        
        # Extract words (simple tokenization)
        words = re.findall(r'\b[a-z]{3,}\b', all_text.lower())
        
        # Filter stop words and count
        filtered_words = [w for w in words if w not in stop_words]
        word_counts = Counter(filtered_words)
        
        # Get top N keywords
        top_keywords = [word for word, count in word_counts.most_common(top_n)]
        
        return top_keywords
    
    def _generate_topic_name(self, article_texts: List[Dict],
                            keywords: List[str]) -> str:
        """
        Generate topic name from article texts and keywords.
        
        Simple keyword-based approach. Can be enhanced with LLM.
        
        Args:
            article_texts: Article text data
            keywords: Extracted keywords
        
        Returns:
            Topic name string
        """
        # Simple approach: use top keywords
        if keywords:
            # Capitalize and join top 2-3 keywords
            name_parts = [kw.capitalize() for kw in keywords[:3]]
            return ' '.join(name_parts)
        
        # Fallback: use first article title if available
        if article_texts and article_texts[0].get('metadata', {}).get('article_name'):
            title = article_texts[0]['metadata']['article_name']
            # Take first few words
            words = title.split()[:4]
            return ' '.join(words)
        
        return f"Topic {len(article_texts)}"
    
    def _get_category_ids(self, article_ids: List[int]) -> List[int]:
        """Get unique category IDs for articles."""
        if not article_ids:
            return []
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT category_id
                FROM clan_kb_articles
                WHERE id = ANY(%s)
                AND category_id IS NOT NULL
            """, (article_ids,))
            
            results = cursor.fetchall()
            return [row['category_id'] for row in results]
    
    def _classify_topic_type(self, article_texts: List[Dict]) -> str:
        """
        Classify topic type: practical, historical, cultural, design, product, etc.
        
        Args:
            article_texts: Article text data
        
        Returns:
            Topic type string
        """
        # Simple keyword-based classification
        # Can be enhanced with LLM or more sophisticated NLP
        
        type_keywords = {
            'practical': ['how', 'guide', 'measure', 'fit', 'care', 'maintain', 'wear', 'choose'],
            'historical': ['history', 'origin', 'evolution', 'century', 'tradition', 'ancient', 'past'],
            'cultural': ['heritage', 'tradition', 'significance', 'meaning', 'identity', 'culture'],
            'design': ['design', 'create', 'custom', 'pattern', 'color', 'style', 'tartan'],
            'product': ['product', 'fabric', 'material', 'quality', 'specification', 'kilt']
        }
        
        # Combine all texts
        all_text = ' '.join([item['text'].lower() for item in article_texts])
        
        # Score each type
        type_scores = {}
        for topic_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            type_scores[topic_type] = score
        
        # Return highest scoring type, or 'general' if no clear match
        if type_scores:
            max_type = max(type_scores.items(), key=lambda x: x[1])
            if max_type[1] > 0:
                return max_type[0]
        
        return 'general'
