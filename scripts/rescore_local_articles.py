#!/usr/bin/env python3
"""Re-score existing articles from local sources with heuristic scoring."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

from config.database import db_manager
from newsletter.services.scoring import score_items
from psycopg.types.json import Json

def main():
    """Re-score all articles from local sources."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Get all articles from local sources that need re-scoring
            cur.execute('''
                SELECT nsi.id, nsi.source_name, nsi.title, nsi.url, nsi.published_at,
                       nsi.location, nsi.category, nsi.raw_data, nsi.cached_at
                FROM newsletter_source_item nsi
                INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
                WHERE ns.region IS NOT NULL
                AND nsi.category = 'news'
                AND (nsi.heuristic_score = 0 OR nsi.heuristic_score IS NULL)
            ''')
            articles = [dict(r) for r in cur.fetchall()]
            
            if not articles:
                print('No articles found to re-score')
                return
            
            print(f'Re-scoring {len(articles)} articles from local sources...')
            
            # Re-score them (heuristic scoring is applied automatically for local sources)
            scored = score_items(articles)
            
            # Update in database
            updated = 0
            for item in scored:
                try:
                    cur.execute('''
                        UPDATE newsletter_source_item
                        SET heuristic_score = %s, heuristic_flags = %s
                        WHERE id = %s
                    ''', (
                        item.get('heuristic_score', 0.0),
                        Json(item.get('heuristic_flags', [])),
                        item['id']
                    ))
                    updated += 1
                except Exception as e:
                    print(f"Error updating article {item.get('id')}: {e}")
                    continue
            
            conn.commit()
            print(f'✓ Updated {updated} articles with heuristic scores')
            
            # Show summary
            cur.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN heuristic_score > 0 THEN 1 END) as with_score,
                    COUNT(CASE WHEN heuristic_score >= 3.0 THEN 1 END) as above_threshold
                FROM newsletter_source_item nsi
                INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
                WHERE ns.region IS NOT NULL
                AND nsi.category = 'news'
            ''')
            stats = cur.fetchone()
            print(f'\nSummary:')
            print(f'  Total articles: {stats["total"]}')
            print(f'  With heuristic score > 0: {stats["with_score"]}')
            print(f'  Above threshold (>= 3.0): {stats["above_threshold"]}')

if __name__ == '__main__':
    main()

