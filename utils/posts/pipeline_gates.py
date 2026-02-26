"""
W2 N4: Single source of truth for stage advancement artefact gates.
Unified with GET /api/posts/<id>/pipeline-state and advance_post_stage().
"""

from typing import Dict, Any

from config.database import db_manager
from utils.posts.early_stage import get_canonical_stage
from utils.taxonomy_helpers import get_post_type


def get_stage_advancement_requirements(post_id: int) -> Dict[str, Any]:
    """
    Returns artefact requirements for advancing from the current workflow stage.
    Used by pipeline-state (reasons_blocked) and advance_post_stage().

    Returns:
        {
            "current_stage": "ideas",
            "can_advance": True | False,
            "deficits": {
                "selected": {"have": X, "need": 10},
                "categories": {"have": Y, "need": 3},
                "sections": {"have": Z, "need": 6}
            },
            "reason": "Need at least 10 selected ideas (have X); ..."  # only parts relevant to current stage
        }
    """
    current_stage = get_canonical_stage(post_id)
    post_type = get_post_type(post_id)

    selected_total = 0
    selected_categories = 0
    required_total = 0
    sections_count = 0

    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS total, "
            "       COUNT(*) FILTER (WHERE is_selected) AS selected, "
            "       COUNT(DISTINCT category) FILTER (WHERE is_selected) AS categories "
            "FROM post_required_idea WHERE post_id = %s",
            (post_id,),
        )
        r = cursor.fetchone()
        if r is not None:
            if isinstance(r, dict):
                required_total = int(r.get("total", 0))
                selected_total = int(r.get("selected", 0))
                selected_categories = int(r.get("categories", 0))
            else:
                required_total = int(r[0]) if len(r) > 0 else 0
                selected_total = int(r[1]) if len(r) > 1 else 0
                selected_categories = int(r[2]) if len(r) > 2 else 0

        cursor.execute(
            "SELECT COUNT(*) AS sections FROM post_section WHERE post_id = %s",
            (post_id,),
        )
        r2 = cursor.fetchone()
        if r2 is not None:
            sections_count = int(r2.get("sections", 0) if isinstance(r2, dict) else r2[0])

    deficits = {
        "total_ideas": {"have": required_total, "need": 30},
        "selected": {"have": selected_total, "need": 10},
        "categories": {"have": selected_categories, "need": 3},
        "sections": {"have": sections_count, "need": 6},
    }

    # Formatted strings for pipeline-state reasons_blocked (built once for all returns).
    ideas_reason = f"Need at least 30 ideas (have {required_total})." if required_total < 30 else ""
    cluster_reason = (
        f"Need at least 10 selected ideas (have {deficits['selected']['have']}); "
        f"at least 3 categories (have {deficits['categories']['have']}); "
        f"and at least 6 sections (have {deficits['sections']['have']})."
    )

    # For non-themed posts, no artefact gates from this helper (other stages may still gate in early_stage).
    if post_type != "themed":
        return {
            "current_stage": current_stage,
            "can_advance": True,
            "deficits": deficits,
            "reason": "",
            "ideas_reason": ideas_reason,
            "cluster_reason": cluster_reason,
        }

    can_advance = True
    parts = []

    if current_stage == "ideas":
        if selected_total < 10:
            can_advance = False
            parts.append(f"Need at least 10 selected ideas (have {selected_total})")
        if selected_categories < 3:
            can_advance = False
            parts.append(f"at least 3 categories (have {selected_categories})")
        if parts:
            reason = "; ".join(parts) + "."
        else:
            reason = ""

    elif current_stage == "structure":
        if sections_count < 6:
            can_advance = False
            reason = f"Need at least 6 sections (have {sections_count})."
        else:
            reason = ""

    else:
        reason = ""

    return {
        "current_stage": current_stage,
        "can_advance": can_advance,
        "deficits": deficits,
        "reason": reason,
        "ideas_reason": ideas_reason,
        "cluster_reason": cluster_reason,
    }
