#!/usr/bin/env python3
"""
Test script for tartan spider - processes just a few tartans to verify functionality
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the spider class directly
sys.path.insert(0, str(Path(__file__).parent))
from spider_tartan_register import TartanSpider
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_spider():
    """Test the spider with a small sample"""
    spider = TartanSpider()
    
    # Test with just letter A
    logger.info("Testing spider with letter A...")
    tartan_links = spider.spider_az_pages(['A'])
    
    if tartan_links:
        logger.info(f"Found {len(tartan_links)} tartans starting with A")
        
        # Test with first 3 tartans only
        test_links = tartan_links[:3]
        logger.info(f"Testing with first {len(test_links)} tartans:")
        
        for url, name in test_links:
            logger.info(f"  - {name}: {url}")
        
        # Process the test tartans
        spider.spider_tartan_details(test_links)
        
        logger.info(f"Test complete! Processed: {spider.processed_count}, Errors: {spider.error_count}")
    else:
        logger.error("No tartan links found for letter A")

if __name__ == "__main__":
    test_spider()
