import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, jsonify, request, current_app
import logging
import os

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="app/templates", static_folder="static")

# DB config (set these as environment variables or in your config)
app.config['DB_NAME'] = os.environ.get('DB_NAME', 'blog')
app.config['DB_USER'] = os.environ.get('DB_USER', 'bloguser')
app.config['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', 'blogpass')
app.config['DB_HOST'] = os.environ.get('DB_HOST', 'localhost')
app.config['DB_PORT'] = os.environ.get('DB_PORT', 5432)

def get_db_conn():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            host=app.config['DB_HOST'],
            port=app.config['DB_PORT'],
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

@app.route("/")
def sections_panel():
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, section_heading, section_description, ideas_to_include, status, section_order
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (22,))
                sections = cur.fetchall()
        return render_template("workflow/standalone_sections.html", sections=sections)
    except Exception as e:
        logger.error(f"Error loading sections: {str(e)}")
        return f"Error loading sections: {str(e)}", 500

@app.route("/api/sections/", methods=["GET", "POST"])
def api_sections():
    if request.method == "GET":
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, section_heading, section_description, ideas_to_include, status, section_order
                        FROM post_section
                        WHERE post_id = %s
                        ORDER BY section_order
                    """, (22,))
                    sections = cur.fetchall()
            return jsonify(sections)
        except Exception as e:
            logger.error(f"Error fetching sections: {str(e)}")
            return jsonify({'error': str(e)}), 500
    elif request.method == "POST":
        try:
            sections = request.json.get("sections", [])
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM post_section WHERE post_id = %s", (22,))
                    for i, section in enumerate(sections):
                        cur.execute("""
                            INSERT INTO post_section (post_id, section_heading, section_description, ideas_to_include, status, section_order)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            22,
                            section.get('section_heading', ''),
                            section.get('section_description', ''),
                            section.get('ideas_to_include', ''),
                            section.get('status', 'draft'),
                            i
                        ))
                    conn.commit()
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error saving sections: {str(e)}")
            return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000) 