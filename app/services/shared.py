"""
Shared services for modular architecture.

This module provides common utilities and cross-module coordination
for the BlogForge workflow system.
"""

from app.database.routes import get_db_conn
import logging

logger = logging.getLogger(__name__)

def get_all_posts_from_db():
    """
    Get all non-deleted posts from the database.
    
    This is a shared service that can be used by any module
    that needs to access post data.
    
    Returns:
        list: List of post dictionaries with 'id', 'title', and 'updated_at' keys
    """
    try:
        conn = get_db_conn()
        if not conn:
            logger.error("Could not establish database connection")
            return []
        
        cur = conn.cursor()
        
        # Query posts, excluding deleted ones
        cur.execute('''
            SELECT id, title, updated_at
            FROM post
            WHERE status != 'deleted'
            ORDER BY updated_at DESC NULLS LAST
        ''')
        
        posts = []
        for row in cur.fetchall():
            posts.append({
                'id': row['id'], 
                'title': row['title'],
                'updated_at': row['updated_at']
            })
        
        cur.close()
        conn.close()
        return posts
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return []

def get_workflow_stages_from_db():
    """
    Get all workflow stages and their substages from the database.
    
    This is a shared service that can be used by any module
    that needs workflow stage data.
    
    Returns:
        dict: Workflow stages structure
    """
    try:
        conn = get_db_conn()
        if not conn:
            logger.error("Could not establish database connection")
            return get_workflow_stages_fallback()
        
        cur = conn.cursor()
        
        # Query workflow steps using the normalized schema
        cur.execute('''
            SELECT 
                s.name as stage_name,
                ss.name as substage_name,
                ws.name as step_name
            FROM workflow_stage_entity s
            JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
            JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id
            ORDER BY s.stage_order, ss.sub_stage_order, ws.step_order
        ''')
        
        stages = {}
        for row in cur.fetchall():
            stage, substage, step = row['stage_name'], row['substage_name'], row['step_name']
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
        logger.error(f"Database query error: {e}")
        return get_workflow_stages_fallback()

def get_workflow_stages_fallback():
    """Return fallback workflow stages data if database is unavailable."""
    return {
        "Planning": {
            "Idea": ["initial_concept", "Provisional Title"],
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