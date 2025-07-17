from flask import Blueprint, jsonify, request, current_app
from app.db import get_db_conn
import psycopg2.extras
from app.api.workflow.decorators import handle_workflow_errors
import json
# Removed import of deprecated llm_processor module
# Functions will be implemented directly in this file as needed
from datetime import datetime
import sys
import logging

from . import bp

def load_step_config(post_id, stage, substage, step):
    """Load step configuration from workflow_step_entity table."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Convert step name from URL format to database format
        db_step_name = step.replace('_', ' ').title()
        
        # First get the substage_id
        cur.execute("""
            SELECT id FROM workflow_sub_stage_entity 
            WHERE name ILIKE %s
        """, (substage,))
        result = cur.fetchone()
        if not result:
            raise Exception(f"Substage {substage} not found")
        substage_id = result['id']

        # Then get the step configuration
        cur.execute("""
            SELECT config FROM workflow_step_entity 
            WHERE sub_stage_id = %s AND name ILIKE %s
        """, (substage_id, db_step_name))
        result = cur.fetchone()
        if not result or not result['config']:
            raise Exception(f"Step {step} not found in substage {substage} or has no configuration")
        return result['config']

def get_step_id(conn, stage, substage, step):
    """Get step ID from database."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Convert step name from URL format to database format
        db_step_name = step.replace('_', ' ').title()
        
        cur.execute("""
            SELECT wse.id
            FROM workflow_step_entity wse
            JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
            JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
            WHERE wst.name ILIKE %s AND wsse.name ILIKE %s AND wse.name ILIKE %s
        """, (stage, substage, db_step_name))
        result = cur.fetchone()
        if not result:
            raise Exception(f"Step {step} not found")
        return result['id']

def save_section_output(conn, section_ids, output, field):
    """Save output to specific section field."""
    with conn.cursor() as cur:
        for section_id in section_ids:
            cur.execute(f"""
                UPDATE post_section 
                SET {field} = %s 
                WHERE id = %s
            """, (output, section_id))
        conn.commit()

