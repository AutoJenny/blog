#!/usr/bin/env python3
"""
Script to update the Section Planning prompt with two-stage approach
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager

def update_section_planning_prompt():
    """Update the Section Planning prompt with improved two-stage approach"""
    
    prompt_data = {
        'name': 'Section Planning',
        'system_prompt': '''You are a blog structure expert specializing in organizing topics into coherent, engaging sections. Your role is to analyze topic lists and create logical, flowing blog structures.

EXPERTISE:
- Content organization and flow
- Section titling and description
- Topic clustering and allocation
- Reader engagement optimization
- Logical progression and narrative flow

CRITICAL REQUIREMENTS:
- Create exactly 6-8 sections (flexible range)
- Every topic must be allocated to exactly one section
- Use ONLY the topics provided - do not create, modify, or invent topics
- Create compelling section titles that reflect content
- Ensure logical flow between sections''',
        
        'prompt_text': '''Given these topics about [EXPANDED_IDEA], group them into exactly [SECTION_COUNT] thematic sections.

PROCESS:
1. Identify natural topic clusters (6-8 groups)
2. Name each cluster thematically
3. Order clusters for logical flow
4. Ensure every topic is allocated exactly once

OUTPUT FORMAT:
{
  "sections": [
    {
      "id": "intro",
      "title": "Introduction to Scottish Autumn Traditions",
      "description": "Overview of Scotland's autumn heritage and cultural significance",
      "topics": ["Topic 1", "Topic 2", ...],
      "order": 1
    }
  ],
  "metadata": {
    "total_sections": [SECTION_COUNT],
    "total_topics": [TOTAL_TOPICS],
    "allocated_topics": [TOTAL_TOPICS],
    "flow_type": "chronological"
  }
}

VALIDATION REQUIREMENTS:
- Must have exactly [SECTION_COUNT] sections
- All [TOTAL_TOPICS] topics must be allocated
- No duplicate topic allocations
- Section order must follow logical flow'''
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
            print("✅ Section Planning prompt updated successfully!")
            
    except Exception as e:
        print(f"❌ Error updating Section Planning prompt: {e}")

if __name__ == '__main__':
    update_section_planning_prompt()
