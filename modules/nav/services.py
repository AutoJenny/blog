"""Navigation services for workflow module."""

import psycopg2
import os

def get_db_conn():
    """Get database connection for nav module - self-contained implementation."""
    try:
        # Use environment variables or default values for database connection
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'blog')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_workflow_stages():
    """Get all workflow stages and their substages from the database."""
    conn = get_db_conn()
    if not conn:
        # Return fallback data if database connection fails
        return {
            "Planning": {
                "Idea": ["Basic Idea", "Provisional Title"],
                "Research": ["Concepts", "Facts"],
                "Structure": ["Outline", "Allocate Facts"]
            },
            "Writing": {
                "Content": ["Sections"],
                "Meta Info": ["Meta Info"],
                "Images": ["Images"]
            },
            "Publishing": {
                "Preflight": ["Preflight"],
                "Launch": ["Launch"],
                "Syndication": ["Syndication"]
            }
        }
    
    try:
        cur = conn.cursor()
        
        # First, let's see what columns actually exist in the table
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_step_entity'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"Available columns in workflow_step_entity: {columns}")
        
        # Try to query with the most likely column names
        if 'stage_name' in columns and 'substage_name' in columns and 'step_name' in columns:
            cur.execute('''
                SELECT stage_name, substage_name, step_name
                FROM workflow_step_entity
                ORDER BY stage_order, substage_order, step_order
            ''')
        elif 'stage' in columns and 'substage' in columns and 'step' in columns:
            cur.execute('''
                SELECT stage, substage, step
                FROM workflow_step_entity
                ORDER BY stage_order, substage_order, step_order
            ''')
        else:
            # If we can't find the right columns, return fallback data
            print(f"Could not find expected columns in workflow_step_entity table")
            return get_workflow_stages_fallback()
        
        stages = {}
        for row in cur.fetchall():
            stage, substage, step = row
            if stage not in stages:
                stages[stage] = {}
            if substage not in stages[stage]:
                stages[stage][substage] = []
            if step not in stages[stage][substage]:
                stages[stage][substage].append(step)
        
        cur.close()
        conn.close()
        return stages
        
    except Exception as e:
        print(f"Database query error: {e}")
        conn.close()
        return get_workflow_stages_fallback()

def get_workflow_stages_fallback():
    """Return fallback workflow stages data."""
    return {
        "Planning": {
            "Idea": ["Basic Idea", "Provisional Title"],
            "Research": ["Concepts", "Facts"],
            "Structure": ["Outline", "Allocate Facts"]
        },
        "Writing": {
            "Content": ["Sections"],
            "Meta Info": ["Meta Info"],
            "Images": ["Images"]
        },
        "Publishing": {
            "Preflight": ["Preflight"],
            "Launch": ["Launch"],
            "Syndication": ["Syndication"]
        }
    }

def get_all_posts():
    """Get all posts from the database for the post selector."""
    conn = get_db_conn()
    if not conn:
        # Return fallback data if database connection fails
        return [
            {'id': 1, 'title': 'Demo Post (DB Unavailable)'},
            {'id': 2, 'title': 'Second Post (DB Unavailable)'}
        ]
    
    try:
        cur = conn.cursor()
        
        # Query posts table - check what columns exist first
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'post'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"Available columns in post table: {columns}")
        
        # Query posts, excluding deleted ones
        if 'id' in columns and 'title' in columns and 'status' in columns:
            cur.execute('''
                SELECT id, title
                FROM post
                WHERE status != 'deleted'
                ORDER BY id DESC
            ''')
        elif 'id' in columns and 'title' in columns:
            # No status column found, get all posts
            cur.execute('''
                SELECT id, title
                FROM post
                ORDER BY id DESC
            ''')
        else:
            print(f"Could not find expected columns in post table")
            return get_all_posts_fallback()
        
        posts = []
        for row in cur.fetchall():
            post_id, title = row
            posts.append({'id': post_id, 'title': title})
        
        cur.close()
        conn.close()
        return posts
        
    except Exception as e:
        print(f"Database query error: {e}")
        conn.close()
        return get_all_posts_fallback()

def get_all_posts_fallback():
    """Return fallback posts data."""
    return [
        {'id': 1, 'title': 'Demo Post (DB Error)'},
        {'id': 2, 'title': 'Second Post (DB Error)'}
    ]

def get_workflow_context():
    """Get workflow context for the current stage/substage/step."""
    # For now, return a default context
    # This will be enhanced to fetch real data from the database
    return {
        'current_stage': 'planning',
        'current_substage': 'idea',
        'current_step': 'basic_idea',
        'stages': get_workflow_stages(),
        'all_posts': get_all_posts()
    } 