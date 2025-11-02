"""Orchestration job for VisitScotland event processing.

This job:
1. Scrapes VisitScotland pages using VisitScotlandScraper
2. Saves raw JSON files
3. Parses events with LLM (intelligent date/location extraction)
4. Deduplicates against existing events
5. Saves new/updated events to database
"""

import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List

# Add blog-core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from newsletter.sources.visitscotland_scraper import VisitScotlandScraper
from newsletter.services.event_parser_service import parse_events_batch
from newsletter.services.event_deduplication_service import find_and_merge_duplicate
from newsletter.db.queries_sources import store_source_items
from config.database import db_manager
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# VisitScotland pages to scrape
VISITSCOTLAND_PAGES = [
    {
        'name': 'VisitScotland - Scottish Culture Events',
        'url': 'https://www.visitscotland.com/things-to-do/events/scottish-culture',
    },
    {
        'name': 'VisitScotland - Edinburgh Festivals',
        'url': 'https://www.visitscotland.com/things-to-do/events/edinburgh-festivals',
    },
    {
        'name': 'VisitScotland - Highland Games',
        'url': 'https://www.visitscotland.com/things-to-do/events/highland-games',
    },
    {
        'name': 'VisitScotland - Music Festivals',
        'url': 'https://www.visitscotland.com/things-to-do/events/music-festivals',
    },
]


def process_visitscotland_events() -> Dict[str, Any]:
    """Process all VisitScotland event pages.
    
    Returns:
        Dict with summary of processing results
    """
    all_raw_events = []
    all_parsed_events = []
    
    logger.info("Starting VisitScotland event processing")
    
    # Step 1: Scrape all pages
    for page_config in VISITSCOTLAND_PAGES:
        try:
            logger.info(f"Scraping {page_config['name']} from {page_config['url']}")
            
            scraper = VisitScotlandScraper(
                source_name=page_config['name'],
                base_url=page_config['url'],
                category='event'
            )
            
            raw_events = scraper.fetch()
            logger.info(f"  Extracted {len(raw_events)} raw events")
            all_raw_events.extend(raw_events)
            
        except Exception as e:
            logger.error(f"Error scraping {page_config['name']}: {e}", exc_info=True)
            continue
    
    logger.info(f"Total raw events extracted: {len(all_raw_events)}")
    
    if not all_raw_events:
        return {
            'raw_events': 0,
            'parsed_events': 0,
            'stored': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
    
    # Step 2: Parse events with LLM
    logger.info("Parsing events with LLM...")
    try:
        parsed_events = parse_events_batch(all_raw_events)
        logger.info(f"Parsed {len(parsed_events)} events")
        all_parsed_events = parsed_events
    except Exception as e:
        logger.error(f"Error parsing events with LLM: {e}", exc_info=True)
        return {
            'raw_events': len(all_raw_events),
            'parsed_events': 0,
            'stored': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [str(e)]
        }
    
    # Step 3: Prepare events for storage (convert to newsletter_source_item format)
    items_to_store = []
    stored_count = 0
    updated_count = 0
    skipped_count = 0
    
    for parsed_event in all_parsed_events:
        try:
            # Get source name from raw data
            raw_data = parsed_event.get('raw_data', {})
            source_url = raw_data.get('source_url', '')
            
            # Determine source name from URL
            if 'scottish-culture' in source_url:
                source_name = 'VisitScotland - Scottish Culture Events'
            elif 'edinburgh-festivals' in source_url:
                source_name = 'VisitScotland - Edinburgh Festivals'
            elif 'highland-games' in source_url:
                source_name = 'VisitScotland - Highland Games'
            elif 'music-festivals' in source_url:
                source_name = 'VisitScotland - Music Festivals'
            else:
                source_name = 'VisitScotland'
            
            # Convert parsed event to format expected by store_source_items
            item = {
                'title': parsed_event.get('title', 'Unknown'),
                'url': parsed_event.get('url', ''),
                'event_date': parsed_event.get('event_date'),  # May be None
                'location': parsed_event.get('location'),
                'description': parsed_event.get('description', ''),
                'category': 'event',
                'source_name': source_name,
                'raw_data': raw_data,
                'date_text': parsed_event.get('date_text', ''),
            }
            
            # Check for duplicates using deduplication service
            # find_and_merge_duplicate expects a dict and returns (id, was_updated)
            duplicate_id, was_updated = find_and_merge_duplicate(item, update_existing=True)
            
            if duplicate_id:
                if was_updated:
                    updated_count += 1
                    logger.debug(f"Updated existing event: {item['title']}")
                else:
                    skipped_count += 1
                    logger.debug(f"Skipped duplicate: {item['title']}")
            else:
                # New event, add to list
                items_to_store.append(item)
        
        except Exception as e:
            logger.error(f"Error preparing event for storage: {e}", exc_info=True)
            continue
    
    # Step 4: Store new events
    if items_to_store:
        logger.info(f"Storing {len(items_to_store)} new events...")
        try:
            stored_count = store_source_items(items_to_store, update_duplicates=False)
            logger.info(f"Stored {stored_count} new events")
        except Exception as e:
            logger.error(f"Error storing events: {e}", exc_info=True)
    
    return {
        'raw_events': len(all_raw_events),
        'parsed_events': len(all_parsed_events),
        'stored': stored_count,
        'updated': updated_count,
        'skipped': skipped_count,
        'errors': []
    }


def run() -> Dict[str, Any]:
    """Run the VisitScotland event processing job."""
    return process_visitscotland_events()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run()
    
    print("\n" + "="*80)
    print("VisitScotland Event Processing Summary:")
    print(f"  Raw events extracted: {result['raw_events']}")
    print(f"  Events parsed: {result['parsed_events']}")
    print(f"  New events stored: {result['stored']}")
    print(f"  Existing events updated: {result['updated']}")
    print(f"  Duplicates skipped: {result['skipped']}")
    print("="*80)

