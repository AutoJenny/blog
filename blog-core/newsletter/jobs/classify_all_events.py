"""Script to classify all existing events using LLM."""

import sys
import os
from pathlib import Path

# Add blog-core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.database import db_manager
from psycopg.rows import dict_row
from newsletter.services.event_classification_service import classify_event_recurrence
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify_all_events():
    """Classify all events in the database."""
    with db_manager.get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Get all events without classification
            cur.execute("""
                SELECT 
                    id,
                    title,
                    location,
                    source_name,
                    event_date,
                    raw_data->>'recurring_info' as recurring_info,
                    raw_data->>'date_text_preserved' as date_text,
                    raw_data->>'summary' as summary
                FROM newsletter_source_item
                WHERE category = 'event'
                ORDER BY title
            """)
            
            events = cur.fetchall()
            logger.info(f"Found {len(events)} events to classify")
            
            classified = 0
            for event in events:
                try:
                    event_data = {
                        'title': event['title'],
                        'date_text': event.get('date_text', ''),
                        'recurring_info': event.get('recurring_info'),
                        'description': event.get('summary', ''),
                        'location': event.get('location', ''),
                        'source_name': event.get('source_name', ''),
                    }
                    
                    classification = classify_event_recurrence(event_data)
                    
                    # Update database
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET event_recurrence_type = %s
                        WHERE id = %s
                    """, (classification, event['id']))
                    
                    classified += 1
                    logger.info(f"✓ Classified: {event['title'][:50]} → {classification}")
                    
                except Exception as e:
                    logger.error(f"Error classifying event {event.get('title', 'Unknown')}: {e}", exc_info=True)
                    continue
            
            conn.commit()
            logger.info(f"\n✓ Classified {classified} events")
            
            # Show summary
            cur.execute("""
                SELECT event_recurrence_type, COUNT(*) as count
                FROM newsletter_source_item
                WHERE category = 'event'
                GROUP BY event_recurrence_type
                ORDER BY count DESC
            """)
            
            print("\nClassification summary:")
            for row in cur.fetchall():
                print(f"  {row['event_recurrence_type'] or 'Unclassified'}: {row['count']}")


if __name__ == '__main__':
    classify_all_events()

