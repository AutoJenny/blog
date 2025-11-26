"""Newsletter Blueprint - Top-level UI shell.

Routes here stay thin (<60 LOC each) and delegate to services. Keep this file
small; split views into helpers if it approaches ~400–500 LOC.
"""

from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

from newsletter.db.queries_issue import (
    list_issues,
    count_issues,
    soft_delete_issue,
    get_issue,
    update_issue_theme,
    update_issue_subject_preheader,
    list_blocks_by_issue,
    set_block_enabled,
    update_block_payload,
    delete_block,
    insert_block,
    move_block,
    shift_positions,
)
from newsletter.selectors.theme import get_themes_for_week, parse_target_week, get_theme_by_id
from newsletter.services.draft_service import build_weekly_issue
from newsletter.services.qa_service import run_pre_send_checks
from newsletter.services.approval_service import approve_issue, send_issue
from newsletter.services.block_editor_service import get_suggestions, apply_suggestion, save_override, regenerate_text
from newsletter.jobs.weekly_autodraft import run as run_autodraft
from newsletter.db.queries_source_management import (
    list_all_sources,
    get_source,
    create_source,
    update_source,
    delete_source,
    get_cache_status,
    get_item_stats,
)
from newsletter.db.queries_sources import get_cached_items
from newsletter.jobs.prefetch_sources import run as run_prefetch

bp = Blueprint('newsletter', __name__)


@bp.route('/newsletter')
def dashboard():
    """Top-level Newsletter dashboard."""
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
    return redirect(url_for('newsletter.dashboard'))


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
        "spotlight",
        "category",
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
    
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


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
    
    return render_template('newsletter/issue.html', issue_id=issue_id, issue=issue, blocks=blocks, themes=themes, current_theme=current_theme, themed_post=themed_post, spotlight_post=spotlight_post)


