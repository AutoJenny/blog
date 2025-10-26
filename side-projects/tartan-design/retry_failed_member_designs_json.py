#!/usr/bin/env python3
"""
Retry Failed Member Design Descriptions with JSON Format

This script identifies Member Design tartans that failed to get descriptions
and retries them with the improved JSON parsing logic.
"""

import sys
from pathlib import Path
import logging
import time
from collections import defaultdict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager
from member_design_description_generator import MemberDesignDescriptionGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def retry_failed_member_designs_json():
    """Retry generating descriptions for failed Member Design tartans using JSON format"""
    
    # Get failed Member Design tartans
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name
            FROM tartan_designs_clan
            WHERE name ILIKE '%Member Design%' 
            AND (description IS NULL OR description = '')
            ORDER BY name
        """)
        failed_tartans = cursor.fetchall()
    
    if not failed_tartans:
        logger.info("No failed Member Design tartans found")
        return
    
    logger.info(f"Found {len(failed_tartans)} failed Member Design tartans to retry with JSON format")
    
    # Group by base name (removing "Member Design" suffix)
    grouped_designs = defaultdict(list)
    for tartan in failed_tartans:
        base_name = tartan['name'].replace(' Member Design', '').strip()
        grouped_designs[base_name].append(tartan)
    
    logger.info(f"Grouped into {len(grouped_designs)} base name groups")
    
    # Create generator and process each group
    generator = MemberDesignDescriptionGenerator(dry_run=False)
    
    successful_count = 0
    failed_count = 0
    
    for i, (base_name, tartan_group) in enumerate(grouped_designs.items()):
        logger.info(f"\n============================================================")
        logger.info(f"Retrying {i+1}/{len(grouped_designs)}: {base_name} Member Design (JSON)")
        logger.info(f"============================================================")
        logger.info(f"Processing '{base_name} Member Design': {len(tartan_group)} variants")
        
        # Generate description with JSON format
        system_prompt, user_prompt = generator.create_member_design_prompt(tartan_group)
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        try:
            response = generator.llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
            
            if response and 'content' in response:
                generated_description = response['content']
                logger.info(f"Generated response for '{base_name} Member Design' ({len(generated_description)} chars)")
                
                # Parse descriptions with improved JSON logic
                descriptions = generator.parse_llm_response(generated_description, tartan_group)
                
                # Save to database
                with db_manager.get_cursor() as cursor:
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
                logger.error(f"❌ Failed to generate description: {response.get('error', 'Unknown error')}")
                failed_count += len(tartan_group)
                
        except Exception as e:
            logger.error(f"❌ LLM request failed: {e}")
            failed_count += len(tartan_group)
        
        # Add delay between requests
        time.sleep(2)
    
    logger.info(f"\nJSON RETRY SUMMARY:")
    logger.info(f"✅ Successful: {successful_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info(f"📊 Total processed: {len(failed_tartans)}")


if __name__ == "__main__":
    retry_failed_member_designs_json()
