#!/usr/bin/env python3
"""
Fix Bidirectional Links Script
Cleans up inconsistencies in bidirectional linking between clan and register tables
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
        logging.FileHandler('fix_bidirectional_links.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BidirectionalLinkFixer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.fixed_count = 0
        self.error_count = 0
    
    def find_inconsistencies(self):
        """Find all inconsistencies in bidirectional linking"""
        try:
            with db_manager.get_cursor() as cursor:
                # Find register records with clan_id but mismatched clan.register_id
                cursor.execute('''
                    SELECT r.id as register_id, r.tartan_name, r.clan_id, c.register_id as clan_register_id
                    FROM tartan_designs_register r
                    LEFT JOIN tartan_designs_clan c ON c.id = r.clan_id
                    WHERE r.clan_id IS NOT NULL 
                    AND (c.register_id IS NULL OR c.register_id != r.id)
                    ORDER BY r.id
                ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding inconsistencies: {e}")
            return []
    
    def fix_inconsistency(self, register_id, tartan_name, clan_id, clan_register_id):
        """Fix a single inconsistency"""
        logger.info(f"Fixing inconsistency:")
        logger.info(f"  Register ID {register_id}: '{tartan_name}'")
        logger.info(f"  Register.clan_id: {clan_id}")
        logger.info(f"  Clan.register_id: {clan_register_id}")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would clear register.clan_id for register {register_id}")
            return True
        
        try:
            with db_manager.get_cursor() as cursor:
                # Clear the incorrect clan_id from the register record
                cursor.execute("""
                    UPDATE tartan_designs_register 
                    SET clan_id = NULL 
                    WHERE id = %s
                """, (register_id,))
                
                logger.info(f"Cleared clan_id from register record {register_id}")
                return True
        except Exception as e:
            logger.error(f"Error fixing inconsistency for register {register_id}: {e}")
            return False
    
    def run_fix(self):
        """Run the fix process"""
        logger.info("Starting bidirectional link fix...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        
        # Find inconsistencies
        inconsistencies = self.find_inconsistencies()
        if not inconsistencies:
            logger.info("No inconsistencies found!")
            return
        
        logger.info(f"Found {len(inconsistencies)} inconsistencies to fix")
        
        # Fix each inconsistency
        for record in inconsistencies:
            if self.fix_inconsistency(
                record['register_id'], 
                record['tartan_name'], 
                record['clan_id'], 
                record['clan_register_id']
            ):
                self.fixed_count += 1
            else:
                self.error_count += 1
        
        # Final statistics
        logger.info("Bidirectional link fix complete!")
        logger.info(f"Statistics:")
        logger.info(f"  Inconsistencies fixed: {self.fixed_count}")
        logger.info(f"  Errors: {self.error_count}")
    
    def verify_fix(self):
        """Verify the fix results"""
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
                logger.info(f"  Difference: {register_with_clan - clan_with_register}")
                
                # Check for remaining inconsistencies
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM tartan_designs_register r
                    WHERE r.clan_id IS NOT NULL 
                    AND NOT EXISTS (
                        SELECT 1 FROM tartan_designs_clan c 
                        WHERE c.id = r.clan_id AND c.register_id = r.id
                    )
                ''')
                remaining_inconsistencies = cursor.fetchone()['count']
                logger.info(f"  Remaining inconsistencies: {remaining_inconsistencies}")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix bidirectional linking inconsistencies')
    parser.add_argument('--live', action='store_true', help='Run in live mode (default is dry run)')
    parser.add_argument('--verify', action='store_true', help='Verify results after fixing')
    
    args = parser.parse_args()
    
    # Run the fix
    fixer = BidirectionalLinkFixer(dry_run=not args.live)
    fixer.run_fix()
    
    # Verify results if requested
    if args.verify:
        fixer.verify_fix()

if __name__ == "__main__":
    main()

