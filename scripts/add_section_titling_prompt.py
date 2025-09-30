#!/usr/bin/env python3
"""
Add Section Titling prompt to the database
This prompt takes grouped topics and creates engaging titles and subtitles for Scottish heritage audiences
"""

import psycopg2
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def add_section_titling_prompt():
    """Add or update the Section Titling prompt"""
    
    # Connect to database
    conn = psycopg2.connect(**Config.get_database_config())
    cursor = conn.cursor()
    
    try:
        # Check if prompt already exists
        cursor.execute("SELECT id FROM llm_prompt WHERE name = %s", ('Section Titling',))
        existing_prompt = cursor.fetchone()
        
        # System prompt for Scottish heritage content creation
        system_prompt = """You are a Scottish heritage content specialist and engaging blog writer. Your expertise lies in creating compelling, authentic titles and descriptions that resonate with audiences interested in Scottish culture, history, and traditions.

EXPERTISE:
- Scottish heritage and cultural authenticity
- Engaging title creation for heritage audiences
- Compelling descriptions that capture Scottish essence
- Historical accuracy and cultural sensitivity
- Reader engagement through evocative language

CRITICAL REQUIREMENTS:
- Create titles that evoke Scottish heritage and cultural pride
- Use authentic Scottish terminology and references where appropriate
- Ensure descriptions capture the essence and importance of each section
- Make content accessible to both Scottish and international audiences
- Focus on engagement, authenticity, and cultural significance"""

        # Main prompt text
        prompt_text = """Given these thematic groups about [EXPANDED_IDEA], create engaging titles and descriptions for each section that will captivate Scottish heritage enthusiasts and general readers interested in Scottish culture.

THEMATIC GROUPS TO TITLE:
[GROUPS_DATA]

REQUIREMENTS:
- Create compelling titles that evoke Scottish heritage and cultural significance
- Write descriptions that explain what each section covers and why it matters
- Use authentic Scottish terminology and cultural references where appropriate
- Make content accessible to both Scottish and international audiences
- Focus on the cultural importance and historical significance of each theme

OUTPUT FORMAT: Return ONLY valid JSON:
{
  "sections": [
    {
      "id": "section_1",
      "title": "Engaging Scottish Heritage Title",
      "subtitle": "Compelling subtitle that adds depth",
      "description": "Detailed description of what this section covers and its cultural significance",
      "topics": ["Topic 1", "Topic 2", ...],
      "order": 1,
      "cultural_significance": "Brief explanation of why this theme matters to Scottish heritage"
    }
  ],
  "metadata": {
    "total_sections": [SECTION_COUNT],
    "total_topics": [TOTAL_TOPICS],
    "allocated_topics": [TOTAL_TOPICS],
    "audience_focus": "Scottish heritage enthusiasts and cultural readers"
  }
}

TITLE GUIDELINES:
- Use evocative language that captures Scottish spirit
- Include cultural references where appropriate (e.g., "Celtic", "Highland", "Ancient Scottish")
- Make titles accessible to international audiences
- Avoid overly academic or dry language
- Focus on emotional connection and cultural pride

DESCRIPTION GUIDELINES:
- Explain what readers will learn in this section
- Highlight the cultural and historical significance
- Connect themes to broader Scottish heritage
- Use engaging, accessible language
- Include why this content matters to Scottish culture"""

        if existing_prompt:
            # Update existing prompt
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = %s, prompt_text = %s, updated_at = NOW()
                WHERE id = %s
            """, (system_prompt, prompt_text, existing_prompt[0]))
            print(f"Updated existing Section Titling prompt (ID: {existing_prompt[0]})")
        else:
            # Insert new prompt
            cursor.execute("""
                INSERT INTO llm_prompt (name, description, system_prompt, prompt_text, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (
                'Section Titling',
                'Creates engaging titles and descriptions for grouped topics, specifically designed for Scottish heritage audiences',
                system_prompt,
                prompt_text
            ))
            print("Added new Section Titling prompt")
        
        # Commit changes
        conn.commit()
        print("Section Titling prompt successfully saved to database")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_section_titling_prompt()
