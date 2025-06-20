print('DEBUG: Loaded app/blog/routes.py from', __file__)
from flask import render_template, jsonify, request, redirect, url_for, abort, Blueprint, current_app
from app.blog import bp
from slugify import slugify
import logging
from datetime import datetime
from app.blog.fields import WORKFLOW_FIELDS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, dotenv_values
from humanize import naturaltime
import pytz
import json
from app.llm.services import LLMService

# Load DATABASE_URL from assistant_config.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_conn():
    # Always reload assistant_config.env and ignore pre-existing env
    config = dotenv_values(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
    db_url = config.get('DATABASE_URL')
    if not db_url or db_url.strip() == '':
        print("[ERROR] DATABASE_URL is not set or is empty! Please check your assistant_config.env or environment variables.")
        raise RuntimeError("DATABASE_URL is not set or is empty! Please check your assistant_config.env or environment variables.")
    print(f"[DEBUG] DATABASE_URL used: {db_url}")
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@bp.route("/new", methods=["POST"])
def new_post():
    try:
        data = request.get_json()
        if not data or "basic_idea" not in data:
            return jsonify({"error": "basic_idea is required"}), 400
        temp_title = data["basic_idea"][:50] + "..."
        base_slug = slugify(temp_title)
        counter = 0
        slug = base_slug
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Ensure slug uniqueness
                while True:
                    cur.execute("SELECT 1 FROM post WHERE slug = %s", (slug,))
                    if not cur.fetchone():
                        break
                    counter += 1
                    slug = f"{base_slug}-{counter}"
                # Insert post (no idea_seed)
                cur.execute(
                    """
                    INSERT INTO post (title, slug, summary, created_at, updated_at)
                    VALUES (%s, %s, '', NOW(), NOW()) RETURNING id
                    """,
                    (temp_title, slug)
                )
                post_id = cur.fetchone()["id"]
                # Insert post_development with idea_seed
                cur.execute(
                    """
                    INSERT INTO post_development (post_id, idea_seed)
                    VALUES (%s, %s)
                    """,
                    (post_id, data["basic_idea"])
                )
                # --- CLONE post_substage_action from previous post ---
                cur.execute("SELECT id FROM post WHERE id != %s ORDER BY id DESC LIMIT 1", (post_id,))
                prev_row = cur.fetchone()
                if prev_row:
                    prev_post_id = prev_row["id"]
                    cur.execute("SELECT substage, action_id, input_field, output_field, button_label, button_order FROM post_substage_action WHERE post_id = %s", (prev_post_id,))
                    actions = cur.fetchall()
                    for a in actions:
                        cur.execute('''
                            INSERT INTO post_substage_action (post_id, substage, action_id, input_field, output_field, button_label, button_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''', (post_id, a["substage"], a["action_id"], a["input_field"], a["output_field"], a["button_label"], a["button_order"]))
                conn.commit()
        return jsonify({
            "message": "Post created successfully",
            "slug": slug,
            "id": post_id
        })
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@bp.route('/<slug>')
def legacy_slug(slug):
    post = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post WHERE slug = %s", (slug,))
                post = cur.fetchone()
                if not post:
                    abort(404)
    except Exception as e:
        abort(500, str(e))
    if post:
        return redirect(url_for('blog.post_view', post_id=post["id"], view='preview'), code=301)
    else:
        abort(404)


@bp.route("/api/v1/post/<int:post_id>/development", methods=["GET"])
def get_post_development(post_id):
    dev = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                dev = cur.fetchone()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not dev:
        return jsonify({"error": "Not found"}), 404
    # Exclude id and post_id
    return jsonify({k: v for k, v in dev.items() if k not in ["id", "post_id"]})


@bp.route("/api/v1/post/<int:post_id>/development", methods=["POST"])
def update_post_development(post_id):
    data = request.get_json()
    updated_at = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get columns except id, post_id
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_development' AND column_name NOT IN ('id', 'post_id')")
                columns = [row["column_name"] for row in cur.fetchall()]
                # Build update statement
                set_clauses = []
                values = []
                for field in columns:
                    if field in data:
                        set_clauses.append(f"{field} = %s")
                        values.append(data[field])
                if set_clauses:
                    values.append(post_id)
                    cur.execute(f"UPDATE post_development SET {', '.join(set_clauses)} WHERE post_id = %s RETURNING *", tuple(values))
                    dev = cur.fetchone()
                # Also update parent post's updated_at
                cur.execute("UPDATE post SET updated_at = NOW() WHERE id = %s RETURNING updated_at", (post_id,))
                updated_at = cur.fetchone()["updated_at"]
                conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "success", "updated_at": updated_at.isoformat() if updated_at else None})


