#!/usr/bin/env python3
"""
Script to add the Section Planning prompt to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import DatabaseManager

def add_section_planning_prompt():
    """Add the Section Planning prompt to the database"""
    
    db_manager = DatabaseManager()
    
    prompt_data = {
        'name': 'Section Planning',
        'system_prompt': '''You are an expert content strategist specializing in organizing topics into coherent, engaging sections for blog posts. Your role is to analyze a list of topics and group them into logical sections that create a compelling narrative flow.

Key principles:
- Create sections that build upon each other logically
- Ensure each section has a clear theme and purpose
- Distribute topics evenly across sections
- Consider the reader's journey and learning progression
- Maintain thematic coherence within each section''',
        
        'prompt_text': '''Given the following topics, organize them into [SECTION_COUNT] sections using a [SECTION_STYLE] approach.

Topics to organize:
[TOPICS]

Please provide your response in the following format:

Section 1: [Section Title]
[Brief description of what this section covers]

- Topic 1
- Topic 2
- Topic 3

Section 2: [Section Title]
[Brief description of what this section covers]

- Topic 1
- Topic 2
- Topic 3

[Continue for all sections]

Make sure each section has a clear theme and that topics are logically grouped together. Each section should have between 3-8 topics depending on the total number of topics and sections.'''
    }
    
    try:
        with db_manager.get_cursor() as cursor:
            # Check if prompt already exists
            cursor.execute("""
                SELECT id FROM llm_prompt 
                WHERE name = %s
            """, (prompt_data['name'],))
            
            existing = cursor.fetchone()
            
            if existing:
                print(f"Prompt '{prompt_data['name']}' already exists with ID {existing['id']}")
                # Update existing prompt
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s, updated_at = NOW()
                    WHERE id = %s
                """, (prompt_data['system_prompt'], prompt_data['prompt_text'], existing['id']))
                print(f"Updated existing prompt with ID {existing['id']}")
            else:
                # Insert new prompt (let the database handle the ID)
                cursor.execute("""
                    INSERT INTO llm_prompt (name, system_prompt, prompt_text, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                """, (prompt_data['name'], prompt_data['system_prompt'], prompt_data['prompt_text']))
                
                # Get the ID of the inserted record
                cursor.execute("""
                    SELECT id FROM llm_prompt 
                    WHERE name = %s 
                    ORDER BY id DESC 
                    LIMIT 1
                """, (prompt_data['name'],))
                
                result = cursor.fetchone()
                print(f"Created new prompt '{prompt_data['name']}' with ID {result['id']}")
            
            cursor.connection.commit()
            print("Section Planning prompt added successfully!")
            
    except Exception as e:
        print(f"Error adding Section Planning prompt: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = add_section_planning_prompt()
    if success:
        print("✅ Section Planning prompt setup completed successfully!")
    else:
        print("❌ Failed to setup Section Planning prompt")
        sys.exit(1)
