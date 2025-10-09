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
    """Build a section-specific brainstorming prompt"""
    # Create context about other sections to avoid overlap
    other_sections_context = ""
    for i, section in enumerate(all_sections):
        if section.get('title') != section_title:
            other_sections_context += f"- {section.get('title', f'Section {i+1}')}: {section.get('description', '')}\n"
    
    prompt = f"""Generate exactly 6 diverse, specific topics for the section "{section_title}" in a blog post titled "{post_title}".

SECTION DETAILS:
Title: {section_title}
Description: {section_description}

CONTEXT:
This is part of a comprehensive blog post with the following other sections:
{other_sections_context}

REQUIREMENTS:
- Generate exactly 6 topics
- Each topic must fit perfectly within this section's theme
- Avoid overlap with other sections listed above
- Make topics specific and actionable
- Focus on Welsh mythology and folklore themes

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

Generate topics that are specific to {section_title} and Welsh mythology/folklore themes."""

    if expanded_idea:
        prompt += f"\n\nEXPANDED IDEA CONTEXT:\n{expanded_idea[:500]}..."
    
    return prompt

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
            
            # Build section-specific brainstorming prompt
            section_prompt = build_section_specific_prompt(
                title, section_title, section_description, sections_data, expanded_idea
            )
            
            brainstorming_messages = [
                {'role': 'system', 'content': 'You are a creative content strategist specializing in generating focused, thematic blog topics. Generate exactly 6 diverse, specific topics that fit perfectly within the target section while avoiding overlap with other sections.'},
                {'role': 'user', 'content': section_prompt}
            ]
            
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', brainstorming_messages, max_tokens=3000)
            
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
        
        # Build final allocation data
        all_allocations = []
        for section_id, topics in all_section_topics.items():
            all_allocations.extend(topics)
        
        structured_sections = {'sections': sections_data}
        allocation_data = build_allocation_data(all_allocations, structured_sections)
        
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
