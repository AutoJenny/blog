#!/usr/bin/env python3
"""
Add Product Profile Section Structure Prompt

Creates the default prompt for product profile section structure design.
This prompt is specifically for profile posts (product profiles).
"""

import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_product_profile_section_structure_prompt():
    """Add the Product Profile Section Structure prompt to the database"""
    
    name = 'Product Profile Section Structure'
    
    system_prompt = """You are a blog structure specialist. Design an 8-section product profile blog post structure.

CRITICAL CONTEXT:
- You are generating a section structure for POST ID {post_id}
- POST TITLE: {post_title}
- PRODUCT: {product_name}
- PRODUCT ID: {product_id}

This structure is SPECIFICALLY for this post and product. Do not use any other context.

CONSTRAINTS:
- Create exactly 8 sections
- 6 required sections: Hero Block, The Object/In Context (combined), Features & Specifications, Materials & Making/The Maker (combined), Care & Maintenance, Explore Further
- 2 optional sections: Heritage & Origins (if heritage data available), Gallery (always provisional)
- Each section should have a clear purpose and flow
- Sections should build logically from introduction to conclusion
- Use the provided product data to inform section content

REQUIRED SECTION TYPES (MUST USE EXACTLY THESE VALUES):
1. "profile_hero" - Hero Block (Required)
2. "profile_object_context" - The Object / In Context (Required, Combined Section)
3. "profile_features" - Features & Specifications (Required)
4. "profile_heritage" - Heritage & Origins (Optional)
5. "profile_materials_maker" - Materials & Making / The Maker (Required, Combined Section - The Maker content is optional within this section)
6. "profile_care" - Care & Maintenance (Required)
7. "profile_gallery" - Gallery (Optional, Provisional)
8. "profile_explore" - Explore Further (Required, Final Section)

OUTPUT:
- STRICT JSON ONLY - NO MARKDOWN, NO CODE BLOCKS, NO EXPLANATORY TEXT
- Start your response with {{ and end with }}
- Exactly 11 sections with clear purposes
- Return ONLY the JSON object, nothing before or after
- Each section must include: section_code, section_type (MUST be one of the 11 types above), title, description, optional (boolean), provisional (boolean), data_sources (array), conditional_logic (string or null)

FORMAT:
{{
  "sections": [
    {{ "section_code": "S01", "section_type": "profile_hero", "title": "Hero Block", "description": "...", "optional": false, "provisional": false, "data_sources": ["product_data.name", "product_data.image_url"], "conditional_logic": null }},
    {{ "section_code": "S02", "section_type": "profile_object_context", "title": "The Object / In Context", "description": "Combined section covering product concept, design, distinctive qualities, usage, occasions, styling, and cultural fit", "optional": false, "provisional": false, "data_sources": ["product_data.description", "product_data.product_type_data.occasions"], "conditional_logic": null }},
    {{ "section_code": "S03", "section_type": "profile_features", "title": "Features & Specifications", "description": "...", "optional": false, "provisional": false, "data_sources": ["product_data.specifications", "product_data.configurable_options"], "conditional_logic": null }},
    {{ "section_code": "S04", "section_type": "profile_heritage", "title": "Heritage & Origins", "description": "...", "optional": true, "provisional": false, "data_sources": ["product_data.heritage_data", "category_heritage"], "conditional_logic": "Include if heritage data available" }},
    {{ "section_code": "S05", "section_type": "profile_materials_maker", "title": "Materials & Making / The Maker", "description": "Combined section covering materials, processes, craftsmanship, and producer/workshop story. The Maker content is optional within this section if supplier data is available.", "optional": false, "provisional": false, "data_sources": ["product_data.product_type_data.materials", "product_data.supplier_name"], "conditional_logic": "Section is always required; The Maker content within it is optional if supplier data exists" }},
    {{ "section_code": "S06", "section_type": "profile_care", "title": "Care & Maintenance", "description": "...", "optional": false, "provisional": false, "data_sources": ["product_data.product_type_data"], "conditional_logic": null }},
    {{ "section_code": "S07", "section_type": "profile_gallery", "title": "Gallery", "description": "...", "optional": true, "provisional": true, "data_sources": ["product_data.image_url"], "conditional_logic": "Provisional - depends on image availability" }},
    {{ "section_code": "S08", "section_type": "profile_explore", "title": "Explore Further", "description": "...", "optional": false, "provisional": false, "data_sources": ["product_data.url"], "conditional_logic": null }}
  ]
}}

CRITICAL: Your response must be valid JSON that can be parsed directly. Do not wrap it in markdown code blocks or add any explanatory text. You MUST include all 8 sections with the exact section_type values listed above."""

    prompt_text = """Design an 8-section product profile blog structure for this SPECIFIC post and product.

POST CONTEXT:
- Post ID: {post_id}
- Post Title: {post_title}
- Product: {product_name}
- Product ID: {product_id}

PRODUCT DATA:
{product_data_summary}

STANDARD PRODUCT PROFILE SECTIONS (8 total - MUST USE EXACT section_type VALUES):
1. "profile_hero" - Hero Block (Required) - Visual introduction with headline and standfirst
2. "profile_object_context" - The Object / In Context (Required, Combined) - Product concept, design, distinctive qualities, usage, occasions, styling, and cultural fit
3. "profile_features" - Features & Specifications (Required) - Features, options, technical details
4. "profile_heritage" - Heritage & Origins (Optional) - Historical context if heritage data exists
5. "profile_materials_maker" - Materials & Making / The Maker (Required, Combined) - Materials, processes, craftsmanship, and producer/workshop story. The Maker content is optional within this section if supplier data is available, but the section itself is always required.
6. "profile_care" - Care & Maintenance (Required) - Care instructions, cleaning, storage
7. "profile_gallery" - Gallery (Optional, Provisional) - Visual showcase (depends on image availability)
8. "profile_explore" - Explore Further (Required, Final Section) - Commerce links

COMBINED SECTIONS EXPLANATION:
- "profile_object_context": Combines "The Object" (product concept, design, distinctive qualities) with "In Context" (usage, occasions, styling, cultural fit) into a single comprehensive section
- "profile_materials_maker": Combines "Materials & Making" (materials, processes, craftsmanship) with "The Maker" (producer/workshop story). The section is always required, but The Maker content within it is optional if supplier data exists.

VALIDATION RULES:
- Create exactly 8 sections
- Use EXACT section_type values listed above
- Mark optional sections with "optional": true
- Mark Gallery as both "optional": true and "provisional": true
- Each section needs: section_code, section_type (MUST match one of the 8 types above), title, description, optional, provisional, data_sources, conditional_logic
- Output STRICT JSON ONLY - NO MARKDOWN CODE BLOCKS, NO EXPLANATORY TEXT
- Start response with {{ and end with }}
- Return ONLY the JSON object, nothing before or after

REQUIRED SECTION TYPES (ALL MUST BE PRESENT):
- profile_hero (required)
- profile_object_context (required, combined)
- profile_features (required)
- profile_materials_maker (required, combined - Maker content optional within section)
- profile_care (required)
- profile_explore (required, final section)
- profile_heritage (optional)
- profile_gallery (optional, provisional)

CRITICAL: Your response must be valid JSON that can be parsed directly. Do not wrap it in ```json code blocks or add any explanatory text. You MUST include all 8 sections with the exact section_type values listed above."""

    description = """Prompt for designing 8-section product profile blog post structures. 
Includes 6 required sections and 2 optional sections (Heritage & Origins, Gallery).
Combined sections: The Object/In Context, Materials & Making/The Maker.
Explicitly identifies post and product in context to prevent data leakage."""

    try:
        with db_manager.get_cursor() as cursor:
            # Check if prompt already exists
            cursor.execute("""
                SELECT id FROM llm_prompt 
                WHERE name = %s
            """, (name,))
            
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"Prompt '{name}' already exists with ID {existing['id']}")
                # Update existing prompt
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s, description = %s, updated_at = NOW()
                    WHERE id = %s
                """, (system_prompt, prompt_text, description, existing['id']))
                logger.info(f"Updated existing prompt with ID {existing['id']}")
            else:
                # Insert new prompt
                cursor.execute("""
                    INSERT INTO llm_prompt (name, system_prompt, prompt_text, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (name, system_prompt, prompt_text, description))
                
                # Get the ID of the inserted record
                cursor.execute("""
                    SELECT id FROM llm_prompt 
                    WHERE name = %s 
                    ORDER BY id DESC 
                    LIMIT 1
                """, (name,))
                
                result = cursor.fetchone()
                logger.info(f"Created new prompt '{name}' with ID {result['id']}")
            
            cursor.connection.commit()
            logger.info("Product Profile Section Structure prompt added successfully!")
            
    except Exception as e:
        logger.error(f"Error adding Product Profile Section Structure prompt: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True

if __name__ == '__main__':
    success = add_product_profile_section_structure_prompt()
    sys.exit(0 if success else 1)