@bp.route('/newsletter/issue/<int:issue_id>/preview')
def preview_issue(issue_id: int):
    blocks = []
    issue = None
    try:
        blocks = list_blocks_by_issue(issue_id=issue_id)
        issue = get_issue(issue_id=issue_id)
    except Exception:
        blocks = []
    
    # Load base64 tile data for background
    tile_base64_data = None
    try:
        # Get project root (blueprints/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        tile_path = os.path.join(project_root, 'static', 'images', 'newsletter', 'tile_base64.txt')
        if os.path.exists(tile_path):
            with open(tile_path, 'r') as f:
                tile_base64_data = f.read().strip()
        else:
            # Try absolute path as fallback
            abs_path = '/Users/autojenny/Documents/projects/blog/static/images/newsletter/tile_base64.txt'
            if os.path.exists(abs_path):
                with open(abs_path, 'r') as f:
                    tile_base64_data = f.read().strip()
        if tile_base64_data:
            import logging
            logging.getLogger(__name__).info(f"Loaded tile background ({len(tile_base64_data)} chars)")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not load tile background: {e}")
        pass  # Tile is optional
    
    # Convert local image paths to clan.com URLs for feature blocks
    # Also convert markdown links to HTML for snapshot blocks
    import re
    processed_blocks = []
    for b in blocks:
        block_data = {"type": b["type"], "payload_json": b["payload_json"].copy() if b["payload_json"] else {}}
        
        # If this is a snapshot block, convert markdown links to HTML
        if b["type"] == "snapshot":
            payload = block_data["payload_json"]
            # Convert [title](url) to HTML links
            def markdown_to_html(text):
                if not text:
                    return ""
                # Convert [title](url) to <a href="url">title</a>
                return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color:#6b4e3d; text-decoration:underline;">\1</a>', text)
            
            if payload.get("news_paragraph"):
                payload["news_paragraph"] = markdown_to_html(payload["news_paragraph"])
            if payload.get("events_paragraph"):
                payload["events_paragraph"] = markdown_to_html(payload["events_paragraph"])
        
        # If this is a feature block with a hero_image, try to convert local path to clan.com URL
        if b["type"] == "feature" and block_data["payload_json"].get("hero_image"):
            hero_image = block_data["payload_json"]["hero_image"]
            post_id = block_data["payload_json"].get("id")
            
            # If it's a local path, try to find the clan.com URL
            if hero_image.startswith("/static/") and post_id:
                try:
                    from config.database import db_manager
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT clan_uploaded_url 
                            FROM section_image_mappings 
                            WHERE post_id = %s 
                              AND section_id IS NULL
                              AND local_image_path = %s
                            LIMIT 1
                        """, (post_id, hero_image))
                        result = cursor.fetchone()
                        if result and result.get('clan_uploaded_url'):
                            block_data["payload_json"]["hero_image"] = result['clan_uploaded_url']
                            import logging
                            logging.getLogger(__name__).info(f"Converted feature block hero_image from {hero_image} to {result['clan_uploaded_url']}")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Could not convert hero_image path: {e}")
                    pass  # Keep original path if conversion fails
        
        processed_blocks.append(block_data)
    
    # Map blocks to pass each payload as "block" expected by partials
    return render_template(
        'newsletter/render.html',
        subject=f"Issue {issue_id}",
        issue=issue,
        blocks=processed_blocks,
        tile_base64_data=tile_base64_data
    )


@bp.route('/newsletter/issue/<int:issue_id>/qa')
def qa_issue(issue_id: int):
    checks = []
    try:
        checks = run_pre_send_checks(issue_id)
    except Exception:
        checks = []
    return render_template('newsletter/qa.html', issue_id=issue_id, checks=checks)


@bp.route('/newsletter/issue/<int:issue_id>/approve', methods=['POST'])
def approve_issue_route(issue_id: int):
    approve_issue(issue_id=issue_id)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/send', methods=['POST'])
def send_issue_route(issue_id: int):
    adapter = request.form.get('adapter', 'preview')
    result = send_issue(issue_id=issue_id, adapter=adapter)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/theme', methods=['POST'])
def update_theme_route(issue_id: int):
    """Update theme for an issue."""
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
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/autodraft', methods=['POST'])
def trigger_autodraft():
    try:
        result = run_autodraft()
        issue_id = result.get('issue_id') if result else None
        if not issue_id:
            return redirect(url_for('newsletter.dashboard')), 302
        return redirect(url_for('newsletter.view_issue', issue_id=issue_id))
    except Exception as e:
        # Log error and redirect to dashboard
        import logging
        logging.error(f"Autodraft failed: {e}", exc_info=True)
        return redirect(url_for('newsletter.dashboard'))


# Block management endpoints

@bp.route('/newsletter/block/<int:block_id>/toggle', methods=['POST'])
def toggle_block(block_id: int):
    enabled = request.form.get('enabled', 'true').lower() == 'true'
    set_block_enabled(block_id=block_id, enabled=enabled)
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/block/<int:block_id>/update', methods=['POST'])
def update_block(block_id: int):
    import json
    from newsletter.db.queries_issue import get_block
    from newsletter.services.product_tracking import mark_products_newsletter_launched, extract_product_ids_from_payload
    
    raw = request.form.get('payload_json') or '{}'
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {}
    
    # Get block type to check if we need to mark products as launched
    block = get_block(block_id=block_id)
    block_type = block.get('type', '') if block else ''
    
    update_block_payload(block_id=block_id, payload=payload)
    
    # Mark products as newsletter launched if this is a new_products block
    if block_type == 'new_products':
        product_ids = extract_product_ids_from_payload(payload, block_type)
        if product_ids:
            mark_products_newsletter_launched(product_ids)
    
    # Mark profile post as newsletter spotlighted if this is a spotlight block
    if block_type == 'spotlight':
        from newsletter.services.product_tracking import mark_post_newsletter_spotlighted, extract_post_id_from_spotlight_payload
        post_id = extract_post_id_from_spotlight_payload(payload)
        if post_id:
            mark_post_newsletter_spotlighted(post_id)
    
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/block/<int:block_id>/delete', methods=['POST'])
def remove_block(block_id: int):
    issue_id = int(request.form.get('issue_id', '0'))
    delete_block(block_id=block_id)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/block/add', methods=['POST'])
def add_block(issue_id: int):
    block_type = request.form.get('type', 'evergreen')
    # Calculate position: optional provided, else append to end
    try:
        existing = list_blocks_by_issue(issue_id=issue_id)
        desired = request.form.get('position')
        if desired is not None and desired != '':
            try:
                desired_pos = int(desired)
            except Exception:
                desired_pos = 0
            if desired_pos < 0:
                desired_pos = 0
            if existing:
                max_pos = max(b.get('position', 0) for b in existing)
                if desired_pos > max_pos + 1:
                    desired_pos = max_pos + 1
                # Shift existing blocks at and after desired_pos
                shift_positions(issue_id=issue_id, from_position=desired_pos)
            position = desired_pos
        else:
            if existing:
                max_pos = max(b.get('position', 0) for b in existing)
                position = max_pos + 1
            else:
                position = 0
    except Exception:
        position = 9999
    payload = {}
    insert_block(issue_id=issue_id, block_type=block_type, position=position, enabled=True, payload=payload)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/block/<int:block_id>/move', methods=['POST'])
def move_block_route(block_id: int):
    direction = request.form.get('direction', 'up')
    move_block(block_id=block_id, direction=direction)
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


# Block editor API endpoints (JSON)

@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/suggestions', methods=['GET'])
def get_block_suggestions(issue_id: int, block_id: int):
    """Get suggestions for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        block_type = block.get('type', '')
        
        logger.debug(f"Getting suggestions for block {block_id} (type: {block_type}, week: {target_week})")
        
        result = get_suggestions(
            block_id=block_id,
            block_type=block_type,
            issue_id=issue_id,
            target_week=target_week
        )
        
        logger.debug(f"Suggestions result: {len(result.get('suggestions', []))} suggestions found")
        
        # If no suggestions and no error, provide helpful message
        if not result.get('suggestions') and not result.get('error'):
            result['error'] = 'No suggestions available. Make sure source prefetch has run and there is content in the database.'
        
        return jsonify(result)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error getting suggestions: {e}", exc_info=True)
        return jsonify({'error': str(e), 'suggestions': [], 'current': None, 'metadata': {}}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/select-suggestion', methods=['POST'])
def select_block_suggestion(issue_id: int, block_id: int):
    """Apply a suggestion to a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        block_type = block.get('type', '')
        
        request_data = request.json if request.is_json else {}
        suggestion_id = request_data.get('suggestion_id')
        auto_select = request_data.get('auto_select', False)
        product_ids = request_data.get('product_ids')  # For new_products blocks
        
        if suggestion_id:
            try:
                suggestion_id = int(suggestion_id)
            except Exception:
                suggestion_id = None
        
        # For auto_select (e.g., re-choose products), ignore suggestion_id
        if auto_select:
            suggestion_id = None
        
        result = apply_suggestion(
            block_id=block_id,
            block_type=block_type,
            issue_id=issue_id,
            target_week=target_week,
            suggestion_id=suggestion_id,
            product_ids=product_ids  # Pass product IDs for new_products
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/override', methods=['POST'])
def override_block_text(issue_id: int, block_id: int):
    """Save manual text override for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        block_type = block.get('type', '')
        override_text = ''
        
        if request.is_json:
            override_text = request.json.get('text', '')
        else:
            override_text = request.form.get('text', '')
        
        result = save_override(
            block_id=block_id,
            block_type=block_type,
            override_text=override_text
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-products-intro', methods=['POST'])
def generate_products_intro(issue_id: int, block_id: int):
    """Generate intro paragraph for New Products Spotlight block."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.services.products_intro_service import generate_products_intro as generate_intro
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if block.get('type') != 'new_products':
            return jsonify({'error': 'This endpoint is only for new_products blocks'}), 400
        
        payload = block.get('payload_json', {})
        products = payload.get('items', [])
        
        if not products or len(products) == 0:
            return jsonify({'error': 'No products selected. Please select products first.'}), 400
        
        # Generate intro paragraph
        intro = generate_intro(products)
        
        return jsonify({
            'success': True,
            'intro': intro
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating products intro: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/confirm-products', methods=['POST'])
def confirm_products(issue_id: int, block_id: int):
    """Confirm product selection: save intro and mark products as launched."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.services.product_tracking import mark_products_newsletter_launched, extract_product_ids_from_payload
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if block.get('type') != 'new_products':
            return jsonify({'error': 'This endpoint is only for new_products blocks'}), 400
        
        # Get intro from request
        request_data = request.json if request.is_json else {}
        intro = request_data.get('intro', '')
        
        # Get current payload
        payload = block.get('payload_json', {})
        products = payload.get('items', [])
        
        if not products or len(products) == 0:
            return jsonify({'error': 'No products selected. Please select products first.'}), 400
        
        # Update payload with intro
        payload['intro'] = intro
        
        # Update block payload
        update_block_payload(block_id=block_id, payload=payload)
        
        # Mark products as newsletter launched
        product_ids = extract_product_ids_from_payload(payload, 'new_products')
        if product_ids:
            mark_products_newsletter_launched(product_ids)
        
        return jsonify({
            'success': True,
            'message': 'Products confirmed and marked as launched'
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error confirming products: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/preview', methods=['GET'])
def preview_block(issue_id: int, block_id: int):
    """Get rendered HTML preview for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        # For now, return payload; later can render full HTML
        payload = block.get('payload_json', {})
        block_type = block.get('type', '')
        
        return jsonify({
            'block_type': block_type,
            'payload': payload,
            'html': '',  # TODO: render actual HTML template
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Intro Block Component Generation Endpoints
@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-weather', methods=['GET'])
def generate_weather_component(issue_id: int, block_id: int):
    """Generate weather component for intro block."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.services.weather_analysis_service import get_weather_for_intro
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        weather_result = get_weather_for_intro(target_week=target_week)
        
        if weather_result:
            return jsonify({
                'success': True,
                'text': weather_result.get('summary_text', ''),
                'source_name': weather_result.get('source_name', ''),
                'url': weather_result.get('url', ''),
                'analysis': weather_result.get('analysis', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No weather data available for this period',
                'text': ''
            })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating weather component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-events', methods=['GET'])
def generate_events_component(issue_id: int, block_id: int):
    """Generate events component for intro block using LLM to create conversational comment."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.services.suggestion_service import generate_suggestions
        from newsletter.services.events_summary_service import get_event_detail
        from blueprints.header.llm_service import LLMService
        import os
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        
        # Get top event suggestion
        event_suggestions = generate_suggestions(block_type='intro', target_week=target_week, count=5, skip_validation=True)
        event_items = [s for s in event_suggestions if s.get('category') == 'event']
        
        if not event_items:
            return jsonify({
                'success': False,
                'error': 'No event suggestions available',
                'text': ''
            })
        
        event_item = event_items[0]
        event_id = event_item.get('id')
        
        # Get full event details including description
        event_detail = get_event_detail(event_id) if event_id else None
        
        # Extract event information
        source = event_item.get('source_name', '')
        title = event_item.get('title', '')
        location = event_item.get('location', '')
        url = event_item.get('url', '')
        
        # Get additional details from event_detail or raw_data
        description = ''
        date_text = ''
        if event_detail:
            description = event_detail.get('description', '') or event_detail.get('raw_data', {}).get('description', '')
            date_text = event_detail.get('date_text', '') or event_detail.get('raw_data', {}).get('date_text', '')
        else:
            # Fallback to raw_data from event_item
            raw_data = event_item.get('raw_data', {})
            description = raw_data.get('description', '') or raw_data.get('summary', '')
            date_text = raw_data.get('date_text', '')
        
        # Get event date
        event_date = event_item.get('event_date') or (event_detail.get('event_date') if event_detail else None)
        if event_date:
            if isinstance(event_date, str):
                from dateutil import parser
                try:
                    event_date = parser.parse(event_date)
                except:
                    event_date = None
        
        # Use LLM to generate conversational comment
        llm_service = LLMService()
        
        system_prompt = """You are writing a conversational, chatty comment about a Scottish cultural event for a heritage newsletter.
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, observational tone - like you're chatting with a friend about something interesting you've discovered.
Focus on what makes this event interesting or notable, not just announcing it.
Keep it to ONE sentence, maximum 30 words.
Write naturally - avoid clichés or repeated phrases. Each comment should be unique based on what's actually interesting about the event."""
        
        # Build user prompt with event details
        event_info_parts = []
        event_info_parts.append(f"EVENT: {title}")
        if location:
            event_info_parts.append(f"LOCATION: {location}")
        if source:
            event_info_parts.append(f"ORGANIZER: {source}")
        if event_date:
            event_info_parts.append(f"DATE: {event_date.strftime('%d %B %Y') if hasattr(event_date, 'strftime') else str(event_date)}")
        if date_text:
            event_info_parts.append(f"DATE TEXT: {date_text}")
        if description:
            # Limit description length for prompt
            desc_preview = description[:500] if len(description) > 500 else description
            event_info_parts.append(f"DESCRIPTION: {desc_preview}")
        
        user_prompt = f"""Write a single conversational sentence about this Scottish cultural event:

{chr(10).join(event_info_parts)}

Write ONE conversational sentence that:
1. Comments on what's interesting or notable about this event
2. Mentions the event naturally (not just "X has announced Y")
3. Highlights something that would appeal to someone interested in Scottish heritage/culture
4. Uses natural, varied language - avoid clichés
5. Sounds like a human observation, not a press release

Think about:
- What makes this event special or interesting?
- What would catch someone's attention?
- What cultural or historical significance does it have?
- What's the human angle or story?

If the description reveals something interesting (historical context, unique features, cultural significance), mention that naturally.

Your response should be ONLY the sentence, nothing else."""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error generating events component: {result['error']}")
                # Fallback to simple format
                if location:
                    text = f"Meanwhile, {source} has announced {title} in {location}."
                else:
                    text = f"Meanwhile, {source} has announced {title}."
            else:
                text = result.get('content', '').strip()
                # Clean up the response
                text = text.strip('"\'')
                text = text.strip()
                # Ensure it ends with proper punctuation
                if text and not text[-1] in '.!?':
                    text += '.'
                
                # Fallback if LLM returned empty
                if not text:
                    if location:
                        text = f"Meanwhile, {source} has announced {title} in {location}."
                    else:
                        text = f"Meanwhile, {source} has announced {title}."
        
        except Exception as e:
            logger.error(f"Error calling LLM for events component: {e}", exc_info=True)
            # Fallback to simple format
            if location:
                text = f"Meanwhile, {source} has announced {title} in {location}."
            else:
                text = f"Meanwhile, {source} has announced {title}."
        
        return jsonify({
            'success': True,
            'text': text,
            'source_name': source,
            'title': title,
            'location': location,
            'url': url,
            'suggestion_id': event_id
        })
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating events component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-theme', methods=['GET'])
def generate_theme_component(issue_id: int, block_id: int):
    """Generate theme component for intro block using LLM to create conversational comment."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.selectors.theme import parse_target_week, get_theme_by_id
        from blueprints.header.llm_service import LLMService
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Get theme from issue
        theme_id = issue.get('theme_id')
        if not theme_id:
            return jsonify({
                'success': False,
                'error': 'No theme selected for this issue',
                'text': ''
            })
        
        theme = get_theme_by_id(theme_id)
        if not theme:
            return jsonify({
                'success': False,
                'error': 'Theme not found',
                'text': ''
            })
        
        # Extract theme information
        theme_title = theme.get('idea_title', '')
        idea_description = theme.get('idea_description', '')
        seasonal_context = theme.get('seasonal_context', '')
        content_type = theme.get('content_type', '')
        tags = theme.get('tags', [])
        week_number = theme.get('week_number', '')
        
        # Use LLM to generate conversational comment
        llm_service = LLMService()
        
        system_prompt = """You are writing a conversational, chatty comment about a weekly theme for a Scottish heritage newsletter.
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, observational tone - like you're chatting with a friend about what you'll be exploring this week.
Focus on what makes this theme interesting or relevant, not just announcing it.
Keep it to ONE sentence, maximum 30 words.
Write naturally - avoid clichés or repeated phrases. Each comment should be unique based on what's actually interesting about the theme."""
        
        # Build user prompt with theme details
        theme_info_parts = []
        theme_info_parts.append(f"THEME: {theme_title}")
        if seasonal_context:
            theme_info_parts.append(f"SEASONAL CONTEXT: {seasonal_context}")
        if idea_description:
            # Limit description length for prompt
            desc_preview = idea_description[:500] if len(idea_description) > 500 else idea_description
            theme_info_parts.append(f"DESCRIPTION: {desc_preview}")
        if content_type:
            theme_info_parts.append(f"CONTENT TYPE: {content_type}")
        if tags:
            tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)
            theme_info_parts.append(f"TAGS: {tags_str}")
        if week_number:
            theme_info_parts.append(f"WEEK: {week_number}")
        
        user_prompt = f"""Write a single conversational sentence about this week's theme for the newsletter:

{chr(10).join(theme_info_parts)}

Write ONE conversational sentence that:
1. Comments on what's interesting or relevant about this theme
2. Mentions the theme naturally (not just "we're exploring X")
3. Highlights why this theme matters for someone interested in Scottish heritage/culture
4. Uses natural, varied language - avoid clichés
5. Sounds like a human observation, not a formal announcement

Think about:
- What makes this theme special or relevant?
- What would catch someone's attention?
- What cultural or historical significance does it have?
- Why is this theme timely or interesting?
- What's the human angle or story?

If the description reveals something interesting (historical context, cultural significance, seasonal relevance), mention that naturally.

Your response should be ONLY the sentence, nothing else."""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error generating theme component: {result['error']}")
                # Fallback to simple format
                if seasonal_context:
                    text = f"This week we're exploring {theme_title.lower()}, {seasonal_context.lower()}."
                else:
                    text = f"This week we're exploring {theme_title.lower()}."
            else:
                text = result.get('content', '').strip()
                # Clean up the response
                text = text.strip('"\'')
                text = text.strip()
                # Ensure it ends with proper punctuation
                if text and not text[-1] in '.!?':
                    text += '.'
                
                # Fallback if LLM returned empty
                if not text:
                    if seasonal_context:
                        text = f"This week we're exploring {theme_title.lower()}, {seasonal_context.lower()}."
                    else:
                        text = f"This week we're exploring {theme_title.lower()}."
        
        except Exception as e:
            logger.error(f"Error calling LLM for theme component: {e}", exc_info=True)
            # Fallback to simple format
            if seasonal_context:
                text = f"This week we're exploring {theme_title.lower()}, {seasonal_context.lower()}."
            else:
                text = f"This week we're exploring {theme_title.lower()}."
        
        return jsonify({
            'success': True,
            'text': text,
            'theme_title': theme_title,
            'seasonal_context': seasonal_context,
            'theme_id': theme_id
        })
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating theme component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/compile-intro', methods=['POST'])
def compile_intro(issue_id: int, block_id: int):
    """Compile weather, events, and theme into final intro paragraph using LLM."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from blueprints.header.llm_service import LLMService
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        weather_text = data.get('weather_text', '').strip()
        events_text = data.get('events_text', '').strip()
        theme_text = data.get('theme_text', '').strip()
        
        # Filter out placeholder/loading messages
        def is_valid_component(text):
            if not text:
                return False
            # Filter out placeholder messages
            invalid_phrases = ['Click "Generate"', 'Generating', 'Error:', 'No content yet']
            return not any(phrase in text for phrase in invalid_phrases)
        
        valid_components = []
        if is_valid_component(weather_text):
            valid_components.append(('weather', weather_text))
        if is_valid_component(events_text):
            valid_components.append(('events', events_text))
        if is_valid_component(theme_text):
            valid_components.append(('theme', theme_text))
        
        if not valid_components:
            return jsonify({
                'success': False,
                'error': 'No valid components provided to compile',
                'text': ''
            })
        
        # Use LLM to create coherent paragraph
        llm_service = LLMService()
        
        system_prompt = """You are writing the opening paragraph for a Scottish heritage newsletter.
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, welcoming tone - like you're greeting friends and catching them up.
Create a single, coherent paragraph (2-4 sentences) that weaves together the provided information naturally.
Do NOT just concatenate the sentences - rewrite them into a flowing, natural paragraph.
Decide on the best order: which element creates the best opening? Which should close?
Make it feel like a natural conversation, not a list of announcements."""
        
        # Build user prompt with all components
        components_info = []
        for comp_type, comp_text in valid_components:
            components_info.append(f"{comp_type.upper()}: {comp_text}")
        
        user_prompt = f"""You have three pieces of information about this week's newsletter:

{chr(10).join(components_info)}

Your task:
1. Consider all three elements as information (not as sentences to repeat)
2. Decide on the best order:
   - Which creates the best opening? (What would naturally start a conversation?)
   - Which should close? (What provides a good transition into the newsletter content?)
3. Rewrite them into a single coherent, welcoming paragraph (2-4 sentences) that:
   - Welcomes readers to this week's newsletter
   - Weaves the information together naturally
   - Doesn't just repeat the original wording - use the information to create new, flowing sentences
   - Feels like a natural conversation, not a list
   - Creates a warm, inviting opening

Think about:
- What's the most natural way to start? (Weather? Theme? Event?)
- How do these elements relate to each other?
- What creates the best flow and transition into the newsletter?

Your response should be ONLY the paragraph, nothing else."""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error compiling intro: {result['error']}")
                # Fallback: simple concatenation
                compiled_text = ' '.join([text for _, text in valid_components])
            else:
                compiled_text = result.get('content', '').strip()
                # Clean up the response
                compiled_text = compiled_text.strip('"\'')
                compiled_text = compiled_text.strip()
                
                # Fallback if LLM returned empty
                if not compiled_text:
                    compiled_text = ' '.join([text for _, text in valid_components])
        
        except Exception as e:
            logger.error(f"Error calling LLM for compile intro: {e}", exc_info=True)
            # Fallback: simple concatenation
            compiled_text = ' '.join([text for _, text in valid_components])
        
        # Save to block payload
        payload = block.get('payload_json', {}) or {}
        payload['text'] = compiled_text
        payload['weather_text'] = weather_text
        payload['events_text'] = events_text
        payload['theme_text'] = theme_text
        payload['manual_override'] = False
        
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'text': compiled_text
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error compiling intro: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


# Snapshot Block Component Generation Endpoints
@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-news', methods=['GET'])
def generate_news_component(issue_id: int, block_id: int):
    """Generate news component for snapshot block - returns top news items with summaries."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.services.suggestion_service import generate_suggestions
        from newsletter.db.queries_sources import get_cached_items
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        
        # Get used news item IDs from previous newsletters (exclude current issue)
        used_item_ids = set()
        try:
            from config.database import db_manager
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all snapshot blocks from other issues that have news_items
                    cur.execute("""
                        SELECT nb.payload_json
                        FROM newsletter_block nb
                        JOIN newsletter_issue ni ON nb.issue_id = ni.id
                        WHERE nb.type = 'snapshot'
                        AND nb.issue_id != %s
                        AND nb.payload_json IS NOT NULL
                        AND nb.payload_json != '{}'::jsonb
                        AND nb.payload_json ? 'news_items'
                    """, (issue_id,))
                    blocks = cur.fetchall()
                    for block_row in blocks:
                        payload = dict(block_row)['payload_json']
                        news_items_list = payload.get('news_items', [])
                        for item in news_items_list:
                            if isinstance(item, dict) and item.get('id'):
                                used_item_ids.add(item['id'])
        except Exception as e:
            logger.warning(f"Error getting used news items: {e}")
        
        # Get top news items (category='news')
        news_items = get_cached_items(category='news', days_back=14, limit=50)  # Get more to filter out used ones
        
        if not news_items:
            return jsonify({
                'success': False,
                'error': 'No news items available',
                'items': []
            })
        
        # Filter out items already used in previous newsletters
        if used_item_ids:
            news_items = [item for item in news_items if item.get('id') not in used_item_ids]
            logger.info(f"Filtered out {len(used_item_ids)} used news items, {len(news_items)} remaining")
        
        if not news_items:
            return jsonify({
                'success': False,
                'error': 'No new news items available (all have been used in previous newsletters)',
                'items': []
            })
        
        # Score and sort by combined_score
        from newsletter.services.scoring import score_items
        from datetime import datetime
        scored = score_items(news_items, reference_date=datetime.now())
        scored.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Take top 5 items
        top_news = scored[:5]
        
        # Format items with summaries
        formatted_items = []
        for item in top_news:
            # Convert datetime to ISO string if present
            published_at = item.get('published_at')
            if published_at and hasattr(published_at, 'isoformat'):
                published_at = published_at.isoformat()
            elif published_at:
                published_at = str(published_at)
            
            formatted_items.append({
                'id': item.get('id'),
                'title': item.get('title', ''),
                'source_name': item.get('source_name', ''),
                'url': item.get('url', ''),
                'summary': item.get('raw_data', {}).get('description', '')[:200] if item.get('raw_data', {}).get('description') else '',
                'published_at': published_at,
                'combined_score': float(item.get('combined_score', 0))
            })
        
        # Save to block payload
        payload = block.get('payload_json', {}) or {}
        payload['news_items'] = formatted_items
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'items': formatted_items
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating news component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-snapshot-events', methods=['GET'])
def generate_snapshot_events_component(issue_id: int, block_id: int):
    """Generate events component for snapshot block - returns top event items with summaries."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.db.queries_sources import get_cached_items
        from newsletter.services.scoring import score_items
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        
        # Get used event item IDs from previous newsletters (exclude current issue)
        used_item_ids = set()
        try:
            from config.database import db_manager
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all snapshot blocks from other issues that have events_items
                    cur.execute("""
                        SELECT nb.payload_json
                        FROM newsletter_block nb
                        JOIN newsletter_issue ni ON nb.issue_id = ni.id
                        WHERE nb.type = 'snapshot'
                        AND nb.issue_id != %s
                        AND nb.payload_json IS NOT NULL
                        AND nb.payload_json != '{}'::jsonb
                        AND nb.payload_json ? 'events_items'
                    """, (issue_id,))
                    blocks = cur.fetchall()
                    for block_row in blocks:
                        payload = dict(block_row)['payload_json']
                        events_items_list = payload.get('events_items', [])
                        for item in events_items_list:
                            if isinstance(item, dict) and item.get('id'):
                                used_item_ids.add(item['id'])
        except Exception as e:
            logger.warning(f"Error getting used event items: {e}")
        
        # Get top event items (category='event')
        event_items = get_cached_items(category='event', days_back=14, limit=50)  # Get more to filter out used ones
        
        if not event_items:
            return jsonify({
                'success': False,
                'error': 'No event items available',
                'items': []
            })
        
        # Filter out items already used in previous newsletters
        if used_item_ids:
            event_items = [item for item in event_items if item.get('id') not in used_item_ids]
            logger.info(f"Filtered out {len(used_item_ids)} used event items, {len(event_items)} remaining")
        
        if not event_items:
            return jsonify({
                'success': False,
                'error': 'No new event items available (all have been used in previous newsletters)',
                'items': []
            })
        
        # Score and sort by combined_score
        scored = score_items(event_items, reference_date=datetime.now())
        scored.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Take top 5 items
        top_events = scored[:5]
        
        # Format items with summaries
        formatted_items = []
        for item in top_events:
            # Convert datetime to ISO string if present
            event_date = item.get('event_date')
            if event_date and hasattr(event_date, 'isoformat'):
                event_date = event_date.isoformat()
            elif event_date:
                event_date = str(event_date)
            
            formatted_items.append({
                'id': item.get('id'),
                'title': item.get('title', ''),
                'source_name': item.get('source_name', ''),
                'url': item.get('url', ''),
                'location': item.get('location', ''),
                'event_date': event_date,
                'summary': item.get('raw_data', {}).get('description', '')[:200] if item.get('raw_data', {}).get('description') else '',
                'combined_score': float(item.get('combined_score', 0))
            })
        
        # Save to block payload
        payload = block.get('payload_json', {}) or {}
        payload['events_items'] = formatted_items
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'items': formatted_items
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating events component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/compile-snapshot', methods=['POST'])
def compile_snapshot(issue_id: int, block_id: int):
    """Compile news and events into two chatty paragraphs with embedded links using LLM."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from blueprints.header.llm_service import LLMService
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        payload = block.get('payload_json', {}) or {}
        news_items = payload.get('news_items', [])
        events_items = payload.get('events_items', [])
        
        if not news_items and not events_items:
            return jsonify({
                'success': False,
                'error': 'No items available. Please generate news and/or events components first.',
                'result': None
            })
        
        # Use LLM to generate two chatty paragraphs
        llm_service = LLMService()
        
        # Build context for LLM
        news_context = []
        for item in news_items[:10]:  # Limit to top 10 for context
            news_context.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'source': item.get('source_name', ''),
                'summary': item.get('summary', '')
            })
        
        events_context = []
        for item in events_items[:10]:  # Limit to top 10 for context
            events_context.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'source': item.get('source_name', ''),
                'location': item.get('location', ''),
                'summary': item.get('summary', '')
            })
        
        system_prompt = """You are a newsletter writer creating a chatty "In the News" section for a Scottish heritage newsletter.

Your task is to write TWO separate paragraphs:
1. NEWS PARAGRAPH: A chatty overview of the news stories, mentioning story titles with embedded markdown links [title](url)
2. EVENTS PARAGRAPH: A chatty overview of the events, mentioning event titles with embedded markdown links [title](url)

IMPORTANT FORMATTING REQUIREMENTS:
- Start your response with exactly "NEWS:" on its own line
- Then write the news paragraph (3-5 sentences, conversational tone)
- Then write exactly "EVENTS:" on its own line  
- Then write the events paragraph (3-5 sentences, conversational tone)

Where stories overlap or discuss the same topic, mention them together naturally.
Write in a warm, conversational, engaging tone - like a friend sharing interesting news.
Each paragraph should be 3-5 sentences and flow naturally. Use markdown links: [Story Title](url)"""
        
        user_prompt = f"""Create two chatty paragraphs for "In the News" section.

NEWS STORIES TO COVER:
{chr(10).join([f"- {item['title']} ({item['source']}): {item['url']}" + (f" - {item['summary'][:100]}" if item.get('summary') else "") for item in news_context])}

EVENTS TO COVER:
{chr(10).join([f"- {item['title']} ({item['source']})" + (f" in {item['location']}" if item.get('location') else "") + f": {item['url']}" + (f" - {item['summary'][:100]}" if item.get('summary') else "") for item in events_context])}

REQUIRED OUTPUT FORMAT (follow exactly):
NEWS:
[Write a chatty 3-5 sentence paragraph about the news stories. Mention story titles with markdown links like [Story Title](url). Write conversationally, like sharing interesting news with a friend. If stories are related, mention them together.]

EVENTS:
[Write a chatty 3-5 sentence paragraph about the events. Mention event titles with markdown links like [Event Title](url). Write conversationally about what's happening. If events are related, mention them together.]

Remember: Start with "NEWS:" on its own line, then the paragraph, then "EVENTS:" on its own line, then the events paragraph."""
        
        try:
            logger.info(f"Calling LLM to generate snapshot paragraphs for {len(news_context)} news items and {len(events_context)} events")
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error generating snapshot paragraphs: {result['error']}")
                return jsonify({
                    'success': False,
                    'error': f'LLM generation failed: {result["error"]}. Please try again.',
                    'result': None
                }), 500
            
            response = result.get('content', '').strip()
            logger.info(f"LLM response received: {response[:200] if response else 'None'}...")
            
            # Parse the response to extract news and events paragraphs
            news_paragraph = ""
            events_paragraph = ""
            
            if response:
                response_text = response.strip()
                logger.info(f"Processing LLM response (length: {len(response_text)})")
                
                # Try to split by "NEWS:" and "EVENTS:" markers (case insensitive)
                response_upper = response_text.upper()
                if "NEWS:" in response_upper and "EVENTS:" in response_upper:
                    # Find the actual case-sensitive markers
                    news_idx = response_text.upper().find("NEWS:")
                    events_idx = response_text.upper().find("EVENTS:")
                    
                    if news_idx < events_idx:
                        news_paragraph = response_text[news_idx + 5:events_idx].strip()
                        events_paragraph = response_text[events_idx + 7:].strip()
                        logger.info("Parsed using NEWS:/EVENTS: markers")
                elif "NEWS" in response_upper and "EVENTS" in response_upper:
                    # Try alternative parsing - look for section headers
                    lines = response_text.split('\n')
                    current_section = None
                    news_lines = []
                    events_lines = []
                    
                    for line in lines:
                        line_upper = line.upper().strip()
                        if 'NEWS' in line_upper and ('PARAGRAPH' in line_upper or ':' in line):
                            current_section = 'news'
                            continue
                        elif 'EVENTS' in line_upper and ('PARAGRAPH' in line_upper or ':' in line):
                            current_section = 'events'
                            continue
                        elif current_section == 'news' and line.strip() and not line.strip().startswith('#'):
                            news_lines.append(line.strip())
                        elif current_section == 'events' and line.strip() and not line.strip().startswith('#'):
                            events_lines.append(line.strip())
                    
                    news_paragraph = ' '.join(news_lines).strip()
                    events_paragraph = ' '.join(events_lines).strip()
                    logger.info(f"Parsed using section headers - news: {len(news_paragraph)} chars, events: {len(events_paragraph)} chars")
                else:
                    # If no clear markers, try to intelligently split
                    # Look for paragraph breaks (double newlines or periods followed by space and capital)
                    logger.warning("No clear NEWS/EVENTS markers found, attempting intelligent split")
                    
                    if news_items and events_items:
                        # Try to find a natural break point
                        # Look for sentence endings followed by what might be a new paragraph
                        sentences = []
                        current_sentence = ""
                        for char in response_text:
                            current_sentence += char
                            if char in '.!?' and len(current_sentence.strip()) > 20:
                                sentences.append(current_sentence.strip())
                                current_sentence = ""
                        if current_sentence.strip():
                            sentences.append(current_sentence.strip())
                        
                        if len(sentences) >= 4:
                            # Split roughly in half, but try to keep paragraphs together
                            mid_point = len(sentences) // 2
                            news_paragraph = ' '.join(sentences[:mid_point])
                            events_paragraph = ' '.join(sentences[mid_point:])
                            logger.info("Split response into two paragraphs by sentence count")
                        else:
                            # Just use the whole response for news if we can't split well
                            news_paragraph = response_text
                            events_paragraph = ""
                            logger.warning("Could not split response, using all as news")
                    elif news_items:
                        news_paragraph = response_text
                    elif events_items:
                        events_paragraph = response_text
                
                # Clean up paragraphs - remove any remaining markers
                news_paragraph = news_paragraph.replace('NEWS:', '').replace('NEWS', '').strip()
                events_paragraph = events_paragraph.replace('EVENTS:', '').replace('EVENTS', '').strip()
                
                # Remove leading/trailing quotes or colons
                news_paragraph = news_paragraph.lstrip(':').strip('"').strip("'").strip()
                events_paragraph = events_paragraph.lstrip(':').strip('"').strip("'").strip()
            
            # Log what we parsed
            logger.info(f"Parsed news_paragraph length: {len(news_paragraph)}, events_paragraph length: {len(events_paragraph)}")
            
            # Validate that we got actual content
            if not news_paragraph and news_items:
                logger.error("News paragraph is empty after LLM call")
                return jsonify({
                    'success': False,
                    'error': 'LLM failed to generate news paragraph. Please try again.',
                    'result': None
                }), 500
            if not events_paragraph and events_items:
                logger.error("Events paragraph is empty after LLM call")
                return jsonify({
                    'success': False,
                    'error': 'LLM failed to generate events paragraph. Please try again.',
                    'result': None
                }), 500
            
            # Save to block payload
            payload['news_paragraph'] = news_paragraph
            payload['events_paragraph'] = events_paragraph
            payload['compiled_at'] = datetime.now().isoformat()
            payload['manual_override'] = False
            
            update_block_payload(block_id=block_id, payload=payload)
            
            return jsonify({
                'success': True,
                'result': {
                    'news_paragraph': news_paragraph,
                    'events_paragraph': events_paragraph
                }
            })
            
        except Exception as llm_error:
            logger.error(f"LLM error in compile_snapshot: {llm_error}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'LLM generation failed: {str(llm_error)}. Please try again.',
                'result': None
            }), 500
            
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error compiling snapshot: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-feature-summary', methods=['POST'])
def generate_feature_summary(issue_id: int, block_id: int):
    """Generate chatty summary for feature block post using LLM."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.services.feature_summary_service import generate_feature_summary as generate_summary
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        post_id = data.get('post_id')
        title = data.get('title', '')
        expanded_idea = data.get('expanded_idea', '')
        
        if not post_id:
            return jsonify({'error': 'post_id required'}), 400
        
        # Generate chatty summary
        summary = generate_summary(title=title, expanded_idea=expanded_idea)
        
        # Update block payload with new summary
        payload = block.get('payload_json', {}) or {}
        payload['excerpt'] = summary
        payload['id'] = post_id
        payload['title'] = title
        payload['url'] = data.get('url', payload.get('url', ''))
        payload['hero_image'] = data.get('hero_image', payload.get('hero_image', ''))
        
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'excerpt': summary
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating feature summary: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


# Source Management Routes

@bp.route('/newsletter/weather/summary')
def weather_summary():
    """Get weather summary for past week and forecast."""
    try:
        from newsletter.services.weather_summary_service import generate_weather_summary
        
        days_back = request.args.get('days_back', 7, type=int)
        days_ahead = request.args.get('days_ahead', 7, type=int)
        
        summary = generate_weather_summary(days_back=days_back, days_ahead=days_ahead)
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/weather_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating weather summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/weather_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/weather')
def weather_summary_page():
    """Weather summary page UI."""
    return render_template('newsletter/weather_summary.html')


@bp.route('/newsletter/news/summary')
def news_summary():
    """Get news summary from synopses."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.news_synopsis_service import generate_news_summary
        
        days_back = request.args.get('days_back', 7, type=int)
        limit = request.args.get('limit', 100, type=int)  # Default to 100, allow override
        sort_by = request.args.get('sort_by', 'combined_score')  # combined_score, suitability_score, published_at
        
        summary = generate_news_summary(days_back=days_back, limit=limit, sort_by=sort_by)
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/news_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating news summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/news_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/news')
def news_summary_page():
    """News summary page UI."""
    return render_template('newsletter/news_summary.html')