@bp.route("/api/v1/post/<int:post_id>/sections", methods=["GET"])
def get_sections(post_id):
    sections = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post_section WHERE post_id = %s ORDER BY section_order", (post_id,))
                sections = cur.fetchall()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # Exclude post_id from each section
    return jsonify([{k: v for k, v in s.items() if k != "post_id"} for s in sections])


@bp.route("/api/v1/post/<int:post_id>/sections", methods=["POST"])
def add_section(post_id):
    data = request.get_json() or {}
    section_id = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO post_section (
                        post_id, section_order, section_heading, 
                        section_description, first_draft
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        post_id, 
                        data.get("section_order", 0), 
                        data.get("section_heading", ""),
                        data.get("section_description", ""),
                        data.get("first_draft", "")
                    )
                )
                section_id = cur.fetchone()["id"]
                conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"id": section_id})


@bp.route("/api/v1/section/<int:section_id>", methods=["PUT"])
def update_section(section_id):
    data = request.get_json()
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get columns except id, post_id
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_section' AND column_name NOT IN ('id', 'post_id')")
                columns = [row["column_name"] for row in cur.fetchall()]
                set_clauses = []
                values = []
                for field in columns:
                    if field in data:
                        set_clauses.append(f"{field} = %s")
                        values.append(data[field])
                if set_clauses:
                    values.append(section_id)
                    cur.execute(f"UPDATE post_section SET {', '.join(set_clauses)} WHERE id = %s RETURNING *", tuple(values))
                    conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "success"})


@bp.route("/api/v1/section/<int:section_id>", methods=["DELETE"])
def delete_section(section_id):
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM post_section WHERE id = %s", (section_id,))
                conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route("/test_insert", methods=["GET"])
