"""
Canonical blog post status transition helper.
W2-FIX-4: Single source of truth for post.status writes.
"""

import json
import logging
from typing import Optional, Tuple

from config.database import db_manager

logger = logging.getLogger(__name__)

USE_NOW = object()  # Sentinel: set column = CURRENT_TIMESTAMP
USE_NOW_IF_NULL = object()  # Sentinel: set column = COALESCE(column, CURRENT_TIMESTAMP)
VALID_STATUSES = frozenset({'draft', 'in_process', 'published', 'archived', 'deleted'})

# (from_status, to_status) -> allowed. Terminal: deleted cannot transition.
# Published must be archived before deletion.
ALLOWED_TRANSITIONS = {
    ('draft', 'in_process'),
    ('draft', 'deleted'),
    ('in_process', 'published'),
    ('in_process', 'draft'),   # revoke ready
    ('in_process', 'deleted'),
    ('published', 'archived'),
    ('archived', 'draft'),
    ('archived', 'deleted'),
}


def get_post_status(post_id: int) -> Optional[str]:
    """Get current post status."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT status FROM post WHERE id = %s", (post_id,))
        row = cursor.fetchone()
    return (row.get('status') or '').strip().lower() if row else None


def transition_post_status(
    post_id: int,
    target_status: str,
    actor: str = 'system',
    reason: Optional[str] = None,
    override: bool = False,
    extra_updates: Optional[dict] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Transition post status with validation.
    Returns (success, error_message). If success, error_message is None.
    
    extra_updates: dict of column -> value to set in same UPDATE (e.g. clan_post_id, clan_error).
    """
    target = (target_status or '').strip().lower()
    if target not in VALID_STATUSES:
        return False, f"Invalid target status: {target_status}. Allowed: {', '.join(sorted(VALID_STATUSES))}"

    current = get_post_status(post_id)
    if not current:
        return False, "Post not found"

    if current == 'deleted':
        return False, "Cannot transition from deleted (terminal state)"

    if override:
        # Admin bypass - allow any transition from non-deleted
        pass
    elif (current, target) not in ALLOWED_TRANSITIONS:
        return False, (
            f"Transition not allowed: {current} -> {target}. "
            f"Valid transitions: draft->in_process, draft->deleted, in_process->published, "
            f"in_process->draft, in_process->deleted, published->archived, published->deleted, "
            f"archived->draft, archived->deleted"
        )

    sets = ["status = %s", "updated_at = CURRENT_TIMESTAMP"]
    vals = [target]

    extra_allowed = (
        'clan_post_id', 'clan_uploaded_url', 'clan_error', 'clan_last_attempt',
        'first_published_at', 'publish_at', 'extra_settings'
    )
    if extra_updates:
        for k, v in extra_updates.items():
            if k in extra_allowed:
                if v is USE_NOW:
                    sets.append(f"{k} = CURRENT_TIMESTAMP")
                elif v is USE_NOW_IF_NULL:
                    sets.append(f"{k} = COALESCE({k}, CURRENT_TIMESTAMP)")
                elif v is None and k == 'clan_error':
                    sets.append("clan_error = NULL")
                elif v is not None:
                    sets.append(f"{k} = %s")
                    vals.append(v)

    vals.append(post_id)
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            f"UPDATE post SET {', '.join(sets)} WHERE id = %s",
            vals
        )
        if cursor.rowcount == 0:
            return False, "Post not found"
        cursor.connection.commit()

    logger.info(f"Post {post_id} status: {current} -> {target} (actor={actor})")
    return True, None


def set_post_paused(post_id: int, paused: bool) -> Tuple[bool, Optional[str]]:
    """
    Set extra_settings.paused for automation pause/resume.
    Does NOT change post.status.
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "SELECT extra_settings FROM post WHERE id = %s",
            (post_id,)
        )
        row = cursor.fetchone()
    if not row:
        return False, "Post not found"

    extra = row.get('extra_settings') or {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            extra = {}

    extra['paused'] = bool(paused)
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "UPDATE post SET extra_settings = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (json.dumps(extra), post_id)
        )
        if cursor.rowcount == 0:
            return False, "Post not found"
        cursor.connection.commit()
    return True, None


def require_post_editable(
    post_id: int,
    allowed_statuses: frozenset = frozenset({'draft', 'in_process'}),
    override_param: str = 'override',
    request=None,
) -> Tuple[Optional[str], Optional[int]]:
    """
    Check if post is editable. Returns (error_message, status_code) if blocked, else (None, None).
    request: Flask request object to check override_param.
    """
    status = get_post_status(post_id)
    if not status:
        return "Post not found", 404
    if status in allowed_statuses:
        return None, None
    if request and request.args.get(override_param) == '1':
        return None, None  # Admin override
    blocked_statuses = ', '.join(sorted(VALID_STATUSES - allowed_statuses))
    return (
        f"Post is {status}. Editing allowed only for: {', '.join(sorted(allowed_statuses))}. "
        f"Blocked statuses: {blocked_statuses}. Use Mark Ready to set in_process, or ?override=1 for admin.",
        403
    )


def is_post_paused(post_id: int) -> bool:
    """Check if post has extra_settings.paused = true."""
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "SELECT extra_settings FROM post WHERE id = %s",
            (post_id,)
        )
        row = cursor.fetchone()
    if not row:
        return False
    extra = row.get('extra_settings') or {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            return False
    return bool(extra.get('paused'))
