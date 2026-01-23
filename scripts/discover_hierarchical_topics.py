#!/usr/bin/env python3
"""
Discover Hierarchical KB Topics Script

Discovers topics at multiple levels of granularity:
- Broad themes (Level 1)
- Specific sub-themes (Level 2)

Usage:
    python scripts/discover_hierarchical_topics.py [--broad-clusters N] [--granular-threshold FLOAT]
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

from utils.kb_topic_discovery.hierarchical_discovery import HierarchicalTopicDiscoverer
from utils.kb_topic_discovery.storage import store_topics
from utils.kb_topic_discovery.similarity import TopicSimilarityCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main discovery process."""
    parser = argparse.ArgumentParser(description='Discover hierarchical KB topics')
    parser.add_argument('--broad-clusters', type=int, default=15,
                       help='Number of broad theme clusters (default: 15)')
    parser.add_argument('--granular-threshold', type=float, default=0.75,
                       help='Similarity threshold for granular sub-clustering (default: 0.75, higher = more specific)')
    parser.add_argument('--min-broad-size', type=int, default=10,
                       help='Minimum articles for broad topics (default: 10)')
    parser.add_argument('--min-granular-size', type=int, default=3,
                       help='Minimum articles for granular sub-topics (default: 3)')
    parser.add_argument('--compute-similarity', action='store_true',
                       help='Compute and store similarity matrix')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Hierarchical KB Topic Discovery")
    logger.info("=" * 80)
    logger.info(f"Broad clusters: {args.broad_clusters}")
    logger.info(f"Granular threshold: {args.granular_threshold}")
    logger.info(f"Min broad size: {args.min_broad_size}")
    logger.info(f"Min granular size: {args.min_granular_size}")
    logger.info("")
    
    # Step 1: Discover hierarchical topics
    logger.info("Step 1: Discovering hierarchical topics...")
    discoverer = HierarchicalTopicDiscoverer()
    
    topics = discoverer.discover_hierarchical_topics(
        broad_clusters=args.broad_clusters,
        granular_threshold=args.granular_threshold,
        min_broad_size=args.min_broad_size,
        min_granular_size=args.min_granular_size
    )
    
    if not topics:
        logger.error("No topics discovered")
        return 1
    
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
    
    broad_topics = [t for t in topics if t.get('is_broad', True)]
    granular_topics = [t for t in topics if not t.get('is_broad', True)]
    
    logger.info(f"Total topics: {len(topics)}")
    logger.info(f"  - Broad themes (Level 1): {len(broad_topics)}")
    logger.info(f"  - Granular sub-topics (Level 2): {len(granular_topics)}")
    logger.info("")
    logger.info("Sample broad themes:")
    for i, topic in enumerate(broad_topics[:5], 1):
        logger.info(f"  {i}. {topic['topic_name']} ({topic['article_count']} articles)")
    
    if len(broad_topics) > 5:
        logger.info(f"  ... and {len(broad_topics) - 5} more")
    
    logger.info("")
    logger.info("Sample granular sub-topics:")
    for i, topic in enumerate(granular_topics[:5], 1):
        parent_name = next((t['topic_name'] for t in broad_topics if t.get('id') == topic.get('parent_id')), 'Unknown')
        logger.info(f"  {i}. {topic['topic_name']} (under: {parent_name}, {topic['article_count']} articles)")
    
    if len(granular_topics) > 5:
        logger.info(f"  ... and {len(granular_topics) - 5} more")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
