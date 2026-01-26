#!/usr/bin/env python3
"""
Discover Hierarchical KB Topics Script - GRANULAR VERSION

This version uses more granular clustering parameters to create:
- More Level 1 topics (20-30 instead of 8-15)
- Smaller, more specific topics that better reflect content balance
- More granular sub-topics

Usage:
    python scripts/discover_hierarchical_topics_granular.py [--broad-clusters N] [--granular-threshold FLOAT]
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
    """Main discovery process with granular settings."""
    parser = argparse.ArgumentParser(description='Discover hierarchical KB topics with granular clustering')
    parser.add_argument('--broad-clusters', type=int, default=25,
                       help='Number of broad theme clusters (default: 25, increased for more granularity)')
    parser.add_argument('--granular-threshold', type=float, default=0.82,
                       help='Similarity threshold for granular sub-clustering (default: 0.82, higher = more specific)')
    parser.add_argument('--min-broad-size', type=int, default=6,
                       help='Minimum articles for broad topics (default: 6, lowered to allow more clusters)')
    parser.add_argument('--min-granular-size', type=int, default=2,
                       help='Minimum articles for granular sub-topics (default: 2, lowered for more granularity)')
    parser.add_argument('--compute-similarity', action='store_true',
                       help='Compute and store similarity matrix')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run discovery without storing to database (for testing)')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Hierarchical KB Topic Discovery - GRANULAR MODE")
    logger.info("=" * 80)
    logger.info(f"Broad clusters: {args.broad_clusters} (increased for more granularity)")
    logger.info(f"Granular threshold: {args.granular_threshold} (higher = more specific sub-topics)")
    logger.info(f"Min broad size: {args.min_broad_size} (lowered to allow more clusters)")
    logger.info(f"Min granular size: {args.min_granular_size} (lowered for more granularity)")
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
    
    # Analyze results before storing
    broad_topics = [t for t in topics if t.get('is_broad', True)]
    granular_topics = [t for t in topics if not t.get('is_broad', True)]
    
    logger.info("=" * 80)
    logger.info("Discovery Results Analysis")
    logger.info("=" * 80)
    logger.info(f"Total topics: {len(topics)}")
    logger.info(f"  - Broad themes (Level 1): {len(broad_topics)}")
    logger.info(f"  - Granular sub-topics (Level 2): {len(granular_topics)}")
    logger.info("")
    
    # Analyze article distribution
    if broad_topics:
        article_counts = [t.get('article_count', len(t.get('article_ids', []))) for t in broad_topics]
        avg_articles = sum(article_counts) / len(article_counts) if article_counts else 0
        max_articles = max(article_counts) if article_counts else 0
        min_articles = min(article_counts) if article_counts else 0
        
        logger.info(f"Level 1 article distribution:")
        logger.info(f"  - Average: {avg_articles:.1f} articles per topic")
        logger.info(f"  - Range: {min_articles} - {max_articles} articles")
        logger.info(f"  - Target: < 50 articles per topic for better granularity")
        logger.info("")
    
    logger.info("Sample broad themes:")
    for i, topic in enumerate(broad_topics[:10], 1):
        article_count = topic.get('article_count', len(topic.get('article_ids', [])))
        logger.info(f"  {i}. {topic['topic_name']} ({article_count} articles)")
    
    if len(broad_topics) > 10:
        logger.info(f"  ... and {len(broad_topics) - 10} more")
    
    logger.info("")
    logger.info("Sample granular sub-topics:")
    for i, topic in enumerate(granular_topics[:10], 1):
        article_count = topic.get('article_count', len(topic.get('article_ids', [])))
        parent_temp_id = topic.get('parent_id')
        parent_name = next((t['topic_name'] for t in broad_topics if t.get('temp_id') == parent_temp_id), 'Unknown')
        logger.info(f"  {i}. {topic['topic_name']} (under: {parent_name}, {article_count} articles)")
    
    if len(granular_topics) > 10:
        logger.info(f"  ... and {len(granular_topics) - 10} more")
    
    logger.info("")
    
    if args.dry_run:
        logger.info("DRY RUN: Not storing topics to database")
        return 0
    
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
    
    # Final summary
    logger.info("=" * 80)
    logger.info("Discovery Complete")
    logger.info("=" * 80)
    logger.info(f"Total topics stored: {len(topics)}")
    logger.info(f"  - Broad themes (Level 1): {len(broad_topics)}")
    logger.info(f"  - Granular sub-topics (Level 2): {len(granular_topics)}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Review topics at /kb-topics/editor")
    logger.info("  2. Exclude any topics that are too broad or not relevant")
    logger.info("  3. Run auto-arrange to generate weekly rota")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
