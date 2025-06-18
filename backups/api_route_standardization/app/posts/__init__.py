from flask import Blueprint, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from dotenv import load_dotenv

bp = Blueprint('posts', __name__)

# Load DATABASE_URL from assistant_config.env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def time_ago(dt):
    if not dt:
        return ''
    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds//60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds//3600)}h ago"
    elif seconds < 604800:
        return f"{int(seconds//86400)}d ago"
    else:
        return dt.strftime('%Y-%m-%d')

@bp.app_template_filter('time_ago')
def jinja_time_ago(dt):
    return time_ago(dt)

@bp.route('/')
def listing():
    posts = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, pd.idea_seed, p.title, p.status, p.created_at, p.updated_at
                    FROM post p
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    ORDER BY p.created_at DESC
                """)
                posts = cur.fetchall()
    except Exception as e:
        posts = []
    return render_template('posts/list.html', posts=posts) 