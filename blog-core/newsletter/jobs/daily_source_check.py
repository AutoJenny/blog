"""Daily scheduled job for checking all newsletter sources and refreshing cache."""

from __future__ import annotations

import logging
from datetime import datetime
from newsletter.jobs.prefetch_sources import run as run_prefetch

logger = logging.getLogger(__name__)


def run(config: dict | None = None) -> dict:
    """Run daily source check job.
    
    Args:
        config: Optional configuration dict with:
            - run_time: str in HH:MM format (default: "06:00")
            - enabled: bool (default: True)
    
    Returns:
        Result dict from prefetch job
    """
    if config is None:
        config = {}
    
    enabled = config.get('enabled', True)
    if not enabled:
        logger.info("Daily source check is disabled")
        return {
            'success': False,
            'error': 'Job disabled',
            'skipped': True,
        }
    
    run_time = config.get('run_time', '06:00')
    logger.info(f"Starting daily source check (scheduled for {run_time})")
    
    start_time = datetime.now()
    
    try:
        # Run the prefetch job with specialized processing
        result = run_prefetch()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Daily source check completed in {elapsed:.2f} seconds")
        
        # Add timing information
        result['duration_seconds'] = elapsed
        result['completed_at'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"Daily source check failed: {e}", exc_info=True)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': False,
            'error': str(e),
            'duration_seconds': elapsed,
            'completed_at': datetime.now().isoformat(),
        }


# Entry point for cron/scheduler
if __name__ == '__main__':
    import sys
    import os
    
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run job
    result = run()
    
    if result.get('success'):
        print(f"✓ Daily source check completed successfully")
        print(f"  Fetched: {result.get('fetched', 0)} items")
        print(f"  Events: {result.get('events', {}).get('imported', 0)} imported")
        print(f"  News analyzed: {result.get('news_analyzed', 0)}")
        print(f"  Stored: {result.get('stored', 0)} items")
        sys.exit(0)
    else:
        print(f"✗ Daily source check failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

