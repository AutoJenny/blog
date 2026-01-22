#!/usr/bin/env python3
"""
KB Topic Discovery Runner

Periodic job to discover new topics from KB and maintain rota schedule.
Runs when:
- New KB articles added
- KB articles updated
- Manual trigger
"""

import sys
import os
import logging
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.kb_topic_discovery.clustering import KBTopicClusterer
from utils.kb_topic_discovery.similarity import TopicSimilarityCalculator
from utils.kb_topic_discovery.rota_generator import RotaGenerator
from utils.kb_topic_discovery.content_aggregator import TopicContentAggregator
from utils.kb_topic_discovery.storage import store_topics
from config.database import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_for_new_kb_articles() -> bool:
    """
    Check if there are new or updated KB articles since last discovery.
    
    Returns:
        True if new/updated articles found
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Get last discovery time
            cursor.execute("""
                SELECT MAX(discovered_at) as last_discovery
                FROM kb_topics
            """)
            
            result = cursor.fetchone()
            last_discovery = result['last_discovery'] if result else None
            
            # Check for new/updated articles
            if last_discovery:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM clan_kb_articles
                    WHERE (clan_created_at > %s OR clan_updated_at > %s)
                    AND is_active = TRUE
                """, (last_discovery, last_discovery))
            else:
                # First run - check if any articles exist
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM clan_kb_articles
                    WHERE is_active = TRUE
                """)
            
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            return count > 0
    except Exception as e:
        logger.warning(f"Error checking for new articles: {e}")
        return True  # Assume there are updates if we can't check


def run_topic_discovery():
    """
    Run topic discovery process.
    """
    logger.info("Running topic discovery...")
    
    clusterer = KBTopicClusterer()
    topics = clusterer.discover_topics(method='kmeans', min_cluster_size=3)
    
    if not topics:
        logger.warning("No topics discovered")
        return False
    
    # Store topics
    if not store_topics(topics):
        logger.error("Failed to store topics")
        return False
    
    # Compute similarity matrix
    similarity_calc = TopicSimilarityCalculator()
    similarity_calc.compute_similarity_matrix(topics)
    
    logger.info(f"Discovered and stored {len(topics)} topics")
    return True


def maintain_rota():
    """
    Maintain rota schedule - fill gaps and update diversity scores.
    """
    logger.info("Maintaining rota schedule...")
    
    # Check for upcoming weeks without topics
    today = date.today()
    weeks_ahead = 4
    
    gaps = []
    for i in range(weeks_ahead):
        check_date = today + timedelta(weeks=i)
        year, week, _ = check_date.isocalendar()
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM kb_topic_rota
                WHERE scheduled_year = %s AND scheduled_week = %s
            """, (year, week))
            
            if not cursor.fetchone():
                gaps.append((year, week, check_date))
    
    if gaps:
        logger.info(f"Found {len(gaps)} gaps in rota schedule")
        
        # Generate rota for gaps
        rota_gen = RotaGenerator()
        
        # Start from first gap
        if gaps:
            start_date = gaps[0][2]
            # Ensure it's a Monday
            if start_date.weekday() != 0:
                days_until_monday = (7 - start_date.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                start_date += timedelta(days=days_until_monday)
            
            # Generate rota for gaps
            rota = rota_gen.generate_rota(
                start_date=start_date,
                weeks=len(gaps),
                lookback_weeks=6,
                min_similarity_gap=0.7
            )
            
            # Save rota
            rota_gen.save_rota(rota)
            logger.info(f"Filled {len(rota)} gaps in rota")
    else:
        logger.info("No gaps in rota schedule")
    
    # Aggregate content for upcoming topics
    aggregate_upcoming_content(weeks_ahead=2)


def aggregate_upcoming_content(weeks_ahead: int = 2):
    """
    Aggregate content for upcoming topics in rota.
    
    Args:
        weeks_ahead: Number of weeks ahead to aggregate
    """
    logger.info(f"Aggregating content for next {weeks_ahead} weeks...")
    
    today = date.today()
    aggregator = TopicContentAggregator()
    
    aggregated = 0
    for i in range(weeks_ahead):
        check_date = today + timedelta(weeks=i)
        year, week, _ = check_date.isocalendar()
        
        # Get rota entry
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, topic_id
                FROM kb_topic_rota
                WHERE scheduled_year = %s AND scheduled_week = %s
            """, (year, week))
            
            rota_entry = cursor.fetchone()
            if not rota_entry:
                continue
            
            # Check if content already exists
            cursor.execute("""
                SELECT id FROM kb_topic_content
                WHERE topic_id = %s AND rota_id = %s
            """, (rota_entry['topic_id'], rota_entry['id']))
            
            if cursor.fetchone():
                continue  # Already aggregated
            
            # Aggregate content
            content_data = aggregator.aggregate_content(rota_entry['topic_id'], limit=5)
            if content_data:
                aggregator.save_aggregated_content(
                    rota_entry['topic_id'],
                    rota_entry['id'],
                    content_data
                )
                aggregated += 1
    
    logger.info(f"Aggregated content for {aggregated} topics")


def should_regenerate_rota() -> bool:
    """
    Determine if rota should be regenerated.
    
    Returns:
        True if rota should be regenerated
    """
    # Regenerate if:
    # 1. New topics discovered
    # 2. Many topics updated
    # 3. Rota is incomplete
    
    # Check if rota has gaps
    today = date.today()
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM kb_topic_rota
            WHERE scheduled_date >= %s
            AND scheduled_date <= %s
        """, (today, today + timedelta(weeks=52)))
        
        result = cursor.fetchone()
        rota_count = result['count'] if result else 0
        
        # If less than 48 weeks scheduled, regenerate
        if rota_count < 48:
            return True
    
    return False


def main():
    """Main runner function."""
    logger.info("=" * 80)
    logger.info("KB Topic Discovery Runner")
    logger.info("=" * 80)
    
    # Check for new articles
    has_new_articles = check_for_new_kb_articles()
    
    if has_new_articles:
        logger.info("New or updated KB articles detected - running discovery")
        run_topic_discovery()
    else:
        logger.info("No new KB articles - skipping discovery")
    
    # Maintain rota
    maintain_rota()
    
    # Regenerate rota if needed
    if should_regenerate_rota():
        logger.info("Regenerating rota schedule...")
        rota_gen = RotaGenerator()
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        start_date = today + timedelta(days=days_until_monday)
        
        rota = rota_gen.generate_rota(start_date=start_date, weeks=52)
        rota_gen.save_rota(rota)
        logger.info("Rota regenerated")
    
    logger.info("Runner complete")


if __name__ == '__main__':
    main()
