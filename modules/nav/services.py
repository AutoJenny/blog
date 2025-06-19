"""Navigation services for workflow module."""

# Import shared services from MAIN_HUB
try:
    from app.services.shared import get_all_posts_from_db, get_workflow_stages_from_db
except ImportError:
    # Fallback for standalone development when shared services aren't available
    def get_all_posts_from_db():
        """Fallback posts data for standalone development."""
        return [
            {'id': 1, 'title': 'Demo Post (Standalone Mode)'},
            {'id': 2, 'title': 'Second Post (Standalone Mode)'}
        ]
    
    def get_workflow_stages_from_db():
        """Fallback workflow stages for standalone development."""
        return get_workflow_stages_fallback()

def get_db_conn():
    """Get database connection for nav module - self-contained implementation."""
    # This is kept for backward compatibility but should use shared services
    try:
        # Try to import shared DB utility
        from app.db import get_db_conn as shared_get_db_conn
        return shared_get_db_conn()
    except ImportError:
        # Fallback for standalone development
        import psycopg2
        import os
        
        try:
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
    # Use shared service from MAIN_HUB
    return get_workflow_stages_from_db()

def get_all_posts():
    """Get all posts from the database for the post selector."""
    # Use shared service from MAIN_HUB
    return get_all_posts_from_db()

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