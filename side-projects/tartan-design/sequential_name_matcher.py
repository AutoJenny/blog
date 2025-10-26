import sys
from pathlib import Path
import logging
import re
import argparse
import time

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager
from blueprints.planning_llm import LLMService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SequentialNameMatcher:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.llm_service = LLMService()
        self.processed_count = 0
        self.matched_count = 0
        self.test_count = 0
        
    def extract_base_name_and_suffix(self, name):
        """
        Extract base name and suffix from clan tartan names.
        Examples:
        - "Aberdeen Football Club #2" -> ("Aberdeen Football Club", 2)
        - "Aberdeen Football Club" -> ("Aberdeen Football Club", 0)
        - "Anderson Arisaid #3" -> ("Anderson Arisaid", 3)
        """
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
        """
        Extract base name and date from register tartan names.
        Examples:
        - "Aberdeen Football Club (1995)" -> ("Aberdeen Football Club", 1995)
        - "Aberdeen Football Club" -> ("Aberdeen Football Club", None)
        - "Anderson Dress 2001" -> ("Anderson Dress", 2001)
        """
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
    
    def find_sequential_matches(self):
        """
        Find potential sequential matches between clan and register tables.
        Returns list of match groups.
        """
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
                        
                        # Check if counts match
                        if len(clan_list) == len(register_list) and len(clan_list) > 1:
                            # Create sequential matches
                            for i, ((clan_record, clan_suffix), (register_record, register_year)) in enumerate(zip(clan_list, register_list)):
                                matches.append({
                                    'base_name': base_name,
                                    'clan_record': clan_record,
                                    'register_record': register_record,
                                    'clan_suffix': clan_suffix,
                                    'register_year': register_year,
                                    'match_index': i
                                })
                
                logger.info(f"Found {len(matches)} potential sequential matches")
                return matches
                
        except Exception as e:
            logger.error(f"Error finding sequential matches: {e}")
            return []
    
    def create_enhanced_description_prompt(self, clan_data, register_data):
        """Create enhanced prompt that includes date information"""
        
        system_prompt = """You are a skilled tartan historian and textile expert with deep knowledge of Scottish heritage and traditional weaving. Your task is to write engaging, accurate descriptions of tartan designs that capture both their technical characteristics and cultural significance.

CRITICAL: Write in UK English ONLY. Use proper British spellings: colours (not colors), honour (not honor), centre (not center), favour (not favor), etc. Use British idioms and expressions.

Use inspirational but accurate language that would appeal to both tartan enthusiasts and general readers. Focus on the cultural and historical aspects whilst maintaining technical accuracy.

Your response should be a single, well-crafted paragraph of approximately 100-150 words that:
- Describes the tartan's purpose and significance based on the registration notes
- Mentions the category (Clan, Name, Fashion, Corporate, etc.) and what this means
- Notes any restrictions if they exist (but don't mention if there are none)
- Includes the designer's name only if it adds value to the description
- Uses evocative language about Scottish heritage and tradition
- Stays true to the facts provided in the registration notes
- Avoids making up technical details not provided in the source material
- Uses ONLY UK English spellings throughout
- Incorporates the tartan's date/year if provided to give historical context"""

        # Build the user prompt with enhanced information
        user_prompt = f"""Please write a compelling description for this tartan design:

**Tartan Name:** {clan_data['name']}
**Category:** {register_data['category']}
**Restrictions:** {register_data['restrictions']}
**Designer:** {register_data['designer']}"""

        # Add date information if available
        if register_data['tartan_date']:
            user_prompt += f"\n**Tartan Date:** {register_data['tartan_date']}"
        if register_data['registration_date']:
            user_prompt += f"\n**Registration Date:** {register_data['registration_date']}"
            
        user_prompt += f"\n**Registration Notes:**\n{register_data['registration_notes']}"
        
        return system_prompt, user_prompt
    
    def test_sequential_matches(self, limit=5):
        """Test a limited number of sequential matches"""
        matches = self.find_sequential_matches()
        
        if not matches:
            logger.info("No sequential matches found")
            return
        
        logger.info(f"Testing first {min(limit, len(matches))} sequential matches:")
        logger.info("=" * 80)
        
        for i, match in enumerate(matches[:limit]):
            logger.info(f"\nTEST {i+1}: {match['base_name']}")
            logger.info(f"CLAN: '{match['clan_record']['name']}' (suffix: {match['clan_suffix']})")
            logger.info(f"REGISTER: '{match['register_record']['tartan_name']}' (year: {match['register_year']})")
            
            # Generate description
            system_prompt, user_prompt = self.create_enhanced_description_prompt(
                match['clan_record'], 
                match['register_record']
            )
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            try:
                response = self.llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
                
                if response and 'content' in response:
                    generated_description = response['content']
                    logger.info(f"\nGENERATED DESCRIPTION:\n{generated_description}")
                    logger.info("-" * 80)
                else:
                    logger.error(f"Failed to generate description: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"LLM request failed: {e}")
            
            # Add delay between requests
            time.sleep(2)
    
    def generate_descriptions_for_matches(self, matches):
        """Generate and save descriptions for all sequential matches"""
        if not matches:
            logger.info("No matches to process")
            return
        
        logger.info(f"Generating descriptions for {len(matches)} sequential matches...")
        
        successful_count = 0
        failed_count = 0
        
        for i, match in enumerate(matches):
            logger.info(f"\nProcessing {i+1}/{len(matches)}: {match['clan_record']['name']} -> {match['register_record']['tartan_name']}")
            
            # Generate description
            system_prompt, user_prompt = self.create_enhanced_description_prompt(
                match['clan_record'], 
                match['register_record']
            )
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            try:
                response = self.llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
                
                if response and 'content' in response:
                    generated_description = response['content']
                    
                    # Save to database
                    if not self.dry_run:
                        with db_manager.get_cursor() as cursor:
                            cursor.execute('''
                                UPDATE tartan_designs_clan 
                                SET description = %s 
                                WHERE id = %s
                            ''', (generated_description, match['clan_record']['id']))
                        
                        logger.info(f"✅ Description saved for {match['clan_record']['name']}")
                        successful_count += 1
                    else:
                        logger.info(f"DRY RUN: Would save description for {match['clan_record']['name']}")
                        logger.info(f"Generated: {generated_description[:100]}...")
                        successful_count += 1
                else:
                    logger.error(f"❌ Failed to generate description: {response.get('error', 'Unknown error')}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ LLM request failed: {e}")
                failed_count += 1
            
            # Add delay between requests
            time.sleep(2)
        
        logger.info(f"\nSUMMARY:")
        logger.info(f"✅ Successful: {successful_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"📊 Total processed: {len(matches)}")
    
    def analyze_match_patterns(self):
        """Analyze the patterns of matches found"""
        matches = self.find_sequential_matches()
        
        if not matches:
            logger.info("No sequential matches found")
            return
        
        # Group by base name to show patterns
        base_name_groups = {}
        for match in matches:
            base_name = match['base_name']
            if base_name not in base_name_groups:
                base_name_groups[base_name] = []
            base_name_groups[base_name].append(match)
        
        logger.info(f"SEQUENTIAL MATCH ANALYSIS:")
        logger.info(f"Total base names with sequential matches: {len(base_name_groups)}")
        logger.info(f"Total individual matches: {len(matches)}")
        logger.info("\nExamples of sequential match patterns:")
        
        for i, (base_name, group_matches) in enumerate(list(base_name_groups.items())[:10]):
            logger.info(f"\n{i+1}. {base_name} ({len(group_matches)} variants):")
            for match in group_matches:
                logger.info(f"   CLAN: '{match['clan_record']['name']}' -> REGISTER: '{match['register_record']['tartan_name']}'")
        
        if len(base_name_groups) > 10:
            logger.info(f"\n... and {len(base_name_groups) - 10} more base names with sequential matches")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sequential name-based tartan description generation")
    parser.add_argument('--live', action='store_true', help='Run in live mode (make database changes). Default is dry run.')
    parser.add_argument('--test', action='store_true', help='Run test generation on sample matches')
    parser.add_argument('--analyze', action='store_true', help='Analyze match patterns without generating descriptions')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of test generations (default: 5)')
    args = parser.parse_args()

    matcher = SequentialNameMatcher(dry_run=not args.live)
    
    if not args.live:
        logger.info("Running in DRY RUN mode - no database changes will be made")
    else:
        logger.info("Running in LIVE mode - database will be updated")

    if args.analyze:
        matcher.analyze_match_patterns()
    elif args.test:
        matcher.test_sequential_matches(limit=args.limit)
    elif args.live:
        # Live mode - generate descriptions for all matches
        matches = matcher.find_sequential_matches()
        if matches:
            matcher.generate_descriptions_for_matches(matches)
        else:
            logger.info("No sequential matches found to process")
    else:
        logger.info("Use --analyze to see match patterns, --test to generate sample descriptions, or --live to generate all descriptions")
