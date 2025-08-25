from flask import Flask, jsonify, request
from db import get_db_conn

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/workflow/posts/<int:post_id>/sections', methods=['GET', 'POST'])
def manage_sections(post_id):
    if request.method == 'GET':
        # Get all sections for a post
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        id, section_heading AS title, section_description AS description, section_order AS order_index,
                        ideas_to_include, facts_to_include, draft AS content, polished, highlighting, image_concepts, image_prompts,
                        watermarking, image_meta_descriptions, image_captions, generated_image_url, image_generation_metadata, image_id, status
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
        return jsonify({'sections': sections})
    else:  # POST
        data = request.get_json()
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO post_section (
                        post_id, section_heading, section_description, section_order
                    ) VALUES (%s, %s, %s, %s)
                    RETURNING id, section_heading AS title, section_description AS description, section_order AS order_index
                """, (
                    post_id,
                    data.get('title'),
                    data.get('description'),
                    data.get('orderIndex')
                ))
                section = cur.fetchone()
                conn.commit()
        return jsonify(section), 201

@app.route('/api/workflow/posts/<int:post_id>/sections/<int:section_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_section(post_id, section_id):
    if request.method == 'GET':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        id, section_heading AS title, section_description AS description, section_order AS order_index,
                        ideas_to_include, facts_to_include, draft AS content, polished, highlighting, image_concepts, image_prompts,
                        watermarking, image_meta_descriptions, image_captions, generated_image_url, image_generation_metadata, image_id, status
                    FROM post_section
                    WHERE post_id = %s AND id = %s
                """, (post_id, section_id))
                section = cur.fetchone()
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        return jsonify(section)
    elif request.method == 'PUT':
        data = request.get_json()
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE post_section SET
                        section_heading = %s,
                        section_description = %s,
                        section_order = %s
                    WHERE id = %s AND post_id = %s
                    RETURNING id, section_heading AS title, section_description AS description, section_order AS order_index
                """, (
                    data.get('title'),
                    data.get('description'),
                    data.get('orderIndex'),
                    section_id,
                    post_id
                ))
                section = cur.fetchone()
                conn.commit()
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        return jsonify(section)
    else:  # DELETE
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM post_section WHERE id = %s AND post_id = %s RETURNING id", (section_id, post_id))
                deleted = cur.fetchone()
                conn.commit()
        if not deleted:
            return jsonify({'error': 'Section not found'}), 404
        return jsonify({'deleted': deleted['id']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
