import sys
from pathlib import Path
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_matching_patterns():
    """Analyze how records were matched to identify problematic STWR-only matches"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute('''
                SELECT 
                    c.id as clan_id,
                    c.name as clan_name,
                    c.legacy_id,
                    c.register_id,
                    c.description,
                    r.tartan_name as register_name,
                    r.sta_ref,
                    r.stwr_ref,
                    r.reference
                FROM tartan_designs_clan c
                JOIN tartan_designs_register r ON c.register_id = r.id
                WHERE c.register_id IS NOT NULL
                AND c.description IS NOT NULL
                AND c.description != ''
                ORDER BY c.id
            ''')
            
            records = cursor.fetchall()
            
            # Categorize matches
            sta_only_matches = []
            stwr_only_matches = []
            both_matches = []
            reference_matches = []
            
            for record in records:
                sta_ref = record['sta_ref']
                stwr_ref = record['stwr_ref']
                reference = record['reference']
                legacy_id = record['legacy_id']
                
                # Determine how this match was made
                sta_match = (sta_ref and sta_ref != 'none' and str(sta_ref) == str(legacy_id))
                stwr_match = (stwr_ref and stwr_ref != 'none' and str(stwr_ref) == str(legacy_id))
                ref_match = (reference and str(reference) == str(legacy_id))
                
                if sta_match and stwr_match:
                    both_matches.append(record)
                elif sta_match and not stwr_match:
                    sta_only_matches.append(record)
                elif stwr_match and not sta_match:
                    stwr_only_matches.append(record)
                elif ref_match:
                    reference_matches.append(record)
            
            logger.info(f"MATCHING ANALYSIS:")
            logger.info(f"Total records with descriptions: {len(records)}")
            logger.info(f"STA-only matches: {len(sta_only_matches)}")
            logger.info(f"STWR-only matches: {len(stwr_only_matches)}")
            logger.info(f"Both STA and STWR matches: {len(both_matches)}")
            logger.info(f"Reference matches: {len(reference_matches)}")
            
            return {
                'sta_only': sta_only_matches,
                'stwr_only': stwr_only_matches,
                'both': both_matches,
                'reference': reference_matches
            }
            
    except Exception as e:
        logger.error(f"Error analyzing matching patterns: {e}")
        return None

def check_name_similarity(clan_name, register_name):
    """Check if clan and register names are similar enough to be valid matches"""
    if not clan_name or not register_name:
        return False
    
    clan_lower = clan_name.lower()
    register_lower = register_name.lower()
    
    # Exact match
    if clan_lower == register_lower:
        return True
    
    # One contains the other
    if clan_lower in register_lower or register_lower in clan_lower:
        return True
    
    # Similar after removing common variations
    clan_clean = clan_lower.replace('[default]', '').replace('(default)', '').replace('#', '').strip()
    register_clean = register_lower.replace('[default]', '').replace('(default)', '').replace('#', '').strip()
    
    if clan_clean == register_clean:
        return True
    
    # Check if they're variations of the same name
    if abs(len(clan_clean) - len(register_clean)) <= 3:
        return True
    
    return False

def clean_stwr_only_descriptions(dry_run=True):
    """Remove descriptions from records that were matched only by STWR reference"""
    try:
        patterns = analyze_matching_patterns()
        if not patterns:
            return
        
        stwr_only_records = patterns['stwr_only']
        logger.info(f"Found {len(stwr_only_records)} STWR-only matches")
        
        # Check name similarity for STWR matches
        problematic_stwr = []
        valid_stwr = []
        
        for record in stwr_only_records:
            if check_name_similarity(record['clan_name'], record['register_name']):
                valid_stwr.append(record)
            else:
                problematic_stwr.append(record)
        
        logger.info(f"STWR-only matches with similar names: {len(valid_stwr)}")
        logger.info(f"STWR-only matches with different names: {len(problematic_stwr)}")
        
        if dry_run:
            logger.info("DRY RUN - Would delete descriptions for these problematic STWR matches:")
            for i, record in enumerate(problematic_stwr[:10]):
                logger.info(f"{i+1}. CLAN: '{record['clan_name']}' -> REGISTER: '{record['register_name']}'")
            if len(problematic_stwr) > 10:
                logger.info(f"... and {len(problematic_stwr) - 10} more")
        else:
            # Actually delete the descriptions
            clan_ids = [record['clan_id'] for record in problematic_stwr]
            if clan_ids:
                with db_manager.get_cursor() as cursor:
                    cursor.execute('''
                        UPDATE tartan_designs_clan 
                        SET description = NULL 
                        WHERE id = ANY(%s)
                    ''', (clan_ids,))
                
                logger.info(f"Deleted descriptions for {len(clan_ids)} problematic STWR-only matches")
        
        return problematic_stwr
        
    except Exception as e:
        logger.error(f"Error cleaning STWR-only descriptions: {e}")
        return []

def check_sta_matches(dry_run=True):
    """Check STA matches for potential issues"""
    try:
        patterns = analyze_matching_patterns()
        if not patterns:
            return
        
        sta_records = patterns['sta_only'] + patterns['both']
        logger.info(f"Checking {len(sta_records)} STA matches for name similarity")
        
        problematic_sta = []
        valid_sta = []
        
        for record in sta_records:
            if check_name_similarity(record['clan_name'], record['register_name']):
                valid_sta.append(record)
            else:
                problematic_sta.append(record)
        
        logger.info(f"STA matches with similar names: {len(valid_sta)}")
        logger.info(f"STA matches with different names: {len(problematic_sta)}")
        
        if problematic_sta:
            logger.info("Problematic STA matches found:")
            for i, record in enumerate(problematic_sta[:10]):
                logger.info(f"{i+1}. CLAN: '{record['clan_name']}' -> REGISTER: '{record['register_name']}'")
            if len(problematic_sta) > 10:
                logger.info(f"... and {len(problematic_sta) - 10} more")
        
        return problematic_sta
        
    except Exception as e:
        logger.error(f"Error checking STA matches: {e}")
        return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up problematic tartan descriptions")
    parser.add_argument('--live', action='store_true', help='Actually delete descriptions (default is dry run)')
    parser.add_argument('--check-sta', action='store_true', help='Also check STA matches for issues')
    args = parser.parse_args()
    
    if not args.live:
        logger.info("Running in DRY RUN mode - no descriptions will be deleted")
    else:
        logger.info("Running in LIVE mode - descriptions will be deleted")
    
    # Clean STWR-only matches
    problematic_stwr = clean_stwr_only_descriptions(dry_run=not args.live)
    
    # Check STA matches if requested
    if args.check_sta:
        problematic_sta = check_sta_matches(dry_run=not args.live)
    
    logger.info("Analysis complete")
