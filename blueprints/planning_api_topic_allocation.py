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

GUIDELINES FOR TOPIC GENERATION:

TIME-BASED GUIDANCE:
- If the target section is about MODERN/CONTEMPORARY themes (e.g., "Contemporary Applications", "Modern Impact", "Enduring Legacy", "Current Relevance"), prioritize topics about:
  * Current practices, modern applications, contemporary relevance, recent developments
  * Topics that focus on how the theme applies today rather than historical origins
- If the target section is about ANCIENT/HISTORICAL themes (e.g., "Ancient Foundations", "Historical Origins", "Traditional Roots"), prioritize topics about:
  * Historical origins, traditional foundations, early developments, classical practices
  * Topics that focus on the historical context rather than modern applications

THEMATIC GUIDANCE:
- Read each other section's description to understand the overall structure
- Generate topics that are PRIMARILY relevant to "{section_title}" 
- If a topic could fit in multiple sections, choose the one where it's MOST relevant
- Focus on generating 6 topics that are useful and relevant, even if there's some thematic overlap
- It's better to have 6 good topics with some overlap than to have fewer topics

STRICT REQUIREMENTS:
1. Generate exactly 6 topics - THIS IS MANDATORY, you MUST generate 6 topics
2. Each topic should fit primarily within "{section_title}" - some thematic overlap with other sections is acceptable if the topic is MOST relevant to this section
3. Prioritize topics that are MOST relevant to "{section_title}" even if they could also relate to other sections
4. If you cannot find 6 topics that fit EXCLUSIVELY, generate topics that are PRIMARILY aligned with "{section_title}" - it's better to have 6 topics with some overlap than fewer topics
5. Each topic must be specific, actionable, and thematically aligned with "{section_title}"
6. Topics must align with the blog post "{post_title}" overall theme but focus on "{section_title}" 
7. CRITICAL: You MUST generate 6 topics - do not skip any section, even if it's challenging

VALIDATION CHECKLIST - Before including any topic, verify:
□ This topic is PRIMARILY relevant to "{section_title}" based on its description
□ This topic is MORE relevant to "{section_title}" than to other sections
□ This topic is specific and actionable for "{section_title}"
□ This topic aligns with the blog post "{post_title}" overall theme
□ If you have fewer than 6 topics, generate additional topics that are relevant to "{section_title}" even if they have some thematic overlap

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

REMEMBER: 
- Generate exactly 6 topics - this is MANDATORY
- Topics should be PRIMARILY relevant to "{section_title}" 
- Some thematic overlap with other sections is acceptable if the topic is MOST relevant to this section
- It's better to generate 6 topics with some overlap than to generate fewer topics
- Every section MUST have topics - do not skip any section"""

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
    """Generate section-specific topics instead of forcing existing ideas into sections. W2-FIX-7: gated by planning (idea, structured)."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')

        if not post_id:
            return jsonify({'success': False, 'error': 'Post ID is required'}), 400

        from utils.posts.workflow_stage import require_workflow_stage
        gate, gate_code = require_workflow_stage(post_id, 'planning', request=request)
        if gate:
            return jsonify({**gate, 'success': False}), gate_code

        # Get post data - use subtitle (expanded idea description) instead of expanded_idea
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, p.subtitle, pd.section_structure, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            title = result['title']
            section_structure = result['section_structure']
            # Use subtitle (expanded idea description) with fallback to expanded_idea for backwards compatibility
            expanded_idea = result.get('subtitle') or result.get('expanded_idea')
            logger.info(f"Database query result - section_structure: {section_structure is not None}, expanded_idea available: {expanded_idea is not None}")
        
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
        
        # Load Topic Allocation prompt from database using explicit selection (once before loop)
        prompt_name = None
        system_prompt = None
        with db_manager.get_cursor() as cursor:
            # Get selected prompt name from post settings
            if post_id:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('topic_allocation_prompt_name')
            
            # LEGACY: If no selection exists, use default
            if not prompt_name:
                prompt_name = 'Topic Allocation'
            
            # Get the selected prompt - NO FALLBACKS
            cursor.execute("""
                SELECT system_prompt
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                logger.error(f'Selected prompt "{prompt_name}" not found for post {post_id}')
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            system_prompt = prompt_data['system_prompt']
        
        # Use default system prompt if database lookup failed (shouldn't happen, but safety fallback)
        if not system_prompt:
            system_prompt = 'You are a content strategist for section-specific topic generation. Your task is to generate exactly 6 topics that are PRIMARILY relevant to ONE specified section based on its title and description. You will be given ONE target section and information about other sections. Generate topics that are MOST relevant to the target section - some thematic overlap with other sections is acceptable if the topic is primarily aligned with the target section. CRITICAL: You MUST generate exactly 6 topics for every section - do not skip any section. It is better to have 6 topics with some overlap than fewer topics.'
        
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
                {'role': 'system', 'content': system_prompt},
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
                
                # Ensure we have at least some topics - if zero, log warning
                if len(section_topics) == 0:
                    logger.warning(f"Section {section_id} ({section_title}) received ZERO topics from LLM. This may indicate the prompt was too strict or the LLM failed to generate topics.")
                
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
            section_code = f"S{str(i+1).zfill(2)}"
            for topic_obj in all_section_topics.get(section_code, []):
                section_topics.append(topic_obj.get('topic_title', 'Untitled Topic'))
            
            # Log warning if section has zero topics
            if len(section_topics) == 0:
                logger.warning(f"Section {section_id} ({section_theme}) has ZERO topics allocated. Section code: {section_code}, Available section topics keys: {list(all_section_topics.keys())}")
            
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
