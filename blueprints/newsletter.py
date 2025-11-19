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
    """Create a new draft issue and populate initial blocks."""
    result = build_weekly_issue()
    return redirect(url_for('newsletter.view_issue', issue_id=result["issue_id"]))


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
    
    return render_template('newsletter/issue.html', issue_id=issue_id, issue=issue, blocks=blocks, themes=themes, current_theme=current_theme)


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
    
    # Map blocks to pass each payload as "block" expected by partials
    return render_template(
        'newsletter/render.html',
        subject=f"Issue {issue_id}",
        issue=issue,
        blocks=[{"type": b["type"], "payload_json": b["payload_json"]} for b in blocks],
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
    raw = request.form.get('payload_json') or '{}'
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {}
    update_block_payload(block_id=block_id, payload=payload)
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
        
        suggestion_id = request.json.get('suggestion_id') if request.is_json else None
        if suggestion_id:
            try:
                suggestion_id = int(suggestion_id)
            except Exception:
                suggestion_id = None
        
        result = apply_suggestion(
            block_id=block_id,
            block_type=block_type,
            issue_id=issue_id,
            target_week=target_week,
            suggestion_id=suggestion_id
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

