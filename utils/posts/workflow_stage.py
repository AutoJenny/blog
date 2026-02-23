"""
Persisted workflow stage model for posts.
W2-FIX-5: Strict internal progression inside status=draft.

Stages: idea → structured → drafted → imaged → essentials_complete → ready → published
Stored in post.extra_settings.workflow_stage.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any

from config.database import db_manager

logger = logging.getLogger(__name__)

STAGES: List[str] = [
    "idea",
    "structured",
    "drafted",
    "imaged",
    "essentials_complete",
    "ready",
    "published",
]

# Route groups and their allowed stages (from W2-DESIGN-2)
ROUTE_GATES = {
    "planning": {"idea", "structured"},
    "authoring": {"structured", "drafted"},
    "imaging": {"drafted", "imaged"},
    "launchpad_essentials": {"imaged", "essentials_complete"},
    "publish": {"essentials_complete", "ready", "published"},
}


def _get_header_image(post_id: int) -> Optional[Dict[str, Any]]:
    """Use same logic as preflight (post_images via blog-launchpad)."""
    try:
        blog_launchpad_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "blog-launchpad",
        )
        if blog_launchpad_path not in sys.path:
            sys.path.insert(0, blog_launchpad_path)
        from publish.header_image_finder import get_header_image
        return get_header_image(post_id)
    except Exception as e:
        logger.warning(f"Could not load header image for post {post_id}: {e}")
        return None


def _stage_index(stage: str) -> int:
    """Return 0-based index of stage in STAGES; -1 if unknown."""
    try:
        return STAGES.index(stage)
    except ValueError:
        return -1


def _meets_structured(post_id: int, cursor) -> bool:
    """Sections exist: section_structure AND topic_allocation AND (sections or post_section rows)."""
    cursor.execute("""
        SELECT pd.section_structure, pd.topic_allocation, pd.sections,
               (SELECT COUNT(*) FROM post_section ps WHERE ps.post_id = p.id AND ps.section_order <= 7) as section_count
        FROM post p
        LEFT JOIN post_development pd ON pd.post_id = p.id
        WHERE p.id = %s
    """, (post_id,))
    row = cursor.fetchone()
    if not row:
        return False
    has_structure = bool(row.get("section_structure"))
    has_allocation = bool(row.get("topic_allocation"))
    has_sections = bool(row.get("sections")) or (row.get("section_count") or 0) > 0
    return has_structure and has_allocation and has_sections


def _meets_drafted(post_id: int, cursor) -> bool:
    """All sections (order <= 7) have non-empty draft."""
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN draft IS NOT NULL AND TRIM(draft) != '' THEN 1 ELSE 0 END) as drafted
        FROM post_section
        WHERE post_id = %s AND section_order <= 7
    """, (post_id,))
    row = cursor.fetchone()
    if not row or (row.get("total") or 0) == 0:
        return False
    return (row.get("drafted") or 0) == (row.get("total") or 0)


def _meets_imaged(post_id: int, cursor) -> bool:
    """All sections have image (image_filename on post_section, or post_images section_optimized)."""
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN ps.image_filename IS NOT NULL AND ps.image_filename != ''
                        OR EXISTS (SELECT 1 FROM post_images pi WHERE pi.section_id = ps.id AND pi.image_type = 'section_optimized')
                   THEN 1 ELSE 0 END) as imaged
        FROM post_section ps
        WHERE ps.post_id = %s AND ps.section_order <= 7
    """, (post_id,))
    row = cursor.fetchone()
    if not row or (row.get("total") or 0) == 0:
        return False
    return (row.get("imaged") or 0) == (row.get("total") or 0)


def _meets_essentials(post_id: int) -> bool:
    """title/idea_seed, subtitle, header image."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.title, p.subtitle, pd.idea_seed
            FROM post p
            LEFT JOIN post_development pd ON pd.post_id = p.id
            WHERE p.id = %s
        """, (post_id,))
        row = cursor.fetchone()
    if not row:
        return False
    title = (row.get("title") or "").strip()
    idea_seed = (row.get("idea_seed") or "").strip()
    subtitle = (row.get("subtitle") or "").strip()
    has_title = bool(title or idea_seed)
    has_subtitle = bool(subtitle)
    header = _get_header_image(post_id)
    has_header = bool(header and header.get("path"))
    return has_title and has_subtitle and has_header


def _preflight_ok(post_id: int) -> bool:
    """Run preflight validator; return True if ok."""
    from utils.publishing.validators import validate_post_for_clan_publish
    result = validate_post_for_clan_publish(post_id)
    return bool(result.get("ok"))


def _compute_highest_valid_stage(post_id: int) -> str:
    """
    Compute the highest stage whose criteria are met (no DB write).
    Walks from published down to idea. W2-FIX-6: Used for integrity validation.
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "SELECT p.id, p.status FROM post p WHERE p.id = %s",
            (post_id,),
        )
        row = cursor.fetchone()
    if not row:
        return "idea"

    status = (row.get("status") or "").strip().lower()

    if status == "published":
        return "published"

    if status == "in_process":
        if _preflight_ok(post_id):
            return "ready"
        if _meets_essentials(post_id):
            return "essentials_complete"
        with db_manager.get_cursor() as cursor:
            if _meets_imaged(post_id, cursor):
                return "imaged"
            if _meets_drafted(post_id, cursor):
                return "drafted"
            if _meets_structured(post_id, cursor):
                return "structured"
        return "idea"

    # status draft
    if _meets_essentials(post_id):
        return "essentials_complete"
    with db_manager.get_cursor() as cursor:
        if _meets_imaged(post_id, cursor):
            return "imaged"
        if _meets_drafted(post_id, cursor):
            return "drafted"
        if _meets_structured(post_id, cursor):
            return "structured"
    return "idea"


