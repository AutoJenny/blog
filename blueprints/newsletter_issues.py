"""Newsletter Issues Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import (
    get_issue,
    list_issues,
    count_issues,
    soft_delete_issue,
    update_issue_theme,
    update_issue_subject_preheader,
    list_blocks_by_issue,
    insert_block,
    shift_positions,
)
from newsletter.selectors.theme import get_themes_for_week, parse_target_week, get_theme_by_id
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_issues', __name__)


@bp.route('/newsletter')
def dashboard():
    """Top-level Newsletter dashboard."""
    from newsletter.db.queries_issue import count_issues, list_issues
    
    status_filter = request.args.get('status')
    q = request.args.get('q')
    show_deleted = request.args.get('show_deleted', '0') == '1'
    try:
        page = max(1, int(request.args.get('page', '1')))
    except Exception:
        page = 1
    per_page = 12
    offset = (page - 1) * per_page
    issues = []
    try:
        total = count_issues(status=status_filter, q=q, show_deleted=show_deleted)
        issues = list_issues(limit=per_page, offset=offset, status=status_filter, q=q, show_deleted=show_deleted)
    except Exception:
        total = 0
        issues = []
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template('newsletter/index.html', page_title='Newsletter', issues=issues, status_filter=status_filter, q=q, page=page, total_pages=total_pages, show_deleted=show_deleted)



@bp.route('/newsletter/issue/<int:issue_id>/delete', methods=['POST'])
def delete_issue_route(issue_id: int):
    """Soft delete an issue."""
    soft_delete_issue(issue_id=issue_id)
    return redirect(url_for('newsletter_issues.dashboard'))



@bp.route('/newsletter/issue', methods=['POST'])
def create_or_regenerate_issue():
    """Create a new draft issue with theme title and empty template blocks for manual completion."""
    from datetime import date
    from newsletter.selectors.theme import select_default_theme
    from newsletter.db.queries_issue import create_issue, upsert_block
    
    # Get current week
    iso_year, iso_week, _ = date.today().isocalendar()
    target_week = f"{iso_year}W{iso_week:02d}"
    
    # Get theme for the week
    theme = select_default_theme(target_week=target_week)
    theme_id = theme.get('id') if theme else None
    
    # Generate subject and preheader from theme
    if theme:
        subject = f"{theme.get('idea_title', 'This week in Scotland')} — {target_week}"
        preheader = theme.get('seasonal_context') or theme.get('idea_description') or "A quick wander through culture & craft."
    else:
        subject = f"This week in Scotland — {target_week}"
        preheader = "A quick wander through culture & craft."
    
    # Create issue
    issue_id = create_issue(target_week=target_week, subject=subject, preheader=preheader, theme_id=theme_id)
    
    # Create empty template blocks (no auto-selection, just structure)
    block_types = [
        "intro",
        "feature",
        "snapshot",
        "new_products",
        "words_of_the_week",
        "spotlight",
        "seasonal_recipe",
        "evergreen",
        "closing",
    ]
    
    position = 0
    for block_type in block_types:
        if block_type == "closing":
            payload = {"text": "Warmly, from Scotland"}
        else:
            # Empty payload - user will fill manually
            payload = {}
        
        upsert_block(issue_id=issue_id, block_type=block_type, position=position, enabled=True, payload=payload)
        position += 1
    
    return redirect(url_for('newsletter_issues.view_issue', issue_id=issue_id))



@bp.route('/newsletter/issue/<int:issue_id>')
def view_issue(issue_id: int):
    """Simple issue view showing blocks list (preview comes later)."""
    issue = None
    themes = []
    try:
        issue = get_issue(issue_id=issue_id)
        if issue and issue.get('target_week'):
            week_number = parse_target_week(issue['target_week'])
            themes = get_themes_for_week(week_number)
    except Exception:
        pass
    
    blocks = []
    try:
        blocks = list_blocks_by_issue(issue_id=issue_id)
    except Exception:
        blocks = []
    # Auto-generate one of each block type if none exist yet
    if not blocks:
        default_types = [
            "intro",
            "feature",
            "snapshot",
            "new_products",
            "spotlight",
            "category",
            "weekly_words",
            "evergreen",
            "closing",
        ]
        pos = 0
        for t in default_types:
            insert_block(issue_id=issue_id, block_type=t, position=pos, enabled=True, payload={})
            pos += 1
        try:
            blocks = list_blocks_by_issue(issue_id=issue_id)
        except Exception:
            blocks = []
    else:
        # Ensure Intro exists for existing issues; if missing, prepend at position 0
        has_intro = any((b.get("type") == "intro") for b in blocks)
        if not has_intro:
            try:
                shift_positions(issue_id=issue_id, from_position=0)
                insert_block(issue_id=issue_id, block_type="intro", position=0, enabled=True, payload={})
                blocks = list_blocks_by_issue(issue_id=issue_id)
            except Exception:
                pass
    
    current_theme = None
    if issue and issue.get('theme_id'):
        try:
            current_theme = get_theme_by_id(issue['theme_id'])
        except Exception:
            pass
    
    # Get themed blog post for this week
    themed_post = None
    if issue and issue.get('target_week'):
        try:
            from datetime import date
            from utils.week_post_resolver import resolve_post_for_week
            from config.database import db_manager
            
            # Parse year and week from target_week
            target_week = issue['target_week']
            if 'W' in target_week:
                year_str, week_str = target_week.split('W')
                year = int(year_str)
                week_number = int(week_str)
                
                # Resolve post for this week
                post_id = resolve_post_for_week(year, week_number)
                if post_id:
                    # Get post details including status
                    with db_manager.get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT id, title, status, slug
                                FROM post
                                WHERE id = %s
                            """, (post_id,))
                            post_row = cur.fetchone()
                            if post_row:
                                # Validate post is not deleted before using it
                                if post_row['status'] != 'deleted':
                                    themed_post = dict(post_row)
                                else:
                                    # Log warning if deleted post was resolved
                                    import logging
                                    logging.getLogger(__name__).warning(
                                        f"resolve_post_for_week returned deleted post {post_id} "
                                        f"for week {target_week}. This should not happen after fix."
                                    )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting themed post: {e}")
            pass
    
    # Get spotlight profile post (most recent published, not yet used)
    spotlight_post = None
    try:
        from newsletter.selectors.products import select_spotlight_profile_post
        spotlight_post = select_spotlight_profile_post()
        if spotlight_post:
            # Get post status
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT status
                        FROM post
                        WHERE id = %s
                    """, (spotlight_post.get('id'),))
                    status_row = cur.fetchone()
                    if status_row:
                        spotlight_post['status'] = dict(status_row).get('status', 'unknown')
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error getting spotlight post: {e}")
        pass
    
    # Get words of the week for current week
    words_of_the_week = {}
    if issue and issue.get('target_week'):
        try:
            from datetime import date
            from newsletter.selectors.words_of_the_week import get_words_of_the_week
            
            # Parse year and week from target_week
            target_week = issue['target_week']
            if 'W' in target_week:
                year_str, week_str = target_week.split('W')
                week_number = int(week_str)
            else:
                week_number = int(target_week)
            
            words_of_the_week = get_words_of_the_week(week_number=week_number)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting words of the week: {e}")
            pass
    
    # Get seasonal recipe post (most recent published, not yet used)
    seasonal_recipe_post = None
    try:
        from newsletter.selectors.seasonal_recipe import select_seasonal_recipe_post
        seasonal_recipe_post = select_seasonal_recipe_post()
        if seasonal_recipe_post:
            # Get post status
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT status
                        FROM post
                        WHERE id = %s
                    """, (seasonal_recipe_post.get('id'),))
                    status_row = cur.fetchone()
                    if status_row:
                        seasonal_recipe_post['status'] = dict(status_row).get('status', 'unknown')
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error getting seasonal recipe post: {e}")
        pass
    
    return render_template('newsletter/issue.html', issue_id=issue_id, issue=issue, blocks=blocks, themes=themes, current_theme=current_theme, themed_post=themed_post, spotlight_post=spotlight_post, words_of_the_week=words_of_the_week, seasonal_recipe_post=seasonal_recipe_post)



@bp.route('/newsletter/issue/<int:issue_id>/theme', methods=['POST'])
def update_theme_route(issue_id: int):
    """Update theme for an issue."""
    from newsletter.db.queries_issue import update_issue_subject_preheader
    
    theme_id = request.form.get('theme_id')
    if theme_id and theme_id != '':
        try:
            theme_id_int = int(theme_id)
            theme = get_theme_by_id(theme_id_int)
            if theme:
                update_issue_theme(issue_id=issue_id, theme_id=theme_id_int)
                # Update subject and preheader from theme
                subject = f"{theme.get('idea_title', 'This week in Scotland')} — {get_issue(issue_id).get('target_week', '')}"
                preheader = theme.get('seasonal_context') or theme.get('idea_description') or "A quick wander through culture & craft."
                update_issue_subject_preheader(issue_id=issue_id, subject=subject, preheader=preheader)
        except Exception:
            pass
    else:
        update_issue_theme(issue_id=issue_id, theme_id=None)
    return redirect(url_for('newsletter_issues.view_issue', issue_id=issue_id))


