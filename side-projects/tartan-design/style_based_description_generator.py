#!/usr/bin/env python3
"""
Style-Based Description Generator for Tartan Designs

This script generates descriptions for tartans in the _clan table that contain
'hunting', 'dance', or 'dress' in their names, focusing on imaginative descriptions
based on traditional tartan style conventions.

Author: AI Assistant
Date: 2025-10-25
"""

import sys
import logging
import argparse
from pathlib import Path
from collections import defaultdict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager
from blueprints.planning_llm import LLMService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StyleBasedDescriptionGenerator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.llm_service = LLMService()
        
    def get_style_based_tartans(self):
        """Get tartans with 'hunting', 'dance', or 'dress' in their names that don't have descriptions"""
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, base_name, suffix
                FROM tartan_designs_clan
                WHERE (description IS NULL OR description = '')
                AND (
                    LOWER(name) LIKE '%hunting%' OR 
                    LOWER(name) LIKE '%dance%' OR 
                    LOWER(name) LIKE '%dress%'
                )
                ORDER BY name
            """)
            return cursor.fetchall()
    
    def group_tartans_by_base_name(self, tartans):
        """Group tartans by their base name for holistic description generation"""
        groups = defaultdict(list)
        for tartan in tartans:
            base_name = tartan['base_name'] or tartan['name']
            groups[base_name].append(tartan)
        return groups
    
    def create_style_description_prompt(self, tartan_group):
        """Create a prompt for generating style-based descriptions"""
        base_name = tartan_group[0]['base_name'] or tartan_group[0]['name']
        
        # Determine the style type - prioritize dress > dance > hunting
        style_type = None
        if 'dress' in base_name.lower():
            style_type = 'dress'
        elif 'dance' in base_name.lower():
            style_type = 'dance'
        elif 'hunting' in base_name.lower():
            style_type = 'hunting'
        
        # Extract the name element (before the style word)
        name_element = self.extract_name_element(base_name, style_type)
        
        # Build tartan list with full names (let LLM handle the complexity)
        tartan_list = []
        for tartan in tartan_group:
            tartan_list.append(f"  - ID {tartan['id']}: '{tartan['name']}' (suffix: '{tartan['suffix']}')")
        
        tartan_list_str = '\n'.join(tartan_list)
        
        system_prompt = """You are a tartan expert and creative writer specialising in Scottish textile traditions. You understand the historical and cultural significance of different tartan styles and can craft engaging, imaginative descriptions that capture both the visual characteristics and cultural context of tartan patterns.

CRITICAL: Use UK English spellings throughout (colours, centre, honour, etc.)"""

        user_prompt = f"""Generate imaginative descriptions for these {style_type} tartans:

{tartan_list_str}

CONTEXT ABOUT {style_type.upper()} TARTANS:
{self.get_style_context(style_type)}

NAME ANALYSIS:
The tartan name element '{name_element}' could refer to either:
- A SURNAME (family/clan name): Focus on family heritage, clan history, ancestral connections, and traditional family associations
- A PLACE NAME (geographical location): Focus on landscape, regional characteristics, local history, geographical features, and area-specific traditions

Use your knowledge to determine which is more likely and write accordingly.

IMPORTANT: Some tartan names may contain multiple style keywords (e.g., "Dress Dance"). In such cases, focus on the PRIMARY style indicated by the name structure. For "Dress Dance" tartans, treat them as dress tartans with dance-appropriate characteristics.

TASK:
Create unique, engaging descriptions for each tartan that:
1. Accurately reflect the technical characteristics of {style_type} tartans
2. Explain how the colour palette differs from the main clan tartan
3. Describe the specific use case and context (formal wear, outdoor activities, dance performance)
4. Highlight any colour variations or distinctive features in the specific variant
5. Use vivid, descriptive language while maintaining technical accuracy

OUTPUT FORMAT:
For each tartan, provide a description starting with the tartan name, followed by your imaginative description.

Focus on:
- Technical accuracy about {style_type} tartan characteristics
- How the colour palette differs from the main clan tartan (e.g., "white background replacing navy" for dress tartans)
- Specific use cases and contexts (formal ceremonies, outdoor activities, dance performance)
- Visual characteristics and colour schemes
- Historical and cultural significance (surname or place-based)
- How colour variants enhance the pattern for their intended purpose

