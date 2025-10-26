import sys
from pathlib import Path
import logging
import argparse
from collections import defaultdict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HolisticBaseMatcher:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        
    def analyze_base_name_matches(self):
        """
        Analyze base name matches between clan and register tables.
        Only considers clan records WITHOUT descriptions.
        """
        try:
            with db_manager.get_cursor() as cursor:
                logger.info("Analyzing base name matches...")
                
                # Get clan records WITHOUT descriptions, grouped by base_name
                cursor.execute('''
                    SELECT 
                        base_name,
                        COUNT(*) as clan_count,
                        STRING_AGG(DISTINCT name, ' | ') as clan_names,
                        STRING_AGG(DISTINCT suffix, ' | ') as clan_suffixes
                    FROM tartan_designs_clan 
                    WHERE description IS NULL OR description = ''
                    AND base_name IS NOT NULL
                    GROUP BY base_name
                    ORDER BY clan_count DESC, base_name
                ''')
                clan_groups = cursor.fetchall()
                
                logger.info(f"Found {len(clan_groups)} unique base names in clan table (without descriptions)")
                
                # Get register records grouped by base_name
                cursor.execute('''
                    SELECT 
                        base_name,
                        COUNT(*) as register_count,
                        STRING_AGG(DISTINCT tartan_name, ' | ') as register_names,
                        STRING_AGG(DISTINCT suffix, ' | ') as register_suffixes
                    FROM tartan_designs_register 
                    WHERE base_name IS NOT NULL
                    GROUP BY base_name
                    ORDER BY register_count DESC, base_name
                ''')
                register_groups = cursor.fetchall()
                
                logger.info(f"Found {len(register_groups)} unique base names in register table")
                
                # Create lookup dictionary for register base names
                register_lookup = {group['base_name']: group for group in register_groups}
                
                # Analyze matches
                matches = []
                no_matches = []
                
                for clan_group in clan_groups:
                    clan_base_name = clan_group['base_name']
                    
                    if clan_base_name in register_lookup:
                        register_group = register_lookup[clan_base_name]
                        matches.append({
                            'base_name': clan_base_name,
                            'clan_count': clan_group['clan_count'],
                            'register_count': register_group['register_count'],
                            'clan_names': clan_group['clan_names'],
                            'clan_suffixes': clan_group['clan_suffixes'],
                            'register_names': register_group['register_names'],
                            'register_suffixes': register_group['register_suffixes']
                        })
                    else:
                        no_matches.append(clan_group)
                
                # Report results
                logger.info(f"\n{'='*80}")
                logger.info(f"HOLISTIC BASE NAME MATCHING ANALYSIS")
                logger.info(f"{'='*80}")
                logger.info(f"Clan records without descriptions: {sum(g['clan_count'] for g in clan_groups)}")
                logger.info(f"Unique clan base names (no descriptions): {len(clan_groups)}")
                logger.info(f"Unique register base names: {len(register_groups)}")
                logger.info(f"Exact base name matches: {len(matches)}")
                logger.info(f"Clan base names with no register matches: {len(no_matches)}")
                
                # Show top matches
                logger.info(f"\n{'='*80}")
                logger.info(f"TOP 20 BASE NAME MATCHES")
                logger.info(f"{'='*80}")
                
                sorted_matches = sorted(matches, key=lambda x: x['clan_count'] + x['register_count'], reverse=True)
                for i, match in enumerate(sorted_matches[:20]):
                    logger.info(f"{i+1:2d}. {match['base_name']}")
                    logger.info(f"    Clan: {match['clan_count']} variants ({match['clan_suffixes']})")
                    logger.info(f"    Register: {match['register_count']} variants ({match['register_suffixes']})")
                    logger.info(f"    Clan names: {match['clan_names'][:100]}{'...' if len(match['clan_names']) > 100 else ''}")
                    logger.info(f"    Register names: {match['register_names'][:100]}{'...' if len(match['register_names']) > 100 else ''}")
                    logger.info("")
                
                # Show some examples of no matches
                logger.info(f"\n{'='*80}")
                logger.info(f"SAMPLE CLAN BASE NAMES WITH NO REGISTER MATCHES")
                logger.info(f"{'='*80}")
                
                sorted_no_matches = sorted(no_matches, key=lambda x: x['clan_count'], reverse=True)
                for i, no_match in enumerate(sorted_no_matches[:10]):
                    logger.info(f"{i+1:2d}. {no_match['base_name']} ({no_match['clan_count']} variants)")
                    logger.info(f"    Names: {no_match['clan_names'][:100]}{'...' if len(no_match['clan_names']) > 100 else ''}")
                    logger.info(f"    Suffixes: {no_match['clan_suffixes']}")
                    logger.info("")
                
                # Summary statistics
                total_clan_variants_with_matches = sum(match['clan_count'] for match in matches)
                total_clan_variants_no_matches = sum(no_match['clan_count'] for no_match in no_matches)
                
                logger.info(f"\n{'='*80}")
                logger.info(f"SUMMARY STATISTICS")
                logger.info(f"{'='*80}")
                logger.info(f"Clan variants with register matches: {total_clan_variants_with_matches}")
                logger.info(f"Clan variants with no register matches: {total_clan_variants_no_matches}")
                logger.info(f"Total clan variants (no descriptions): {total_clan_variants_with_matches + total_clan_variants_no_matches}")
                logger.info(f"Match rate: {total_clan_variants_with_matches / (total_clan_variants_with_matches + total_clan_variants_no_matches) * 100:.1f}%")
                
                return matches, no_matches
                
        except Exception as e:
            logger.error(f"Error analyzing base name matches: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Analyze holistic base name matches between clan and register tables')
    parser.add_argument('--live', action='store_true', help='Run in live mode (currently only analysis)')
    parser.add_argument('--analyze', action='store_true', help='Analyze base name matches')
    
    args = parser.parse_args()
    
    if not args.analyze and not args.live:
        args.analyze = True  # Default to analysis mode
    
    matcher = HolisticBaseMatcher(dry_run=not args.live)
    
    if args.analyze or args.live:
        logger.info("Starting holistic base name matching analysis...")
        matches, no_matches = matcher.analyze_base_name_matches()
        logger.info("✅ Analysis complete!")
    else:
        logger.info("Use --analyze to analyze base name matches")

if __name__ == "__main__":
    main()
