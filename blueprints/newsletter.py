"""Newsletter Blueprint - Top-level UI shell.

Routes here stay thin (<60 LOC each) and delegate to services. Keep this file
small; split views into helpers if it approaches ~400–500 LOC.
"""

from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, request
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
from newsletter.jobs.weekly_autodraft import run as run_autodraft

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
    try:
        blocks = list_blocks_by_issue(issue_id=issue_id)
    except Exception:
        blocks = []
    # Map blocks to pass each payload as "block" expected by partials
    normalized = []
    for b in blocks:
        normalized.append({
            "type": b.get("type"),
            "payload_json": b.get("payload_json", {}),
        })
    # The partials expect a variable named `block` when included; render will set it via context assignment
    # We pass blocks and reuse includes that reference `block` by setting it before each include in template
    # Simpler: in template we refer to b.payload_json as `block` using Jinja context; here we just pass blocks
    return render_template('newsletter/render.html', subject=f"Issue {issue_id}", blocks=[{"type": b["type"], "payload_json": b["payload_json"]} for b in blocks])


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