@bp.route('/newsletter/events/summary')
def events_summary():
    """Get events summary."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.events_summary_service import generate_events_summary
        
        days_back = request.args.get('days_back', 365, type=int)  # Default to 1 year back
        days_ahead = request.args.get('days_ahead', 365, type=int)  # Default to 1 year ahead
        source_name = request.args.get('source', None, type=str)
        location = request.args.get('location', None, type=str)
        
        recurrence_type = request.args.get('recurrence_type', None, type=str)
        
        summary = generate_events_summary(
            days_back=days_back,
            days_ahead=days_ahead,
            source_name=source_name,
            location=location,
            recurrence_type=recurrence_type
        )
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/events_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating events summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/events_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/events')
def events_summary_page():
    """Events summary page UI."""
    return render_template('newsletter/events_summary.html')


@bp.route('/newsletter/events/<int:event_id>')
def event_detail(event_id: int):
    """Get detailed view of a single event."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.events_summary_service import get_event_detail
        
        event = get_event_detail(event_id)
        
        if not event:
            return render_template('newsletter/event_detail.html', error='Event not found'), 404
        
        return render_template('newsletter/event_detail.html', event=event)
    except Exception as e:
        logger.error(f"Error fetching event detail: {e}", exc_info=True)
        return render_template('newsletter/event_detail.html', error=str(e)), 500