Remember: Use UK English spellings throughout (colours, centre, honour, etc.)"""

        return system_prompt, user_prompt
    
    def extract_name_element(self, base_name, style_type):
        """Extract the name element before the style word"""
        # Remove the style word and any trailing words
        name_parts = base_name.lower().split()
        
        # Find the style word position
        style_positions = []
        for i, part in enumerate(name_parts):
            if style_type in part:
                style_positions.append(i)
        
        if style_positions:
            # Take everything before the first occurrence of the style word
            first_style_pos = min(style_positions)
            name_element = ' '.join(name_parts[:first_style_pos])
        else:
            # Fallback: take the first word
            name_element = name_parts[0] if name_parts else base_name
        
        return name_element.title()
    
    def get_style_context(self, style_type):
        """Get contextual information about different tartan styles"""
        contexts = {
            'hunting': """Hunting tartans are designed for practicality and camouflage rather than ceremony. They feature darker, muted colours — greens, browns, blues instead of reds or whites — created for outdoor, sporting, and field use (hunting, riding, stalking). The sett (pattern) remains the same as the main clan tartan, but recoloured to blend with natural landscapes. Worn traditionally in tweed or wool cloth for durability, common in Highland country wear — jackets, trews, plaids, field kilts. Examples: MacDonald Hunting uses the MacDonald sett rendered in greens and blues instead of red; Stewart Hunting features earthy tones, often green background replacing red.""",
            
            'dance': """Dance tartans aren't an official historical category like Dress or Hunting, but the term is used in Highland wear and dance circles for fabrics designed specifically for Highland dancers. Typical features include lightweight wool (often 10–11 oz) to allow movement and airflow, bright, high-contrast colours that show clearly on stage and in motion, often adapted from a Dress tartan or special performance weave, may use white or pastel backgrounds and clear striping so the pattern is visible in twirling skirts. Some clans and suppliers market specific "Dance" versions of their setts, but these are usually custom designations, not official clan variants.""",
            
            'dress': """Dress tartans are variants of clan or district tartans that are lightened in colour, traditionally for formal or ceremonial wear, especially by women. Key traits: Replace the main dark ground (often black or navy) with white, cream, or pale background; designed originally for evening or dance wear (Highland balls, dress uniforms); often used for skirts, shawls, sashes, or formal kilts; the sett (pattern) stays the same as the clan tartan — only the palette changes; in military or men's wear, sometimes used for formal kilt hose or plaids. Examples: MacDonald Dress = standard MacDonald sett with white background; Gordon Dress = Gordon tartan with yellow/light ground. So, "Dress" = same clan pattern, lighter and more decorative, typically white-based, for formal or festive use."""
        }
        return contexts.get(style_type, "Traditional Scottish tartan with cultural significance.")
    
    def parse_llm_response(self, response_text, tartan_group):
        """Parse the LLM response to extract descriptions for each tartan"""
        descriptions = {}
        
        # Simple approach: split by tartan names and extract descriptions
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
                # The LLM often simplifies names by removing HTML tags and [AKA] markers
                simplified_name = tartan_name.replace('<br/>', ' ').replace('<br>', ' ').replace('[AKA]', '').replace(';', '').strip()
                # Also try just the first part before any [AKA] or semicolon
                first_part = tartan_name.split('<br/>')[0].split('[AKA]')[0].split(';')[0].strip()
                
                if (tartan_name.lower() in line.lower() or 
                    simplified_name.lower() in line.lower() or
                    first_part.lower() in line.lower()):
                    # Found the tartan name, collect following lines as description
                    for j in range(i + 1, len(lines)):
                        desc_line = lines[j].strip()
                        
                        # Stop if we hit another tartan name or end of response
                        if (desc_line.startswith('**') or 
                            any(other_tartan['name'].lower() in desc_line.lower() 
                                for other_tartan in tartan_group if other_tartan['id'] != tartan_id)):
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
    
    def generate_descriptions_for_group(self, base_name, tartan_group):
        """Generate descriptions for a group of tartans with the same base name"""
        try:
            logger.info(f"Processing '{base_name}': {len(tartan_group)} variants")
            
            # Create prompt
            system_prompt, user_prompt = self.create_style_description_prompt(tartan_group)
            
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
                descriptions = self.parse_llm_response(generated_text, tartan_group)
                
                # Save to database
                if not self.dry_run:
                    with db_manager.get_cursor() as cursor:
                        for tartan in tartan_group:
                            tartan_id = tartan['id']
                            if tartan_id in descriptions:
                                description = descriptions[tartan_id]
                                cursor.execute('''
                                    UPDATE tartan_designs_clan 
                                    SET description = %s 
                                    WHERE id = %s
                                ''', (description, tartan_id))
                                logger.info(f"✅ Saved description for {tartan['name']}")
                            else:
                                logger.warning(f"⚠️ No description generated for {tartan['name']}")
                else:
                    logger.info("DRY RUN - Would save descriptions:")
                    for tartan in tartan_group:
                        tartan_id = tartan['id']
                        if tartan_id in descriptions:
                            logger.info(f"  {tartan['name']}: {descriptions[tartan_id][:100]}...")
                        else:
                            logger.warning(f"  ⚠️ No description for {tartan['name']}")
                
                return len(descriptions)
            else:
                logger.error(f"❌ Failed to generate response for '{base_name}'")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error processing '{base_name}': {e}")
            return 0
    
    def generate_all_style_descriptions(self):
        """Generate descriptions for all style-based tartans"""
        logger.info("Finding style-based tartans without descriptions...")
        
        tartans = self.get_style_based_tartans()
        if not tartans:
            logger.info("No style-based tartans found without descriptions")
            return
        
        logger.info(f"Found {len(tartans)} style-based tartans without descriptions")
        
        # Group by base name
        groups = self.group_tartans_by_base_name(tartans)
        logger.info(f"Grouped into {len(groups)} base name groups")
        
        total_successful = 0
        total_failed = 0
        
        for i, (base_name, tartan_group) in enumerate(groups.items(), 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {i}/{len(groups)}: {base_name}")
            logger.info(f"{'='*60}")
            
            successful = self.generate_descriptions_for_group(base_name, tartan_group)
            total_successful += successful
            total_failed += len(tartan_group) - successful
            
            # Add delay between requests
            import time
            time.sleep(2)
        
        logger.info(f"\n{'='*60}")
        logger.info("STYLE-BASED GENERATION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Successful: {total_successful}")
        logger.info(f"❌ Failed: {total_failed}")
        logger.info(f"📊 Total processed: {len(tartans)}")


def main():
    parser = argparse.ArgumentParser(description='Generate style-based descriptions for tartans')
    parser.add_argument('--live', action='store_true', help='Run in live mode (save to database)')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Run in dry-run mode (default)')
    
    args = parser.parse_args()
    
    # Override dry_run if --live is specified
    dry_run = not args.live
    
    generator = StyleBasedDescriptionGenerator(dry_run=dry_run)
    generator.generate_all_style_descriptions()


if __name__ == "__main__":
    main()
