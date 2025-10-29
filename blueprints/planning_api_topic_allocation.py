"""
Planning Topic Allocation API Module

Micro-file for topic allocation related API endpoints extracted from planning_original_backup_deprecated.py
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def save_topic_allocation(post_id, allocation_data, raw_response=None):
    """Save topic allocation to database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET topic_allocation = %s, allocation_completed_at = NOW()
                WHERE post_id = %s
            """, (json.dumps(allocation_data), post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, topic_allocation, allocation_completed_at, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW(), NOW())
                """, (post_id, json.dumps(allocation_data)))
            
            cursor.connection.commit()
    except Exception as e:
        logger.error(f"Error saving topic allocation: {e}")

def build_section_specific_prompt(post_title, section_title, section_description, all_sections, expanded_idea=None):
    """Build a section-specific brainstorming prompt using positive and negative data"""
    
    # Extract boundaries and exclusions for current section if available
    current_boundaries = ""
    current_exclusions = ""
    current_section_index = None
    for idx, section in enumerate(all_sections):
        # Match by title or theme, handling both formats
        section_match_title = section.get('title') or section.get('theme', '')
        if section_match_title == section_title:
            current_section_index = idx
            if section.get('boundaries'):
                boundaries = section.get('boundaries')
                if isinstance(boundaries, list):
                    current_boundaries = "\n".join([f"- {b}" for b in boundaries if b])
                elif boundaries:
                    current_boundaries = f"- {boundaries}"
            if section.get('exclusions'):
                exclusions = section.get('exclusions')
                if isinstance(exclusions, list):
                    current_exclusions = "\n".join([f"- {e}" for e in exclusions if e])
                elif exclusions:
                    current_exclusions = f"- {exclusions}"
            break
    
    # Build explicit exclusion list from OTHER sections (negative data)
    # This should exclude the current section and include all others
    exclusion_list = []
    exclusion_count = 0
    for i, section in enumerate(all_sections):
        other_title = section.get('title') or section.get('theme', f'Section {i+1}')
        other_desc = section.get('description', '')
        # Use index comparison as primary check, with title as fallback
        if current_section_index is not None:
            is_current_section = (i == current_section_index)
        else:
            is_current_section = (other_title == section_title)
        
        if not is_current_section:
            exclusion_count += 1
            exclusion_list.append(f"{exclusion_count}. \"{other_title}\" - {other_desc}")
    
    exclusion_text = "\n".join(exclusion_list) if exclusion_list else "No other sections defined."
    
    prompt = f"""You are generating topics for EXACTLY ONE section in the blog post "{post_title}".

═══════════════════════════════════════════════════════════════
TARGET SECTION (GENERATE TOPICS FOR THIS - ONLY THIS):
═══════════════════════════════════════════════════════════════
Title: {section_title}
Description: {section_description}
{f"- Boundaries: {current_boundaries}" if current_boundaries else ""}
{f"- Exclusions: {current_exclusions}" if current_exclusions else ""}

═══════════════════════════════════════════════════════════════
FORBIDDEN SECTIONS (DO NOT GENERATE TOPICS FOR THESE):
═══════════════════════════════════════════════════════════════
{exclusion_text}

CRITICAL EXCLUSION RULES - READ CAREFULLY:

TIME-BASED EXCLUSIONS:
- If the target section is about MODERN/CONTEMPORARY themes (e.g., "Contemporary Applications", "Modern Impact", "Enduring Legacy", "Current Relevance"), you MUST NOT generate topics about:
  * Historical origins, ancient roots, traditional foundations, early developments, classical practices
  * Mythological beginnings, pre-modern traditions, archaic customs
  * Topics that belong in sections about "Ancient Foundations", "Historical Origins", "Traditional Roots"
- If the target section is about ANCIENT/HISTORICAL themes (e.g., "Ancient Foundations", "Historical Origins", "Traditional Roots"), you MUST NOT generate topics about:
  * Modern applications, contemporary practices, current relevance, future implications
  * Modern-day impact, 21st-century adaptations, recent developments
  * Topics that belong in sections about "Contemporary Applications", "Modern Impact", "Enduring Legacy"

THEMATIC EXCLUSIONS:
- Read each forbidden section's description carefully
- If your topic mentions themes, concepts, or content described in ANY forbidden section, REJECT it immediately
- Each topic must be thematically IMPOSSIBLE to place in any forbidden section above
- If you cannot determine whether a topic fits ONLY the target section, REJECT it
- Before finalizing EACH of the 6 topics, ask yourself: "Could this topic fit in ANY forbidden section based on its description?" If the answer is YES or UNCERTAIN, REJECT it and generate a different topic

EXAMPLES OF WRONG TOPICS TO GENERATE (Generic Patterns):
- If target section is about modern/contemporary themes and a forbidden section is about ancient/historical themes, DO NOT generate any topic about: historical origins, ancient roots, traditional foundations, early developments
- If target section is about ancient/historical themes and a forbidden section is about modern/contemporary themes, DO NOT generate any topic about: modern applications, contemporary practices, current relevance, recent developments
- ANY topic that relates to themes, concepts, or time periods described in ANY forbidden section is FORBIDDEN, regardless of how interesting or relevant it seems

STRICT REQUIREMENTS:
1. Generate exactly 6 topics
2. Each topic MUST fit EXCLUSIVELY and ONLY within "{section_title}" 
3. DO NOT generate any topic that could logically belong in ANY forbidden section listed above
4. DO NOT generate topics about themes, eras, or concepts described in forbidden sections
5. If a topic's theme overlaps with ANY forbidden section description, you MUST REJECT that topic
6. Each topic must be specific, actionable, and thematically aligned ONLY with "{section_title}"
7. Topics must align with the blog post "{post_title}" overall theme but stay within "{section_title}" boundaries

VALIDATION CHECKLIST - Before including any topic, verify:
□ This topic fits ONLY "{section_title}" based on its description
□ This topic does NOT fit any forbidden section above
□ This topic's themes do NOT overlap with themes from forbidden sections
□ This topic cannot be placed in any other section
□ If this topic were shown to someone reading the forbidden sections, they would NOT think it belongs there

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{{
  "topics": [
    {{
      "title": "Specific topic title",
      "description": "Brief description of what this topic covers",
      "category": "general"
    }},
    ...
  ]
}}

REMEMBER: Generate topics that are EXCLUSIVELY specific to "{section_title}" and CANNOT belong in any forbidden section listed above."""

    # Include full expanded_idea context if available (no truncation)
    if expanded_idea:
        prompt += f"\n\n═══════════════════════════════════════════════════════════════\nEXPANDED IDEA CONTEXT:\n═══════════════════════════════════════════════════════════════\n{expanded_idea}"
    
    return prompt, exclusion_count

