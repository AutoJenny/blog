#!/usr/bin/env python3
"""
Test LLM Description Generation for Tartan Designs
Tests the prompt with sample records before running on full dataset
"""

import sys
from pathlib import Path
import logging

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
        logging.FileHandler('tartan_llm_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TartanDescriptionGenerator:
    def __init__(self):
        self.llm_service = LLMService()
        
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
    
    def test_with_sample_records(self):
        """Test the description generation with sample records"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get a few diverse sample records
                cursor.execute('''
                    SELECT id, tartan_name, category, restrictions, designer, registration_notes
                    FROM tartan_designs_register 
                    WHERE registration_notes IS NOT NULL 
                    AND registration_notes != '' 
                    AND registration_notes != 'none'
                    AND registration_notes != 'Registration notes:'
                    ORDER BY id
                    LIMIT 5
                ''')
                
                records = cursor.fetchall()
                
                if not records:
                    logger.error("No suitable test records found")
                    return
                
                logger.info(f"Testing with {len(records)} sample records...")
                
                for i, record in enumerate(records, 1):
                    print(f"\n{'='*80}")
                    print(f"TEST {i}: {record['tartan_name']}")
                    print(f"{'='*80}")
                    print(f"Category: {record['category']}")
                    print(f"Designer: {record['designer']}")
                    print(f"Restrictions: {record['restrictions']}")
                    print(f"\nRegistration Notes:")
                    print(f"{record['registration_notes']}")
                    print(f"\n{'-'*80}")
                    
                    # Generate description
                    description = self.generate_description(record)
                    
                    if description:
                        print(f"GENERATED DESCRIPTION:")
                        print(f"{description}")
                    else:
                        print("FAILED TO GENERATE DESCRIPTION")
                    
                    print(f"\n{'='*80}")
                    
        except Exception as e:
            logger.error(f"Error in test: {e}")

def main():
    """Main function"""
    logger.info("Starting tartan description generation test...")
    
    generator = TartanDescriptionGenerator()
    generator.test_with_sample_records()
    
    logger.info("Test complete!")

if __name__ == "__main__":
    main()