def process_sections_sequentially(conn, post_id, step_id, section_ids, timeout_per_section, output_field, output_table, frontend_prompt):
    """Process sections sequentially with actual LLM processing."""
    results = {}
    total_time = 0
    
    # Require frontend prompt - no fallback
    if not frontend_prompt:
        raise Exception("Frontend prompt is required - no fallback to database prompts")
    
    print(f"[PROCESS_SECTIONS] Using frontend prompt: {frontend_prompt[:200]}...")
    
    # Get LLM configuration
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT provider_type, model_name, api_base
        FROM llm_config
        WHERE is_active = true
        ORDER BY id DESC
        LIMIT 1
    """)
    config = cur.fetchone()
    if not config:
        config = {
            'provider_type': 'ollama',
            'model_name': 'llama3.1:70b',
            'api_base': 'http://localhost:11434'
        }
    
    for section_id in section_ids:
        start_time = datetime.now()
        
        try:
            # Get section data for context - fetch all available fields
            cur.execute("""
                SELECT 
                    section_heading, section_description, draft, ideas_to_include, facts_to_include,
                    polished, highlighting, image_concepts, image_prompts, watermarking,
                    image_meta_descriptions, image_captions, image_generation_metadata
                FROM post_section 
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            section_data = cur.fetchone()
            
            if not section_data:
                raise Exception(f"Section {section_id} not found")
            
            # Check if this is a template prompt (contains placeholders) or pre-populated prompt
            is_template = '[SECTION_HEADING_PLACEHOLDER]' in frontend_prompt or '[IDEAS_TO_INCLUDE_PLACEHOLDER]' in frontend_prompt or '[DRAFT_CONTENT_PLACEHOLDER]' in frontend_prompt
            
            if is_template:
                # Template prompt - replace placeholders with section-specific data
                llm_prompt = frontend_prompt
                
                # Define field mappings: database_field -> placeholder -> display_name
                field_mappings = {
                    'section_heading': ('[SECTION_HEADING_PLACEHOLDER]', 'Section Heading'),
                    'section_description': ('[SECTION_DESCRIPTION_PLACEHOLDER]', 'Section Description'),
                    'ideas_to_include': ('[IDEAS_TO_INCLUDE_PLACEHOLDER]', 'Ideas to Include'),
                    'facts_to_include': ('[FACTS_TO_INCLUDE_PLACEHOLDER]', 'Facts to Include'),
                    'draft': ('[DRAFT_CONTENT_PLACEHOLDER]', 'Draft Content'),
                    'polished': ('[POLISHED_CONTENT_PLACEHOLDER]', 'Polished Content'),
                    'highlighting': ('[HIGHLIGHTING_PLACEHOLDER]', 'Highlighting'),
                    'image_concepts': ('[IMAGE_CONCEPTS_PLACEHOLDER]', 'Image Concepts'),
                    'image_prompts': ('[IMAGE_PROMPTS_PLACEHOLDER]', 'Image Prompts'),
                    'watermarking': ('[WATERMARKING_PLACEHOLDER]', 'Watermarking'),
                    'image_meta_descriptions': ('[IMAGE_META_DESCRIPTIONS_PLACEHOLDER]', 'Image Meta Descriptions'),
                    'image_captions': ('[IMAGE_CAPTIONS_PLACEHOLDER]', 'Image Captions'),
                    'image_generation_metadata': ('[IMAGE_GENERATION_METADATA_PLACEHOLDER]', 'Image Generation Metadata')
                }
                
                # Replace all placeholders with actual section data
                for field_name, (placeholder, display_name) in field_mappings.items():
                    print(f"[PROCESS_SECTIONS] Checking field: {field_name}, placeholder: {placeholder}")
                    print(f"[PROCESS_SECTIONS] Section data for {field_name}: {section_data.get(field_name, 'NOT FOUND')}")
                    
                    if field_name in section_data and section_data[field_name]:
                        field_value = str(section_data[field_name])
                        llm_prompt = llm_prompt.replace(placeholder, field_value)
                        print(f"[PROCESS_SECTIONS] Replaced {placeholder} with section {section_id} data: {field_name}")
                        print(f"[PROCESS_SECTIONS] Field value length: {len(field_value)}")
                    elif placeholder in llm_prompt:
                        # Replace placeholder with empty/default value
                        llm_prompt = llm_prompt.replace(placeholder, 'No data available')
                        print(f"[PROCESS_SECTIONS] Replaced {placeholder} with default value for section {section_id}")
                    else:
                        print(f"[PROCESS_SECTIONS] Placeholder {placeholder} not found in prompt")
                
                print(f"[PROCESS_SECTIONS] Template processing complete for section {section_id}")
                print(f"[PROCESS_SECTIONS] Final prompt contains [DRAFT_CONTENT_PLACEHOLDER]: {'[DRAFT_CONTENT_PLACEHOLDER]' in llm_prompt}")
                
            else:
                # Legacy pre-populated prompt - use existing replacement logic
                llm_prompt = frontend_prompt
                
                # Replace the generic section heading and description with the actual section data
                import re
                
                # Replace section heading
                section_heading_pattern = r'Section Heading: .*'
                actual_section_heading = f"Section Heading: {section_data['section_heading']}"
                llm_prompt = re.sub(section_heading_pattern, actual_section_heading, llm_prompt)
                
                # Replace section description
                section_description_pattern = r'Section Description: .*'
                actual_section_description = f"Section Description: {section_data['section_description']}"
                llm_prompt = re.sub(section_description_pattern, actual_section_description, llm_prompt)
                
                # Dynamically replace all section-specific input fields
                for field_name, field_value in section_data.items():
                    if field_value and field_name not in ['section_heading', 'section_description']:
                        display_name = field_name.replace('_', ' ').title()
                        field_pattern = rf'{display_name}: .*?(?=\n|$)'
                        actual_field_content = f"{display_name}: {field_value}"
                        llm_prompt = re.sub(field_pattern, actual_field_content, llm_prompt, flags=re.MULTILINE)
                        print(f"[PROCESS_SECTIONS] Legacy replacement: {display_name} for section {section_id}")
            
            print(f"[PROCESS_SECTIONS] Section {section_id} ({section_data['section_heading']}) - Updated prompt with section-specific data")
            print(f"[PROCESS_SECTIONS] LLM prompt for section {section_id}: {llm_prompt[:300]}...")
            
            # Call LLM with frontend prompt as-is
            import requests
            llm_request = {
                "model": config['model_name'],
                "prompt": llm_prompt,
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False
            }
            
            response = requests.post(
                f"{config['api_base']}/api/generate",
                json=llm_request,
                timeout=timeout_per_section
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM request failed: {response.text}")
            
            result = response.json()
            output = result.get('response', '').strip()
            
            # Save output to specific section
            if output_table == 'post_section':
                cur.execute(f"""
                    UPDATE post_section 
                    SET {output_field} = %s 
                    WHERE id = %s AND post_id = %s
                """, (output, section_id, post_id))
            else:
                # Fallback to post_development if needed
                cur.execute(f"""
                    UPDATE post_development 
                    SET {output_field} = %s 
                    WHERE post_id = %s
                """, (output, post_id))
            
            conn.commit()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            total_time += processing_time
            
            results[section_id] = {
                "success": True,
                "result": output,
                "processing_time": processing_time,
                "section_heading": section_data['section_heading']
            }
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            total_time += processing_time
            results[section_id] = {
                "success": False,
                "error": str(e),
                "section_id": section_id,
                "processing_time": processing_time
            }
    
    return {
        "results": results,
        "summary": f"Processed {len(section_ids)} sections in {total_time:.2f} seconds",
        "total_time": total_time
    }

def process_step(post_id, stage, substage, step, frontend_inputs=None):
    """Process a workflow step."""
    # This is a placeholder - the actual processing is now done in the endpoint
    # that uses Live Preview content
    return "Step processed using Live Preview content"

def process_writing_step(post_id, stage, substage, step, section_ids, frontend_inputs):
    """Process a Writing stage step with section-specific handling."""
    try:
        conn = get_db_conn()
        step_id = get_step_id(conn, stage, substage, step)
        
        # Extract output field mapping and prompt from frontend inputs
        output_field = frontend_inputs.get('output_field') if frontend_inputs else None
        output_table = frontend_inputs.get('output_table', 'post_section') if frontend_inputs else 'post_section'
        frontend_prompt = frontend_inputs.get('prompt') if frontend_inputs else None
        
        print(f"[PROCESS_WRITING_STEP] Frontend inputs: {frontend_inputs}")
        print(f"[PROCESS_WRITING_STEP] Frontend prompt: {frontend_prompt[:200] if frontend_prompt else 'None'}...")
        
        if not output_field:
            raise Exception("No output field specified")
        
        if not frontend_prompt:
            raise Exception("Frontend prompt is required - no fallback to database prompts")
        
        # If section_ids are provided, use sequential processing
        if section_ids:
            timeout_per_section = frontend_inputs.get('timeout_per_section', 300) if frontend_inputs else 300
            
            result = process_sections_sequentially(
                conn, post_id, step_id, section_ids, timeout_per_section, 
                output_field, output_table, frontend_prompt
            )
            
            conn.close()
            
            return {
                'success': True,
                'results': result['results'],
                'summary': result['summary'],
                'parameters': {
                    'sections_processed': section_ids,
                    'timeout_per_section': timeout_per_section,
                    'output_field': output_field,
                    'output_table': output_table,
                    'total_time': result['total_time']
                }
            }
        else:
            # Fallback to standard processing if no sections specified
            result = process_step(post_id, stage, substage, step, frontend_inputs)
            conn.close()
            
            return {
                'success': True,
                'results': [{'output': result}],
                'parameters': {'sections_processed': []}
            }
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return {
            'success': False,
            'error': str(e),
            'sections_processed': section_ids if section_ids else []
        }

@bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get post details including workflow state."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get post details with workflow state
        cur.execute("""
            SELECT p.*, 
                   ws.name as current_stage,
                   w.status as workflow_status
            FROM post p
            LEFT JOIN workflow w ON w.post_id = p.id
            LEFT JOIN workflow_stage_entity ws ON ws.id = w.stage_id
            WHERE p.id = %s
        """, (post_id,))
        
        post = cur.fetchone()
        if not post:
            return jsonify({'error': 'Post not found'}), 404
            
        # Get workflow progress
        cur.execute("""
            SELECT 
                pws.id,
                ws.name as stage_name,
                pws.status,
                pws.completed_at
            FROM post_workflow_stage pws
            JOIN workflow_stage_entity ws ON ws.id = pws.stage_id
            WHERE pws.post_id = %s
            ORDER BY pws.completed_at
        """, (post_id,))
        progress = cur.fetchall()
        
        return jsonify({
            'id': post['id'],
            'title': post['title'],
            'workflow': {
                'currentStage': post['current_stage'],
                'status': post['workflow_status'],
                'progress': [
                    {
                        'stage': p['stage_name'],
                        'status': p['status'],
                        'completedAt': p['completed_at'].isoformat() if p['completed_at'] else None
                    } for p in progress
                ]
            }
        })

@bp.route('/posts/<int:post_id>/development', methods=['GET', 'POST'])
def post_development(post_id):
    """Handle post development state."""
    if request.method == 'GET':
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get development state
            cur.execute("""
                SELECT pd.*
                FROM post_development pd
                WHERE pd.post_id = %s
            """, (post_id,))
            
            dev = cur.fetchone()
            if not dev:
                return jsonify({'error': 'Development state not found'}), 404
                
            return jsonify({
                'postId': dev['post_id'],
                'outline': dev['outline'],
                'draft': dev['draft'],
                'status': dev['status'],
                'lastUpdated': dev['updated_at'].isoformat()
            })
    
    else:  # POST
        data = request.get_json()
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Update development state
            cur.execute("""
                INSERT INTO post_development (
                    post_id, outline, draft, status
                ) VALUES (
                    %s, %s, %s, %s
                )
                ON CONFLICT (post_id) DO UPDATE
                SET outline = EXCLUDED.outline,
                    draft = EXCLUDED.draft,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING post_id, outline, draft, status, updated_at
            """, (
                post_id,
                data.get('outline', ''),
                data.get('draft', ''),
                data.get('status', 'in_progress')
            ))
            
            dev = cur.fetchone()
            conn.commit()
            
            return jsonify({
                'postId': dev['post_id'],
                'outline': dev['outline'],
                'draft': dev['draft'],
                'status': dev['status'],
                'lastUpdated': dev['updated_at'].isoformat()
            })

@bp.route('/posts/<int:post_id>/sections', methods=['GET', 'POST'])
def manage_sections(post_id):
    """Get all sections or create a new section for a post."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # First check if post exists
        cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Post not found'}), 404
            
        if request.method == 'GET':
            # Get all sections with their elements and all database fields
            cur.execute("""
                SELECT 
                    s.id,
                    s.section_heading as title,
                    s.section_description as description,
                    s.section_order as order_index,
                    s.ideas_to_include,
                    s.facts_to_include,
                    s.draft as content,
                    s.polished,
                    s.highlighting,
                    s.image_concepts,
                    s.image_prompts,
                    s.watermarking,
                    s.image_meta_descriptions,
                    s.image_captions,
                    s.generated_image_url,
                    s.image_generation_metadata,
                    s.image_id,
                    s.status,
                    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'fact') as facts,
                    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'idea') as ideas,
                    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'theme') as themes
                FROM post_section s
                LEFT JOIN post_section_elements e ON e.section_id = s.id
                WHERE s.post_id = %s
                GROUP BY s.id, s.section_heading, s.section_description, s.section_order, 
                         s.ideas_to_include, s.facts_to_include, s.draft, s.polished,
                         s.highlighting, s.image_concepts, s.image_prompts, 
                         s.watermarking, s.image_meta_descriptions, s.image_captions, 
                         s.generated_image_url, s.image_generation_metadata, s.image_id, s.status
                ORDER BY s.section_order
            """, (post_id,))
            
            sections = cur.fetchall()
            return jsonify({
                'sections': [
                    {
                        'id': s['id'],
                        'title': s['title'],
                        'description': s['description'],
                        'orderIndex': s['order_index'],
                        'ideas_to_include': s['ideas_to_include'],
                        'facts_to_include': s['facts_to_include'],
                        'content': s['content'],
                        'draft': s['content'],  # Map content to draft for backward compatibility
                        'polished': s.get('polished', ''),  # Add polished field
                        'highlighting': s['highlighting'],
                        'image_concepts': s['image_concepts'],
                        'image_prompts': s['image_prompts'],
                        'watermarking': s['watermarking'],
                        'image_captions': s['image_captions'],
                        'image_meta_descriptions': s['image_meta_descriptions'],
                        'generated_image_url': s['generated_image_url'],
                        'image_generation_metadata': s['image_generation_metadata'],
                        'image_id': s['image_id'],
                        'position': s['order_index'],
                        'status': s['status'],
                        'elements': {
                            'facts': s['facts'] if s['facts'] and s['facts'][0] is not None else [],
                            'ideas': s['ideas'] if s['ideas'] and s['ideas'][0] is not None else [],
                            'themes': s['themes'] if s['themes'] and s['themes'][0] is not None else []
                        }
                    } for s in sections
                ]
            })
        
        else:  # POST
            data = request.get_json()
            
            try:
                # Start transaction
                cur.execute("BEGIN")
                
                # Create new section
                cur.execute("""
                    INSERT INTO post_section (
                        post_id,
                        section_heading,
                        section_description,
                        section_order
                    ) VALUES (
                        %s, %s, %s, %s
                    ) RETURNING id, section_heading, section_description, section_order
                """, (
                    post_id,
                    data.get('title'),
                    data.get('description'),
                    data.get('orderIndex')
                ))
                
                section = cur.fetchone()
                section_id = section['id']
                
                # Add elements
                elements = data.get('elements', {})
                for element_type in ['fact', 'idea', 'theme']:
                    element_texts = elements.get(element_type + 's', [])
                    for order, text in enumerate(element_texts):
                        cur.execute("""
                            INSERT INTO post_section_elements (
                                post_id, section_id, element_type, element_text, element_order
                            ) VALUES (
                                %s, %s, %s, %s, %s
                            )
                        """, (
                            post_id,
                            section_id,
                            element_type,
                            text,
                            order
                        ))
                
                # Commit transaction
                cur.execute("COMMIT")
                
                # Return created section with elements
                cur.execute("""
                    SELECT 
                        s.id,
                        s.section_heading as title,
                        s.section_description as description,
                        s.section_order as order_index,
                        array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'fact') as facts,
                        array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'idea') as ideas,
                        array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'theme') as themes
                    FROM post_section s
                    LEFT JOIN post_section_elements e ON e.section_id = s.id
                    WHERE s.post_id = %s AND s.id = %s
                    GROUP BY s.id, s.section_heading, s.section_description, s.section_order
                """, (post_id, section_id))
                
                section = cur.fetchone()
                return jsonify({
                    'id': section['id'],
                    'title': section['title'],
                    'description': section['description'],
                    'orderIndex': section['order_index'],
                    'elements': {
                        'facts': section['facts'] if section['facts'] and section['facts'][0] is not None else [],
                        'ideas': section['ideas'] if section['ideas'] and section['ideas'][0] is not None else [],
                        'themes': section['themes'] if section['themes'] and section['themes'][0] is not None else []
                    }
                }), 201
                
            except Exception as e:
                cur.execute("ROLLBACK")
                return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/sections/<int:section_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_section(post_id, section_id):
    """Manage a specific section."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # First check if post exists
        cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Post not found'}), 404
            
        if request.method == 'GET':
            # Get section details with elements and image fields
            cur.execute("""
                SELECT 
                    s.id,
                    s.section_heading as title,
                    s.section_description as description,
                    s.section_order as order_index,
                    s.ideas_to_include,
                    s.facts_to_include,
                    s.draft,
                    s.polished,
                    s.image_concepts,
                    s.image_prompts,
                    s.watermarking,
                    s.image_meta_descriptions,
                    s.image_captions,
                    s.image_prompt_example_id,
                    s.generated_image_url,
                    s.image_generation_metadata,
                    s.image_id,
                    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'fact') as facts,
                    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'idea') as ideas,
                    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'theme') as themes
                FROM post_section s
                LEFT JOIN post_section_elements e ON e.section_id = s.id
                WHERE s.post_id = %s AND s.id = %s
                GROUP BY s.id, s.section_heading, s.section_description, s.section_order, 
                         s.ideas_to_include, s.facts_to_include, s.draft, s.polished, s.image_concepts, s.image_prompts, 
                         s.watermarking, s.image_meta_descriptions, s.image_captions, 
                         s.image_prompt_example_id, s.generated_image_url, s.image_generation_metadata, s.image_id
            """, (post_id, section_id))
            
            section = cur.fetchone()
            if not section:
                return jsonify({'error': 'Section not found'}), 404
                
            return jsonify({
                'id': section['id'],
                'title': section['title'],
                'description': section['description'],
                'orderIndex': section['order_index'],
                'ideas_to_include': section['ideas_to_include'],
                'facts_to_include': section['facts_to_include'],
                'draft': section['draft'],
                'polished': section['polished'],
                'image_concepts': section['image_concepts'],
                'image_prompts': section['image_prompts'],
                'watermarking': section['watermarking'],
                'image_meta_descriptions': section['image_meta_descriptions'],
                'image_captions': section['image_captions'],
                'image_prompt_example_id': section['image_prompt_example_id'],
                'generated_image_url': section['generated_image_url'],
                'image_generation_metadata': section['image_generation_metadata'],
                'image_id': section['image_id'],
                'elements': {
                    'facts': section['facts'] if section['facts'] and section['facts'][0] is not None else [],
                    'ideas': section['ideas'] if section['ideas'] and section['ideas'][0] is not None else [],
                    'themes': section['themes'] if section['themes'] and section['themes'][0] is not None else []
                }
            })
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            try:
                # Start transaction
                cur.execute("BEGIN")
                
                # Update section (including image fields)
                cur.execute("""
                    UPDATE post_section
                    SET section_heading = %s,
                        section_description = %s,
                        section_order = %s,
                        image_concepts = %s,
                        image_prompts = %s,
                        watermarking = %s,
                        image_meta_descriptions = %s,
                        image_captions = %s,
                        image_prompt_example_id = %s,
                        generated_image_url = %s,
                        image_generation_metadata = %s::jsonb,
                        image_id = %s
                    WHERE post_id = %s AND id = %s
                    RETURNING id, section_heading, section_description, section_order
                """, (
                    data.get('title'),
                    data.get('description'),
                    data.get('orderIndex'),
                    data.get('image_concepts'),
                    data.get('image_prompts'),
                    data.get('watermarking'),
                    data.get('image_meta_descriptions'),
                    data.get('image_captions'),
                    data.get('image_prompt_example_id'),
                    data.get('generated_image_url'),
                    json.dumps(data.get('image_generation_metadata')) if data.get('image_generation_metadata') else None,
                    data.get('image_id'),
                    post_id,
                    section_id
                ))
                
                section = cur.fetchone()
                if not section:
                    cur.execute("ROLLBACK")
                    return jsonify({'error': 'Section not found'}), 404
                
                # Update elements
                elements = data.get('elements', {})
                
                # Delete existing elements
                cur.execute("DELETE FROM post_section_elements WHERE section_id = %s", (section_id,))
                
                # Insert new elements
                for element_type in ['fact', 'idea', 'theme']:
                    element_texts = elements.get(element_type + 's', [])
                    for order, text in enumerate(element_texts):
                        cur.execute("""
                            INSERT INTO post_section_elements (
                                post_id, section_id, element_type, element_text, element_order
                            ) VALUES (
                                %s, %s, %s, %s, %s
                            )
                        """, (
                            post_id,
                            section_id,
                            element_type,
                            text,
                            order
                        ))
                
                # Commit transaction
                cur.execute("COMMIT")
                
                # Return updated section with elements and image fields
                cur.execute("""
                    SELECT 
                        s.id,
                        s.section_heading as title,
                        s.section_description as description,
                        s.section_order as order_index,
                        s.ideas_to_include,
                        s.facts_to_include,
                        s.draft,
                        s.polished,
                        s.image_concepts,
                        s.image_prompts,
                        s.watermarking,
                        s.image_meta_descriptions,
                        s.image_captions,
                        s.image_prompt_example_id,
                        s.generated_image_url,
                        s.image_generation_metadata,
                        s.image_id,
                        array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'fact') as facts,
                        array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'idea') as ideas,
                        array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'theme') as themes
                    FROM post_section s
                    LEFT JOIN post_section_elements e ON e.section_id = s.id
                    WHERE s.post_id = %s AND s.id = %s
                    GROUP BY s.id, s.section_heading, s.section_description, s.section_order,
                             s.ideas_to_include, s.facts_to_include, s.draft, s.polished, s.image_concepts, s.image_prompts,
                             s.watermarking, s.image_meta_descriptions, s.image_captions,
                             s.image_prompt_example_id, s.generated_image_url, s.image_generation_metadata, s.image_id
                """, (post_id, section_id))
                
                section = cur.fetchone()
                return jsonify({
                    'id': section['id'],
                    'title': section['title'],
                    'description': section['description'],
                    'orderIndex': section['order_index'],
                    'ideas_to_include': section['ideas_to_include'],
                    'facts_to_include': section['facts_to_include'],
                    'draft': section['draft'],
                    'polished': section['polished'],
                    'image_concepts': section['image_concepts'],
                    'image_prompts': section['image_prompts'],
                    'watermarking': section['watermarking'],
                    'image_meta_descriptions': section['image_meta_descriptions'],
                    'image_captions': section['image_captions'],
                    'image_prompt_example_id': section['image_prompt_example_id'],
                    'generated_image_url': section['generated_image_url'],
                    'image_generation_metadata': section['image_generation_metadata'],
                    'image_id': section['image_id'],
                    'elements': {
                        'facts': section['facts'] if section['facts'] and section['facts'][0] is not None else [],
                        'ideas': section['ideas'] if section['ideas'] and section['ideas'][0] is not None else [],
                        'themes': section['themes'] if section['themes'] and section['themes'][0] is not None else []
                    }
                })
                
            except Exception as e:
                cur.execute("ROLLBACK")
                return jsonify({'error': str(e)}), 500
            
        else:  # DELETE
            try:
                # Start transaction
                cur.execute("BEGIN")
                
                # Delete elements first (due to foreign key constraint)
                cur.execute("""
                    DELETE FROM post_section_elements
                    WHERE post_id = %s AND section_id = %s
                    RETURNING id
                """, (post_id, section_id))
                
                # Then delete the section
                cur.execute("""
                    DELETE FROM post_section
                    WHERE post_id = %s AND id = %s
                    RETURNING id
                """, (post_id, section_id))
                
                if not cur.fetchone():
                    cur.execute("ROLLBACK")
                    return jsonify({'error': 'Section not found'}), 404
                
                # Commit transaction
                cur.execute("COMMIT")
                return '', 204
                
            except Exception as e:
                cur.execute("ROLLBACK")
                return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/sections/<int:section_id>/fields', methods=['GET', 'PUT'])
