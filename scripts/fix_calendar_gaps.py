#!/usr/bin/env python3
"""
Fix gaps in calendar sequential lists by ensuring all positions are filled.

This script checks each category and ensures that:
1. All positions from 1 to max(position) are filled
2. No positions are missing
3. All weeks will have items assigned
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.calendar_sequential_resolver import get_item_count, calculate_position_for_week
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_category(category: str, profile_type: str = None):
    """Check a category for gaps and report them."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all items and their positions
            if category == 'theme':
                cursor.execute("""
                    SELECT id, position, theme_title as title
                    FROM calendar_themes
                    ORDER BY position
                """)
            elif category == 'recipe':
                cursor.execute("""
                    SELECT id, position, recipe_title as title
                    FROM calendar_recipes
                    ORDER BY position
                """)
            elif category in ('profile_product', 'profile_surname'):
                if category == 'profile_product':
                    profile_type = 'product'
                else:
                    profile_type = 'surname'
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.profile_type = %s
                    ORDER BY cps.position
                """, (profile_type,))
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT id, position, idea_title as title
                    FROM calendar_ideas
                    WHERE item_classification = 'weekly_word'
                    ORDER BY position
                """)
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT id, position, idea_title as title
                    FROM calendar_ideas
                    WHERE item_classification = 'weekly_phrase'
                    ORDER BY position
                """)
            else:
                logger.warning(f"Unknown category: {category}")
                return
            
            items = cursor.fetchall()
            item_count = len(items)
            
            if item_count == 0:
                logger.warning(f"No items found for category {category}")
                return
            
            # Check for gaps
            positions = [item['position'] for item in items if item['position'] is not None]
            if not positions:
                logger.warning(f"No positions found for category {category}")
                return
            
            max_pos = max(positions)
            expected_positions = set(range(1, max_pos + 1))
            actual_positions = set(positions)
            missing_positions = expected_positions - actual_positions
            
            if missing_positions:
                logger.error(f"Category {category}: Missing positions: {sorted(missing_positions)}")
                logger.error(f"  Total items: {item_count}, Max position: {max_pos}")
                logger.error(f"  Expected positions 1-{max_pos}, but missing: {sorted(missing_positions)}")
                
                # Check which weeks would be affected
                for year in [2025, 2026]:
                    for week in range(1, 53):
                        pos = calculate_position_for_week(category, year, week)
                        if pos in missing_positions:
                            logger.error(f"  Week {year}-W{week:02d} would have no item (position {pos} is missing)")
            else:
                logger.info(f"Category {category}: All positions 1-{max_pos} are filled ({item_count} items)")
            
            # Check for duplicate positions
            from collections import Counter
            position_counts = Counter(positions)
            duplicates = {pos: count for pos, count in position_counts.items() if count > 1}
            if duplicates:
                logger.error(f"Category {category}: Duplicate positions: {duplicates}")
            
            return {
                'category': category,
                'item_count': item_count,
                'max_position': max_pos,
                'missing_positions': sorted(missing_positions) if missing_positions else [],
                'duplicates': duplicates
            }
    
    except Exception as e:
        logger.error(f"Error checking category {category}: {e}", exc_info=True)
        return None


def main():
    """Check all categories for gaps."""
    categories = ['theme', 'recipe', 'profile_product', 'profile_surname', 'weekly_word', 'weekly_phrase']
    
    logger.info("Checking all categories for gaps...")
    results = []
    
    for category in categories:
        result = check_and_fix_category(category)
        if result:
            results.append(result)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    
    for result in results:
        if result['missing_positions']:
            logger.error(f"{result['category']}: {len(result['missing_positions'])} missing positions")
        elif result['duplicates']:
            logger.error(f"{result['category']}: {len(result['duplicates'])} duplicate positions")
        else:
            logger.info(f"{result['category']}: OK ({result['item_count']} items, positions 1-{result['max_position']})")


if __name__ == '__main__':
    main()

