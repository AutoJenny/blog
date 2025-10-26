#!/usr/bin/env python3
"""
Tartan Description Generator - Production Script
Generates LLM descriptions for all tartan designs and saves to clan table
"""

import sys
from pathlib import Path
import logging
import argparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager
from blueprints.planning_llm import LLMService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tartan_description_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TartanDescriptionGenerator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.llm_service = LLMService()
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
    def create_description_prompt(self, tartan_data):
        """Create the prompt for generating tartan descriptions"""
        
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
- Uses ONLY UK English spellings throughout"""

        user_prompt = f"""Please write a compelling description for this tartan design:

**Tartan Name:** {tartan_data['tartan_name']}
**Category:** {tartan_data['category']}
**Designer:** {tartan_data['designer'] if tartan_data['designer'] else 'Not specified'}
**Restrictions:** {tartan_data['restrictions'] if tartan_data['restrictions'] and tartan_data['restrictions'].lower() not in ['none', 'null', ''] else 'None'}
**Registration Notes:** {tartan_data['registration_notes']}

Write a single paragraph description that captures the essence and significance of this tartan design."""

        return system_prompt, user_prompt
    
    def generate_description(self, tartan_data):
        """Generate description for a single tartan record"""
        try:
            system_prompt, user_prompt = self.create_description_prompt(tartan_data)
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            logger.info(f"Generating description for: {tartan_data['tartan_name']}")
            
            response = self.llm_service.execute_llm_request(
                'ollama', 
                'llama3.2:latest', 
                messages, 
                max_tokens=2000
            )
            
            if response and 'content' in response:
                return response['content'].strip()
            else:
                logger.error(f"Failed to generate description: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return None
    
    def get_register_records_with_clan_links(self):
        """Get all register records that have clan_id links"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute('''
                    SELECT r.id, r.tartan_name, r.category, r.restrictions, r.designer, r.registration_notes, r.clan_id
                    FROM tartan_designs_register r
                    WHERE r.clan_id IS NOT NULL
                    AND r.registration_notes IS NOT NULL 
                    AND r.registration_notes != '' 
                    AND r.registration_notes != 'none'
                    AND r.registration_notes != 'Registration notes:'
                    ORDER BY r.id
                ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching register records: {e}")
            return []
    
    def update_clan_description(self, clan_id, description):
        """Update the description field in the clan table"""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would update clan_id {clan_id} with description: {description[:100]}...")
                return True
            
            with db_manager.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE tartan_designs_clan 
                    SET description = %s 
                    WHERE id = %s
                ''', (description, clan_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated clan_id {clan_id} with new description")
                    return True
                else:
                    logger.warning(f"No clan record found with id {clan_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating clan description for id {clan_id}: {e}")
            return False
    
    def process_all_records(self):
        """Process all register records and generate descriptions"""
        logger.info("Starting tartan description generation...")
        
        records = self.get_register_records_with_clan_links()
        
        if not records:
            logger.error("No suitable records found for processing")
            return
        
        logger.info(f"Found {len(records)} records to process")
        
        for record in records:
            self.processed_count += 1
            
            logger.info(f"Processing {self.processed_count}/{len(records)}: {record['tartan_name']}")
            
            # Generate description
            description = self.generate_description(record)
            
            if description:
                # Update the clan table
                if self.update_clan_description(record['clan_id'], description):
                    self.success_count += 1
                else:
                    self.error_count += 1
            else:
                self.error_count += 1
                logger.error(f"Failed to generate description for {record['tartan_name']}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total processed: {self.processed_count}")
        logger.info(f"Successfully updated: {self.success_count}")
        logger.info(f"Errors: {self.error_count}")
        logger.info(f"Skipped: {self.skipped_count}")
        
        if self.dry_run:
            logger.info("*** DRY RUN MODE - No actual database updates were made ***")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate tartan descriptions using LLM')
    parser.add_argument('--live', action='store_true', 
                       help='Run in live mode (default is dry run)')
    
    args = parser.parse_args()
    
    dry_run = not args.live
    
    if dry_run:
        logger.info("Running in DRY RUN mode - no database changes will be made")
    else:
        logger.info("Running in LIVE mode - database will be updated")
    
    generator = TartanDescriptionGenerator(dry_run=dry_run)
    generator.process_all_records()

if __name__ == "__main__":
    main()
