"""
Legacy workflow stage module. W2 Phase 1: Canonical authoring stage is post.workflow_stage only.
This module provides require_workflow_stage (gates) and backward-compat get_workflow_stage.
Stage mutation is ONLY via POST /api/posts/<id>/advance-stage (early_stage.advance_post_stage).
Legacy stages (idea, structured, ...) and extra_settings.workflow_stage are deprecated; not read for logic, not written.
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

# Route groups and allowed canonical stages (post.workflow_stage). W2 Phase 1.
CANONICAL_ROUTE_GATES = {
    "planning": {"ideas", "structure"},
    "authoring": {"titling", "authoring"},
    "imaging": {"imaging"},
    "launchpad_essentials": {"imaging", "review"},
    "publish": {"review"},
}
# Legacy (deprecated); kept for reference only.
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
    W2 Phase 1: No persistence. Returns current canonical stage and was_downgraded=False.
    Stage must not be mutated outside advance-stage endpoint.
    """
    from utils.posts.early_stage import get_canonical_stage
    current = get_canonical_stage(post_id)
    return current, False


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
    W2 Phase 1: Return canonical authoring stage (post.workflow_stage only).
    persist_if_missing and validate are ignored; no inference, no write.
    """
    from utils.posts.early_stage import get_canonical_stage
    return get_canonical_stage(post_id)


def set_workflow_stage(
    post_id: int,
    stage: str,
    actor: str = "system",
    merge_extra: Optional[dict] = None,
) -> Tuple[bool, Optional[str]]:
    """
    W2 Phase 1: No-op. Authoring stage may only be set via POST /api/posts/<id>/advance-stage.
    extra_settings.workflow_stage is never written again.
    """
    logger.debug("W2: set_workflow_stage is deprecated (no-op); post_id=%s stage=%s actor=%s", post_id, stage, actor)
    return True, None


def ensure_workflow_stage_idea(post_id: int) -> None:
    """
    W2 Phase 1: No-op. New posts get workflow_stage=metadata from DB default.
    """
    pass


def can_transition(
    post_id: int,
    target_stage: str,
    override: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Check if transition to target_stage is allowed (legacy stages; for backward compat only).
    W2 Phase 1: Stage advances only via advance_post_stage; this is advisory.
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
    Return the next canonical stage we can advance to, or None.
    W2 Phase 2: Uses utils.posts.stage_order only.
    """
    from utils.posts.early_stage import get_canonical_stage
    from utils.posts.stage_order import STAGE_ORDER, stage_index
    current = get_canonical_stage(post_id)
    idx = stage_index(current)
    if idx >= len(STAGE_ORDER) - 1:
        return None
    return STAGE_ORDER[idx + 1]


def advance_stage(
    post_id: int,
    target_stage: str,
    actor: str = "system",
    override: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    W2 Phase 1: No-op for persistence. Stage may only advance via POST /api/posts/<id>/advance-stage.
    Returns (True, None) so callers do not break; no DB write.
    """
    logger.debug("W2: advance_stage is deprecated (no-op); post_id=%s target=%s actor=%s", post_id, target_stage, actor)
    return True, None


def require_workflow_stage(
    post_id: int,
    route_group: str,
    request=None,
    override_param: str = "override",
) -> Tuple[Optional[Dict], Optional[int]]:
    """
    Gate: require post to be in an allowed canonical stage for the route group.
    Reads post.workflow_stage only (W2 Phase 1).
    Returns (error_dict, status_code) if blocked, else (None, None).
    """
    if route_group not in CANONICAL_ROUTE_GATES:
        return None, None

    override = False
    if request:
        override = (
            request.args.get(override_param) == "1"
            or (request.json and request.json.get(override_param))
        )

    if override:
        return None, None

    from utils.posts.early_stage import get_canonical_stage
    current = get_canonical_stage(post_id)
    allowed = CANONICAL_ROUTE_GATES[route_group]

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
