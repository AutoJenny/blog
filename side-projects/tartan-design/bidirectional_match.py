#!/usr/bin/env python3
"""
Tartan Register to Clan Table Bidirectional Matching Script
Updates only matching records with bidirectional linking (register_id <-> clan_id)
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
        logging.FileHandler('tartan_bidirectional_matching.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TartanBidirectionalMatcher:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.matched_count = 0
        self.error_count = 0
        self.stats = {
            'sta_ref_matches': 0,
            'stwr_ref_matches': 0,
            'register_records_processed': 0
        }
    
    def get_register_records(self):
        """Get all records from tartan_designs_register"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, tartan_name, sta_ref, stwr_ref, reference, designer, category
                    FROM tartan_designs_register 
                    ORDER BY id
                """)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching register records: {e}")
            return []
    
    def get_clan_record_by_legacy_id(self, legacy_id):
        """Get clan record by legacy_id (handles both string and numeric legacy_ids)"""
        try:
            with db_manager.get_cursor() as cursor:
                # Try to convert to integer first, if that fails, use as string
                try:
                    legacy_id_int = int(legacy_id)
                    cursor.execute("""
                        SELECT id, name, legacy_id, register_id
                        FROM tartan_designs_clan 
                        WHERE legacy_id = %s
                    """, (legacy_id_int,))
                except (ValueError, TypeError):
                    # If conversion fails, try as string
                    cursor.execute("""
                        SELECT id, name, legacy_id, register_id
                        FROM tartan_designs_clan 
                        WHERE legacy_id::text = %s
                    """, (str(legacy_id),))
                
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching clan record by legacy_id {legacy_id}: {e}")
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
    
    def process_register_record(self, register_record):
        """Process a single register record - only for matches"""
        self.stats['register_records_processed'] += 1
        
        register_id = register_record['id']
        tartan_name = register_record['tartan_name']
        sta_ref = register_record['sta_ref']
        stwr_ref = register_record['stwr_ref']
        reference = register_record['reference']
        
        logger.info(f"Processing register record {register_id}: '{tartan_name}'")
        
        # Step 1: Try to match by sta_ref -> legacy_id
        if sta_ref and sta_ref.lower() not in ['none', 'null', '']:
            clan_record = self.get_clan_record_by_legacy_id(sta_ref)
            if clan_record:
                logger.info(f"  ✓ Matched by STA ref {sta_ref} to clan record {clan_record['id']}")
                if self.update_bidirectional_links(clan_record['id'], register_id):
                    self.stats['sta_ref_matches'] += 1
                    self.matched_count += 1
                else:
                    self.error_count += 1
                return True  # Found a match, stop processing
        
        # Step 2: Try to match by stwr_ref -> legacy_id
        if stwr_ref and stwr_ref.lower() not in ['none', 'null', '']:
            clan_record = self.get_clan_record_by_legacy_id(stwr_ref)
            if clan_record:
                logger.info(f"  ✓ Matched by STWR ref {stwr_ref} to clan record {clan_record['id']}")
                if self.update_bidirectional_links(clan_record['id'], register_id):
                    self.stats['stwr_ref_matches'] += 1
                    self.matched_count += 1
                else:
                    self.error_count += 1
                return True  # Found a match, stop processing
        
        # Step 3: Try to match by reference -> legacy_id (fallback)
        if reference:
            clan_record = self.get_clan_record_by_legacy_id(reference)
            if clan_record:
                logger.info(f"  ✓ Matched by reference {reference} to clan record {clan_record['id']}")
                if self.update_bidirectional_links(clan_record['id'], register_id):
                    self.matched_count += 1
                else:
                    self.error_count += 1
                return True  # Found a match, stop processing
        
        # No match found - skip this record
        logger.info(f"  → No match found, skipping record")
        return False
    
    def run_bidirectional_matching(self):
        """Run the bidirectional matching process - only for matching records"""
        logger.info("Starting tartan register to clan table bidirectional matching...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        logger.info("Processing ONLY matching records (not creating new ones)")
        
        # Get all register records
        register_records = self.get_register_records()
        if not register_records:
            logger.error("No register records found")
            return
        
        logger.info(f"Found {len(register_records)} register records to process")
        
        # Process each register record
        matches_found = 0
        for record in register_records:
            if self.process_register_record(record):
                matches_found += 1
            
            # Progress update every 100 records
            if self.stats['register_records_processed'] % 100 == 0:
                logger.info(f"Progress: {self.stats['register_records_processed']} processed, {matches_found} matches found")
        
        # Final statistics
        logger.info("Bidirectional matching complete!")
        logger.info(f"Statistics:")
        logger.info(f"  Register records processed: {self.stats['register_records_processed']}")
        logger.info(f"  STA ref matches: {self.stats['sta_ref_matches']}")
        logger.info(f"  STWR ref matches: {self.stats['stwr_ref_matches']}")
        logger.info(f"  Total matches processed: {self.matched_count}")
        logger.info(f"  Errors: {self.error_count}")
    
    def verify_results(self):
        """Verify the bidirectional matching results"""
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
                
                # Show some sample bidirectional matches
                cursor.execute("""
                    SELECT c.id as clan_id, c.name as clan_name, c.register_id, 
                           r.id as register_id, r.tartan_name, r.clan_id
                    FROM tartan_designs_clan c
                    JOIN tartan_designs_register r ON c.register_id = r.id
                    WHERE c.register_id IS NOT NULL AND r.clan_id IS NOT NULL
                    ORDER BY c.id
                    LIMIT 5
                """)
                
                matches = cursor.fetchall()
                logger.info("Sample bidirectional matches:")
                for match in matches:
                    logger.info(f"  Clan ID {match['clan_id']}: '{match['clan_name']}' <-> Register ID {match['register_id']}: '{match['tartan_name']}'")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bidirectional match tartan register records to clan table')
    parser.add_argument('--live', action='store_true', help='Run in live mode (default is dry run)')
    parser.add_argument('--verify', action='store_true', help='Verify results after matching')
    
    args = parser.parse_args()
    
    # Run bidirectional matching
    matcher = TartanBidirectionalMatcher(dry_run=not args.live)
    matcher.run_bidirectional_matching()
    
    # Verify results if requested
    if args.verify:
        matcher.verify_results()

if __name__ == "__main__":
    main()
