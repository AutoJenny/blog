"""
Early development round stage model (Instruction Set 8).
Explicit workflow_stage column on post. No silent auto-advance.
Stage only advances when user explicitly calls advance_post_stage (e.g. "Advance Stage" button).
W2 Phase 2: Stage ordering from utils.posts.stage_order only.
"""

import logging
from typing import Tuple, Optional

from config.database import db_manager
from utils.posts.stage_order import STAGE_ORDER, stage_index

logger = logging.getLogger(__name__)


def get_canonical_stage(post_id: int) -> str:
    """
    Read authoring stage from post.workflow_stage ONLY.
    No fallback. No inference. Single source of truth (W2 Phase 1).
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT workflow_stage FROM post WHERE id = %s",
                (post_id,),
            )
            row = cursor.fetchone()
    except Exception:
        return "metadata"
    if not row:
        return "metadata"
    col = getattr(row, "workflow_stage", None) or (row.get("workflow_stage") if isinstance(row, dict) else None)
    if col and str(col).strip() in STAGE_ORDER:
        return str(col).strip()
    return "metadata"


def get_early_stage(post_id: int) -> str:
    """Alias for get_canonical_stage. Reads post.workflow_stage only (no fallback)."""
    return get_canonical_stage(post_id)


def _meets_metadata_to_ideas(post_id: int, cursor) -> bool:
    cursor.execute(
        "SELECT title, subtitle FROM post WHERE id = %s",
        (post_id,),
    )
    row = cursor.fetchone()
    if not row:
        return False
    title = (row.get("title") or "").strip() if isinstance(row, dict) else (getattr(row, "title", None) or "").strip()
    subtitle = (row.get("subtitle") or "").strip() if isinstance(row, dict) else (getattr(row, "subtitle", None) or "").strip()
    return bool(title and subtitle)


def _count_required_ideas(post_id: int, cursor) -> int:
    try:
        cursor.execute(
            "SELECT COUNT(*) AS c FROM post_required_idea WHERE post_id = %s",
            (post_id,),
        )
        row = cursor.fetchone()
        if not row:
            return 0
        return int(row.get("c", 0) if isinstance(row, dict) else (row[0] if row else 0))
    except Exception:
        return 0


def _count_sections(post_id: int, cursor) -> int:
    cursor.execute(
        "SELECT COUNT(*) AS c FROM post_section WHERE post_id = %s",
        (post_id,),
    )
    row = cursor.fetchone()
    if not row:
        return 0
    return int(row.get("c", 0) if isinstance(row, dict) else (row[0] if row else 0))


def _all_sections_have_titles(post_id: int, cursor) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN section_heading IS NOT NULL AND TRIM(section_heading) <> '' THEN 1 ELSE 0 END) AS with_title
        FROM post_section WHERE post_id = %s
        """,
        (post_id,),
    )
    row = cursor.fetchone()
    if not row:
        return True
    total = int(row.get("total", 0) if isinstance(row, dict) else (row[0] if row else 0))
    with_title = int(row.get("with_title", 0) if isinstance(row, dict) else (row[1] if row else 0))
    return total == 0 or total == with_title


def _at_least_one_section_has_body(post_id: int, cursor) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM post_section
        WHERE post_id = %s AND draft IS NOT NULL AND TRIM(draft) <> ''
        LIMIT 1
        """,
        (post_id,),
    )
    return cursor.fetchone() is not None


def _condition_met(post_id: int, from_stage: str, cursor) -> Tuple[bool, Optional[str]]:
    """Return (met, error_message)."""
    if from_stage == "metadata":
        ok = _meets_metadata_to_ideas(post_id, cursor)
        return (ok, None if ok else "Title and subtitle are required before advancing to Ideas.")
    if from_stage == "ideas":
        # N4: Gated by get_stage_advancement_requirements (10 selected, 3 categories).
        return (True, None)
    if from_stage == "structure":
        # N4: Gated by get_stage_advancement_requirements (6 sections).
        return (True, None)
    if from_stage == "titling":
        ok = _all_sections_have_titles(post_id, cursor)
        return (ok, None if ok else "All sections must have titles before advancing to Authoring.")
    if from_stage == "authoring":
        ok = _at_least_one_section_has_body(post_id, cursor)
        return (ok, None if ok else "At least one section must have body text before advancing to Imaging.")
    if from_stage == "imaging":
        return (True, None)  # Relaxed: can advance to review without images
    if from_stage == "review":
        return (False, "Already at final stage")
    return (False, "Unknown stage")


def advance_post_stage(post_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Advance post to the next stage if condition is met. No skipping.
    Returns (success, error_message, new_stage).
    Does NOT auto-advance; call only from explicit user action (e.g. Advance Stage button).
    N4: Artefact gates (ideas/structure) enforced via get_stage_advancement_requirements.
    """
    current = get_early_stage(post_id)
    idx = stage_index(current)
    if idx >= len(STAGE_ORDER) - 1:
        return (False, "Already at final stage", current)

    # N4: Single source of truth for artefact gates (same as pipeline-state).
    from utils.posts.pipeline_gates import get_stage_advancement_requirements
    requirements = get_stage_advancement_requirements(post_id)
    if not requirements.get("can_advance", True):
        return (False, requirements.get("reason") or "Artefact requirements not met", None)

    next_stage = STAGE_ORDER[idx + 1]
    with db_manager.get_cursor() as cursor:
        met, err = _condition_met(post_id, current, cursor)
        if not met:
            return (False, err or "Condition not met", None)

        cursor.execute(
            "UPDATE post SET workflow_stage = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (next_stage, post_id),
        )
        if cursor.rowcount == 0:
            return (False, "Post not found", None)
        cursor.connection.commit()

    logger.info("Early stage advanced: post_id=%s %s -> %s", post_id, current, next_stage)
    return (True, None, next_stage)
