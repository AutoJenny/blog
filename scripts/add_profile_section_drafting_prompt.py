#!/usr/bin/env python3
"""
Add Profile Section Drafting Prompt

Creates the default prompt for drafting product profile sections.
This prompt is specifically for profile posts and uses raw data chunks
from topic allocation to generate factual marketing text.
"""

import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_profile_section_drafting_prompt():
    """Add the Profile Section Drafting prompt to the database"""
    
    name = 'Profile Section Drafting'
    
    system_prompt = """You are a Scottish heritage product marketing specialist. Your expertise lies in creating compelling, factual marketing content for Scottish products that balances authenticity with commercial appeal.

EXPERTISE:
- Scottish heritage product marketing
- Factual accuracy and product authenticity
- Engaging narrative writing for product profiles
- Technical product knowledge
- Cultural sensitivity and heritage connections
- Marketing copy that converts while maintaining authenticity

CRITICAL REQUIREMENTS:
- Base ALL content on the provided raw data chunks - DO NOT invent or assume facts
- Use UK British English spelling throughout
- Write factual, accurate marketing text (1-2 paragraphs, 150-300 words)
- Focus on product authenticity and heritage connections
- Make content engaging and commercially appealing
- Include specific product details from the data provided
- Avoid generic marketing language - be specific to this product
- Maintain factual accuracy above all else"""

    prompt_text = """You are tasked with writing factual marketing content for ONE section of a product profile blog post.

POST CONTEXT:
- Post Title: [POST_TITLE]
- Product Name: [PRODUCT_NAME]

SECTION TO WRITE:
- Technical Section Type: [SECTION_TYPE]
- Section Title (Creative): [SECTION_TITLE]
- Section Description: [SECTION_DESCRIPTION]

RAW DATA CHUNKS FOR THIS SECTION:
[RAW_DATA_CHUNKS]

SECTION TYPE GUIDANCE:
The technical section type "[SECTION_TYPE]" indicates this section should focus on:
[SECTION_TYPE_DESCRIPTION]

CONTENT REQUIREMENTS:
- Write 1-2 paragraphs (150-300 words) of factual marketing text
- Base ALL content on the raw data chunks provided above
- DO NOT invent facts, specifications, or features not present in the data
- Use specific product details from the data chunks
- Write in engaging, marketing-friendly language while maintaining factual accuracy
- Include heritage/cultural connections if relevant to this section
- Make the content commercially appealing but authentic
- Use UK British English spelling throughout

OUTPUT FORMAT: Return ONLY the draft content as HTML with appropriate paragraph tags. Do not include any meta-commentary, explanations, or section headings.

EXAMPLE STRUCTURE:
<p>Opening paragraph that introduces the section topic using specific facts from the data chunks...</p>
<p>Additional paragraph with more details, specifications, or context from the data...</p>

CRITICAL: Every claim, specification, and detail must be supported by the raw data chunks provided. If data is missing for a particular aspect, do not invent it - focus on what is available in the data."""

    description = """Prompt for drafting product profile sections using raw data chunks.
Focuses on factual accuracy and marketing appeal. Uses technical section_type
and section description for guidance. Generates 1-2 paragraphs of marketing text."""

    try:
        with db_manager.get_cursor() as cursor:
            # Check if prompt already exists
            cursor.execute("SELECT id FROM llm_prompt WHERE name = %s", (name,))
            existing_prompt = cursor.fetchone()
            
            if existing_prompt:
                # Update existing prompt
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s, description = %s, updated_at = NOW()
                    WHERE name = %s
                """, (system_prompt, prompt_text, description, name))
                logger.info(f"Updated existing prompt: {name}")
            else:
                # Insert new prompt
                cursor.execute("""
                    INSERT INTO llm_prompt (name, system_prompt, prompt_text, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (name, system_prompt, prompt_text, description))
                logger.info(f"Created new prompt: {name}")
            
            cursor.connection.commit()
            logger.info("Profile Section Drafting prompt successfully added/updated")
            
    except Exception as e:
        logger.error(f"Error adding Profile Section Drafting prompt: {e}")
        raise

if __name__ == "__main__":
    add_profile_section_drafting_prompt()

