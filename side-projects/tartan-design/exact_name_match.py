#!/usr/bin/env python3
"""
Tartan Name Exact Match Script
Finds exact name matches between tartan_designs_clan and tartan_designs_register
for clan records that don't have a register_id yet, and creates bidirectional links
"""

import sys
from pathlib import Path
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tartan_name_exact_match.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TartanNameExactMatcher:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.matched_count = 0
        self.error_count = 0
        self.stats = {
            'exact_name_matches': 0,
            'clan_records_processed': 0
        }
    
    def get_unmatched_clan_records(self):
        """Get clan records that don't have a register_id yet"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, legacy_id, register_id
                    FROM tartan_designs_clan 
                    WHERE register_id IS NULL
                    ORDER BY id
                """)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching unmatched clan records: {e}")
            return []
    
    def find_exact_name_match(self, clan_name):
        """Find register record with exact name match"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, tartan_name, clan_id
                    FROM tartan_designs_register 
                    WHERE tartan_name = %s
                    AND clan_id IS NULL
                """, (clan_name,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error finding exact name match for '{clan_name}': {e}")
            return None
    
    def update_bidirectional_links(self, clan_id, register_id):
        """Update both tables with bidirectional links"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update bidirectional links:")
            logger.info(f"  Clan record {clan_id} -> register_id {register_id}")
            logger.info(f"  Register record {register_id} -> clan_id {clan_id}")
            return True
        
        try:
            with db_manager.get_cursor() as cursor:
                # Update clan table with register_id
                cursor.execute("""
                    UPDATE tartan_designs_clan 
                    SET register_id = %s 
                    WHERE id = %s
                """, (register_id, clan_id))
                
                # Update register table with clan_id
                cursor.execute("""
                    UPDATE tartan_designs_register 
                    SET clan_id = %s 
                    WHERE id = %s
                """, (clan_id, register_id))
                
                logger.info(f"Updated bidirectional links: Clan {clan_id} <-> Register {register_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating bidirectional links for clan {clan_id}, register {register_id}: {e}")
            return False
    
    def process_clan_record(self, clan_record):
        """Process a single clan record - only for exact name matches"""
        self.stats['clan_records_processed'] += 1
        
        clan_id = clan_record['id']
        clan_name = clan_record['name']
        
        logger.info(f"Processing clan record {clan_id}: '{clan_name}'")
        
        # Find exact name match in register table
        register_match = self.find_exact_name_match(clan_name)
        
        if register_match:
            register_id = register_match['id']
            register_name = register_match['tartan_name']
            
            logger.info(f"  ✓ Found exact name match: Register ID {register_id}: '{register_name}'")
            
            if self.update_bidirectional_links(clan_id, register_id):
                self.stats['exact_name_matches'] += 1
                self.matched_count += 1
            else:
                self.error_count += 1
            return True  # Found a match
        else:
            logger.info(f"  → No exact name match found")
            return False  # No match found
    
    def run_exact_name_matching(self):
        """Run the exact name matching process"""
        logger.info("Starting tartan name exact matching...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        logger.info("Processing ONLY clan records without register_id")
        
        # Get unmatched clan records
        clan_records = self.get_unmatched_clan_records()
        if not clan_records:
            logger.info("No unmatched clan records found")
            return
        
        logger.info(f"Found {len(clan_records)} unmatched clan records to process")
        
        # Process each clan record
        matches_found = 0
        for record in clan_records:
            if self.process_clan_record(record):
                matches_found += 1
            
            # Progress update every 100 records
            if self.stats['clan_records_processed'] % 100 == 0:
                logger.info(f"Progress: {self.stats['clan_records_processed']} processed, {matches_found} matches found")
        
        # Final statistics
        logger.info("Exact name matching complete!")
        logger.info(f"Statistics:")
        logger.info(f"  Clan records processed: {self.stats['clan_records_processed']}")
        logger.info(f"  Exact name matches: {self.stats['exact_name_matches']}")
        logger.info(f"  Total matches processed: {self.matched_count}")
        logger.info(f"  Errors: {self.error_count}")
    
    def verify_results(self):
        """Verify the exact name matching results"""
        try:
            with db_manager.get_cursor() as cursor:
                # Count clan records with register_id
                cursor.execute("SELECT COUNT(*) FROM tartan_designs_clan WHERE register_id IS NOT NULL")
                clan_with_register = cursor.fetchone()['count']
                
                # Count register records with clan_id
                cursor.execute("SELECT COUNT(*) FROM tartan_designs_register WHERE clan_id IS NOT NULL")
                register_with_clan = cursor.fetchone()['count']
                
                logger.info("Verification results:")
                logger.info(f"  Clan records with register_id: {clan_with_register}")
                logger.info(f"  Register records with clan_id: {register_with_clan}")
                
                # Show some sample exact name matches
                cursor.execute("""
                    SELECT c.id as clan_id, c.name as clan_name, c.register_id, 
                           r.id as register_id, r.tartan_name, r.clan_id
                    FROM tartan_designs_clan c
                    JOIN tartan_designs_register r ON c.register_id = r.id
                    WHERE c.register_id IS NOT NULL AND r.clan_id IS NOT NULL
                    AND c.name = r.tartan_name
                    ORDER BY c.id
                    LIMIT 5
                """)
                
                matches = cursor.fetchall()
                logger.info("Sample exact name matches:")
                for match in matches:
                    logger.info(f"  Clan ID {match['clan_id']}: '{match['clan_name']}' <-> Register ID {match['register_id']}: '{match['tartan_name']}'")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Find exact name matches between clan and register tables')
    parser.add_argument('--live', action='store_true', help='Run in live mode (default is dry run)')
    parser.add_argument('--verify', action='store_true', help='Verify results after matching')
    
    args = parser.parse_args()
    
    # Run exact name matching
    matcher = TartanNameExactMatcher(dry_run=not args.live)
    matcher.run_exact_name_matching()
    
    # Verify results if requested
    if args.verify:
        matcher.verify_results()

if __name__ == "__main__":
    main()

