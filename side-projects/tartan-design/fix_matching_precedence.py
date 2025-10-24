#!/usr/bin/env python3
"""
Fix Matching Precedence Script
Ensures that reference-based matching (STA ref, STWR ref, reference) takes precedence over exact name matching
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
        logging.FileHandler('fix_matching_precedence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MatchingPrecedenceFixer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.fixed_count = 0
        self.error_count = 0
    
    def find_precedence_violations(self):
        """Find clan records that should have been matched by reference-based matching"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute('''
                    SELECT c.id, c.name, c.register_id, c.legacy_id, r.tartan_name, r.sta_ref, r.stwr_ref, r.reference
                    FROM tartan_designs_clan c
                    JOIN tartan_designs_register r ON c.register_id = r.id
                    WHERE c.register_id IS NOT NULL
                    AND (
                        (r.sta_ref IS NOT NULL AND r.sta_ref != '' AND r.sta_ref != 'none' AND r.sta_ref != 'null' AND c.legacy_id::text = r.sta_ref)
                        OR (r.stwr_ref IS NOT NULL AND r.stwr_ref != '' AND r.stwr_ref != 'none' AND r.stwr_ref != 'null' AND c.legacy_id::text = r.stwr_ref)
                        OR (r.reference IS NOT NULL AND r.reference != '' AND r.reference != 'none' AND r.reference != 'null' AND c.legacy_id::text = r.reference)
                    )
                    ORDER BY c.id
                ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding precedence violations: {e}")
            return []
    
    def find_correct_register_match(self, clan_record):
        """Find the correct register record that should be matched based on reference"""
        try:
            with db_manager.get_cursor() as cursor:
                legacy_id = clan_record['legacy_id']
                
                # Try STA ref first
                cursor.execute('''
                    SELECT id, tartan_name, sta_ref, stwr_ref, reference
                    FROM tartan_designs_register 
                    WHERE sta_ref IS NOT NULL 
                    AND sta_ref != '' 
                    AND sta_ref != 'none' 
                    AND sta_ref != 'null'
                    AND sta_ref = %s
                    AND clan_id IS NULL
                ''', (str(legacy_id),))
                sta_match = cursor.fetchone()
                if sta_match:
                    return sta_match, 'STA ref'
                
                # Try STWR ref
                cursor.execute('''
                    SELECT id, tartan_name, sta_ref, stwr_ref, reference
                    FROM tartan_designs_register 
                    WHERE stwr_ref IS NOT NULL 
                    AND stwr_ref != '' 
                    AND stwr_ref != 'none' 
                    AND stwr_ref != 'null'
                    AND stwr_ref = %s
                    AND clan_id IS NULL
                ''', (str(legacy_id),))
                stwr_match = cursor.fetchone()
                if stwr_match:
                    return stwr_match, 'STWR ref'
                
                # Try reference
                cursor.execute('''
                    SELECT id, tartan_name, sta_ref, stwr_ref, reference
                    FROM tartan_designs_register 
                    WHERE reference IS NOT NULL 
                    AND reference != '' 
                    AND reference != 'none' 
                    AND reference != 'null'
                    AND reference = %s
                    AND clan_id IS NULL
                ''', (str(legacy_id),))
                ref_match = cursor.fetchone()
                if ref_match:
                    return ref_match, 'Reference'
                
                return None, None
        except Exception as e:
            logger.error(f"Error finding correct register match for clan {clan_record['id']}: {e}")
            return None, None
    
    def fix_precedence_violation(self, clan_record, correct_register, match_type):
        """Fix a single precedence violation"""
        clan_id = clan_record['id']
        current_register_id = clan_record['register_id']
        correct_register_id = correct_register['id']
        
        logger.info(f"Fixing precedence violation:")
        logger.info(f"  Clan ID {clan_id}: '{clan_record['name']}'")
        logger.info(f"  Current match: Register ID {current_register_id}: '{clan_record['tartan_name']}' (exact name)")
        logger.info(f"  Correct match: Register ID {correct_register_id}: '{correct_register['tartan_name']}' ({match_type})")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update:")
            logger.info(f"  Clan {clan_id}: register_id {current_register_id} -> {correct_register_id}")
            logger.info(f"  Register {current_register_id}: clan_id {clan_id} -> NULL")
            logger.info(f"  Register {correct_register_id}: clan_id NULL -> {clan_id}")
            return True
        
        try:
            with db_manager.get_cursor() as cursor:
                # Update clan record to point to correct register
                cursor.execute("""
                    UPDATE tartan_designs_clan 
                    SET register_id = %s 
                    WHERE id = %s
                """, (correct_register_id, clan_id))
                
                # Clear clan_id from current register record
                cursor.execute("""
                    UPDATE tartan_designs_register 
                    SET clan_id = NULL 
                    WHERE id = %s
                """, (current_register_id,))
                
                # Set clan_id on correct register record
                cursor.execute("""
                    UPDATE tartan_designs_register 
                    SET clan_id = %s 
                    WHERE id = %s
                """, (clan_id, correct_register_id))
                
                logger.info(f"Updated precedence: Clan {clan_id} now matched to Register {correct_register_id} ({match_type})")
                return True
        except Exception as e:
            logger.error(f"Error fixing precedence violation for clan {clan_id}: {e}")
            return False
    
    def run_fix(self):
        """Run the precedence fix process"""
        logger.info("Starting matching precedence fix...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        
        # Find precedence violations
        violations = self.find_precedence_violations()
        if not violations:
            logger.info("No precedence violations found!")
            return
        
        logger.info(f"Found {len(violations)} precedence violations to fix")
        
        # Fix each violation
        for clan_record in violations:
            correct_register, match_type = self.find_correct_register_match(clan_record)
            
            if correct_register:
                if self.fix_precedence_violation(clan_record, correct_register, match_type):
                    self.fixed_count += 1
                else:
                    self.error_count += 1
            else:
                logger.warning(f"No correct register match found for clan {clan_record['id']}")
                self.error_count += 1
        
        # Final statistics
        logger.info("Matching precedence fix complete!")
        logger.info(f"Statistics:")
        logger.info(f"  Precedence violations fixed: {self.fixed_count}")
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
                
                # Check for remaining precedence violations
                violations = self.find_precedence_violations()
                logger.info(f"  Remaining precedence violations: {len(violations)}")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix matching precedence to prioritize reference-based matching')
    parser.add_argument('--live', action='store_true', help='Run in live mode (default is dry run)')
    parser.add_argument('--verify', action='store_true', help='Verify results after fixing')
    
    args = parser.parse_args()
    
    # Run the fix
    fixer = MatchingPrecedenceFixer(dry_run=not args.live)
    fixer.run_fix()
    
    # Verify results if requested
    if args.verify:
        fixer.verify_fix()

if __name__ == "__main__":
    main()
