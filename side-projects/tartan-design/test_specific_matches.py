#!/usr/bin/env python3
"""
Test script for tartan table matching with specific records that should match
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

def test_specific_matches():
    """Test the matching logic with specific records that should match"""
    logger.info("Testing tartan table matching with specific records...")
    
    # Run in dry-run mode
    matcher = TartanMatcher(dry_run=True)
    
    # Test with specific register IDs that should have matches
    test_ids = [14, 19, 35, 39, 54, 97, 114, 115]  # These should have STA/STWR matches
    
    logger.info(f"Testing with register IDs: {test_ids}")
    
    # Get the specific records
    register_records = matcher.get_register_records()
    test_records = [r for r in register_records if r['id'] in test_ids]
    
    logger.info(f"Found {len(test_records)} test records:")
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
    logger.info(f"  Total matched: {matcher.matched_count}")
    logger.info(f"  Total created: {matcher.created_count}")
    logger.info(f"  Errors: {matcher.error_count}")

if __name__ == "__main__":
    test_specific_matches()

