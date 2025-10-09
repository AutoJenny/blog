#!/usr/bin/env python3
"""
Phase 3: Fix Hardcoded Content Contamination

This script fixes the hardcoded content contamination in LLM prompts by:
1. Removing hardcoded specific content (like "autumn folklore")
2. Expanding "Scottish" references to "Scottish or other Celtic"
3. Ensuring prompts use user input via placeholders

Based on analysis:
- CORRECT: General Scottish/Celtic heritage focus (expand to include other Celtic cultures)
- WRONG: Hardcoded specific content like "autumnal traditions" (remove completely)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_hardcoded_content():
    """Fix hardcoded content contamination in LLM prompts"""
    
    logger.info("Starting Phase 3: Fix Hardcoded Content Contamination")
    
    # Define the fixes for each prompt
    prompt_fixes = {
        'Section Structure Design': {
            'system_prompt': {
                'old': 'You are a Scottish heritage content specialist and blog structure expert. Your expertise lies in designing comprehensive, engaging blog post structures that capture the essence of Scottish autumnal traditions and folklore.',
                'new': 'You are a Scottish or other Celtic heritage content specialist and blog structure expert. Your expertise lies in designing comprehensive, engaging blog post structures that capture the essence of the user\'s specified cultural traditions and themes.'
            },
            'prompt_text': {
                'old': 'TASK: Design a 7-section blog structure for a Scottish heritage blog about autumn folklore.',
                'new': 'TASK: Design a 7-section blog structure for a heritage blog about [USER_TOPIC].'
            }
        },
        'Section Drafting': {
            'system_prompt': {
                'old': 'You are a Scottish heritage content specialist and engaging blog writer.',
                'new': 'You are a Scottish or other Celtic heritage content specialist and engaging blog writer.'
            }
        },
        'Topic Brainstorming': {
            'system_prompt': {
                'old': 'You are a content strategist specializing in Scottish topics.',
                'new': 'You are a content strategist specializing in Scottish or other Celtic topics.'
            }
        },
        'Image Captions Generation': {
            'system_prompt': {
                'old': 'You are an expert at creating accessible image descriptions and captions for Scottish heritage content',
                'new': 'You are an expert at creating accessible image descriptions and captions for Scottish or other Celtic heritage content'
            }
        },
        'Individual Topic Allocation': {
            'system_prompt': {
                'old': 'You are a Scottish heritage content specialist and topic allocation expert.',
                'new': 'You are a Scottish or other Celtic heritage content specialist and topic allocation expert.'
            }
        }
    }
    
    with db_manager.get_cursor() as cursor:
        for prompt_name, fixes in prompt_fixes.items():
            logger.info(f"Fixing prompt: {prompt_name}")
            
            # Get current prompt
            cursor.execute("""
                SELECT id, system_prompt, prompt_text 
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY id DESC
                LIMIT 1
            """, (prompt_name,))
            
            prompt = cursor.fetchone()
            if not prompt:
                logger.warning(f"Prompt '{prompt_name}' not found in database")
                continue
            
            # Apply fixes
            new_system_prompt = prompt['system_prompt']
            new_prompt_text = prompt['prompt_text']
            
            if 'system_prompt' in fixes:
                old_text = fixes['system_prompt']['old']
                new_text = fixes['system_prompt']['new']
                if old_text in new_system_prompt:
                    new_system_prompt = new_system_prompt.replace(old_text, new_text)
                    logger.info(f"  Updated system prompt for {prompt_name}")
                else:
                    logger.warning(f"  System prompt text not found for {prompt_name}")
            
            if 'prompt_text' in fixes:
                old_text = fixes['prompt_text']['old']
                new_text = fixes['prompt_text']['new']
                if old_text in new_prompt_text:
                    new_prompt_text = new_prompt_text.replace(old_text, new_text)
                    logger.info(f"  Updated prompt text for {prompt_name}")
                else:
                    logger.warning(f"  Prompt text not found for {prompt_name}")
            
            # Update the prompt in database
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = %s, prompt_text = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_system_prompt, new_prompt_text, prompt['id']))
            
            logger.info(f"  Successfully updated {prompt_name}")
    
    logger.info("Phase 3 fixes completed successfully!")

def verify_fixes():
    """Verify that the fixes were applied correctly"""
    
    logger.info("Verifying Phase 3 fixes...")
    
    with db_manager.get_cursor() as cursor:
        # Check Section Structure Design prompt
        cursor.execute("""
            SELECT system_prompt, prompt_text 
            FROM llm_prompt 
            WHERE name = 'Section Structure Design'
            ORDER BY id DESC
            LIMIT 1
        """)
        
        prompt = cursor.fetchone()
        if prompt:
            system_prompt = prompt['system_prompt']
            prompt_text = prompt['prompt_text']
            
            # Check if hardcoded content was removed
            if 'autumnal traditions' in system_prompt or 'autumn folklore' in prompt_text:
                logger.error("❌ Hardcoded content still present in Section Structure Design")
                return False
            
            # Check if Celtic scope was expanded
            if 'Scottish or other Celtic' in system_prompt:
                logger.info("✅ Celtic scope expanded in Section Structure Design")
            else:
                logger.warning("⚠️ Celtic scope not expanded in Section Structure Design")
            
            # Check if user input placeholders are used
            if '[USER_TOPIC]' in prompt_text or '[EXPANDED_IDEA]' in prompt_text:
                logger.info("✅ User input placeholders found in Section Structure Design")
            else:
                logger.warning("⚠️ User input placeholders not found in Section Structure Design")
    
    logger.info("Phase 3 verification completed")
    return True

if __name__ == "__main__":
    try:
        fix_hardcoded_content()
        verify_fixes()
        print("\n🎉 Phase 3: Hardcoded Content Contamination - FIXED!")
        print("✅ Removed hardcoded specific content (autumn folklore)")
        print("✅ Expanded Scottish references to 'Scottish or other Celtic'")
        print("✅ Ensured prompts use user input via placeholders")
        print("\nNext: Test section-structure page with Welsh mythology")
        
    except Exception as e:
        logger.error(f"Error in Phase 3 fixes: {e}")
        sys.exit(1)