def test_insert():
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO post (title, slug, published, deleted, content, created_at, updated_at)
                    VALUES (%s, %s, FALSE, FALSE, '', NOW(), NOW()) RETURNING id
                """, ("Test Post", "test-post"))
                post_id = cur.fetchone()["id"]
                # Insert post development
                cur.execute(
                    """
                    INSERT INTO post_development (post_id, basic_idea)
                    VALUES (%s, %s)
                    RETURNING id
                """,
                    (post_id, "")
                )
                conn.commit()
        return jsonify({"success": True, "message": "Test post created", "id": post_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/<slug>", methods=["GET"])
def get_post(slug):
    post = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post WHERE slug = %s", (slug,))
                post = cur.fetchone()
                if not post:
                    abort(404)
    except Exception as e:
        abort(500, str(e))
    if post:
        return jsonify(
            {
                "id": post["id"],
                "slug": post["slug"],
                "title": post["title"],
                "content": post["content"],
                "published": post["published"],
                "deleted": post["deleted"],
                "created_at": post["created_at"].isoformat() if post["created_at"] else None,
                "updated_at": post["updated_at"].isoformat() if post["updated_at"] else None,
            }
        )
    else:
        return jsonify({"error": "Post not found"}), 404


@bp.route("/<slug>", methods=["PUT"])
def update_post(slug):
    post = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post WHERE slug = %s", (slug,))
                post = cur.fetchone()
                if not post:
                    abort(404)
                data = request.get_json() or {}
                if "title" in data:
                    cur.execute("UPDATE post SET title = %s WHERE id = %s", (data["title"], post["id"]))
                if "content" in data:
                    cur.execute("UPDATE post SET content = %s WHERE id = %s", (data["content"], post["id"]))
                cur.execute("UPDATE post SET updated_at = NOW() WHERE id = %s", (post["id"],))
                conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(
        {
            "id": post["id"],
            "slug": post["slug"],
            "title": post["title"],
            "content": post["content"],
            "published": post["published"],
            "deleted": post["deleted"],
            "created_at": post["created_at"].isoformat() if post["created_at"] else None,
            "updated_at": post["updated_at"].isoformat() if post["updated_at"] else None,
        }
    )


@bp.route("/api/v1/post/<int:post_id>/fields/<field>", methods=["PUT"])
def update_post_field(post_id, field):
    data = request.get_json()
    updated_at = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Only allow updating valid fields in post table
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post'")
                valid_fields = [row["column_name"] for row in cur.fetchall()]
                if field not in valid_fields:
                    return jsonify({"error": "Invalid field"}), 400
                cur.execute(f"UPDATE post SET {field} = %s, updated_at = NOW() WHERE id = %s RETURNING updated_at", (data.get("value", ""), post_id))
                updated_at = cur.fetchone()["updated_at"]
                conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "success", "updated_at": updated_at.isoformat() if updated_at else None})


@bp.route("/api/v1/posts/<int:post_id>/sections/<int:section_id>/fields/<field>", methods=["PUT"])
def update_section_field(post_id, section_id, field):
    data = request.get_json()
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_section' AND column_name NOT IN ('id', 'post_id')")
                valid_fields = [row["column_name"] for row in cur.fetchall()]
                if field not in valid_fields:
                    return jsonify({"error": "Invalid field"}), 400
                cur.execute(f"UPDATE post_section SET {field} = %s WHERE id = %s AND post_id = %s RETURNING *", (data.get("value", ""), section_id, post_id))
                conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "success"})


# Public-facing post detail view
@bp.route("/public/<int:post_id>/")
def post_public(post_id):
    post = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                if not post or not (post["published"] or post["status"] == 'in_process') or post["deleted"]:
                    abort(404)
    except Exception as e:
        abort(500, str(e))
    sections = None
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post_section WHERE post_id = %s ORDER BY section_order", (post_id,))
                sections = cur.fetchall()
    except Exception as e:
        sections = []
    if sections:
        return render_template("blog/post_public.html", post=post, sections=sections)
    else:
        abort(500, "Sections not found")


@bp.route('/posts', methods=['GET'])
def posts_listing():
    import logging
    logger = logging.getLogger("blog_debug")
    posts = []
    substages = {}
    show_deleted = request.args.get('show_deleted', '0') == '1'
    debug = request.args.get('debug', '0') == '1'
    # Print DATABASE_URL
    print(f"[DEBUG] Flask DATABASE_URL: {DATABASE_URL}", flush=True)
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Print current database, user, schema
                cur.execute("SELECT current_database(), current_user, current_schema();")
                dbinfo = cur.fetchone()
                print(f"[DEBUG] DB info: {dbinfo}", flush=True)
                # Get all substages
                cur.execute("SELECT id, name FROM workflow_sub_stage_entity ORDER BY id;")
                substages = {row['id']: row['name'] for row in cur.fetchall()}
                # Get posts with substage_id, filter by deleted status
                if show_deleted:
                    cur.execute("""
                        SELECT id, title, status, created_at, updated_at, slug, substage_id
                        FROM post
                        WHERE status = 'deleted'
                        ORDER BY created_at DESC
                    """)
                else:
                    cur.execute("""
                        SELECT id, title, status, created_at, updated_at, slug, substage_id
                        FROM post
                        WHERE status != 'deleted'
                        ORDER BY created_at DESC
                    """)
                posts = cur.fetchall()
                print(f"[DEBUG] Raw posts from DB: {posts}", flush=True)
        logger.info(f"[DEBUG] posts_listing: fetched {len(posts)} posts: {posts}")
    except Exception as e:
        logger.error(f"[DEBUG] posts_listing: exception {e}")
        posts = []
    # Format dates as 'ago' using humanize, with Europe/London timezone
    london = pytz.timezone('Europe/London')
    now = datetime.now(london)
    for post in posts:
        created = post['created_at']
        updated = post['updated_at']
        if created and created.tzinfo is None:
            created = london.localize(created)
        if updated and updated.tzinfo is None:
            updated = london.localize(updated)
        post['created_ago'] = naturaltime(now - created) if created else ''
        post['updated_ago'] = naturaltime(now - updated) if updated else ''
    if debug:
        from flask import jsonify
        return jsonify({"posts": posts, "substages": substages, "show_deleted": show_deleted})
    return render_template('blog/posts_list.html', posts=posts, substages=substages, show_deleted=show_deleted)


@bp.route('/blog/<int:post_id>/develop')
def deprecated_develop(post_id):
    abort(404)


@bp.route("/api/v1/post_development/fields", methods=["GET"])
def get_post_development_fields():
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_development' AND column_name NOT IN ('id', 'post_id')")
                columns = [row["column_name"] for row in cur.fetchall()]
        return jsonify({"fields": columns})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.errorhandler(404)
def api_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    # Fallback to default HTML error page for non-API
    return render_template('errors/404.html'), 404
