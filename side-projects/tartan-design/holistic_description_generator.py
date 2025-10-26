import sys
from pathlib import Path
import logging
import argparse
import time
from collections import defaultdict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager
from blueprints.planning_llm import LLMService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HolisticDescriptionGenerator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.llm_service = LLMService()
        
    def get_matched_base_names(self):
        """Get all base names that exist in both clan and register tables"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get clan base names without descriptions
                cursor.execute('''
                    SELECT DISTINCT base_name
                    FROM tartan_designs_clan 
                    WHERE description IS NULL OR description = ''
                    AND base_name IS NOT NULL
                ''')
                clan_base_names = {row['base_name'] for row in cursor.fetchall()}
                
                # Get register base names
                cursor.execute('''
                    SELECT DISTINCT base_name
                    FROM tartan_designs_register 
                    WHERE base_name IS NOT NULL
                ''')
                register_base_names = {row['base_name'] for row in cursor.fetchall()}
                
                # Find matches
                matched_base_names = clan_base_names.intersection(register_base_names)
                
                logger.info(f"Found {len(matched_base_names)} base names with matches")
                return sorted(matched_base_names)
                
        except Exception as e:
            logger.error(f"Error getting matched base names: {e}")
            raise
    
    def get_base_name_groups(self, base_name):
        """Get all clan and register records for a specific base name"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get clan records
                cursor.execute('''
                    SELECT id, name, base_name, suffix, description
                    FROM tartan_designs_clan 
                    WHERE base_name = %s
                    AND (description IS NULL OR description = '')
                    ORDER BY suffix, name
                ''', (base_name,))
                clan_records = cursor.fetchall()
                
                # Get register records
                cursor.execute('''
                    SELECT id, tartan_name, base_name, suffix, category, designer, 
                           restrictions, registration_notes, tartan_date, registration_date
                    FROM tartan_designs_register 
                    WHERE base_name = %s
                    ORDER BY suffix, tartan_name
                ''', (base_name,))
                register_records = cursor.fetchall()
                
                return clan_records, register_records
                
        except Exception as e:
            logger.error(f"Error getting base name groups for '{base_name}': {e}")
            raise
    
    def create_holistic_prompt(self, clan_records, register_records):
        """Create a sophisticated prompt for holistic description generation"""
        
        # Build clan group description
        clan_group_desc = f"CLAN GROUP: '{clan_records[0]['base_name']}' ({len(clan_records)} variants)\n"
        for i, record in enumerate(clan_records):
            clan_group_desc += f"  {i+1}. ID {record['id']}: '{record['name']}' (suffix: '{record['suffix']}')\n"
        
        # Build register group description
        register_group_desc = f"REGISTER GROUP: '{register_records[0]['base_name']}' ({len(register_records)} variants)\n"
        for i, record in enumerate(register_records):
            register_group_desc += f"  {i+1}. ID {record['id']}: '{record['tartan_name']}' (suffix: '{record['suffix']}')\n"
            if record.get('registration_notes'):
                register_group_desc += f"      Notes: {record['registration_notes'][:200]}{'...' if len(record['registration_notes']) > 200 else ''}\n"
            if record.get('category'):
                register_group_desc += f"      Category: {record['category']}\n"
            if record.get('designer'):
                register_group_desc += f"      Designer: {record['designer']}\n"
            register_group_desc += "\n"
        
        system_prompt = """You are a tartan expert writing descriptions for Scottish tartan patterns. Your task is to generate accurate, inspirational descriptions using UK English spellings and idioms.

CRITICAL REQUIREMENTS:
- Use UK English spellings: colours (not colors), centre (not center), honour (not honor), etc.
- Write in an engaging, informative style suitable for tartan enthusiasts
- Focus on the pattern characteristics, historical context, and visual appeal
- Each description should be 2-3 sentences, approximately 50-100 words
- Be accurate and avoid speculation

SUFFIX PATTERN ANALYSIS:
- Clan suffixes often indicate colour variants (Brown, Green, Blue) or sequential versions (#2, #3)
- Register suffixes often indicate years ((1990), (1995)) or specific versions ((Official), (Personal))
- Consider how suffixes relate to the base pattern and its variations"""

        user_prompt = f"""You must generate descriptions ONLY for these specific clan records:

{clan_group_desc}

Use this register information for context:

{register_group_desc}

CRITICAL INSTRUCTIONS:
- Generate descriptions ONLY for the clan IDs listed in the CLAN GROUP section above
- Do NOT generate descriptions for any register records
- Use the register information only as context to understand the pattern family

TASK:
1. Analyze the suffix patterns to understand the relationship between variants
2. For each clan record, identify the most relevant register record(s) based on suffix patterns and context
3. Generate a unique description for each clan record, drawing from the relevant register information

OUTPUT FORMAT:
For each clan record listed above, provide:
CLAN_ID_[ID]: [Your description here]

Focus on:
- Pattern characteristics and visual elements
- Historical or cultural significance
- How this variant relates to the base pattern
- Any unique features mentioned in the register notes

Remember: Use UK English spellings throughout (colours, centre, honour, etc.)"""

        return system_prompt, user_prompt
    
    def parse_llm_response(self, response_text, clan_records):
        """Parse the LLM response to extract descriptions for each clan record"""
        descriptions = {}
        
        lines = response_text.strip().split('\n')
        current_id = None
        current_desc = []
        
        for line in lines:
            line = line.strip()
            
            # Check for markdown bold format: **ID: Name**
            if line.startswith('**') and ':' in line and line.endswith('**'):
                # Save previous description if exists
                if current_id and current_desc:
                    descriptions[current_id] = ' '.join(current_desc).strip()
                
                # Start new description
                try:
                    # Extract ID from "**2810: MacKellar Dress Purple**"
                    id_part = line[2:].split(':')[0].strip()  # Remove ** and get ID
                    current_id = int(id_part)
                    current_desc = []
                except (IndexError, ValueError):
                    logger.warning(f"Could not parse clan ID from markdown line: {line}")
                    current_id = None
                    current_desc = []
            
            # Check for CLAN_ID_ format (multiple variations)
            elif 'CLAN_ID_' in line and ':' in line:
                # Save previous description if exists
                if current_id and current_desc:
                    descriptions[current_id] = ' '.join(current_desc).strip()
                
                # Start new description
                try:
                    # Handle formats like:
                    # "1. CLAN_ID_2810: 'MacKellar Dress Purple'"
                    # "CLAN_ID_2810: description"
                    if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                        # Extract ID from numbered format
                        id_part = line.split('CLAN_ID_')[1].split(':')[0]
                        current_id = int(id_part)
                        # Skip the clan name part and start collecting description
                        current_desc = []
                    else:
                        # Direct CLAN_ID format
                        current_id = int(line.split('CLAN_ID_')[1].split(':')[0])
                        desc_part = line.split(':', 1)[1].strip() if ':' in line else ''
                        # Remove quoted clan name if present
                        if desc_part.startswith("'") and "'" in desc_part[1:]:
                            desc_part = desc_part.split("'", 2)[2].strip()
                        current_desc = [desc_part] if desc_part else []
                except (IndexError, ValueError):
                    logger.warning(f"Could not parse clan ID from line: {line}")
                    current_id = None
                    current_desc = []
            
            # Check for (ID XXX): format
            elif '(ID ' in line and '):' in line:
                # Save previous description if exists
                if current_id and current_desc:
                    descriptions[current_id] = ' '.join(current_desc).strip()
                
                # Start new description
                try:
                    id_part = line.split('(ID ')[1].split('):')[0]
                    current_id = int(id_part)
                    desc_part = line.split('):', 1)[1].strip() if '):' in line else ''
                    current_desc = [desc_part] if desc_part else []
                except (IndexError, ValueError):
                    logger.warning(f"Could not parse clan ID from line: {line}")
                    current_id = None
                    current_desc = []
            
            elif current_id and line and not line.startswith('Anderson') and not line.startswith('Here are') and not line.startswith('I\'ll provide') and not line.startswith('Note:'):
                # Continue current description (skip headers and titles)
                current_desc.append(line)
        
        # Save last description
        if current_id and current_desc:
            descriptions[current_id] = ' '.join(current_desc).strip()
        
        return descriptions
    
    def generate_descriptions_for_base_name(self, base_name):
        """Generate descriptions for all clan variants of a base name"""
        try:
            clan_records, register_records = self.get_base_name_groups(base_name)
            
            if not clan_records:
                logger.warning(f"No clan records found for base name: {base_name}")
                return
            
            if not register_records:
                logger.warning(f"No register records found for base name: {base_name}")
                return
            
            logger.info(f"Processing '{base_name}': {len(clan_records)} clan variants, {len(register_records)} register variants")
            
            # Create holistic prompt
            system_prompt, user_prompt = self.create_holistic_prompt(clan_records, register_records)
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Call LLM
            response = self.llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
            
            if response and 'content' in response:
                generated_text = response['content']
                logger.info(f"Generated response for '{base_name}' ({len(generated_text)} chars)")
                
                # Parse response
                descriptions = self.parse_llm_response(generated_text, clan_records)
                
                # Save to database
                if not self.dry_run:
                    with db_manager.get_cursor() as cursor:
                        for clan_record in clan_records:
                            clan_id = clan_record['id']
                            if clan_id in descriptions:
                                description = descriptions[clan_id]
                                cursor.execute('''
                                    UPDATE tartan_designs_clan 
                                    SET description = %s 
                                    WHERE id = %s
                                ''', (description, clan_id))
                                logger.info(f"✅ Saved description for {clan_record['name']}")
                            else:
                                logger.warning(f"⚠️ No description generated for {clan_record['name']}")
                else:
                    logger.info(f"DRY RUN - Would save descriptions for {len(descriptions)} records")
                    for clan_id, description in descriptions.items():
                        clan_name = next(r['name'] for r in clan_records if r['id'] == clan_id)
                        logger.info(f"  {clan_name}: {description[:100]}{'...' if len(description) > 100 else ''}")
            else:
                logger.error(f"❌ Failed to generate descriptions for '{base_name}': {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error generating descriptions for '{base_name}': {e}")
    
    def generate_all_descriptions(self, limit=None):
        """Generate descriptions for all matched base names"""
        try:
            matched_base_names = self.get_matched_base_names()
            
            if limit:
                matched_base_names = matched_base_names[:limit]
            
            logger.info(f"Generating descriptions for {len(matched_base_names)} base names...")
            
            successful_count = 0
            failed_count = 0
            
            for i, base_name in enumerate(matched_base_names):
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing {i+1}/{len(matched_base_names)}: {base_name}")
                logger.info(f"{'='*60}")
                
                try:
                    self.generate_descriptions_for_base_name(base_name)
                    successful_count += 1
                except Exception as e:
                    logger.error(f"Failed to process '{base_name}': {e}")
                    failed_count += 1
                
                # Add delay between requests
                time.sleep(2)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"GENERATION COMPLETE")
            logger.info(f"{'='*60}")
            logger.info(f"✅ Successful: {successful_count}")
            logger.info(f"❌ Failed: {failed_count}")
            logger.info(f"📊 Total processed: {len(matched_base_names)}")
            
        except Exception as e:
            logger.error(f"Error in generate_all_descriptions: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Generate holistic descriptions for matched base names')
    parser.add_argument('--live', action='store_true', help='Run in live mode - update database')
    parser.add_argument('--test', action='store_true', help='Test with a single base name')
    parser.add_argument('--limit', type=int, help='Limit number of base names to process')
    parser.add_argument('--base-name', type=str, help='Process specific base name (for testing)')
    
    args = parser.parse_args()
    
    generator = HolisticDescriptionGenerator(dry_run=not args.live)
    
    if args.test or args.base_name:
        # Test mode - process single base name
        if args.base_name:
            base_name = args.base_name
        else:
            # Get first matched base name for testing
            matched_names = generator.get_matched_base_names()
            base_name = matched_names[0] if matched_names else None
            
        if base_name:
            logger.info(f"Testing with base name: {base_name}")
            generator.generate_descriptions_for_base_name(base_name)
        else:
            logger.error("No base names available for testing")
    else:
        # Full generation
        generator.generate_all_descriptions(limit=args.limit)

if __name__ == "__main__":
    main()
