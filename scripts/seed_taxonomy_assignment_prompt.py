#!/usr/bin/env python3
"""
Seed Taxonomy Assignment LLM Prompt

Creates the LLM prompt for taxonomy assignment in the database
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def seed_taxonomy_prompt():
    """Seed the Taxonomy Assignment prompt in the database"""
    
    system_prompt = """You are a content classification expert specializing in Scottish heritage and culture. Your task is to analyze blog post concepts and select the most appropriate taxonomy classification based on the content's theme, type, and format.

Your selections must be precise and well-reasoned:
- Theme: Choose the top-level thematic grouping that best fits the content
- Content Type: Select the specific content category that belongs to the chosen theme (CRITICAL: the content type MUST belong to the selected theme)
- Format: Choose the format that best suits how this content will be presented

Return ONLY valid JSON with your selections and brief reasoning."""

    prompt_text = """Based on the expanded idea provided, select the most appropriate taxonomy classification.

EXPANDED IDEA:
{expanded_idea}

AVAILABLE THEMES:
{themes_list}

AVAILABLE CONTENT TYPES:
{content_types_list}

AVAILABLE FORMATS:
{formats_list}

CRITICAL REQUIREMENTS:
1. You MUST select exactly one Theme, one Content Type, and one Format
2. The Content Type MUST belong to the selected Theme (check the parent_id/theme relationship)
3. Consider the content's primary focus when selecting:
   - Heritage & History: Historical events, clan stories, myths, traditions
   - Culture & Life: Modern celebrations, craftspeople, products
   - Scotland & Nature: Landscapes, seasons, tartans, textiles
4. Choose Format based on how the content will be presented (Article is most common for long-form)
5. Return ONLY valid JSON in this exact format:
{{
  "theme_id": <integer>,
  "content_type_id": <integer>,
  "format_id": <integer>,
  "reasoning": "<ONE brief sentence explaining your selections - keep it SHORT>"
}}

Return only the JSON object, no other text or markdown formatting."""

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if prompt already exists
                cursor.execute("""
                    SELECT id, name FROM llm_prompt WHERE name = 'Taxonomy Assignment'
                """)
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing prompt
                    cursor.execute("""
                        UPDATE llm_prompt
                        SET system_prompt = %s,
                            prompt_text = %s,
                            updated_at = NOW()
                        WHERE name = 'Taxonomy Assignment'
                    """, (system_prompt, prompt_text))
                    print(f"Updated prompt: Taxonomy Assignment (ID: {existing['id']})")
                else:
                    # Insert new prompt
                    cursor.execute("""
                        INSERT INTO llm_prompt (name, system_prompt, prompt_text, created_at, updated_at)
                        VALUES ('Taxonomy Assignment', %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (system_prompt, prompt_text))
                    result = cursor.fetchone()
                    print(f"Created prompt: Taxonomy Assignment (ID: {result['id']})")
                
                conn.commit()
                print("Prompt update successful!")
                
    except Exception as e:
        print(f"Error seeding taxonomy prompt: {e}")
        sys.exit(1)

if __name__ == '__main__':
    seed_taxonomy_prompt()

