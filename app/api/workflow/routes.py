from flask import Blueprint, jsonify, request, current_app
from app.db import get_db_conn
import psycopg2.extras
from app.api.workflow.decorators import handle_workflow_errors
import json

from . import bp

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
            # Get all sections with their elements
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
                WHERE s.post_id = %s
                GROUP BY s.id, s.section_heading, s.section_description, s.section_order
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
            # Get section details with elements
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
            if not section:
                return jsonify({'error': 'Section not found'}), 404
                
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
            })
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            try:
                # Start transaction
                cur.execute("BEGIN")
                
                # Update section
                cur.execute("""
                    UPDATE post_section
                    SET section_heading = %s,
                        section_description = %s,
                        section_order = %s
                    WHERE post_id = %s AND id = %s
                    RETURNING id, section_heading, section_description, section_order
                """, (
                    data.get('title'),
                    data.get('description'),
                    data.get('orderIndex'),
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
                
                # Return updated section with elements
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

        post_id = data.get('post_id')
        output_field = data.get('output_field')
        output_table = data.get('output_table')
        
        if not all([post_id, output_field, output_table]):
            return jsonify({'error': 'post_id, output_field, and output_table are required'}), 400

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

@bp.route('/steps/<int:step_id>/field_selection/<int:post_id>', methods=['GET'])
@handle_workflow_errors
def get_field_selection(step_id, post_id):
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
                    return jsonify({'error': 'Step has no configuration'}), 404

                # Check for user output mapping
                user_mapping = None
                if (config.get('settings', {}).get('llm', {}).get('user_output_mapping')):
                    user_mapping = config['settings']['llm']['user_output_mapping']
                
                # Fallback to default mapping if no user mapping
                if not user_mapping:
                    default_mapping = config.get('settings', {}).get('llm', {}).get('output_mapping')
                    if default_mapping:
                        user_mapping = default_mapping

                if not user_mapping:
                    return jsonify({'error': 'No output mapping found'}), 404

                return jsonify({
                    'success': True,
                    'data': user_mapping
                })

    except Exception as e:
        current_app.logger.error(f"Error getting field selection: {str(e)}")
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

@bp.route('/posts/<int:post_id>/<stage>/<substage>/llm', methods=['POST'])
@handle_workflow_errors
def run_workflow_llm(post_id, stage, substage):
    """Execute an LLM request for a specific workflow step."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        step = data.get('step')
        if not step:
            return jsonify({'error': 'Step is required'}), 400

        # Import the process_step function from the workflow scripts
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'workflow', 'scripts'))
        from llm_processor import process_step

        # Execute the LLM step
        result = process_step(post_id, stage, substage, step)

        return jsonify({
            'success': True,
            'data': {'result': result},
            'error': None
        })

    except Exception as e:
        current_app.logger.error(f"Error running LLM for step {step}: {str(e)}")
        return jsonify({
            'success': False,
            'data': None,
            'error': {'message': str(e)}
        }), 500 