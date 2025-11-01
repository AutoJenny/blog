#!/usr/bin/env python3
"""
Script to update the Idea Expansion prompt for Scottish/Celtic focus and Important Notes support
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager

def update_idea_expansion_prompt():
    """Update the Idea Expansion prompt"""
    
    new_prompt_text = """[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.

[system] Expand the following Selected Theme into a focused, concise paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language and keep it tightly focused.

Selected Theme:
[theme_data]

CRITICAL REQUIREMENTS:
1. You MUST focus exclusively on characteristically Scottish and/or Celtic cultural and historical aspects. This blog is specifically about Scotland, its heritage, traditions, and cultural identity. Every idea must connect to distinctly Scottish or Celtic themes.
2. You MUST incorporate ALL the information provided in the Selected Theme above, including the Title and Description. These are essential context that must be included.
3. **ABSOLUTELY CRITICAL - MANDATORY**: If Important Notes are marked with "=== CRITICAL: IMPORTANT NOTES ===" above, you MUST explicitly include EACH AND EVERY one of these in your expanded idea. Each Important Note represents a specific topic, theme, or point that MUST appear in your response. You cannot simply allude to these topics - you must explicitly mention and incorporate each one. Each Important Note is mandatory and non-negotiable - you must address every single point listed. DO NOT omit, skip, or gloss over any Important Note. If the Important Note says "Mention X", you MUST explicitly mention X in your expanded idea.
4. Maintain academic accuracy while being accessible to a general audience.
5. Suggest clear, focused angles and themes for development - avoid broad or generic topics that could apply anywhere.
6. Keep the expanded idea concise and focused - aim for 3-4 sentences maximum.
7. Use UK-British spellings and idioms.
8. Return only the expanded brief, with no additional commentary or formatting"""
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Find the prompt
                cursor.execute("""
                    SELECT id, name 
                    FROM llm_prompt 
                    WHERE name ILIKE '%idea%expansion%' OR name ILIKE '%scottish%idea%'
                    ORDER BY id DESC
                    LIMIT 1
                """)
                prompt = cursor.fetchone()
                
                if prompt:
                    # Update existing prompt
                    cursor.execute("""
                        UPDATE llm_prompt 
                        SET prompt_text = %s, updated_at = %s
                        WHERE id = %s
                    """, (new_prompt_text, datetime.now(), prompt['id']))
                    print(f"Updated prompt: {prompt['name']} (ID: {prompt['id']})")
                else:
                    # Create new prompt
                    cursor.execute("""
                        INSERT INTO llm_prompt (name, prompt_text, prompt_type, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, ('Scottish Idea Expansion', new_prompt_text, 'task', datetime.now(), datetime.now()))
                    print("Created new prompt: Scottish Idea Expansion")
                
                conn.commit()
                print("Prompt update successful!")
                
    except Exception as e:
        print(f"Error updating prompt: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    update_idea_expansion_prompt()

