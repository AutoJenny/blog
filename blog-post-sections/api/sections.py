import json
import os
import psycopg2
import psycopg2.extras
from flask import Blueprint, request, jsonify, render_template
from database import get_db_conn

bp = Blueprint('sections', __name__, url_prefix='/api/sections')

def find_section_image(post_id, section_id):
    """
    Find the first available image for a section in the new directory structure.
    Returns the image path or None if no image found.
    """
    # Path to the blog-images static directory
    blog_images_static = "/Users/nickfiddes/Code/projects/blog/blog-images/static"
    
    # Look for images in the section's raw directory
    section_raw_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "sections", str(section_id), "raw")
    
    if os.path.exists(section_raw_path):
        # Get all image files in the raw directory
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
        image_files = [f for f in os.listdir(section_raw_path) 
                      if f.lower().endswith(image_extensions) and not f.startswith('.')]
        
        if image_files:
            # Return the first image found
            image_filename = image_files[0]
            # Return path relative to blog-images static directory for serving
            return f"/static/content/posts/{post_id}/sections/{section_id}/raw/{image_filename}"
    
    return None

@bp.route('/<int:post_id>', methods=['GET'])
def get_sections(post_id):
    """Get all sections for a post."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                
                # Convert to list of dictionaries and add image information
                sections_list = []
                for section in sections:
                    section_dict = dict(section)
                    
                    # Try to find image in the new directory structure first
                    image_path = find_section_image(post_id, section['id'])
                    
                    if image_path:
                        # Found image in new structure
                        section_dict['image'] = {
                            'path': image_path,
                            'alt_text': section.get('image_captions') or f"Image for {section.get('section_heading', 'section')}"
                        }
                    elif section.get('image_id'):
                        # Fallback to legacy image_id system
                        cur.execute("""
                            SELECT * FROM image WHERE id = %s
                        """, (section['image_id'],))
                        image = cur.fetchone()
                        if image:
                            section_dict['image'] = dict(image)
                    elif section.get('generated_image_url'):
                        # Fallback to generated_image_url
                        section_dict['image'] = {
                            'path': section['generated_image_url'],
                            'alt_text': section.get('image_captions') or 'Section image'
                        }
                    else:
                        # No image found - provide placeholder info
                        section_dict['image'] = {
                            'path': None,
                            'alt_text': f"No image available for {section.get('section_heading', 'this section')}",
                            'placeholder': True
                        }
                    
                    sections_list.append(section_dict)
                
                return jsonify({'sections': sections_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['POST'])
def create_section():
    """Create a new section."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        title = data.get('title', 'New Section')
        description = data.get('description', '')
        
        if not post_id:
            return jsonify({'error': 'post_id is required'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get the next section order
                cur.execute("""
                    SELECT COALESCE(MAX(section_order), 0) + 1 as next_order
                    FROM post_section 
                    WHERE post_id = %s
                """, (post_id,))
                result = cur.fetchone()
                section_order = result['next_order']
                
                # Insert the new section
                cur.execute("""
                    INSERT INTO post_section (
                        post_id, section_order, section_heading, section_description, status
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (post_id, section_order, title, description, 'draft'))
                
                new_section_id = cur.fetchone()['id']
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'section_id': new_section_id,
                    'message': 'Section created successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:section_id>', methods=['PUT'])
def update_section(section_id):
    """Update a section."""
    try:
        data = request.get_json()
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Build update query dynamically based on provided fields
                update_fields = []
                values = []
                
                if 'title' in data:
                    update_fields.append('section_heading = %s')
                    values.append(data['title'])
                
                if 'description' in data:
                    update_fields.append('section_description = %s')
                    values.append(data['description'])
                
                if 'orderIndex' in data:
                    update_fields.append('section_order = %s')
                    values.append(data['orderIndex'])
                
                if 'status' in data:
                    update_fields.append('status = %s')
                    values.append(data['status'])
                
                if 'draft' in data:
                    update_fields.append('draft = %s')
                    values.append(data['draft'])
                
                if 'polished' in data:
                    update_fields.append('polished = %s')
                    values.append(data['polished'])
                
                if 'facts_to_include' in data:
                    update_fields.append('facts_to_include = %s')
                    values.append(data['facts_to_include'])
                
                if 'ideas_to_include' in data:
                    update_fields.append('ideas_to_include = %s')
                    values.append(data['ideas_to_include'])
                
                if 'highlighting' in data:
                    update_fields.append('highlighting = %s')
                    values.append(data['highlighting'])
                
                if 'uk_british' in data:
                    update_fields.append('uk_british = %s')
                    values.append(data['uk_british'])
                
                if 'image_concepts' in data:
                    update_fields.append('image_concepts = %s')
                    values.append(data['image_concepts'])
                
                if 'image_prompts' in data:
                    update_fields.append('image_prompts = %s')
                    values.append(data['image_prompts'])
                
                if 'generation' in data:
                    update_fields.append('generation = %s')
                    values.append(data['generation'])
                
                if 'optimization' in data:
                    update_fields.append('optimization = %s')
                    values.append(data['optimization'])
                
                if 'watermarking' in data:
                    update_fields.append('watermarking = %s')
                    values.append(data['watermarking'])
                
                if 'image_id' in data:
                    update_fields.append('image_id = %s')
                    values.append(data['image_id'])
                
                if 'image_captions' in data:
                    update_fields.append('image_captions = %s')
                    values.append(data['image_captions'])
                
                if 'image_meta_descriptions' in data:
                    update_fields.append('image_meta_descriptions = %s')
                    values.append(data['image_meta_descriptions'])
                
                if 'generated_image_url' in data:
                    update_fields.append('generated_image_url = %s')
                    values.append(data['generated_image_url'])
                
                if 'image_generation_metadata' in data:
                    update_fields.append('image_generation_metadata = %s')
                    values.append(data['image_generation_metadata'])
                
                if not update_fields:
                    return jsonify({'error': 'No valid fields to update'}), 400
                
                # Add section_id to values
                values.append(section_id)
                
                # Execute update
                query = f"""
                    UPDATE post_section 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """
                cur.execute(query, values)
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Section not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Section updated successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:section_id>', methods=['DELETE'])
def delete_section(section_id):
    """Delete a section."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM post_section WHERE id = %s", (section_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Section not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Section deleted successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:section_id>/elements', methods=['GET'])
def get_section_elements(section_id):
    """Get all elements for a section."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM post_section_elements 
                    WHERE section_id = %s 
                    ORDER BY element_order
                """, (section_id,))
                elements = cur.fetchall()
                
                # Convert to list of dictionaries
                elements_list = []
                for element in elements:
                    element_dict = dict(element)
                    elements_list.append(element_dict)
                
                return jsonify({'elements': elements_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:section_id>/elements', methods=['POST'])
def create_section_element(section_id):
    """Create a new element for a section."""
    try:
        data = request.get_json()
        element_type = data.get('element_type')
        element_content = data.get('element_content', '')
        
        if not element_type:
            return jsonify({'error': 'element_type is required'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get the next element order
                cur.execute("""
                    SELECT COALESCE(MAX(element_order), 0) + 1 as next_order
                    FROM post_section_elements 
                    WHERE section_id = %s
                """, (section_id,))
                result = cur.fetchone()
                element_order = result['next_order']
                
                # Insert the new element
                cur.execute("""
                    INSERT INTO post_section_elements (
                        section_id, element_type, element_content, element_order
                    ) VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (section_id, element_type, element_content, element_order))
                
                new_element_id = cur.fetchone()['id']
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'element_id': new_element_id,
                    'message': 'Element created successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:section_id>/elements/<int:element_id>', methods=['PUT'])
def update_section_element(section_id, element_id):
    """Update a section element."""
    try:
        data = request.get_json()
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Build update query dynamically
                update_fields = []
                values = []
                
                if 'element_type' in data:
                    update_fields.append('element_type = %s')
                    values.append(data['element_type'])
                
                if 'element_content' in data:
                    update_fields.append('element_content = %s')
                    values.append(data['element_content'])
                
                if 'element_order' in data:
                    update_fields.append('element_order = %s')
                    values.append(data['element_order'])
                
                if not update_fields:
                    return jsonify({'error': 'No valid fields to update'}), 400
                
                # Add element_id to values
                values.append(element_id)
                
                # Execute update
                query = f"""
                    UPDATE post_section_elements 
                    SET {', '.join(update_fields)}
                    WHERE id = %s AND section_id = %s
                """
                values.append(section_id)
                cur.execute(query, values)
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Element not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Element updated successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:section_id>/elements/<int:element_id>', methods=['DELETE'])
def delete_section_element(section_id, element_id):
    """Delete a section element."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM post_section_elements 
                    WHERE id = %s AND section_id = %s
                """, (element_id, section_id))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Element not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Element deleted successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/sync/<int:post_id>', methods=['POST'])
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
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

@bp.route('/sync/status/<int:post_id>', methods=['GET'])
def get_sync_status(post_id):
    """Get sync status for a post."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get section_headings from post_development
                cur.execute("""
                    SELECT section_headings 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                dev_result = cur.fetchone()
                
                # Get sections from post_section
                cur.execute("""
                    SELECT COUNT(*) as section_count
                    FROM post_section 
                    WHERE post_id = %s
                """, (post_id,))
                sections_result = cur.fetchone()
                
                # Calculate sync status
                has_headings = dev_result and dev_result['section_headings']
                section_count = sections_result['section_count'] if sections_result else 0
                
                # Try to parse headings to get count
                headings_count = 0
                if has_headings:
                    try:
                        headings_data = json.loads(dev_result['section_headings'])
                        if isinstance(headings_data, list):
                            headings_count = len(headings_data)
                    except:
                        pass
                
                # Determine sync status
                if section_count == 0 and headings_count == 0:
                    status = 'empty'
                elif section_count == headings_count:
                    status = 'synced'
                else:
                    status = 'out_of_sync'
                
                return jsonify({
                    'post_id': post_id,
                    'status': status,
                    'section_count': section_count,
                    'headings_count': headings_count,
                    'has_headings': has_headings
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

@bp.route('/summary/<int:post_id>', methods=['GET'])
def summary_panel(post_id):
    """Render a summary of section headings and descriptions for a post."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT section_order, section_heading, section_description
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                return render_template('summary_panel.html', sections=sections, post_id=post_id)
    except Exception as e:
        return f"<div style='color:red;padding:1em;'>Error loading sections: {e}</div>", 500 

@bp.route('/reorder', methods=['POST'])
def reorder_section():
    """Reorder a section up or down in the list"""
    try:
        data = request.get_json()
        section_id = data.get('section_id')
        direction = data.get('direction')  # 'up' or 'down'
        
        if not section_id or not direction:
            return jsonify({'success': False, 'error': 'Missing section_id or direction'}), 400
        
        # Get current section
        current_section = get_section_by_id(section_id)
        if not current_section:
            return jsonify({'success': False, 'error': 'Section not found'}), 404
        
        # Get all sections for this post, ordered by section_order
        post_id = current_section['post_id']
        sections = get_sections_by_post_id(post_id)
        sections.sort(key=lambda x: x.get('section_order', 0))
        
        # Find current section index
        current_index = None
        for i, section in enumerate(sections):
            if section['id'] == int(section_id):
                current_index = i
                break
        
        if current_index is None:
            return jsonify({'success': False, 'error': 'Section not found in ordered list'}), 404
        
        # Calculate new index
        if direction == 'up' and current_index > 0:
            new_index = current_index - 1
        elif direction == 'down' and current_index < len(sections) - 1:
            new_index = current_index + 1
        else:
            return jsonify({'success': False, 'error': 'Cannot move section in that direction'}), 400
        
        # Swap section_order values
        current_order = sections[current_index]['section_order']
        target_order = sections[new_index]['section_order']
        
        # Update both sections
        update_section_order(section_id, target_order)
        update_section_order(sections[new_index]['id'], current_order)
        
        return jsonify({'success': True, 'message': f'Section moved {direction}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_section_by_id(section_id):
    """Get a section by its ID"""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM post_section 
                    WHERE id = %s
                """, (section_id,))
                section = cur.fetchone()
                return dict(section) if section else None
    except Exception as e:
        return None

def get_sections_by_post_id(post_id):
    """Get all sections for a post"""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                return [dict(section) for section in sections]
    except Exception as e:
        return []

def update_section_order(section_id, new_order):
    """Update a section's section_order"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE post_section SET section_order = %s WHERE id = %s",
                    (new_order, section_id)
                )
                conn.commit()
    except Exception as e:
        raise 