#!/usr/bin/env python3
"""
Renumber calendar sequential list positions to be contiguous (1, 2, 3, ... N).

This fixes gaps created by insert_mode operations by renumbering all items
to have contiguous positions starting from 1.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def renumber_category(category: str, dry_run: bool = True):
    """Renumber positions in a category to be contiguous."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get all items with their current positions
                if category == 'theme':
                    cursor.execute("""
                        SELECT id, position, theme_title as title
                        FROM calendar_themes
                        WHERE position IS NOT NULL
                        ORDER BY position, id
                    """)
                elif category == 'recipe':
                    cursor.execute("""
                        SELECT id, position, recipe_title as title
                        FROM calendar_recipes
                        WHERE position IS NOT NULL
                        ORDER BY position, id
                    """)
                elif category == 'profile_product':
                    cursor.execute("""
                        SELECT cps.post_id as id, cps.position, p.title
                        FROM calendar_profile_sequence cps
                        JOIN post p ON cps.post_id = p.id
                        WHERE cps.profile_type = 'product'
                        ORDER BY cps.position, cps.post_id
                    """)
                elif category == 'profile_surname':
                    cursor.execute("""
                        SELECT cps.post_id as id, cps.position, p.title
                        FROM calendar_profile_sequence cps
                        JOIN post p ON cps.post_id = p.id
                        WHERE cps.profile_type = 'surname'
                        ORDER BY cps.position, cps.post_id
                    """)
                elif category == 'weekly_word':
                    cursor.execute("""
                        SELECT id, position, idea_title as title
                        FROM calendar_ideas
                        WHERE item_classification = 'weekly_word' AND position IS NOT NULL
                        ORDER BY position, id
                    """)
                elif category == 'weekly_phrase':
                    cursor.execute("""
                        SELECT id, position, idea_title as title
                        FROM calendar_ideas
                        WHERE item_classification = 'weekly_phrase' AND position IS NOT NULL
                        ORDER BY position, id
                    """)
                else:
                    logger.warning(f"Unknown category: {category}")
                    return
                
                items = cursor.fetchall()
                item_count = len(items)
                
                if item_count == 0:
                    logger.info(f"No items found for category {category}")
                    return
                
                logger.info(f"\nCategory {category}: {item_count} items")
                logger.info(f"Current positions: {[item['position'] for item in items]}")
                
                # Assign new contiguous positions
                updates = []
                for new_pos, item in enumerate(items, start=1):
                    old_pos = item['position']
                    if old_pos != new_pos:
                        updates.append({
                            'id': item['id'],
                            'old_position': old_pos,
                            'new_position': new_pos,
                            'title': item.get('title', 'N/A')
                        })
                
                if not updates:
                    logger.info(f"  All positions already contiguous, no changes needed")
                    return
                
                logger.info(f"  {len(updates)} items need renumbering:")
                for update in updates[:10]:  # Show first 10
                    logger.info(f"    ID {update['id']}: position {update['old_position']} -> {update['new_position']} ({update['title'][:50]})")
                if len(updates) > 10:
                    logger.info(f"    ... and {len(updates) - 10} more")
                
                if dry_run:
                    logger.info(f"  DRY RUN: Would update {len(updates)} items")
                    return
                
                # Perform updates
                updated_count = 0
                for update in updates:
                    if category == 'theme':
                        cursor.execute("""
                            UPDATE calendar_themes
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (update['new_position'], update['id']))
                    elif category == 'recipe':
                        cursor.execute("""
                            UPDATE calendar_recipes
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (update['new_position'], update['id']))
                    elif category == 'profile_product':
                        cursor.execute("""
                            UPDATE calendar_profile_sequence
                            SET position = %s, updated_at = NOW()
                            WHERE post_id = %s AND profile_type = 'product'
                        """, (update['new_position'], update['id']))
                    elif category == 'profile_surname':
                        cursor.execute("""
                            UPDATE calendar_profile_sequence
                            SET position = %s, updated_at = NOW()
                            WHERE post_id = %s AND profile_type = 'surname'
                        """, (update['new_position'], update['id']))
                    elif category == 'weekly_word':
                        cursor.execute("""
                            UPDATE calendar_ideas
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s AND item_classification = 'weekly_word'
                        """, (update['new_position'], update['id']))
                    elif category == 'weekly_phrase':
                        cursor.execute("""
                            UPDATE calendar_ideas
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s AND item_classification = 'weekly_phrase'
                        """, (update['new_position'], update['id']))
                    
                    updated_count += 1
                
                conn.commit()
                logger.info(f"  Updated {updated_count} items")
                
    except Exception as e:
        logger.error(f"Error renumbering category {category}: {e}", exc_info=True)
        if not dry_run:
            conn.rollback()


def main():
    """Renumber all categories."""
    import argparse
    parser = argparse.ArgumentParser(description='Renumber calendar positions to be contiguous')
    parser.add_argument('--execute', action='store_true', help='Actually perform the updates (default is dry-run)')
    parser.add_argument('--category', help='Only renumber this category (default: all)')
    args = parser.parse_args()
    
    categories = ['theme', 'recipe', 'profile_product', 'profile_surname', 'weekly_word', 'weekly_phrase']
    
    if args.category:
        if args.category not in categories:
            logger.error(f"Unknown category: {args.category}")
            return
        categories = [args.category]
    
    logger.info("Renumbering calendar positions to be contiguous...")
    if not args.execute:
        logger.info("DRY RUN MODE - no changes will be made")
        logger.info("Use --execute to actually perform updates\n")
    
    for category in categories:
        renumber_category(category, dry_run=not args.execute)
    
    if not args.execute:
        logger.info("\n" + "="*60)
        logger.info("This was a DRY RUN. Use --execute to apply changes.")
        logger.info("="*60)


if __name__ == '__main__':
    main()

