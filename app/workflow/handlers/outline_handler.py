import json
from typing import Dict, Any
from app.db import get_db_conn

def process_outline_output(post_id: int, outline_data: str) -> Dict[str, Any]:
    """
    Process the outline data from the LLM output and create/update post_section records.
    
    Args:
        post_id: The ID of the post
        outline_data: JSON string containing an array of section objects
        
    Returns:
        Dict containing status and any error messages
    """
    try:
        # Parse the outline data
        sections = json.loads(outline_data)
        
        # Validate that we have an array
        if not isinstance(sections, list):
            return {
                'status': 'error',
                'message': 'Outline data must be an array of section objects'
            }
            
        # Validate required fields for each section
        required_fields = ['title', 'description', 'contents']
        for i, section in enumerate(sections):
            if not all(field in section for field in required_fields):
                return {
                    'status': 'error',
                    'message': f'Missing required fields in section {i+1}. Required: {required_fields}'
                }
            
        # Get database connection
        conn = get_db_conn()
        cur = conn.cursor()
        
        try:
            # Start transaction
            cur.execute('BEGIN')
            
            # Delete existing post_section_elements rows for this post
            cur.execute('DELETE FROM post_section_elements WHERE section_id IN (SELECT id FROM post_section WHERE post_id = %s)', (post_id,))
            
            # Delete existing sections for this post
            cur.execute('DELETE FROM post_section WHERE post_id = %s', (post_id,))
            
            # Insert new sections
            for i, section in enumerate(sections, 1):
                cur.execute("""
                    INSERT INTO post_section 
                    (post_id, section_order, section_heading, section_description, ideas_to_include)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    post_id,
                    i,  # Section order
                    section['title'],
                    section['description'],
                    json.dumps(section['contents'])  # Store contents array as JSON string
                ))
            
            # Commit transaction
            conn.commit()
            
            return {
                'status': 'success',
                'message': f'Successfully processed {len(sections)} sections into post_section'
            }
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            return {
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }
            
        finally:
            cur.close()
            conn.close()
            
    except json.JSONDecodeError:
        return {
            'status': 'error',
            'message': 'Invalid JSON in outline data'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error processing outline: {str(e)}'
        } 