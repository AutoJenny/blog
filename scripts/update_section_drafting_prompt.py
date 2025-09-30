#!/usr/bin/env python3
"""
Update the Section Drafting prompt to use rich context data and improved structure.
This prompt is designed for generating individual section drafts with comprehensive context awareness.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_section_drafting_prompt():
    """Update the Section Drafting prompt with improved context awareness"""
    
    db_manager = DatabaseManager()
    
    # Define the improved prompt
    name = 'Section Drafting'
    
    system_prompt = """You are a Scottish heritage content specialist and engaging blog writer. Your expertise lies in creating compelling, authentic content that resonates with audiences interested in Scottish culture, history, and traditions.

EXPERTISE:
- Scottish heritage and cultural authenticity
- Engaging narrative writing for heritage audiences
- Compelling storytelling that captures Scottish essence
- Historical accuracy and cultural sensitivity
- Reader engagement through evocative language
- Avoiding repetition and maintaining content uniqueness

CRITICAL REQUIREMENTS:
- Create engaging, authentic content that evokes Scottish heritage
- Use authentic Scottish terminology and references where appropriate
- Ensure content is unique and avoids repetition with other sections
- Make content accessible to both Scottish and international audiences
- Focus on engagement, authenticity, and cultural significance
- Write in a warm, engaging tone that draws readers in
- Include specific details, stories, and cultural context
- Avoid generic or bland content that could apply to any topic"""

    prompt_text = """You are tasked with writing a compelling draft for ONE section of a blog post about Scottish autumn folklore and traditions. You have full context of the entire post to ensure uniqueness and avoid repetition.

POST THEME: [SELECTED_IDEA]

SECTION TO WRITE:
Title: [SECTION_TITLE]
Subtitle: [SECTION_SUBTITLE]
Group: [SECTION_GROUP]
Purpose: [GROUP_SUMMARY]
Topics to Cover: [SECTION_TOPICS]

CRITICAL AVOIDANCE REQUIREMENTS:
DO NOT INCLUDE ANY OF THE FOLLOWING TOPICS (covered in other sections):
[AVOID_SECTIONS_DETAILED]

CONTENT REQUIREMENTS:
- Write exactly 200 words of engaging, authentic content
- Focus ONLY on the [SECTION_GROUP] topics listed above
- Use authentic Scottish terminology and cultural references
- Include specific details, stories, or historical context
- Write in a warm, engaging tone that draws readers in
- Ensure content flows naturally and is easy to read
- Make content accessible to both Scottish and international audiences
- STRICTLY AVOID any topics listed in the avoidance section above
- Ensure content is unique and doesn't overlap with other sections

OUTPUT FORMAT: Return ONLY the draft content as HTML with appropriate paragraph tags. Do not include any meta-commentary or explanations.

EXAMPLE STRUCTURE:
<p>Opening paragraph that hooks the reader and introduces the section topic...</p>
<p>Main content paragraph with specific details and cultural context...</p>
<p>Concluding paragraph that ties back to Scottish heritage significance...</p>"""

    try:
        with db_manager.get_cursor() as cursor:
            # Check if prompt exists
            cursor.execute("SELECT id FROM llm_prompt WHERE name = %s", (name,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing prompt
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s, updated_at = NOW()
                    WHERE name = %s
                """, (system_prompt, prompt_text, name))
                logger.info(f"Updated existing prompt: {name}")
            else:
                # Insert new prompt
                cursor.execute("""
                    INSERT INTO llm_prompt (name, system_prompt, prompt_text, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                """, (name, system_prompt, prompt_text))
                logger.info(f"Created new prompt: {name}")
            
            cursor.connection.commit()
            logger.info("Section Drafting prompt updated successfully!")
            
    except Exception as e:
        logger.error(f"Error updating Section Drafting prompt: {e}")
        raise

if __name__ == "__main__":
    update_section_drafting_prompt()
