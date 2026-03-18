"""Seed discovered Scottish newspaper sources into the database.

Reads the discovery results JSON file and inserts sources into newsletter_snapshot_source.
"""

from __future__ import annotations

import json
import sys
import os
import logging
from typing import Any, Dict, List

# Add blog-core to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../../../'))
blog_core = os.path.join(project_root, 'blog-core')
sys.path.insert(0, project_root)
sys.path.insert(0, blog_core)

from newsletter.db.queries_source_management import create_source

logger = logging.getLogger(__name__)


def load_discovery_results(json_file: str = "data/scottish_newspaper_sources.json") -> List[Dict[str, Any]]:
    """Load discovery results from JSON file."""
    if not os.path.exists(json_file):
        logger.error(f"Discovery results file not found: {json_file}")
        logger.info("Run scottish_newspapers.py first to generate discovery results")
        return []
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both list format and dict with 'sources' key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'sources' in data:
            return data['sources']
        else:
            logger.warning(f"Unexpected JSON format in {json_file}")
            return []


def determine_source_type(newspaper: Dict[str, Any]) -> str:
    """Determine source type based on access mode."""
    access_mode = newspaper.get('access_mode', 'blocked')
    if access_mode == 'rss_only':
        return 'rss'
    elif access_mode == 'html_list_only':
        return 'html'
    else:
        return 'html'  # Default fallback


def get_base_url(newspaper: Dict[str, Any]) -> str | None:
    """Get the base URL to use for the source.
    
    Prefers RSS feed URL, then listing page URL, then base_url.
    """
    rss_feeds = newspaper.get('rss_feeds', [])
    if rss_feeds:
        return rss_feeds[0]  # Use first RSS feed
    
    listing_pages = newspaper.get('listing_pages', [])
    if listing_pages:
        return listing_pages[0]  # Use first listing page
    
    return newspaper.get('base_url')


def seed_sources(
    newspapers: List[Dict[str, Any]],
    enabled: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Seed discovered sources into database.
    
    Args:
        newspapers: List of discovered newspaper dicts
        enabled: Whether to enable sources immediately (default: False, test first)
        dry_run: If True, don't actually insert, just report what would be done
    
    Returns:
        Dict with summary statistics
    """
    stats = {
        'total': len(newspapers),
        'inserted': 0,
        'skipped': 0,
        'errors': 0,
        'accessible': 0,
        'blocked': 0,
    }
    
    for newspaper in newspapers:
        name = newspaper.get('name')
        if not name:
            logger.warning("Skipping newspaper with no name")
            stats['skipped'] += 1
            continue
        
        # Skip if no accessible content
        access_mode = newspaper.get('access_mode', 'blocked')
        if access_mode == 'blocked':
            logger.info(f"Skipping {name}: blocked or no accessible content")
            stats['blocked'] += 1
            stats['skipped'] += 1
            continue
        
        stats['accessible'] += 1
        
        # Get base URL
        base_url = get_base_url(newspaper)
        if not base_url:
            logger.warning(f"Skipping {name}: no base URL found")
            stats['skipped'] += 1
            continue
        
        # Determine source type
        source_type = determine_source_type(newspaper)
        
        # Extract region
        region = newspaper.get('region', 'Unknown')
        
        # Get discovery notes
        discovery_notes = newspaper.get('discovery_notes', '')
        
        # Determine preferred/excluded sections (can be customized later)
        preferred_sections = None  # Can be set based on source analysis
        excluded_sections = ['crime', 'court', 'obituary']  # Default exclusions
        
        if dry_run:
            logger.info(f"[DRY RUN] Would insert: {name} ({base_url}) - {access_mode}")
            stats['inserted'] += 1
        else:
            try:
                source_id = create_source(
                    name=name,
                    base_url=base_url,
                    type=source_type,
                    enabled=enabled,
                    region=region,
                    preferred_sections=preferred_sections,
                    excluded_sections=excluded_sections,
                    access_mode=access_mode,
                    discovery_notes=discovery_notes,
                )
                logger.info(f"Inserted source: {name} (ID: {source_id})")
                stats['inserted'] += 1
            except Exception as e:
                logger.error(f"Failed to insert {name}: {e}", exc_info=True)
                stats['errors'] += 1
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed discovered Scottish newspaper sources')
    parser.add_argument(
        '--json-file',
        default='data/scottish_newspaper_sources.json',
        help='Path to discovery results JSON file'
    )
    parser.add_argument(
        '--enabled',
        action='store_true',
        help='Enable sources immediately (default: disabled for testing)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be inserted without actually inserting'
    )
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load discovery results
    newspapers = load_discovery_results(args.json_file)
    if not newspapers:
        logger.error("No newspapers found in discovery results")
        return 1
    
    logger.info(f"Loaded {len(newspapers)} newspapers from discovery results")
    
    # Seed sources
    stats = seed_sources(newspapers, enabled=args.enabled, dry_run=args.dry_run)
    
    # Print summary
    print("\n" + "="*60)
    print("Seeding Summary")
    print("="*60)
    print(f"Total newspapers: {stats['total']}")
    print(f"Accessible sources: {stats['accessible']}")
    print(f"Blocked/no content: {stats['blocked']}")
    print(f"Inserted: {stats['inserted']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    
    if args.dry_run:
        print("\n[DRY RUN] No sources were actually inserted")
    elif not args.enabled:
        print("\nNote: Sources were inserted with enabled=false")
        print("Enable them manually after testing via the UI or database")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