def validate_workflow_stage(post_id: int) -> Tuple[str, bool]:
    """
    W2-FIX-6: Re-evaluate criteria for current stage. If criteria no longer met,
    downgrade to highest valid stage and persist. Returns (stage, was_downgraded).
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "SELECT extra_settings FROM post WHERE id = %s",
            (post_id,),
        )
        row = cursor.fetchone()
    if not row:
        return "idea", False

    extra = row.get("extra_settings") or {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            extra = {}
    current = extra.get("workflow_stage") or "idea"
    if current not in STAGES:
        current = "idea"

    highest_valid = _compute_highest_valid_stage(post_id)
    curr_idx = _stage_index(current)
    valid_idx = _stage_index(highest_valid)

    if curr_idx <= valid_idx:
        return current, False

    reason = f"criteria for '{current}' no longer met; highest valid: {highest_valid}"
    logger.warning(
        "Workflow stage downgrade: post_id=%s old_stage=%s new_stage=%s reason=%s",
        post_id, current, highest_valid, reason,
    )
    set_workflow_stage(post_id, highest_valid, actor="validate_integrity")
    return highest_valid, True


def infer_workflow_stage(post_id: int) -> str:
    """
    Infer workflow stage from post data (no DB write).
    Uses design doc migration logic.
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.status, p.title, pd.idea_seed, pd.expanded_idea,
                   p.theme_id, p.content_type_id, p.format_id
            FROM post p
            LEFT JOIN post_development pd ON pd.post_id = p.id
            WHERE p.id = %s
        """, (post_id,))
        row = cursor.fetchone()
    if not row:
        return "idea"

    status = (row.get("status") or "").strip().lower()

    if status == "published":
        return "published"

    if status == "in_process":
        if _preflight_ok(post_id):
            return "ready"
        return "essentials_complete"

    # status draft
    has_title = bool((row.get("title") or "").strip() or (row.get("idea_seed") or "").strip())
    has_header = bool(_get_header_image(post_id) and _get_header_image(post_id).get("path"))
    has_subtitle = bool((row.get("subtitle") or "").strip())

    if has_title and has_subtitle and has_header:
        if _preflight_ok(post_id):
            return "ready"
        return "essentials_complete"

    with db_manager.get_cursor() as cursor:
        if _meets_imaged(post_id, cursor):
            return "imaged"
        if _meets_drafted(post_id, cursor):
            return "drafted"
        if _meets_structured(post_id, cursor):
            return "structured"

    expanded = (row.get("expanded_idea") or "").strip()
    idea_seed = (row.get("idea_seed") or "").strip()
    theme = row.get("theme_id")
    content = row.get("content_type_id")
    fmt = row.get("format_id")
    has_taxonomy = theme is not None and content is not None and fmt is not None
    has_idea = bool(expanded or idea_seed)

    if has_idea and has_taxonomy:
        return "idea"

    return "idea"


def get_workflow_stage(post_id: int, persist_if_missing: bool = True, validate: bool = True) -> str:
    """
    Get current workflow stage. If missing from extra_settings, infer and optionally persist.
    W2-FIX-6: When validate=True, runs validate_workflow_stage to correct drift.
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "SELECT extra_settings FROM post WHERE id = %s",
            (post_id,),
        )
        row = cursor.fetchone()
    if not row:
        return "idea"

    extra = row.get("extra_settings") or {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            extra = {}

    stage = extra.get("workflow_stage")
    if stage and stage in STAGES:
        if validate:
            stage, _ = validate_workflow_stage(post_id)
        return stage

    inferred = infer_workflow_stage(post_id)
    if persist_if_missing:
        set_workflow_stage(post_id, inferred, actor="system")
    return inferred


def set_workflow_stage(
    post_id: int,
    stage: str,
    actor: str = "system",
    merge_extra: Optional[dict] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Persist workflow_stage in extra_settings. Merge with existing keys.
    Returns (success, error_message).
    """
    if stage not in STAGES:
        return False, f"Invalid stage: {stage}"

    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "SELECT extra_settings FROM post WHERE id = %s",
            (post_id,),
        )
        row = cursor.fetchone()
    if not row:
        return False, "Post not found"

    extra = row.get("extra_settings") or {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            extra = {}

    if not isinstance(extra, dict):
        extra = {}

    extra["workflow_stage"] = stage
    extra["workflow_stage_updated_at"] = datetime.now(timezone.utc).isoformat()
    if merge_extra:
        extra.update(merge_extra)

    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "UPDATE post SET extra_settings = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (json.dumps(extra), post_id),
        )
        if cursor.rowcount == 0:
            return False, "Post not found"
        cursor.connection.commit()

    logger.info(f"Post {post_id} workflow_stage set to {stage} (actor={actor})")
    return True, None


def ensure_workflow_stage_idea(post_id: int) -> None:
    """
    Set workflow_stage=idea for newly created posts. Call from post creation paths.
    """
    set_workflow_stage(post_id, "idea", actor="post_creation")


def can_transition(
    post_id: int,
    target_stage: str,
    override: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Check if transition to target_stage is allowed.
    Returns (allowed, error_message). Allowed = True means no error.
    """
    if override:
        return True, None

    if target_stage not in STAGES:
        return False, f"Invalid target stage: {target_stage}"

    current = get_workflow_stage(post_id, persist_if_missing=True)
    curr_idx = _stage_index(current)
    tgt_idx = _stage_index(target_stage)

    if curr_idx < 0 or tgt_idx < 0:
        return False, "Unknown stage"

    # Allow forward transitions
    if tgt_idx > curr_idx:
        return True, None

    # Same stage: allow (idempotent)
    if tgt_idx == curr_idx:
        return True, None

    # Backward: not allowed (unless admin override)
    return False, f"Cannot go backward: {current} → {target_stage}"


def criteria_met_for_stage(post_id: int, target_stage: str) -> bool:
    """
    Check if entry criteria for target_stage are met (data-wise).
    Used by UI to show "Advance to X" button.
    """
    with db_manager.get_cursor() as cursor:
        if target_stage == "structured":
            return _meets_structured(post_id, cursor)
        if target_stage == "drafted":
            return _meets_drafted(post_id, cursor)
        if target_stage == "imaged":
            return _meets_imaged(post_id, cursor)
        if target_stage == "essentials_complete":
            return _meets_essentials(post_id)
        if target_stage == "ready":
            return _meets_essentials(post_id) and _preflight_ok(post_id)
    return False


def get_next_advanceable_stage(post_id: int) -> Optional[str]:
    """
    Return the next stage we can advance to (criteria met and transition allowed), or None.
    """
    current = get_workflow_stage(post_id, persist_if_missing=True)
    idx = _stage_index(current)
    if idx < 0 or idx >= len(STAGES) - 1:
        return None
    next_stage = STAGES[idx + 1]
    if next_stage == "published":
        return None  # published is via publish action, not advance
    if criteria_met_for_stage(post_id, next_stage):
        return next_stage
    return None


def advance_stage(
    post_id: int,
    target_stage: str,
    actor: str = "system",
    override: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Transition to target_stage if allowed. Persists on success.
    For non-override: also requires criteria for target_stage to be met.
    When advancing to 'ready', also sets status=in_process (Mark Ready).
    Returns (success, error_message).
    """
    ok, err = can_transition(post_id, target_stage, override=override)
    if not ok:
        return False, err
    if not override and target_stage not in ("ready", "published"):
        if not criteria_met_for_stage(post_id, target_stage):
            return False, f"Criteria for '{target_stage}' not met. Complete required work first."
    if target_stage == "ready":
        from utils.posts.status_transitions import transition_post_status
        ok_status, err_status = transition_post_status(post_id, "in_process", actor=actor, override=override)
        if not ok_status:
            return False, err_status or "Could not set status to in_process"
    return set_workflow_stage(post_id, target_stage, actor=actor)


def require_workflow_stage(
    post_id: int,
    route_group: str,
    request=None,
    override_param: str = "override",
) -> Tuple[Optional[Dict], Optional[int]]:
    """
    Gate: require post to be in an allowed stage for the route group.
    Returns (error_dict, status_code) if blocked, else (None, None).
    error_dict includes: stage_blocked, current_stage, required_stage, message.
    """
    if route_group not in ROUTE_GATES:
        return None, None

    override = False
    if request:
        override = (
            request.args.get(override_param) == "1"
            or (request.json and request.json.get(override_param))
        )

    if override:
        return None, None

    current = get_workflow_stage(post_id, persist_if_missing=True)
    allowed = ROUTE_GATES[route_group]

    if current in allowed:
        return None, None

    required = ", ".join(sorted(allowed))
    return (
        {
            "stage_blocked": True,
            "current_stage": current,
            "required_stage": required,
            "message": f"Post is at stage '{current}'. This action requires stage: {required}. Use ?override=1 for admin.",
        },
        403,
    )
