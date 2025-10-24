#!/usr/bin/env python3
"""
Test script for tartan table matching
Tests the matching logic with sample data
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from match_tartan_tables import TartanMatcher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_matching():
    """Test the matching logic"""
    logger.info("Testing tartan table matching logic...")
    
    # Run in dry-run mode
    matcher = TartanMatcher(dry_run=True)
    
    # Get sample data to test
    register_records = matcher.get_register_records()
    logger.info(f"Found {len(register_records)} register records")
    
    if register_records:
        # Test with first 5 records
        test_records = register_records[:5]
        logger.info(f"Testing with first {len(test_records)} records:")
        
        for record in test_records:
            logger.info(f"  Register ID {record['id']}: '{record['tartan_name']}'")
            logger.info(f"    STA ref: {record['sta_ref']}")
            logger.info(f"    STWR ref: {record['stwr_ref']}")
            logger.info(f"    Reference: {record['reference']}")
        
        # Process test records
        for record in test_records:
            matcher.process_register_record(record)
        
        logger.info("Test complete!")
        logger.info(f"Test statistics:")
        logger.info(f"  STA ref matches: {matcher.stats['sta_ref_matches']}")
        logger.info(f"  STWR ref matches: {matcher.stats['stwr_ref_matches']}")
        logger.info(f"  New records created: {matcher.stats['new_records_created']}")
    else:
        logger.error("No register records found for testing")

if __name__ == "__main__":
    test_matching()
