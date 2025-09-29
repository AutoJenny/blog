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
        'system_prompt': '''You are an expert content strategist specializing in organizing blog topics into coherent, engaging sections. Your role is to analyze a list of topics and group them into exactly 6-8 logical sections that create a compelling narrative flow.

CRITICAL REQUIREMENTS:
- Create exactly 6-8 sections (no more, no less)
- Every single topic must be allocated to exactly one section (NO DUPLICATES)
- Use ONLY the topics provided in the input list - do not create, modify, or invent topics
- Each topic must appear in exactly one section only
- Determine the optimal section order for reader engagement
- Balance section sizes (aim for 6-8 topics per section)
- Create compelling section titles that reflect the content
- Force topics into the closest fit if they don't align perfectly

OUTPUT FORMAT: Return ONLY valid JSON, no additional text or commentary.

OPTIMAL ORDERING GUIDANCE:
1. Start with introduction/overview sections
2. Build complexity through historical/background sections
3. Progress to detailed analysis and examples
4. Conclude with contemporary relevance and future implications
5. Ensure logical flow between sections for reader engagement''',
        
        'prompt_text': '''Given the expanded blog concept: [EXPANDED_IDEA]

And these generated topics: [TOPICS]

Organize these topics into exactly [SECTION_COUNT] sections using a [SECTION_STYLE] approach.

CRITICAL REQUIREMENTS:
- Create exactly [SECTION_COUNT] sections (enforced)
- Each topic must be allocated to EXACTLY ONE section only (no duplicates, no exceptions)
- Every topic from the input list must be used exactly once
- Do not create, modify, or invent new topics - use only the provided topics
- Determine optimal section order for reader engagement
- Balance section sizes (aim for 6-8 topics per section)
- Create compelling section titles that reflect the content
- Ensure logical flow and progression between sections

OPTIMAL ORDERING STRATEGY:
1. Introduction/Overview: Start with broad context and significance
2. Historical Foundation: Build understanding of origins and development
3. Core Themes: Explore main concepts and practices
4. Detailed Analysis: Deep dive into specific aspects and examples
5. Modern Context: Connect to contemporary relevance
6. Conclusion/Synthesis: Tie together themes and implications

OUTPUT FORMAT: Return ONLY valid JSON in this exact structure:
{
  "section_headings": ["Section 1 Title", "Section 2 Title", ...],
  "sections": [
    {
      "id": "section_1",
      "title": "Section 1 Title", 
      "description": "Brief description of what this section covers",
      "topics": ["Topic 1", "Topic 2", ...],
      "order": 1
    }
  ],
  "metadata": {
    "total_sections": [SECTION_COUNT],
    "total_topics": [TOTAL_TOPICS],
    "allocated_topics": [TOTAL_TOPICS],
    "style": "[SECTION_STYLE]",
    "generated_at": "[TIMESTAMP]"
  }
}

VALIDATION REQUIREMENTS:
- Must have exactly [SECTION_COUNT] sections
- All [TOTAL_TOPICS] topics must be allocated
- No duplicate topic allocations
- Section order must follow optimal flow guidance'''
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