@bp.route('/newsletter/events/<int:event_id>/recurrence-type', methods=['POST'])
def update_event_recurrence_type(event_id: int):
    """Update event recurrence type (manual override)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = request.get_json()
        recurrence_type = data.get('recurrence_type')
        
        if recurrence_type not in ('annual', 'one_off'):
            return jsonify({'success': False, 'error': 'Invalid recurrence_type. Must be "annual" or "one_off"'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check event exists
                cur.execute("""
                    SELECT id FROM newsletter_source_item
                    WHERE id = %s AND category = 'event'
                """, (event_id,))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                # Update recurrence type
                cur.execute("""
                    UPDATE newsletter_source_item
                    SET event_recurrence_type = %s
                    WHERE id = %s
                """, (recurrence_type, event_id))
                
                conn.commit()
                
                logger.info(f"Updated event {event_id} recurrence type to {recurrence_type}")
                
                return jsonify({
                    'success': True,
                    'message': f'Event classified as {recurrence_type}',
                    'recurrence_type': recurrence_type
                })
    except Exception as e:
        logger.error(f"Error updating event recurrence type: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/events/<int:event_id>/update', methods=['POST'])
def update_event_field(event_id: int):
    """Update a specific field of an event."""
    import logging
    from datetime import datetime
    from psycopg.types.json import Json
    
    logger = logging.getLogger(__name__)
    
    try:
        from config.database import db_manager
        
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        
        if not field:
            return jsonify({'success': False, 'error': 'Field name required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check event exists and get current raw_data
                cur.execute("""
                    SELECT id, raw_data FROM newsletter_source_item
                    WHERE id = %s AND category = 'event'
                """, (event_id,))
                
                row = cur.fetchone()
                if not row:
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                event_id_db, raw_data = row
                if not raw_data:
                    raw_data = {}
                
                # Update based on field type
                if field == 'title':
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET title = %s
                        WHERE id = %s
                    """, (value, event_id))
                    raw_data['title'] = value
                
                elif field == 'description':
                    raw_data['description'] = value
                    raw_data['summary'] = value  # Also update summary
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(raw_data), event_id))
                
                elif field == 'date_text':
                    raw_data['date_text'] = value
                    raw_data['date_text_preserved'] = value
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(raw_data), event_id))
                
                elif field == 'event_date':
                    # Parse date string and update both event_date and raw_data
                    event_date = None
                    if value:
                        try:
                            event_date = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            return jsonify({'success': False, 'error': 'Invalid date format'}), 400
                    
                    raw_data['event_date'] = value if value else None
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET event_date = %s, raw_data = %s
                        WHERE id = %s
                    """, (event_date, Json(raw_data), event_id))
                
                elif field == 'location':
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET location = %s
                        WHERE id = %s
                    """, (value if value else None, event_id))
                    raw_data['location'] = value if value else None
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(raw_data), event_id))
                
                else:
                    return jsonify({'success': False, 'error': f'Unknown field: {field}'}), 400
                
                conn.commit()
                
                logger.info(f"Updated event {event_id} field {field}")
                
                return jsonify({
                    'success': True,
                    'message': f'Field {field} updated',
                    'value': value
                })
    except Exception as e:
        logger.error(f"Error updating event field: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id: int):
    """Delete an event (soft delete by marking as deleted)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from config.database import db_manager
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check event exists
                cur.execute("""
                    SELECT id FROM newsletter_source_item
                    WHERE id = %s AND category = 'event'
                """, (event_id,))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                # Soft delete - mark as deleted
                # Assuming we have a deleted column, otherwise we'll need to add it
                # For now, let's check if deleted column exists, if not, actually delete
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'newsletter_source_item' AND column_name = 'deleted'
                """)
                
                if cur.fetchone():
                    # Soft delete
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET deleted = TRUE
                        WHERE id = %s
                    """, (event_id,))
                else:
                    # Hard delete (if no deleted column)
                    cur.execute("""
                        DELETE FROM newsletter_source_item
                        WHERE id = %s
                    """, (event_id,))
                
                conn.commit()
                
                logger.info(f"Deleted event {event_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Event deleted successfully'
                })
    except Exception as e:
        logger.error(f"Error deleting event: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/news/reanalyze', methods=['POST'])
def reanalyze_news():
    """Re-analyze existing news items with synopsis service."""
    try:
        from newsletter.jobs.reanalyze_news import reanalyze_news_items
        
        result = reanalyze_news_items(days_back=30, limit=50)
        
        return jsonify({
            'success': True,
            'message': f"Re-analyzed {result['processed']} items, skipped {result['skipped']}, errors {result['errors']}",
            'result': result
        })
    except Exception as e:
        logger.error(f"Error re-analyzing news: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/news/clean', methods=['POST'])
def clean_synopses():
    """Clean subscription text from existing synopses."""
    try:
        from newsletter.jobs.clean_existing_synopses import clean_all_synopses
        
        result = clean_all_synopses()
        
        return jsonify({
            'success': True,
            'message': f"Cleaned {result['updated']} synopses, {result['unchanged']} unchanged",
            'result': result
        })
    except Exception as e:
        logger.error(f"Error cleaning synopses: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/sources')
def sources_management():
    """Source aggregation management page."""
    sources = list_all_sources()
    cache_status = get_cache_status()
    item_stats = get_item_stats()
    
    # Get cached items for preview (recent 20)
    recent_items = get_cached_items(days_back=14, limit=20)
    
    return render_template(
        'newsletter/sources.html',
        sources=sources,
        cache_status=cache_status,
        item_stats=item_stats,
        recent_items=recent_items,
    )


@bp.route('/newsletter/sources/add', methods=['POST'])
def add_source():
    """Add a new source."""
    name = request.form.get('name', '').strip()
    base_url = request.form.get('base_url', '').strip()
    source_type = request.form.get('type', 'rss').strip()
    enabled = request.form.get('enabled', 'off') == 'on'
    api_key_ref = request.form.get('api_key_ref', '').strip() or None
    
    if not name or not base_url:
        return redirect(url_for('newsletter.sources_management')), 302
    
    create_source(name=name, base_url=base_url, type=source_type, enabled=enabled, api_key_ref=api_key_ref)
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/edit', methods=['POST'])
def edit_source(source_id: int):
    """Update an existing source."""
    name = request.form.get('name', '').strip()
    base_url = request.form.get('base_url', '').strip()
    source_type = request.form.get('type', 'rss').strip()
    enabled = request.form.get('enabled', 'off') == 'on'
    api_key_ref = request.form.get('api_key_ref', '').strip() or None
    
    updates = {}
    if name:
        updates['name'] = name
    if base_url:
        updates['base_url'] = base_url
    if source_type:
        updates['type'] = source_type
    updates['enabled'] = enabled
    if api_key_ref is not None:
        updates['api_key_ref'] = api_key_ref
    
    update_source(source_id, **updates)
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/delete', methods=['POST'])
def delete_source_route(source_id: int):
    """Delete a source."""
    delete_source(source_id)
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/toggle', methods=['POST'])
def toggle_source(source_id: int):
    """Toggle source enabled/disabled."""
    source = get_source(source_id)
    if source:
        update_source(source_id, enabled=not source.get('enabled', False))
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/fetch', methods=['POST'])
def trigger_fetch():
    """Manually trigger source prefetch job."""
    result = run_prefetch()
    # Could show success/error message, but for now just redirect
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/test', methods=['GET'])
def test_source(source_id: int):
    """Test a source by fetching and returning sample items with proper error handling."""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        source = get_source(source_id)
        if not source:
            logger.warning(f"Source test: source {source_id} not found")
            return jsonify({
                'success': False, 
                'error': 'Source not found',
                'error_type': 'not_found'
            }), 404
        
        if not source.get('enabled'):
            logger.info(f"Source test: {source.get('name')} is disabled")
            return jsonify({
                'success': False, 
                'error': 'Source is disabled. Enable it first to test.',
                'error_type': 'disabled'
            }), 400
        
        # Use manager to create adapter and fetch
        from newsletter.sources.manager import create_adapter_from_source
        
        source_name = source.get('name', 'Unknown')
        source_type = source.get('type', 'unknown')
        source_url = source.get('base_url', '')
        
        logger.info(f"Testing source: {source_name} (type: {source_type}, url: {source_url})")
        
        # Create adapter with explicit error handling
        try:
            adapter = create_adapter_from_source(source)
        except Exception as adapter_error:
            error_msg = f"Failed to create adapter: {str(adapter_error)}"
            logger.error(f"Source test adapter creation failed: {error_msg}", exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'adapter_creation_error',
                'source_name': source_name,
                'source_type': source_type
            }), 500
        
        if not adapter:
            error_msg = f"Could not create adapter for type: {source_type}. Supported types: rss, reddit, html, weather, event, museum"
            logger.error(f"Source test: {error_msg}")
            return jsonify({
                'success': False, 
                'error': error_msg,
                'error_type': 'unsupported_type',
                'source_type': source_type
            }), 400
        
        # Log adapter category assignment for debugging
        adapter_category = None
        if hasattr(adapter, 'category'):
            adapter_category = adapter.category
            logger.info(f"Adapter created: {type(adapter).__name__} with category: {adapter_category}")
        else:
            logger.warning(f"Adapter {type(adapter).__name__} has no category attribute")
        
        # Fetch items with error handling
        try:
            logger.info(f"Fetching items from {source_name}...")
            items = adapter.fetch_and_normalize()
            logger.info(f"Fetched {len(items)} items from {source_name}")
        except Exception as fetch_error:
            error_msg = f"Failed to fetch from source: {str(fetch_error)}"
            logger.error(f"Source test fetch failed for {source_name}: {error_msg}", exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'fetch_error',
                'source_name': source_name,
                'details': str(fetch_error)
            }), 500
        
        if not items:
            return jsonify({
                'success': True,
                'items_count': 0,
                'categories': {},
                'items': [],
                'warning': 'No items found. The source may be empty, require authentication, or the URL may be incorrect.',
                'adapter_category': adapter_category
            })
        
        # Limit to first 10 for preview
        preview_items = items[:10]
        
        # Group by category for debugging and validation
        categories = {}
        category_breakdown = {}
        for item in items:
            cat = item.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
            if cat not in category_breakdown:
                category_breakdown[cat] = []
            category_breakdown[cat].append(item.get('title', 'No title')[:50])
        
        # Validate category assignment
        category_mismatch = False
        expected_category = None
        if adapter_category and categories:
            # Check if adapter category matches items
            if adapter_category not in categories:
                category_mismatch = True
                expected_category = adapter_category
                logger.warning(
                    f"Category mismatch: adapter category '{adapter_category}' but items have categories: {list(categories.keys())}"
                )
        
        return jsonify({
            'success': True,
            'items_count': len(items),
            'categories': categories,
            'category_breakdown': {k: len(v) for k, v in category_breakdown.items()},
            'adapter_category': adapter_category,
            'category_validation': {
                'match': not category_mismatch,
                'expected': expected_category,
                'found': list(categories.keys())
            },
            'items': [
                {
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'category': item.get('category', 'other'),
                    'source_name': item.get('source_name', ''),
                    'published_at': item.get('published_at').isoformat() if item.get('published_at') else None,
                    'event_date': item.get('event_date').isoformat() if item.get('event_date') else None,
                    'raw_data_preview': str(item.get('raw_data', {}))[:100] if item.get('raw_data') else None,
                }
                for item in preview_items
            ],
        })
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Source test failed for source {source_id}: {error_msg}", exc_info=True)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'unexpected_error',
            'traceback': error_trace if logger.level <= logging.DEBUG else None
        }), 500


@bp.route('/newsletter/sources/items')
def cached_items():
    """Full cached items page with filters."""
    from newsletter.db.queries_source_management import list_all_sources
    
    # Get filter parameters
    category_filter = request.args.get('category', '')
    source_filter = request.args.get('source', '')
    days_back = int(request.args.get('days', '14'))
    
    # Get items
    items = get_cached_items(
        category=category_filter if category_filter else None,
        days_back=days_back,
        limit=500  # Increased limit to show more items
    )
    
    # Filter by source if provided
    if source_filter:
        items = [item for item in items if item.get('source_name', '').lower() == source_filter.lower()]
    
    # Get all possible categories (including weather)
    all_categories = ['news', 'weather', 'event', 'community', 'other']
    
    # Get all sources from database (not just cached items)
    all_sources = list_all_sources()
    sources = sorted([s.get('name', '') for s in all_sources if s.get('name')])
    
    return render_template(
        'newsletter/cached_items.html',
        items=items,
        categories=all_categories,
        sources=sources,
        category_filter=category_filter,
        source_filter=source_filter,
        days_back=days_back,
    )