def section_fields(post_id, section_id):
    """Manage fields for a specific section."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # First check if post and section exist
        cur.execute("""
            SELECT s.id 
            FROM post_section s
            JOIN post p ON p.id = s.post_id
            WHERE p.id = %s AND s.id = %s
        """, (post_id, section_id))
        
        if not cur.fetchone():
            return jsonify({'error': 'Post or section not found'}), 404
            
        if request.method == 'GET':
            # Get all fields for the section
            cur.execute("""
                SELECT 
                    f.id,
                    f.name,
                    f.value,
                    f.field_type,
                    f.order_index
                FROM section_field f
                WHERE f.section_id = %s
                ORDER BY f.order_index
            """, (section_id,))
            
            fields = cur.fetchall()
            return jsonify({
                'fields': [
                    {
                        'id': f['id'],
                        'name': f['name'],
                        'value': f['value'],
                        'type': f['field_type'],
                        'orderIndex': f['order_index']
                    } for f in fields
                ]
            })
            
        else:  # PUT
            data = request.get_json()
            fields = data.get('fields', [])
            
            # Update fields in a transaction
            try:
                # First delete existing fields
                cur.execute("DELETE FROM section_field WHERE section_id = %s", (section_id,))
                
                # Then insert new fields
                for field in fields:
                    cur.execute("""
                        INSERT INTO section_field (
                            section_id, name, value, field_type, order_index
                        ) VALUES (
                            %s, %s, %s, %s, %s
                        )
                    """, (
                        section_id,
                        field.get('name'),
                        field.get('value'),
                        field.get('type'),
                        field.get('orderIndex', 0)
                    ))
                
                conn.commit()
                return jsonify({'message': 'Fields updated successfully'})
                
            except Exception as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500

@bp.route('/fields', methods=['GET'])
@handle_workflow_errors
def get_fields():
    """Get all available workflow fields."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT field_name, stage_id, substage_id, order_index 
                FROM workflow_field_mapping 
                ORDER BY order_index
            """)
            fields = cur.fetchall()
            
            return jsonify([dict(field) for field in fields])

@bp.route('/fields/mappings', methods=['GET'])
@handle_workflow_errors
def get_field_mappings():
    """Get all field mappings with stage and substage details."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT 
                    wfm.field_name,
                    wfm.stage_id,
                    ws.name as stage_name,
                    wfm.substage_id,
                    wss.name as substage_name,
                    wfm.order_index
                FROM workflow_field_mapping wfm
                LEFT JOIN workflow_stage_entity ws ON ws.id = wfm.stage_id
                LEFT JOIN workflow_sub_stage_entity wss ON wss.id = wfm.substage_id
                ORDER BY ws.stage_order, wss.sub_stage_order, wfm.order_index
            """)
            mappings = cur.fetchall()
            
            return jsonify([dict(mapping) for mapping in mappings])

@bp.route('/posts/<int:post_id>/fields', methods=['GET'])
@handle_workflow_errors
def get_post_fields(post_id):
    """Get all fields and their values for a specific post."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # First verify post exists
            cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Post not found'}), 404
                
            # Get all fields from post_development
            cur.execute("""
                SELECT pd.* 
                FROM post_development pd
                WHERE pd.post_id = %s
            """, (post_id,))
            
            fields = cur.fetchone()
            
            if not fields:
                return jsonify({'error': 'No development fields found for post'}), 404
                
            # Convert to dict, excluding id and post_id
            field_dict = dict(fields)
            del field_dict['id']
            del field_dict['post_id']
                    
            return jsonify(field_dict)

