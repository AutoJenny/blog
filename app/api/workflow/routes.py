from flask import Blueprint, jsonify, request, current_app
from app.db import get_db_conn
import psycopg2.extras
from app.api.workflow.decorators import handle_workflow_errors
import json
# Removed import of deprecated llm_processor module
# Functions will be implemented directly in this file as needed
from datetime import datetime

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

def process_sections_sequentially(conn, post_id, step_id, section_ids, timeout_per_section):
    """Process sections sequentially with timeout."""
    results = {}
    total_time = 0
    
    for section_id in section_ids:
        start_time = datetime.now()
        
        try:
            # For now, just return a placeholder result
            # This would need to be implemented with the actual LLM processing logic
            results[section_id] = {
                "success": True,
                "result": f"Processed section {section_id}",
                "processing_time": 0
            }
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            results[section_id] = {
                "success": False,
                "error": str(e),
                "section_id": section_id,
                "processing_time": processing_time
            }
    
    return {
        "results": results,
        "summary": f"Processed {len(section_ids)} sections"
    }

def process_step(post_id, stage, substage, step, frontend_inputs=None):
    """Process a workflow step."""
    # This is a placeholder - the actual processing is now done in the endpoint
    # that uses Live Preview content
    return "Step processed using Live Preview content"

def process_writing_step(post_id, stage, substage, step, section_ids, frontend_inputs):
    """
    Process a Writing stage step with section-specific handling.
    
    This function is specifically for Writing stage processing that needs to handle
    section-specific output (saving to post_section table for specific sections).
    """
    try:
        conn = get_db_conn()
        step_id = get_step_id(conn, stage, substage, step)
        
        # If section_ids are provided, use sequential processing with section-specific prompts
        if section_ids:
            # Get timeout from request or use default
            timeout_per_section = frontend_inputs.get('timeout_per_section', 300) if frontend_inputs else 300
            
            # Process sections sequentially with section-specific prompts
            result = process_sections_sequentially(
                conn, post_id, step_id, section_ids, timeout_per_section
            )
            
            conn.close()
            
            # Return format expected by frontend
            return {
                'success': True,
                'results': result['results'],
                'summary': result['summary'],
                'parameters': {
                    'sections_processed': section_ids,
                    'timeout_per_section': timeout_per_section
                }
            }
        else:
            # Fallback to standard processing if no sections specified
            result = process_step(post_id, stage, substage, step, frontend_inputs)
            conn.close()
            
            return {
                'success': True,
                'results': [
                    {
                        'output': result
                    }
                ],
                'parameters': {
                    'sections_processed': []
                }
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
                         s.draft, s.polished, s.image_concepts, s.image_prompts, 
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
                             s.draft, s.polished, s.image_concepts, s.image_prompts,
                             s.watermarking, s.image_meta_descriptions, s.image_captions,
                             s.image_prompt_example_id, s.generated_image_url, s.image_generation_metadata, s.image_id
                """, (post_id, section_id))
                
                section = cur.fetchone()
                return jsonify({
                    'id': section['id'],
                    'title': section['title'],
                    'description': section['description'],
                    'orderIndex': section['order_index'],
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

@bp.route('/posts/<int:post_id>/fields/<field_name>', methods=['PUT'])
@handle_workflow_errors
def update_post_field(post_id, field_name):
    """Update a specific field value for a post."""
    data = request.get_json()
    if 'value' not in data:
        return jsonify({'error': 'Field value is required'}), 400
        
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # First verify post exists
            cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Post not found'}), 404
                
            # Verify field exists in post_development
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_development' 
                AND column_name = %s
            """, (field_name,))
            
            if not cur.fetchone():
                return jsonify({'error': 'Invalid field name'}), 400
                
            # Update the field
            query = f"UPDATE post_development SET {field_name} = %s WHERE post_id = %s"
            cur.execute(query, (data['value'], post_id))
            conn.commit()
            
            return jsonify({'message': 'Field updated successfully'})

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

        output_field = data.get('output_field')
        output_table = data.get('output_table')
        
        if not all([output_field, output_table]):
            return jsonify({'error': 'output_field and output_table are required'}), 400

        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # First verify step exists
                cur.execute("SELECT id, config FROM workflow_step_entity WHERE id = %s", (step_id,))
                step = cur.fetchone()
                if not step:
                    return jsonify({'error': 'Step not found'}), 404

                # Update the config with user output mapping
                config = step['config']
                if not config:
                    config = {}
                
                # Ensure settings.llm exists
                if 'settings' not in config:
                    config['settings'] = {}
                if 'llm' not in config['settings']:
                    config['settings']['llm'] = {}
                
                # Add user output mapping
                config['settings']['llm']['user_output_mapping'] = {
                    'field': output_field,
                    'table': output_table
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

                # Check for user output mapping
                user_mapping = None
                if (config.get('settings', {}).get('llm', {}).get('user_output_mapping')):
                    user_mapping = config['settings']['llm']['user_output_mapping']
                
                # Fallback to default mapping if no user mapping
                if not user_mapping:
                    default_mapping = config.get('settings', {}).get('llm', {}).get('output_mapping')
                    if default_mapping:
                        user_mapping = default_mapping

                # Always return success, even if no mapping found
                return jsonify({'success': True, 'data': user_mapping})

    except Exception as e:
        current_app.logger.error(f"Error getting field selection: {str(e)}")
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

@bp.route('/posts/<int:post_id>/<stage>/<substage>/llm', methods=['POST'])
def run_workflow_llm(post_id, stage, substage):
    """Run LLM processing for a workflow step using Live Preview content."""
    try:
        data = request.get_json()
        step = data.get('step')
        preview_content = data.get('preview_content')
        
        if not step:
            return jsonify({'error': 'Step parameter is required'}), 400
        
        if not preview_content:
            return jsonify({'error': 'Live Preview content is required'}), 400
        
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
                    config_data = step_result[0]
                    output_mapping = config_data.get('settings', {}).get('llm', {}).get('user_output_mapping', {})
                    output_field = output_mapping.get('field')
                    output_table = output_mapping.get('table', 'post_development')
                    
                    if output_field and output_table:
                        if output_table == 'post_development':
                            cur.execute(f"""
                                UPDATE post_development 
                                SET {output_field} = %s 
                                WHERE post_id = %s
                            """, (output, post_id))
                        
                        conn.commit()
        except Exception as e:
            current_app.logger.error(f"Error saving output: {str(e)}")
        
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
        
        print(f"[WRITING_LLM] Processing step: {step}, section_ids: {section_ids}, post_id: {post_id}")
        
        result = process_writing_step(post_id, stage, substage, step, section_ids, frontend_inputs)
        
        print(f"[WRITING_LLM] Result success: {result.get('success')}")
        
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
        
        # Log response diagnostic information
        response_log = f"""# LLM Response Diagnostic Log
# Post ID: {post_id}
# Stage: planning
# Substage: structure
# Step: {step}
# Timestamp: {datetime.now().isoformat()}
# Log Type: llm_response
# Frontend Inputs: {{}}

{output}"""
        
        # Write response diagnostic log
        with open('logs/workflow_diagnostic_llm_response.txt', 'w') as f:
            f.write(response_log)
        
        return jsonify({
            'success': True,
            'result': output
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in direct LLM call: {str(e)}")
        return jsonify({'error': str(e)}), 500 