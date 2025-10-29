import sys
from pathlib import Path
import logging
import re
import csv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SequentialMatchFinder:
    def __init__(self):
        pass
        
    def extract_base_name_and_suffix(self, name):
        """Extract base name and suffix from clan tartan names."""
        if not name:
            return None, 0
            
        # Pattern to match #number suffix
        pattern = r'^(.+?)\s*#(\d+)$'
        match = re.match(pattern, name.strip())
        
        if match:
            base_name = match.group(1).strip()
            suffix_num = int(match.group(2))
            return base_name, suffix_num
        else:
            # No suffix, treat as base name with suffix 0
            return name.strip(), 0
    
    def extract_base_name_and_date(self, name):
        """Extract base name and date from register tartan names."""
        if not name:
            return None, None
            
        # Pattern to match year in parentheses (1900-2099)
        pattern = r'^(.+?)\s*\((\d{4})\)$'
        match = re.match(pattern, name.strip())
        
        if match:
            base_name = match.group(1).strip()
            year = int(match.group(2))
            if 1900 <= year <= 2099:  # Reasonable year range
                return base_name, year
        
        # Pattern to match year suffix without parentheses (1900-2099)
        pattern = r'^(.+?)\s+(\d{4})$'
        match = re.match(pattern, name.strip())
        
        if match:
            base_name = match.group(1).strip()
            year = int(match.group(2))
            if 1900 <= year <= 2099:  # Reasonable year range
                return base_name, year
        
        # No year suffix, treat as base name
        return name.strip(), None
    
    def find_all_sequential_matches(self):
        """Find all potential sequential matches between clan and register tables."""
        try:
            with db_manager.get_cursor() as cursor:
                # Get all clan records without descriptions
                cursor.execute('''
                    SELECT id, name, legacy_id, register_id, description
                    FROM tartan_designs_clan 
                    WHERE description IS NULL OR description = ''
                    ORDER BY name
                ''')
                clan_records = cursor.fetchall()
                
                # Get all register records
                cursor.execute('''
                    SELECT id, tartan_name, category, restrictions, designer, 
                           registration_notes, tartan_date, registration_date
                    FROM tartan_designs_register 
                    ORDER BY tartan_name
                ''')
                register_records = cursor.fetchall()
                
                # Group clan records by base name
                clan_groups = {}
                for record in clan_records:
                    base_name, suffix = self.extract_base_name_and_suffix(record['name'])
                    if base_name:
                        if base_name not in clan_groups:
                            clan_groups[base_name] = []
                        clan_groups[base_name].append((record, suffix))
                
                # Group register records by base name
                register_groups = {}
                for record in register_records:
                    base_name, year = self.extract_base_name_and_date(record['tartan_name'])
                    if base_name:
                        if base_name not in register_groups:
                            register_groups[base_name] = []
                        register_groups[base_name].append((record, year))
                
                # Find matches
                matches = []
                for base_name in clan_groups:
                    if base_name in register_groups:
                        clan_list = clan_groups[base_name]
                        register_list = register_groups[base_name]
                        
                        # Sort by suffix/year
                        clan_list.sort(key=lambda x: x[1])  # Sort by suffix number
                        register_list.sort(key=lambda x: x[1] if x[1] else 0)  # Sort by year
                        
                        # Check if counts match and we have multiple variants
                        if len(clan_list) == len(register_list) and len(clan_list) > 1:
                            # Create sequential matches
                            for i, ((clan_record, clan_suffix), (register_record, register_year)) in enumerate(zip(clan_list, register_list)):
                                matches.append({
                                    'base_name': base_name,
                                    'clan_id': clan_record['id'],
                                    'clan_name': clan_record['name'],
                                    'clan_suffix': clan_suffix,
                                    'register_id': register_record['id'],
                                    'register_name': register_record['tartan_name'],
                                    'register_year': register_year,
                                    'category': register_record['category'],
                                    'designer': register_record['designer'],
                                    'restrictions': register_record['restrictions'],
                                    'registration_notes': register_record['registration_notes'],
                                    'match_index': i,
                                    'total_variants': len(clan_list)
                                })
                
                logger.info(f"Found {len(matches)} potential sequential matches")
                return matches
                
        except Exception as e:
            logger.error(f"Error finding sequential matches: {e}")
            return []
    
    def export_matches_to_csv(self, matches, output_file):
        """Export matches to CSV file"""
        if not matches:
            logger.info("No matches to export")
            return
        
        fieldnames = [
            'base_name', 'total_variants', 'match_index',
            'clan_id', 'clan_name', 'clan_suffix',
            'register_id', 'register_name', 'register_year',
            'category', 'designer', 'restrictions', 'registration_notes'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for match in matches:
                # Truncate long fields for readability
                row = match.copy()
                if row['registration_notes'] and len(row['registration_notes']) > 200:
                    row['registration_notes'] = row['registration_notes'][:200] + "..."
                if row['restrictions'] and len(row['restrictions']) > 100:
                    row['restrictions'] = row['restrictions'][:100] + "..."
                
                writer.writerow(row)
        
        logger.info(f"Exported {len(matches)} matches to {output_file}")
    
    def analyze_match_patterns(self, matches):
        """Analyze and summarize the match patterns"""
        if not matches:
            logger.info("No matches to analyze")
            return
        
        # Group by base name
        base_name_groups = {}
        for match in matches:
            base_name = match['base_name']
            if base_name not in base_name_groups:
                base_name_groups[base_name] = []
            base_name_groups[base_name].append(match)
        
        logger.info(f"\nSEQUENTIAL MATCH ANALYSIS:")
        logger.info(f"Total base names with sequential matches: {len(base_name_groups)}")
        logger.info(f"Total individual matches: {len(matches)}")
        
        # Show summary by base name
        logger.info(f"\nSUMMARY BY BASE NAME:")
        for base_name, group_matches in sorted(base_name_groups.items()):
            variants = group_matches[0]['total_variants']
            logger.info(f"  {base_name}: {variants} variants")
            
            # Show the sequence
            for match in sorted(group_matches, key=lambda x: x['match_index']):
                logger.info(f"    {match['match_index']}: '{match['clan_name']}' -> '{match['register_name']}'")

if __name__ == "__main__":
    finder = SequentialMatchFinder()
    
    # Find all matches
    matches = finder.find_all_sequential_matches()
    
    # Analyze patterns
    finder.analyze_match_patterns(matches)
    
    # Export to CSV
    if matches:
        output_dir = Path(__file__).parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "sequential_matches.csv"
        finder.export_matches_to_csv(matches, output_file)
        
        logger.info(f"\nDetailed match list exported to: {output_file}")
        logger.info("Review this file to verify the matching logic before running live generation.")

