#!/usr/bin/env python3
"""
Tartan Register to Clan Table Matching Script
Matches records between tartan_designs_register and tartan_designs_clan tables
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
        logging.FileHandler('tartan_matching.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TartanMatcher:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.matched_count = 0
        self.created_count = 0
        self.error_count = 0
        self.stats = {
            'sta_ref_matches': 0,
            'stwr_ref_matches': 0,
            'new_records_created': 0,
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
    
    def update_clan_register_id(self, clan_id, register_id):
        """Update clan record with register_id"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update clan record {clan_id} with register_id {register_id}")
            return True
        
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE tartan_designs_clan 
                    SET register_id = %s 
                    WHERE id = %s
                """, (register_id, clan_id))
                logger.info(f"Updated clan record {clan_id} with register_id {register_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating clan record {clan_id}: {e}")
            return False
    
    def create_clan_record(self, register_record):
        """Create new clan record from register record"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create new clan record:")
            logger.info(f"  Name: {register_record['tartan_name']}")
            logger.info(f"  Register ID: {register_record['id']}")
            logger.info(f"  Reference: {register_record['reference']}")
            return True
        
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tartan_designs_clan 
                    (name, legacy_id, register_id, type, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    register_record['tartan_name'],
                    register_record['reference'],  # Use reference as legacy_id
                    register_record['id'],         # Use register id as register_id
                    'Tartan'  # Default type
                ))
                logger.info(f"Created new clan record for '{register_record['tartan_name']}'")
                return True
        except Exception as e:
            logger.error(f"Error creating clan record for '{register_record['tartan_name']}': {e}")
            return False
    
    def process_register_record(self, register_record):
        """Process a single register record"""
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
                if self.update_clan_register_id(clan_record['id'], register_id):
                    self.stats['sta_ref_matches'] += 1
                    self.matched_count += 1
                else:
                    self.error_count += 1
                return
        
        # Step 2: Try to match by stwr_ref -> legacy_id
        if stwr_ref and stwr_ref.lower() not in ['none', 'null', '']:
            clan_record = self.get_clan_record_by_legacy_id(stwr_ref)
            if clan_record:
                logger.info(f"  ✓ Matched by STWR ref {stwr_ref} to clan record {clan_record['id']}")
                if self.update_clan_register_id(clan_record['id'], register_id):
                    self.stats['stwr_ref_matches'] += 1
                    self.matched_count += 1
                else:
                    self.error_count += 1
                return
        
        # Step 3: Try to match by reference -> legacy_id (fallback)
        if reference:
            clan_record = self.get_clan_record_by_legacy_id(reference)
            if clan_record:
                logger.info(f"  ✓ Matched by reference {reference} to clan record {clan_record['id']}")
                if self.update_clan_register_id(clan_record['id'], register_id):
                    self.matched_count += 1
                else:
                    self.error_count += 1
                return
        
        # Step 4: No match found - create new clan record
        logger.info(f"  → No match found, creating new clan record")
        if self.create_clan_record(register_record):
            self.stats['new_records_created'] += 1
            self.created_count += 1
        else:
            self.error_count += 1
    
    def run_matching(self):
        """Run the complete matching process"""
        logger.info("Starting tartan register to clan table matching...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        
        # Get all register records
        register_records = self.get_register_records()
        if not register_records:
            logger.error("No register records found")
            return
        
        logger.info(f"Found {len(register_records)} register records to process")
        
        # Process each register record
        for record in register_records:
            self.process_register_record(record)
            
            # Progress update every 100 records
            if self.stats['register_records_processed'] % 100 == 0:
                logger.info(f"Progress: {self.stats['register_records_processed']} processed")
        
        # Final statistics
        logger.info("Matching complete!")
        logger.info(f"Statistics:")
        logger.info(f"  Register records processed: {self.stats['register_records_processed']}")
        logger.info(f"  STA ref matches: {self.stats['sta_ref_matches']}")
        logger.info(f"  STWR ref matches: {self.stats['stwr_ref_matches']}")
        logger.info(f"  New records created: {self.stats['new_records_created']}")
        logger.info(f"  Total matched: {self.matched_count}")
        logger.info(f"  Total created: {self.created_count}")
        logger.info(f"  Errors: {self.error_count}")
    
    def verify_results(self):
        """Verify the matching results"""
        try:
            with db_manager.get_cursor() as cursor:
                # Count clan records with register_id
                cursor.execute("SELECT COUNT(*) FROM tartan_designs_clan WHERE register_id IS NOT NULL")
                clan_with_register = cursor.fetchone()['count']
                
                # Count total register records
                cursor.execute("SELECT COUNT(*) FROM tartan_designs_register")
                total_register = cursor.fetchone()['count']
                
                # Count clan records
                cursor.execute("SELECT COUNT(*) FROM tartan_designs_clan")
                total_clan = cursor.fetchone()['count']
                
                logger.info("Verification results:")
                logger.info(f"  Clan records with register_id: {clan_with_register}")
                logger.info(f"  Total register records: {total_register}")
                logger.info(f"  Total clan records: {total_clan}")
                
                # Show some sample matches
                cursor.execute("""
                    SELECT c.id, c.name, c.register_id, r.tartan_name, r.reference
                    FROM tartan_designs_clan c
                    JOIN tartan_designs_register r ON c.register_id = r.id
                    ORDER BY c.id
                    LIMIT 5
                """)
                
                matches = cursor.fetchall()
                logger.info("Sample matches:")
                for match in matches:
                    logger.info(f"  Clan ID {match['id']}: '{match['name']}' <-> Register ID {match['register_id']}: '{match['tartan_name']}'")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Match tartan register records to clan table')
    parser.add_argument('--live', action='store_true', help='Run in live mode (default is dry run)')
    parser.add_argument('--verify', action='store_true', help='Verify results after matching')
    
    args = parser.parse_args()
    
    # Run matching
    matcher = TartanMatcher(dry_run=not args.live)
    matcher.run_matching()
    
    # Verify results if requested
    if args.verify:
        matcher.verify_results()

if __name__ == "__main__":
    main()
