#!/usr/bin/env python3
"""
Script to update the Topic Brainstorming prompt for consistent JSON output
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager

def update_topic_brainstorming_prompt():
    """Update the Topic Brainstorming prompt for better JSON consistency"""
    
    prompt_data = {
        'name': 'Topic Brainstorming',
        'system_prompt': '''You are a content strategist specializing in Scottish topics. Generate diverse, specific topic ideas that can be logically grouped into blog sections.

Your expertise includes:
- Scottish history, culture, and traditions
- Content variety (historical, cultural, practical, contemporary, quirky)
- Topic clustering and thematic organization
- Consistent JSON output formatting''',
        
        'prompt_text': '''Generate exactly 50 distinct topic ideas about [EXPANDED_IDEA].

REQUIREMENTS:
- Each topic: 5-8 words maximum
- Include variety: historical, cultural, practical, contemporary, quirky
- Ensure topics can be grouped into 6-8 thematic sections
- Return ONLY: ["Topic 1", "Topic 2", ...] (no numbering, no explanations)

VALIDATION: Count topics, check length, ensure uniqueness

OUTPUT FORMAT: Return ONLY a valid JSON array of strings, no additional text.'''
    }
    
    try:
        with db_manager.get_cursor() as cursor:
            # Check if prompt already exists by name
            cursor.execute("""
                SELECT id FROM llm_prompt
                WHERE name = %s
            """, (prompt_data['name'],))
            
            existing = cursor.fetchone()
            
            if existing:
                print(f"Updating existing prompt '{prompt_data['name']}' with ID {existing['id']}")
                # Update existing prompt
                cursor.execute("""
                    UPDATE llm_prompt
                    SET system_prompt = %s, prompt_text = %s, updated_at = NOW()
                    WHERE id = %s
                """, (prompt_data['system_prompt'], prompt_data['prompt_text'], existing['id']))
            else:
                print(f"Creating new prompt '{prompt_data['name']}'")
                # Insert new prompt
                cursor.execute("""
                    INSERT INTO llm_prompt (name, system_prompt, prompt_text, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                """, (prompt_data['name'], prompt_data['system_prompt'], prompt_data['prompt_text']))
            
            cursor.connection.commit()
            print("✅ Topic Brainstorming prompt updated successfully!")
            
    except Exception as e:
        print(f"❌ Error updating Topic Brainstorming prompt: {e}")

if __name__ == '__main__':
    update_topic_brainstorming_prompt()
