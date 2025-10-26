#!/usr/bin/env python3
"""
Member Design Description Generator

This script identifies tartans with "Member Design" in their names and generates
descriptions that clarify these are designs created using the Clan Tartan Designer
at https://clan.com/tartandesigner/ and have been published and produced as physical products.

The LLM can make educated guesses about the tartan's meaning based on the rest of the name
but should make clear this is only a guess.
"""

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


class MemberDesignDescriptionGenerator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.llm_service = LLMService()
        self.db_manager = db_manager

    def get_member_design_tartans(self):
        """Fetches all tartans with 'Member Design' in their names, including those with existing descriptions."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description
                FROM tartan_designs_clan
                WHERE name ILIKE '%Member Design%'
                ORDER BY name
            """)
            return cursor.fetchall()

    def create_member_design_prompt(self, tartan_group):
        """Create a prompt for generating Member Design descriptions"""
        base_name = tartan_group[0]['name'].replace(' Member Design', '').strip()
        
        # Build tartan list
        tartan_list = []
        for tartan in tartan_group:
            tartan_list.append(f"  - ID {tartan['id']}: '{tartan['name']}'")
        
        tartan_list_str = '\n'.join(tartan_list)
        
        system_prompt = """You are a tartan expert and creative writer specialising in Scottish textile traditions. You understand the significance of modern tartan design tools and can craft engaging descriptions that accurately represent the origin and characteristics of Member Design tartans.

CRITICAL: Use UK English spellings throughout (colours, centre, honour, etc.)"""

        user_prompt = f"""Generate descriptions for these Member Design tartans:

{tartan_list_str}

IMPORTANT CONTEXT:
These tartans are "Member Designs" - they were created using the Clan Tartan Designer at <a href="https://clan.com/tartandesigner/">https://clan.com/tartandesigner/</a> and have been published by their designers and subsequently produced as physical products.

The base name element '{base_name}' could refer to either:
- A SURNAME (family/clan name): Focus on family heritage, clan history, ancestral connections, and traditional family associations
- A PLACE NAME (geographical location): Focus on landscape, regional characteristics, local history, geographical features, and area-specific traditions
- A THEME OR CONCEPT: Focus on the symbolic meaning, cultural significance, or intended purpose

TASK:
Create unique, engaging descriptions for each tartan that:
1. Clearly state that this is a Member Design created using the Clan Tartan Designer
2. Include the HTML link to https://clan.com/tartandesigner/
3. Explain that the design has been published and produced as physical product
4. Make an educated guess about the tartan's meaning based on the name element
5. Clearly indicate this interpretation is speculative ("likely represents", "probably inspired by", "suggests", etc.)
6. Describe the visual characteristics and colour scheme
7. Explain the cultural significance or intended use

OUTPUT FORMAT:
You must respond with valid JSON in this exact format:
{{
  "descriptions": [
    {{
      "tartan_id": [ID_NUMBER],
      "tartan_name": "[FULL_TARTAN_NAME]",
      "description": "[YOUR_DESCRIPTION_HERE]"
    }}
  ]
}}

Focus on:
- Clear identification as a Member Design with proper attribution
- Speculative interpretation of the name element (surname, place, or theme)
- Visual characteristics and colour palette
- Cultural significance and intended purpose
- Professional, informative tone while acknowledging uncertainty

Remember: Use UK English spellings throughout (colours, centre, honour, etc.)"""

        return system_prompt, user_prompt

    def parse_llm_response(self, response_text, tartan_group):
        """Parse the LLM response to extract descriptions for each tartan"""
        descriptions = {}
        
        try:
            import json
            
            # Clean the response text - remove markdown code blocks if present
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]   # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            # Try to parse as JSON first
            response_data = json.loads(cleaned_response)
            
            if 'descriptions' in response_data:
                for desc_item in response_data['descriptions']:
                    tartan_id = desc_item.get('tartan_id')
                    description = desc_item.get('description', '')
                    
                    # Handle nested description object (LLM sometimes puts description in a "text" key)
                    if isinstance(description, dict) and 'text' in description:
                        description = description['text']
                    
                    if tartan_id and description:
                        descriptions[tartan_id] = description.strip()
                
                logger.info(f"Successfully parsed JSON response with {len(descriptions)} descriptions")
                return descriptions
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.info("Falling back to text parsing...")
        
        # Fallback to original text parsing if JSON fails
        lines = response_text.strip().split('\n')
        
        # For each tartan in the group, find its description in the response
        for tartan in tartan_group:
            tartan_name = tartan['name']
            tartan_id = tartan['id']
            
            # Look for the tartan name in the response
            description_found = False
            current_desc = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Check if this line contains the tartan name (exact match or simplified version)
                # The LLM often uses markdown bold formatting: **Tartan Name**
                simplified_name = tartan_name.replace('<br/>', ' ').replace('<br>', ' ').replace('[AKA]', '').replace(';', '').strip()
                first_part = tartan_name.split('<br/>')[0].split('[AKA]')[0].split(';')[0].strip()
                
                # Check for markdown bold format: **Tartan Name**
                markdown_name = f"**{tartan_name}**"
                markdown_simplified = f"**{simplified_name}**"
                markdown_first = f"**{first_part}**"
                
                if (tartan_name.lower() in line.lower() or 
                    simplified_name.lower() in line.lower() or
                    first_part.lower() in line.lower() or
                    markdown_name.lower() in line.lower() or
                    markdown_simplified.lower() in line.lower() or
                    markdown_first.lower() in line.lower()):
                    
                    # Found the tartan name, collect following lines as description
                    for j in range(i + 1, len(lines)):
                        desc_line = lines[j].strip()
                        
                        # Stop if we hit another tartan name (markdown bold or regular)
                        if (desc_line.startswith('**') and 
                            not any(name.lower() in desc_line.lower() 
                                   for name in [tartan_name, simplified_name, first_part])):
                            break
                        
                        # Stop if we hit another tartan name (non-markdown)
                        if (any(other_tartan['name'].lower() in desc_line.lower() 
                               for other_tartan in tartan_group if other_tartan['id'] != tartan_id) and
                            not any(name.lower() in desc_line.lower() 
                                   for name in [tartan_name, simplified_name, first_part])):
                            break
                        
                        # Stop at common ending patterns
                        if (desc_line.startswith('---') or 
                            desc_line.startswith('If you\'d like') or
                            desc_line.startswith('Note:') or
                            desc_line.startswith('**Note:**')):
                            break
                        
                        # Skip empty lines and headers
                        if (desc_line and 
                            not desc_line.startswith('CONTEXT') and 
                            not desc_line.startswith('TASK') and 
                            not desc_line.startswith('OUTPUT') and 
                            not desc_line.startswith('Focus on') and 
                            not desc_line.startswith('Remember') and 
                            not desc_line.startswith('Here are')):
                            current_desc.append(desc_line)
                    
                    if current_desc:
                        descriptions[tartan_id] = ' '.join(current_desc).strip()
                        description_found = True
                        break
            
            if not description_found:
                logger.warning(f"No description found for {tartan_name}")
        
        return descriptions

    def generate_descriptions_for_member_designs(self, tartan_groups):
        """Generate and save descriptions for all Member Design tartans"""
        if not tartan_groups:
            logger.info("No Member Design tartans to process")
            return
        
        logger.info(f"Generating descriptions for {len(tartan_groups)} Member Design tartan groups...")
        
        successful_count = 0
        failed_count = 0
        
        for i, tartan_group in enumerate(tartan_groups):
            group_name = tartan_group[0]['name'].replace(' Member Design', '').strip()
            logger.info(f"\n============================================================")
            logger.info(f"Processing {i+1}/{len(tartan_groups)}: {group_name} Member Design")
            logger.info(f"============================================================")
            logger.info(f"Processing '{group_name} Member Design': {len(tartan_group)} variants")
            
            # Generate description
            system_prompt, user_prompt = self.create_member_design_prompt(tartan_group)
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            try:
                response = self.llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
                
                if response and 'content' in response:
                    generated_description = response['content']
                    logger.info(f"Generated response for '{group_name} Member Design' ({len(generated_description)} chars)")
                    
                    # Parse descriptions
                    descriptions = self.parse_llm_response(generated_description, tartan_group)
                    
                    # Save to database
                    if not self.dry_run:
                        with self.db_manager.get_cursor() as cursor:
                            for tartan in tartan_group:
                                tartan_id = tartan['id']
                                if tartan_id in descriptions:
                                    cursor.execute('''
                                        UPDATE tartan_designs_clan 
                                        SET description = %s 
                                        WHERE id = %s
                                    ''', (descriptions[tartan_id], tartan_id))
                                    logger.info(f"✅ Saved description for {tartan['name']}")
                                    successful_count += 1
                                else:
                                    logger.warning(f"⚠️ No description generated for {tartan['name']}")
                                    failed_count += 1
                    else:
                        logger.info(f"DRY RUN: Would save descriptions for {group_name} Member Design")
                        for tartan in tartan_group:
                            if tartan['id'] in descriptions:
                                logger.info(f"Generated: {descriptions[tartan['id']][:100]}...")
                                successful_count += 1
                            else:
                                logger.warning(f"⚠️ No description generated for {tartan['name']}")
                                failed_count += 1
                else:
                    logger.error(f"❌ Failed to generate description: {response.get('error', 'Unknown error')}")
                    failed_count += len(tartan_group)
                    
            except Exception as e:
                logger.error(f"❌ LLM request failed: {e}")
                failed_count += len(tartan_group)
            
            # Add delay between requests
            time.sleep(2)
        
        logger.info(f"\nSUMMARY:")
        logger.info(f"✅ Successful: {successful_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"📊 Total processed: {sum(len(group) for group in tartan_groups)}")

    def analyze_member_designs(self):
        """Analyze Member Design tartans and group them for processing"""
        logger.info("Analyzing Member Design tartans...")
        
        member_designs = self.get_member_design_tartans()
        
        if not member_designs:
            logger.info("No Member Design tartans found")
            return []
        
        logger.info(f"Found {len(member_designs)} Member Design tartans")
        
        # Group by base name (removing "Member Design" suffix)
        grouped_designs = defaultdict(list)
        for tartan in member_designs:
            base_name = tartan['name'].replace(' Member Design', '').strip()
            grouped_designs[base_name].append(tartan)
        
        logger.info(f"Grouped into {len(grouped_designs)} base name groups")
        
        # Show analysis
        logger.info(f"\n================================================================================")
        logger.info(f"MEMBER DESIGN ANALYSIS")
        logger.info(f"================================================================================")
        
        for base_name, group in sorted(grouped_designs.items()):
            existing_descriptions = sum(1 for t in group if t['description'])
            logger.info(f"{base_name}: {len(group)} variants ({existing_descriptions} with descriptions)")
            for tartan in group:
                status = "✅ Has description" if tartan['description'] else "❌ No description"
                logger.info(f"  - ID {tartan['id']}: {tartan['name']} - {status}")
        
        return list(grouped_designs.values())

    def run(self):
        """Main execution method"""
        logger.info("Starting Member Design Description Generator...")
        
        # Analyze Member Designs
        tartan_groups = self.analyze_member_designs()
        
        if not tartan_groups:
            logger.info("No Member Design tartans found to process")
            return
        
        if self.dry_run:
            logger.info(f"\nDRY RUN MODE - Would process {len(tartan_groups)} groups")
            logger.info("Use --live to actually generate and save descriptions")
        else:
            logger.info(f"\nLIVE MODE - Processing {len(tartan_groups)} groups")
            self.generate_descriptions_for_member_designs(tartan_groups)


def main():
    parser = argparse.ArgumentParser(description='Generate descriptions for Member Design tartans')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Run in dry-run mode (default)')
    parser.add_argument('--live', action='store_true',
                        help='Run in live mode and save descriptions to database')
    
    args = parser.parse_args()
    
    # If --live is specified, override dry_run
    dry_run = not args.live
    
    generator = MemberDesignDescriptionGenerator(dry_run=dry_run)
    generator.run()


if __name__ == "__main__":
    main()
