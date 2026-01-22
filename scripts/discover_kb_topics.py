#!/usr/bin/env python3
"""
Discover KB Topics Script

Discovers topics from Knowledge Base articles using clustering,
stores them in database, and calculates similarity matrix.

Usage:
    python scripts/discover_kb_topics.py [--method kmeans|dbscan|hierarchical] [--n-clusters N] [--min-cluster-size N]
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.kb_topic_discovery.clustering import KBTopicClusterer
from utils.kb_topic_discovery.similarity import TopicSimilarityCalculator
from utils.kb_topic_discovery.storage import store_topics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main discovery process."""
    parser = argparse.ArgumentParser(description='Discover KB topics using clustering')
    parser.add_argument('--method', choices=['kmeans', 'dbscan', 'hierarchical'],
                       default='kmeans', help='Clustering method')
    parser.add_argument('--n-clusters', type=int, default=None,
                       help='Number of clusters (auto-detect if not specified)')
    parser.add_argument('--min-cluster-size', type=int, default=3,
                       help='Minimum cluster size')
    parser.add_argument('--similarity-threshold', type=float, default=0.7,
                       help='Similarity threshold for hierarchical clustering')
    parser.add_argument('--compute-similarity', action='store_true',
                       help='Compute and store similarity matrix after discovery')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("KB Topic Discovery")
    logger.info("=" * 80)
    logger.info(f"Method: {args.method}")
    if args.n_clusters:
        logger.info(f"Number of clusters: {args.n_clusters}")
    logger.info(f"Min cluster size: {args.min_cluster_size}")
    logger.info("")
    
    # Step 1: Discover topics
    logger.info("Step 1: Discovering topics...")
    clusterer = KBTopicClusterer()
    
    topics = clusterer.discover_topics(
        method=args.method,
        n_clusters=args.n_clusters,
        min_cluster_size=args.min_cluster_size,
        similarity_threshold=args.similarity_threshold
    )
    
    if not topics:
        logger.error("No topics discovered")
        return 1
    
    logger.info(f"Discovered {len(topics)} topics")
    logger.info("")
    
    # Step 2: Store topics in database
    logger.info("Step 2: Storing topics in database...")
    if not store_topics(topics):
        logger.error("Failed to store topics")
        return 1
    
    logger.info("")
    
    # Step 3: Compute similarity matrix
    if args.compute_similarity:
        logger.info("Step 3: Computing similarity matrix...")
        similarity_calc = TopicSimilarityCalculator()
        similarities = similarity_calc.compute_similarity_matrix(topics)
        logger.info(f"Computed {len(similarities)} similarity pairs")
        logger.info("")
    
    # Summary
    logger.info("=" * 80)
    logger.info("Discovery Complete")
    logger.info("=" * 80)
    logger.info(f"Topics discovered: {len(topics)}")
    logger.info("")
    logger.info("Sample topics:")
    for i, topic in enumerate(topics[:5], 1):
        logger.info(f"  {i}. {topic['topic_name']} ({topic['article_count']} articles, type: {topic.get('topic_type', 'general')})")
    
    if len(topics) > 5:
        logger.info(f"  ... and {len(topics) - 5} more")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