@bp.route('/posts/<int:post_id>/fields/<field_name>', methods=['POST'])
@handle_workflow_errors
def update_post_field(post_id, field_name):
    """Update a specific field value for a post (post_development or post.status)."""
    data = request.get_json()
    if 'value' not in data:
        return jsonify({'error': 'Field value is required'}), 400
    value = data['value']
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # First verify post exists
            cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Post not found'}), 404
            # Special case: allow updating 'status' in post table
            if field_name == 'status':
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post' AND column_name = 'status'")
                if not cur.fetchone():
                    return jsonify({'error': 'Invalid field name'}), 400
                cur.execute("UPDATE post SET status = %s, updated_at = NOW() WHERE id = %s", (value, post_id))
                conn.commit()
                return jsonify({'status': 'success'})
            # Otherwise, update in post_development
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_development' AND column_name = %s", (field_name,))
            if not cur.fetchone():
                return jsonify({'error': 'Invalid field name'}), 400
            cur.execute(f"UPDATE post_development SET {field_name} = %s WHERE post_id = %s", (value, post_id))
            conn.commit()
            return jsonify({'status': 'success'})

@bp.route('/posts/<int:post_id>/stages', methods=['GET'])
@handle_workflow_errors
def get_post_stages(post_id):
    """Get all stages and their status for a specific post."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # First verify post exists
            cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Post not found'}), 404
                
            # Get all stages with their status
            cur.execute("""
                SELECT 
                    ws.id as stage_id,
                    ws.name as stage_name,
                    ws.description,
                    ws.stage_order,
                    pws.started_at,
                    pws.completed_at,
                    pws.status,
                    pws.input_field,
                    pws.output_field
                FROM workflow_stage_entity ws
                LEFT JOIN post_workflow_stage pws ON pws.stage_id = ws.id AND pws.post_id = %s
                ORDER BY ws.stage_order
            """, (post_id,))
            
            stages = cur.fetchall()
            return jsonify([dict(stage) for stage in stages])

@bp.route('/posts/<int:post_id>/stages/<int:stage_id>', methods=['GET'])
@handle_workflow_errors
def get_post_stage(post_id, stage_id):
    """Get details of a specific stage for a post."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # First verify post exists
            cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Post not found'}), 404
                
            # Get stage details with substages
            cur.execute("""
                WITH stage_info AS (
                    SELECT 
                        ws.id as stage_id,
                        ws.name as stage_name,
                        ws.description,
                        ws.stage_order,
                        pws.started_at,
                        pws.completed_at,
                        pws.status,
                        pws.input_field,
                        pws.output_field
                    FROM workflow_stage_entity ws
                    LEFT JOIN post_workflow_stage pws ON pws.stage_id = ws.id AND pws.post_id = %s
                    WHERE ws.id = %s
                )
                SELECT 
                    si.*,
                    json_agg(
                        json_build_object(
                            'id', wss.id,
                            'name', wss.name,
                            'description', wss.description,
                            'sub_stage_order', wss.sub_stage_order
                        ) ORDER BY wss.sub_stage_order
                    ) as substages
                FROM stage_info si
                LEFT JOIN workflow_sub_stage_entity wss ON wss.stage_id = si.stage_id
                GROUP BY 
                    si.stage_id, si.stage_name, si.description, si.stage_order,
                    si.started_at, si.completed_at, si.status, si.input_field, si.output_field
            """, (post_id, stage_id))
            
            stage = cur.fetchone()
            if not stage:
                return jsonify({'error': 'Stage not found'}), 404
                
            return jsonify(dict(stage))