def build_allocation_data(all_allocations, section_structure):
    """Build structured allocation data for frontend display"""
    sections_data = section_structure.get('sections', [])
    
    allocation_data = {
        'allocations': all_allocations,  # Use the actual generated topics
        'metadata': {
            'total_topics': len(all_allocations),
            'sections_count': len(sections_data),
            'generated_at': datetime.now().isoformat(),
            'method': 'section-specific generation based on individual thematic analysis'
        }
    }
    
    return allocation_data

def api_generate_section_specific_topics():
    """Generate section-specific topics instead of forcing existing ideas into sections"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({'success': False, 'error': 'Post ID is required'}), 400
        
        # Get post data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.section_structure, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            title = result['title']
            section_structure = result['section_structure']
            expanded_idea = result['expanded_idea']
            logger.info(f"Database query result - section_structure: {section_structure is not None}")
        
        # Parse section structure
        if not section_structure:
            return jsonify({'success': False, 'error': 'No section structure found'}), 400
        
        try:
            section_structure = json.loads(section_structure) if isinstance(section_structure, str) else section_structure
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid section structure format'}), 400
        
        # Handle both array format (new) and object format (old) for section_structure
        if isinstance(section_structure, list):
            sections_data = section_structure
        else:
            sections_data = section_structure.get('sections', [])
        
        if not sections_data:
            return jsonify({'success': False, 'error': 'No sections found in structure'}), 400
        
        logger.info(f"Generating section-specific topics for {len(sections_data)} sections")
        
        # Generate topics for each section
        all_section_topics = {}
        total_topics = 0
        llm_service = LLMService()
        
        for i, section in enumerate(sections_data):
            section_id = f"S{str(i+1).zfill(2)}"
            section_title = section.get('title') or section.get('theme', f'Section {i+1}')
            section_description = section.get('description', 'No description available')
            
            logger.info(f"Generating topics for {section_id}: {section_title}")
            logger.info(f"Total sections: {len(sections_data)}, Current section index: {i+1}")
            
            # Build section-specific brainstorming prompt
            section_prompt, exclusion_count = build_section_specific_prompt(
                title, section_title, section_description, sections_data, expanded_idea
            )
            
            logger.info(f"Section {section_id}: Building prompt with 1 positive section, {exclusion_count} negative sections (exclusions)")
            logger.info(f"Section {section_id} TARGET: \"{section_title}\" - {section_description[:100]}...")
            
            # Log which sections are being excluded
            excluded_sections = []
            for idx, sec in enumerate(sections_data):
                if idx != i:
                    excluded_title = sec.get('title') or sec.get('theme', f'Section {idx+1}')
                    excluded_sections.append(excluded_title)
            logger.info(f"Section {section_id} EXCLUDING ({exclusion_count} sections): {', '.join(excluded_sections)}")
            
            # Log prompt summary for debugging
            logger.debug(f"Section {section_id} prompt preview (first 500 chars): {section_prompt[:500]}...")
            
            brainstorming_messages = [
                {'role': 'system', 'content': 'You are a strict content strategist for section-specific topic generation. Your task is to generate exactly 6 topics that fit EXCLUSIVELY within ONE specified section based on its title and description. You will be given ONE target section and MULTIPLE forbidden sections. Topics that could belong to ANY forbidden section MUST be rejected. Each topic must be thematically aligned ONLY with the target section and cannot overlap with themes from ANY other section. If a topic relates to historical origins but the target section is about modern impact, REJECT it. If a topic relates to modern applications but the target section is about ancient foundations, REJECT it.'},
                {'role': 'user', 'content': section_prompt}
            ]
            
            # Increased token budget for better context understanding and response quality
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', brainstorming_messages, max_tokens=6000)
            
            if 'error' in result:
                logger.error(f"LLM error for section {section_id}: {result['error']}")
                continue
            
            content = result.get('content', '').strip()
            
            # Parse topics from response
            try:
                # Extract JSON from response (handle prose + JSON format)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                else:
                    # Fallback: try markdown code blocks
                    if content.startswith('```json') and content.endswith('```'):
                        json_content = content[7:-3].strip()
                    elif content.startswith('```') and content.endswith('```'):
                        json_content = content[3:-3].strip()
                    else:
                        json_content = content
                
                topics_data = json.loads(json_content)
                section_topics = topics_data.get('topics', [])
                
                # Add idea codes and section assignment
                formatted_topics = []
                for j, topic in enumerate(section_topics):
                    idea_code = f"{{{section_id}{str(j+1).zfill(2)}}}"
                    formatted_topics.append({
                        'idea_code': idea_code,
                        'topic_title': topic.get('title', f'Topic {j+1}'),
                        'section_code': f"{{{section_id}}}",
                        'description': topic.get('description', ''),
                        'category': topic.get('category', 'general')
                    })
                
                all_section_topics[section_id] = formatted_topics
                total_topics += len(formatted_topics)
                
                logger.info(f"Generated {len(formatted_topics)} topics for {section_id}")
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for section {section_id}: {e}")
                logger.error(f"Response content: {content[:200]}...")
                continue
        
        # Build final allocation data in the format expected by frontend
        allocation_data = {
            'allocations': [],
            'metadata': {
                'total_topics': total_topics,
                'sections_count': len(sections_data),
                'generated_at': datetime.now().isoformat(),
                'method': 'section-specific generation based on individual thematic analysis'
            }
        }
        
        # Group topics by section for frontend display
        for i, section in enumerate(sections_data):
            section_id = f"section_{i+1}"
            section_theme = section.get('title') or section.get('theme', f'Section {i+1}')
            
            # Get topics for this section
            section_topics = []
            for topic_obj in all_section_topics.get(f"S{str(i+1).zfill(2)}", []):
                section_topics.append(topic_obj.get('topic_title', 'Untitled Topic'))
            
            allocation_data['allocations'].append({
                'section_id': section_id,
                'section_theme': section_theme,
                'topics': section_topics
            })
        
        # Save to database
        save_topic_allocation(post_id, allocation_data)
        
        logger.info(f"Section-specific generation completed: {total_topics} topics across {len(sections_data)} sections")
        
        return jsonify({
            'success': True,
            'message': f'Section-specific topics generated ({total_topics} topics across {len(sections_data)} sections)',
            'allocations': allocation_data,
            'results': allocation_data,
            'raw_response': f'Section-specific generation completed - {total_topics} topics generated with thematic coherence'
        })
        
    except Exception as e:
        logger.error(f"Error in api_generate_section_specific_topics: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

def api_get_topic_allocation(post_id):
    """Get topic allocation for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result['topic_allocation']:
                allocation_data = result['topic_allocation']
                if isinstance(allocation_data, str):
                    allocation_data = json.loads(allocation_data)
                
                return jsonify({
                    'success': True,
                    'allocations': allocation_data
                })
            else:
                return jsonify({'success': True, 'allocations': None})
                
    except Exception as e:
        logger.error(f"Error fetching topic allocation: {e}")
        return jsonify({'error': str(e)}), 500