@bp.route('/posts/<int:post_id>/stages/<int:stage_id>/sub-stages', methods=['GET'])
@handle_workflow_errors
def get_post_substages(post_id, stage_id):
    """Get all substages for a specific stage of a post."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # First verify post and stage exist
            cur.execute("""
                SELECT p.id, ws.id 
                FROM post p 
                CROSS JOIN workflow_stage_entity ws
                WHERE p.id = %s AND ws.id = %s
            """, (post_id, stage_id))
            
            if not cur.fetchone():
                return jsonify({'error': 'Post or stage not found'}), 404
                
            # Get substages with their steps
            cur.execute("""
                WITH substage_info AS (
                    SELECT 
                        wss.id as substage_id,
                        wss.name as substage_name,
                        wss.description,
                        wss.sub_stage_order
                    FROM workflow_sub_stage_entity wss
                    WHERE wss.stage_id = %s
                )
                SELECT 
                    si.*,
                    json_agg(
                        json_build_object(
                            'id', wse.id,
                            'name', wse.name,
                            'description', wse.description,
                            'step_order', wse.step_order,
                            'config', wse.config
                        ) ORDER BY wse.step_order
                    ) as steps
                FROM substage_info si
                LEFT JOIN workflow_step_entity wse ON wse.sub_stage_id = si.substage_id
                GROUP BY 
                    si.substage_id, si.substage_name, si.description, si.sub_stage_order
                ORDER BY si.sub_stage_order
            """, (stage_id,))
            
            substages = cur.fetchall()
            return jsonify([dict(substage) for substage in substages])

@bp.route('/posts/<int:post_id>/stages/<int:stage_id>/transition', methods=['POST'])
@handle_workflow_errors
def transition_stage(post_id, stage_id):
    """Update the status of a stage for a post."""
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
        
    valid_statuses = ['not_started', 'in_progress', 'completed', 'blocked']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # First verify post and stage exist
            cur.execute("""
                SELECT p.id, ws.id 
                FROM post p 
                CROSS JOIN workflow_stage_entity ws
                WHERE p.id = %s AND ws.id = %s
            """, (post_id, stage_id))
            
            if not cur.fetchone():
                return jsonify({'error': 'Post or stage not found'}), 404
                
            # Update or insert stage status
            cur.execute("""
                INSERT INTO post_workflow_stage 
                    (post_id, stage_id, status, started_at, completed_at)
                VALUES 
                    (%s, %s, %s, 
                     CASE WHEN %s = 'in_progress' THEN CURRENT_TIMESTAMP ELSE NULL END,
                     CASE WHEN %s = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END)
                ON CONFLICT (post_id, stage_id) DO UPDATE
                SET 
                    status = EXCLUDED.status,
                    started_at = CASE 
                        WHEN EXCLUDED.status = 'in_progress' AND post_workflow_stage.started_at IS NULL 
                        THEN CURRENT_TIMESTAMP 
                        ELSE post_workflow_stage.started_at 
                    END,
                    completed_at = CASE 
                        WHEN EXCLUDED.status = 'completed' 
                        THEN CURRENT_TIMESTAMP 
                        ELSE NULL 
                    END
            """, (post_id, stage_id, data['status'], data['status'], data['status']))
            
            conn.commit()
            return jsonify({'message': 'Stage status updated successfully'})

@bp.route('/posts/<int:post_id>/stages/<int:stage_id>', methods=['PUT'])
@handle_workflow_errors
def update_stage_fields(post_id, stage_id):
    """Update the input/output fields for a stage."""
    data = request.get_json()
    if not any(k in data for k in ['input_field', 'output_field']):
        return jsonify({'error': 'At least one of input_field or output_field is required'}), 400
        
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # First verify post and stage exist
            cur.execute("""
                SELECT p.id, ws.id 
                FROM post p 
                CROSS JOIN workflow_stage_entity ws
                WHERE p.id = %s AND ws.id = %s
            """, (post_id, stage_id))
            
            if not cur.fetchone():
                return jsonify({'error': 'Post or stage not found'}), 404
                
            # Build update query
            fields = []
            values = [post_id, stage_id]  # Start with post_id and stage_id
            if 'input_field' in data:
                fields.append('input_field')
                values.append(data['input_field'])
            if 'output_field' in data:
                fields.append('output_field')
                values.append(data['output_field'])
                
            # Update the fields
            query = f"""
                INSERT INTO post_workflow_stage (post_id, stage_id, {', '.join(fields)})
                VALUES (%s, %s, {', '.join('%s' for _ in range(len(fields)))})
                ON CONFLICT (post_id, stage_id) 
                DO UPDATE SET {', '.join(f"{field} = EXCLUDED.{field}" for field in fields)}
            """
            
            cur.execute(query, values)
            conn.commit()
            
            return jsonify({'message': 'Stage fields updated successfully'})

@bp.route('/steps/<int:step_id>/field_selection', methods=['POST'])
@handle_workflow_errors
def save_field_selection(step_id):
    """Save the user's field selection for a workflow step."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Handle output field selection (existing functionality)
        output_field = data.get('output_field')
        output_table = data.get('output_table')
        
        # Handle input field selection (new functionality)
        input_field = data.get('input_field')
        input_table = data.get('input_table')
        input_id = data.get('input_id')
        
        # Handle context field selection (new functionality)
        context_field = data.get('context_field')
        context_table = data.get('context_table')
        context_id = data.get('context_id')

        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # First verify step exists
                cur.execute("SELECT id, config FROM workflow_step_entity WHERE id = %s", (step_id,))
                step = cur.fetchone()
                if not step:
                    return jsonify({'error': 'Step not found'}), 404

                # Update the config with user mappings
                config = step['config']
                if not config:
                    config = {}
                
                # Ensure settings.llm exists
                if 'settings' not in config:
                    config['settings'] = {}
                if 'llm' not in config['settings']:
                    config['settings']['llm'] = {}
                
                # Handle output field mapping
                if output_field and output_table:
                    config['settings']['llm']['user_output_mapping'] = {
                        'field': output_field,
                        'table': output_table
                    }
                
                # Handle input field mapping
                if input_field and input_table and input_id:
                    if 'user_input_mappings' not in config['settings']['llm']:
                        config['settings']['llm']['user_input_mappings'] = {}
                    
                    config['settings']['llm']['user_input_mappings'][input_id] = {
                        'field': input_field,
                        'table': input_table
                    }
                
                # Handle context field mapping
                if context_field and context_table and context_id:
                    if 'user_context_mappings' not in config['settings']['llm']:
                        config['settings']['llm']['user_context_mappings'] = {}
                    
                    config['settings']['llm']['user_context_mappings'][context_id] = {
                        'field': context_field,
                        'table': context_table
                    }
                
                # Update the database
                cur.execute("""
                    UPDATE workflow_step_entity 
                    SET config = %s 
                    WHERE id = %s
                """, (json.dumps(config), step_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Field selection saved successfully'
                })

    except Exception as e:
        current_app.logger.error(f"Error saving field selection: {str(e)}")
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

@bp.route('/steps/<int:step_id>/field_selection', methods=['GET'])
@handle_workflow_errors
def get_field_selection(step_id):
    """Get the user's field selection for a workflow step."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get step configuration
                cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
                step = cur.fetchone()
                if not step:
                    return jsonify({'error': 'Step not found'}), 404

                config = step['config']
                if not config:
                    return jsonify({'success': True, 'data': None})

                llm_settings = config.get('settings', {}).get('llm', {})
                
                # Check for user output mapping
                user_output_mapping = llm_settings.get('user_output_mapping')
                
                # Check for user input mappings
                user_input_mappings = llm_settings.get('user_input_mappings', {})
                
                # Check for user context mappings
                user_context_mappings = llm_settings.get('user_context_mappings', {})
                
                # Fallback to default mapping if no user mapping
                if not user_output_mapping:
                    default_mapping = llm_settings.get('output_mapping')
                    if default_mapping:
                        user_output_mapping = default_mapping

                # Return both input and output mappings
                result = {
                    'output': user_output_mapping,
                    'inputs': user_input_mappings,
                    'context': user_context_mappings
                }

                # Always return success, even if no mapping found
                return jsonify({'success': True, 'data': result})

    except Exception as e:
        current_app.logger.error(f"Error getting field selection: {str(e)}")
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

@bp.route('/posts/<int:post_id>/<stage>/<substage>/llm', methods=['POST'])
def run_workflow_llm(post_id, stage, substage):
    # DIRECT FILE LOGGING - GUARANTEED TO WORK
    import os
    from datetime import datetime
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Write immediate function entry log
    with open('logs/planning_stage_direct.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] FUNCTION CALLED - post_id: {post_id}, stage: {stage}, substage: {substage}\n")
        f.write(f"[{datetime.now().isoformat()}] Request method: {request.method}\n")
        f.write(f"[{datetime.now().isoformat()}] Request headers: {dict(request.headers)}\n")
        f.flush()  # Force immediate write
    
    # FORCE LOGGING TEST
    current_app.logger.error("=== FORCE LOGGING TEST - FUNCTION CALLED ===")
    print("=== PRINT TEST - FUNCTION CALLED ===")
    """Run LLM processing for a workflow step using Live Preview content."""
    try:
        data = request.get_json()
        step = data.get('step')
        preview_content = data.get('preview_content')
        
        if not step:
            return jsonify({'error': 'Step parameter is required'}), 400
        
        if not preview_content:
            return jsonify({'error': 'Live Preview content is required'}), 400
        
        # Convert step name from URL format to database format
        import re
        step_db = re.sub(r'\b\w', lambda m: m.group(0).upper(), step.replace('_', ' '))
        
        # Get LLM configuration from database
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT provider_type, model_name, api_base
                FROM llm_config
                WHERE is_active = true
                ORDER BY id DESC
                LIMIT 1
            """)
            config = cur.fetchone()
            if not config:
                # Fallback to default configuration
                config = {
                    'provider_type': 'ollama',
                    'model_name': 'llama3.1:70b',
                    'api_base': 'http://localhost:11434'
                }
        
        # Call LLM directly with the preview content
        import requests
        llm_request = {
            "model": config['model_name'],
            "prompt": preview_content,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        response = requests.post(
            f"{config['api_base']}/api/generate",
            json=llm_request,
            timeout=60
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'LLM request failed: {response.text}'}), 500
        
        result = response.json()
        output = result.get('response', '')
        
        # Save output to database
        output_field = None
        output_table = None
        step_result = None
        config_data = None
        output_mapping = None
        
        # DIRECT FILE LOGGING - VARIABLE INITIALIZATION
        with open('logs/planning_stage_direct.log', 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] VARIABLE INIT - output_field: {output_field}, output_table: {output_table}\n")
            f.write(f"[{datetime.now().isoformat()}] Step DB name: {step_db}\n")
            f.flush()
        
        current_app.logger.info(f"[PLANNING_LLM] Starting output mapping extraction for step: {step_db}")
        
        try:
            with get_db_conn() as conn:
                cur = conn.cursor()
                # Get step configuration to determine output field
                current_app.logger.info(f"[PLANNING_LLM] Executing database query for step: {step_db}")
                cur.execute("""
                    SELECT config FROM workflow_step_entity 
                    WHERE name ILIKE %s
                """, (step_db,))
                step_result = cur.fetchone()
                
                # DIRECT FILE LOGGING - DATABASE QUERY RESULT
                with open('logs/planning_stage_direct.log', 'a') as f:
                    f.write(f"[{datetime.now().isoformat()}] DB QUERY RESULT - step_result found: {step_result is not None}\n")
                    f.write(f"[{datetime.now().isoformat()}] step_result type: {type(step_result)}\n")
                    if step_result:
                        f.write(f"[{datetime.now().isoformat()}] step_result keys: {list(step_result.keys())}\n")
                        f.write(f"[{datetime.now().isoformat()}] step_result['config'] type: {type(step_result['config'])}\n")
                        f.write(f"[{datetime.now().isoformat()}] step_result['config'] value: {step_result['config']}\n")
                    f.flush()
                
                current_app.logger.info(f"[PLANNING_LLM] Step result found: {step_result is not None}")
                
                if step_result and step_result['config']:
                    # DIRECT FILE LOGGING - CONFIG PARSING
                    with open('logs/planning_stage_direct.log', 'a') as f:
                        f.write(f"[{datetime.now().isoformat()}] CONFIG PARSING - step_result['config'] type: {type(step_result['config'])}\n")
                        f.write(f"[{datetime.now().isoformat()}] CONFIG PARSING - step_result['config'] value: {step_result['config']}\n")
                        f.flush()
                    
                    current_app.logger.info(f"[PLANNING_LLM] Step result['config'] type: {type(step_result['config'])}")
                    current_app.logger.info(f"[PLANNING_LLM] Step result['config'] value: {step_result['config']}")
                    
                    # Handle both string and dict types
                    if isinstance(step_result['config'], str):
                        import json
                        config_data = json.loads(step_result['config'])
                        current_app.logger.info(f"[PLANNING_LLM] Parsed config from string, type: {type(config_data)}")
                    else:
                        config_data = step_result['config']
                        current_app.logger.info(f"[PLANNING_LLM] Using config directly as dict, type: {type(config_data)}")
                    
                    current_app.logger.info(f"[PLANNING_LLM] Config data keys: {list(config_data.keys()) if config_data else 'None'}")
                    
                    # DIRECT FILE LOGGING - CONFIG DATA
                    with open('logs/planning_stage_direct.log', 'a') as f:
                        f.write(f"[{datetime.now().isoformat()}] CONFIG DATA - keys: {list(config_data.keys()) if config_data else 'None'}\n")
                        f.flush()
                    
                    settings = config_data.get('settings', {})
                    current_app.logger.info(f"[PLANNING_LLM] Settings found: {settings is not None}")
                    current_app.logger.info(f"[PLANNING_LLM] Settings keys: {list(settings.keys()) if settings else 'None'}")
                    
                    # DIRECT FILE LOGGING - SETTINGS
                    with open('logs/planning_stage_direct.log', 'a') as f:
                        f.write(f"[{datetime.now().isoformat()}] SETTINGS - found: {settings is not None}\n")
                        f.write(f"[{datetime.now().isoformat()}] SETTINGS - keys: {list(settings.keys()) if settings else 'None'}\n")
                        f.flush()
                    
                    llm_settings = settings.get('llm', {})
                    current_app.logger.info(f"[PLANNING_LLM] LLM settings found: {llm_settings is not None}")
                    current_app.logger.info(f"[PLANNING_LLM] LLM settings keys: {list(llm_settings.keys()) if llm_settings else 'None'}")
                    
                    # DIRECT FILE LOGGING - LLM SETTINGS
                    with open('logs/planning_stage_direct.log', 'a') as f:
                        f.write(f"[{datetime.now().isoformat()}] LLM SETTINGS - found: {llm_settings is not None}\n")
                        f.write(f"[{datetime.now().isoformat()}] LLM SETTINGS - keys: {list(llm_settings.keys()) if llm_settings else 'None'}\n")
                        f.flush()
                    
                    output_mapping = llm_settings.get('user_output_mapping', {})
                    current_app.logger.info(f"[PLANNING_LLM] Output mapping extracted: {output_mapping}")
                    
                    # DIRECT FILE LOGGING - OUTPUT MAPPING
                    with open('logs/planning_stage_direct.log', 'a') as f:
                        f.write(f"[{datetime.now().isoformat()}] OUTPUT MAPPING - extracted: {output_mapping}\n")
                        f.flush()
                    
                    output_field = output_mapping.get('field')
                    output_table = output_mapping.get('table', 'post_development')
                    
                    # DIRECT FILE LOGGING - FINAL VARIABLES
                    with open('logs/planning_stage_direct.log', 'a') as f:
                        f.write(f"[{datetime.now().isoformat()}] FINAL VARIABLES - output_field: {output_field}\n")
                        f.write(f"[{datetime.now().isoformat()}] FINAL VARIABLES - output_table: {output_table}\n")
                        f.write(f"[{datetime.now().isoformat()}] output_mapping: {output_mapping}\n")
                        f.flush()
                    
                    current_app.logger.info(f"[PLANNING_LLM] Final output_field: {output_field}")
                    current_app.logger.info(f"[PLANNING_LLM] Final output_table: {output_table}")
                    
                    if output_field and output_table:
                        current_app.logger.info(f"[PLANNING_LLM] Both field and table found, executing database update")
                        update_sql = f"UPDATE {output_table} SET {output_field} = %s WHERE post_id = %s"
                        current_app.logger.info(f"[PLANNING_LLM] Update SQL: {update_sql}")
                        cur.execute(update_sql, (output, post_id))
                        conn.commit()
                        current_app.logger.info(f"[PLANNING_LLM] Database update completed successfully")
                    else:
                        current_app.logger.info(f"[PLANNING_LLM] Missing field or table - field: {output_field}, table: {output_table}")
                else:
                    current_app.logger.info(f"[PLANNING_LLM] No step result found or step result is empty")
        except Exception as e:
            current_app.logger.error(f"[PLANNING_LLM] Error in database operations: {str(e)}")
            current_app.logger.error(f"Error saving output: {str(e)}")
        
        # Log response diagnostic information
        import os
        from datetime import datetime
        
        print(f"[PLANNING_LLM] Writing diagnostic log - output_field: {output_field}, output_table: {output_table}")
        
        response_log = f"""# LLM Response Diagnostic Log (Planning Stage)
# Post ID: {post_id}
# Stage: {stage}
# Substage: {substage}
# Step: {step} -> {step_db}
# Timestamp: {datetime.now().isoformat()}
# Log Type: llm_response_planning_stage

=== LLM OUTPUT ===
{output}

=== OUTPUT MAPPING ===
Field: {output_field}
Table: {output_table}

=== DEBUG INFO ===
Step DB Name: {step_db}
Step Result Found: {step_result is not None}
Config Data Type: {type(config_data) if config_data else 'Not set'}
Output Mapping: {output_mapping}
Raw Config Data: {config_data}

=== COMPREHENSIVE LOGGING ===
Variables at log time:
- output_field: {output_field}
- output_table: {output_table}
- step_result: {step_result is not None}
- config_data: {type(config_data) if config_data else 'None'}
- output_mapping: {output_mapping}
"""
        
        # Write response diagnostic log
        os.makedirs('logs', exist_ok=True)
        with open('logs/workflow_diagnostic_llm_response.txt', 'w') as f:
            f.write(response_log)
        
        # DIRECT FILE LOGGING - FUNCTION COMPLETION
        with open('logs/planning_stage_direct.log', 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] FUNCTION COMPLETED SUCCESSFULLY\n")
            f.write(f"[{datetime.now().isoformat()}] Final output_field: {output_field}\n")
            f.write(f"[{datetime.now().isoformat()}] Final output_table: {output_table}\n")
            f.flush()
        
        return jsonify({
            'success': True,
            'output': output,
            'step': step
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in run_workflow_llm: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/<stage>/<substage>/writing_llm', methods=['POST'])
def run_writing_llm(post_id, stage, substage):
    """Run LLM for Writing stage with section-specific processing."""
    try:
        data = request.get_json()
        step = data.get('step')
        section_ids = data.get('selected_section_ids', [])
        frontend_inputs = data.get('inputs', {})
        
        print(f"[WRITING_LLM] Processing step: {step}")
        print(f"[WRITING_LLM] Section IDs: {section_ids}")
        print(f"[WRITING_LLM] Frontend inputs: {frontend_inputs}")
        
        # Log diagnostic information
        import os
        from datetime import datetime
        
        diagnostic_log = f"""# LLM Message Diagnostic Log (Writing Stage)
# Post ID: {post_id}
# Stage: {stage}
# Substage: {substage}
# Step: {step}
# Timestamp: {datetime.now().isoformat()}
# Log Type: llm_message_writing_stage

=== FRONTEND PROMPT ===
{frontend_inputs.get('prompt', 'No prompt provided')}

=== SECTION IDs ===
{section_ids}

=== OUTPUT MAPPING ===
Field: {frontend_inputs.get('output_field', 'Not specified')}
Table: {frontend_inputs.get('output_table', 'Not specified')}
"""
        
        # Write diagnostic log
        os.makedirs('logs', exist_ok=True)
        with open('logs/workflow_diagnostic_llm_message.txt', 'w') as f:
            f.write(diagnostic_log)
        
        result = process_writing_step(post_id, stage, substage, step, section_ids, frontend_inputs)
        
        print(f"[WRITING_LLM] Result success: {result.get('success')}")
        if result.get('success'):
            print(f"[WRITING_LLM] Processed {len(result.get('parameters', {}).get('sections_processed', []))} sections")
            
            # Log response diagnostic information
            response_log = f"""# LLM Response Diagnostic Log (Writing Stage)
# Post ID: {post_id}
# Stage: {stage}
# Substage: {substage}
# Step: {step}
# Timestamp: {datetime.now().isoformat()}
# Log Type: llm_response_writing_stage
# Frontend Inputs: {frontend_inputs}

"""
            
            # Add results to response log
            for section_id, section_result in result.get('results', {}).items():
                if section_result.get('success'):
                    response_log += f"=== SECTION {section_id} RESULT ===\n{section_result.get('result', 'No result')}\n\n"
                else:
                    response_log += f"=== SECTION {section_id} ERROR ===\n{section_result.get('error', 'Unknown error')}\n\n"
            
            # Write response diagnostic log
            with open('logs/workflow_diagnostic_llm_response.txt', 'w') as f:
                f.write(response_log)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[WRITING_LLM] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/llm/models', methods=['GET'])
@handle_workflow_errors
def get_llm_models():
    """Get all available LLM models from the database (DEV49 logic)."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Get all models with provider information
        cur.execute("""
            SELECT 
                m.id,
                m.name,
                m.provider_id,
                m.description,
                m.strengths,
                p.name as provider_name,
                p.type as provider_type
            FROM llm_model m
            JOIN llm_provider p ON p.id = m.provider_id
            ORDER BY m.name
        """)
        models = cur.fetchall()
        return jsonify([
            {
                'id': str(m['id']),
                'name': m['name'],
                'provider': m['provider_name'],
                'capabilities': [m['strengths']] if m['strengths'] else [],
                'description': m['description'],
                'provider_type': m['provider_type']
            } for m in models
        ])

@bp.route('/substages/<stage>/<substage>/first-step', methods=['GET'])
@handle_workflow_errors
def get_first_step_for_substage(stage, substage):
    """Get the first step for a given stage and substage."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get the first step (lowest step_order) for the given stage/substage
            cur.execute("""
                SELECT 
                    wse.id,
                    wse.name as step_name,
                    wse.description,
                    wse.step_order,
                    wsse.name as substage_name,
                    wst.name as stage_name
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                ORDER BY wse.step_order
                LIMIT 1
            """, (stage, substage))
            
            step = cur.fetchone()
            if not step:
                return jsonify({'error': 'No steps found for this substage'}), 404
                
            return jsonify({
                'id': step['id'],
                'name': step['step_name'],
                'description': step['description'],
                'step_order': step['step_order'],
                'substage_name': step['substage_name'],
                'stage_name': step['stage_name'],
                'url_name': step['step_name'].lower().replace(' ', '_')
            })

@bp.route('/posts/<int:post_id>/sync-sections', methods=['POST'])
@handle_workflow_errors
def sync_sections(post_id):
    """Synchronize sections between post_development.section_headings and post_section table."""
    try:
        data = request.get_json() or {}
        direction = data.get('direction', 'both')  # 'to_sections', 'to_headings', or 'both'
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Verify post exists
                cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
                if not cur.fetchone():
                    return jsonify({'error': 'Post not found'}), 404
                
                # Get current state
                cur.execute("""
                    SELECT section_headings 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                dev_result = cur.fetchone()
                
                cur.execute("""
                    SELECT section_order, section_heading, section_description, status
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                
                changes = []
                
                if direction in ['to_sections', 'both'] and dev_result and dev_result['section_headings']:
                    # Sync from section_headings to post_section
                    try:
                        # Try to parse as direct JSON first
                        headings_text = dev_result['section_headings']
                        headings_data = None
                        
                        # Try direct JSON parsing
                        try:
                            headings_data = json.loads(headings_text)
                        except json.JSONDecodeError:
                            # Try to extract JSON from markdown code blocks
                            import re
                            json_match = re.search(r'```json\s*\n(.*?)\n```', headings_text, re.DOTALL)
                            if json_match:
                                try:
                                    headings_data = json.loads(json_match.group(1))
                                except json.JSONDecodeError:
                                    pass
                        
                        if headings_data and isinstance(headings_data, list):
                            # Clear existing sections
                            cur.execute("DELETE FROM post_section WHERE post_id = %s", (post_id,))
                            
                            # Insert new sections from section_headings
                            for i, heading in enumerate(headings_data):
                                if isinstance(heading, dict):
                                    title = heading.get('title', heading.get('heading', f'Section {i+1}'))
                                    description = heading.get('description', '')
                                    
                                    cur.execute("""
                                        INSERT INTO post_section (
                                            post_id, section_order, section_heading, section_description, status
                                        ) VALUES (%s, %s, %s, %s, %s)
                                    """, (post_id, i+1, title, description, 'draft'))
                            
                            changes.append(f"Created {len(headings_data)} sections from section_headings")
                        else:
                            changes.append("No valid JSON data found in section_headings")
                    except Exception as e:
                        changes.append(f"Error parsing section_headings: {str(e)}")
                
                if direction in ['to_headings', 'both'] and sections:
                    # Sync from post_section to section_headings
                    section_headings = []
                    for section in sections:
                        section_headings.append({
                            "order": section['section_order'],
                            "heading": section['section_heading'],
                            "description": section['section_description'] or "",
                            "status": section['status'] or "draft"
                        })
                    
                    # Update post_development
                    cur.execute("""
                        UPDATE post_development 
                        SET section_headings = %s
                        WHERE post_id = %s
                    """, (json.dumps(section_headings), post_id))
                    
                    changes.append(f"Updated section_headings with {len(sections)} sections")
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Synchronization completed: {", ".join(changes)}',
                    'changes': changes,
                    'direction': direction
                })
                
    except Exception as e:
        current_app.logger.error(f"Error syncing sections for post {post_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500 

@bp.route('/fields/post_section', methods=['GET'])
@handle_workflow_errors
def get_post_section_fields():
    """Get all available fields from the post_section table for Writing stage."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get column information for post_section table
            cur.execute("""
                SELECT 
                    column_name as field_name,
                    column_name as display_name
                FROM information_schema.columns 
                WHERE table_name = 'post_section' 
                AND column_name NOT IN ('id', 'post_id', 'section_order', 'image_id', 'image_prompt_example_id')
                ORDER BY ordinal_position
            """)
            fields = cur.fetchall()
            
            # Convert to list of dictionaries with better display names
            field_list = []
            for field in fields:
                field_dict = dict(field)
                # Create a better display name
                display_name = field_dict['field_name'].replace('_', ' ').title()
                field_dict['display_name'] = display_name
                field_list.append(field_dict)
            
            return jsonify(field_list) 

@bp.route('/post_section_fields', methods=['GET'])
def get_post_section_text_fields():
    """Return a list of text/content fields in the post_section table."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'post_section'
            """)
            columns = cur.fetchall()
    # Only include text/content fields
    text_types = {'text', 'character varying', 'varchar'}
    exclude = {'id', 'post_id', 'section_order', 'image_id', 'image_prompt_example_id'}
    fields = [col['column_name'] for col in columns if col['data_type'] in text_types and col['column_name'] not in exclude]
    return jsonify({'fields': fields})

@bp.route('/debug/context/<int:post_id>/<stage>/<substage>/<step>', methods=['GET'])
def get_debug_context(post_id, stage, substage, step):
    """Get diagnostic context data for the context management interface."""
    try:
        # Read the most recent diagnostic log for this step
        import os
        import glob
        
        # Look for diagnostic logs in the logs directory
        log_pattern = f"logs/workflow_diagnostic_llm_message.txt"
        diagnostic_log = ""
        
        if os.path.exists(log_pattern):
            with open(log_pattern, 'r') as f:
                diagnostic_log = f.read()
        
        # Also try to get the database fields log
        db_fields_log = ""
        db_log_pattern = f"logs/workflow_diagnostic_db_fields.json"
        if os.path.exists(db_log_pattern):
            with open(db_log_pattern, 'r') as f:
                db_fields_log = f.read()
        
        return jsonify({
            'success': True,
            'diagnostic_log': diagnostic_log,
            'db_fields_log': db_fields_log,
            'metadata': {
                'post_id': post_id,
                'stage': stage,
                'substage': substage,
                'step': step,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting debug context: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 

@bp.route('/steps/<int:step_id>/context-config', methods=['POST'])
def save_context_config(step_id):
    """Save context management configuration for a workflow step."""
    data = request.get_json()
    config = data.get('context_sections')
    created_at = data.get('created_at')
    if not config:
        return jsonify({'success': False, 'error': 'No config provided'}), 400
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO workflow_step_context_config (step_id, config, created_at)
                VALUES (%s, %s, %s)
                """,
                (step_id, json.dumps(config), created_at)
            )
            conn.commit()
    return jsonify({'success': True}) 

@bp.route('/test-logging', methods=['GET'])
def test_logging():
    current_app.logger.error("=== TEST LOGGING ENDPOINT CALLED ===")
    print("=== PRINT TEST ENDPOINT CALLED ===")
    return jsonify({"status": "logging test"})

@bp.route('/llm/direct', methods=['POST'])
@handle_workflow_errors
def direct_llm_call():
    """Send preview content directly to LLM."""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        post_id = data.get('post_id')
        step = data.get('step')
        
        if not prompt:
            return jsonify({'error': 'Prompt content is required'}), 400
        
        # Log diagnostic information
        import os
        from datetime import datetime
        
        diagnostic_log = f"""# LLM Message Diagnostic Log
# Post ID: {post_id}
# Stage: planning
# Substage: structure
# Step: {step}
# Timestamp: {datetime.now().isoformat()}
# Log Type: llm_message

{prompt}"""
        
        # Write diagnostic log
        os.makedirs('logs', exist_ok=True)
        with open('logs/workflow_diagnostic_llm_message.txt', 'w') as f:
            f.write(diagnostic_log)
        
        # Get LLM configuration from database
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT provider_type, model_name, api_base
                FROM llm_config
                WHERE is_active = true
                ORDER BY id DESC
                LIMIT 1
            """)
            config = cur.fetchone()
            if not config:
                # Fallback to default configuration
                config = {
                    'provider_type': 'ollama',
                    'model_name': 'llama3.1:70b',
                    'api_base': 'http://localhost:11434'
                }
        
        # Call LLM directly with the preview content
        import requests
        llm_request = {
            "model": config['model_name'],
            "prompt": prompt,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        response = requests.post(
            f"{config['api_base']}/api/generate",
            json=llm_request,
            timeout=60
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'LLM request failed: {response.text}'}), 500
        
        result = response.json()
        output = result.get('response', '')
        
        # Clean the output by removing any trailing characters that aren't part of the JSON
        output = output.strip()
        if output.endswith('%'):
            output = output[:-1].strip()
            
        # For preview, return the raw text
        preview_output = output
        
        # For database storage, try to parse as JSON
        json_output = None
        try:
            # Remove newlines and extra spaces from the output
            json_text = output.replace('\n', '').replace('\\n', '')
            # Parse the output as JSON to validate it
            json_output = json.loads(json_text)
        except json.JSONDecodeError:
            current_app.logger.info("Output is not JSON, using raw text")
            json_output = output
        
        # Save output to database
        try:
            with get_db_conn() as conn:
                cur = conn.cursor()
                # Get step configuration to determine output field
                cur.execute("""
                    SELECT config FROM workflow_step_entity 
                    WHERE name ILIKE %s
                """, (step,))
                step_result = cur.fetchone()
                
                if step_result and step_result[0]:
                    import json
                    config_data = json.loads(step_result[0])
                    output_mapping = config_data.get('settings', {}).get('llm', {}).get('user_output_mapping', {})
                    output_field = output_mapping.get('field')
                    output_table = output_mapping.get('table', 'post_development')
                    
                    if output_field and output_table:
                        if output_table == 'post_development':
                            cur.execute(f"""
                                UPDATE post_development 
                                SET {output_field} = %s 
                                WHERE post_id = %s
                            """, (json.dumps(json_output) if isinstance(json_output, (dict, list)) else json_output, post_id))
                            
                            # If this is the section_headings field, sync to post_section table
                            if output_field == 'section_headings' and isinstance(json_output, list):
                                # Clear existing sections
                                cur.execute("DELETE FROM post_section WHERE post_id = %s", (post_id,))
                                
                                # Insert new sections
                                for i, heading in enumerate(json_output):
                                    if isinstance(heading, dict):
                                        title = heading.get('title', heading.get('heading', f'Section {i+1}'))
                                        description = heading.get('description', '')
                                        
                                        cur.execute("""
                                            INSERT INTO post_section (
                                                post_id, section_order, section_heading, section_description, status
                                            ) VALUES (%s, %s, %s, %s, %s)
                                        """, (post_id, i+1, title, description, 'draft'))
                            
                        conn.commit()
        except Exception as e:
            current_app.logger.error(f"Error saving output: {str(e)}")
        
        # Log response diagnostic information
        response_log = f"""# LLM Response Diagnostic Log
# Post ID: {post_id}
# Stage: planning
# Substage: structure
# Step: {step}
# Timestamp: {datetime.now().isoformat()}
# Log Type: llm_response
# Frontend Inputs: {{}}

{preview_output}"""
        
        # Write response diagnostic log
        with open('logs/workflow_diagnostic_llm_response.txt', 'w') as f:
            f.write(response_log)
        
        return jsonify({
            'success': True,
            'result': preview_output
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in direct LLM call: {str(e)}")
        return jsonify({'error': str(e)}), 500 

@bp.route('/test-direct-file', methods=['GET'])
def test_direct_file():
    with open('logs/direct_file_test.log', 'a') as f:
        f.write('Direct file write test - route executed\n')
    return jsonify({"status": "direct file write test"})

@bp.route('/test-logging-advanced', methods=['GET'])
def test_logging_advanced():
    # Print to stdout
    print('PRINT STDOUT: test_logging_advanced called')
    # Print to stderr
    sys.stderr.write('PRINT STDERR: test_logging_advanced called\n')
    # Add a new file handler at runtime
    handler = logging.FileHandler('logs/runtime_added_handler.log')
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
    current_app.logger.addHandler(handler)
    current_app.logger.info('RUNTIME LOGGER: test_logging_advanced called')
    handler.flush()
    return jsonify({'status': 'logging advanced test'})