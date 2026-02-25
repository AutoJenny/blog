# PLAYBOOKS DO NOT AFFECT STAGE OR AUTOMATION.
# They are informational checklists only.

"""
Substage playbook definitions and state helpers. W2 Phase 3.
Metadata-only: stored in post.extra_settings.substage_playbook and substage_state.
Does not mutate post.workflow_stage. Does not gate automation. Does not auto-trigger anything.
"""

import json
from typing import Dict, Any, List, Tuple, Optional

from config.database import db_manager

# Allowed task statuses. "fail" is for review stage only.
PLAYBOOK_STATUSES = frozenset({"todo", "done", "skipped"})
PLAYBOOK_STATUSES_WITH_FAIL = frozenset({"todo", "done", "skipped", "fail"})

# Static playbook templates by post type. Keys = canonical stage names (ideas, authoring, review).
DEFAULT_PLAYBOOK_THEMED = {
    "ideas": [
        {"id": "angle_diversity", "label": "Angle diversity check"},
        {"id": "specificity_targets", "label": "Specificity targets"},
    ],
    "authoring": [
        {"id": "example_density", "label": "Examples per section"},
        {"id": "generic_phrase_scan", "label": "Generic phrase scan"},
    ],
    "review": [
        {"id": "claims_sourced", "label": "Claims sourced"},
        {"id": "repetition_check", "label": "Repetition/waffle check"},
    ],
}

DEFAULT_PLAYBOOK_RECIPE = {
    "ideas": [
        {"id": "ingredients_aligned", "label": "Ingredients aligned to theme"},
        {"id": "method_steps_clear", "label": "Method steps clear"},
    ],
    "authoring": [
        {"id": "serving_timing", "label": "Serving and timing noted"},
        {"id": "generic_phrase_scan", "label": "Generic phrase scan"},
    ],
    "review": [
        {"id": "claims_sourced", "label": "Claims sourced"},
        {"id": "repetition_check", "label": "Repetition/waffle check"},
    ],
}

DEFAULT_PLAYBOOK_PROFILE = {
    "ideas": [
        {"id": "feature_coverage", "label": "Feature coverage"},
        {"id": "positioning_angle", "label": "Positioning angle"},
    ],
    "authoring": [
        {"id": "example_density", "label": "Examples per section"},
        {"id": "cta_placement", "label": "CTA placement"},
    ],
    "review": [
        {"id": "claims_sourced", "label": "Claims sourced"},
        {"id": "repetition_check", "label": "Repetition/waffle check"},
    ],
}

DEFAULT_PLAYBOOK_CLAN = {
    "ideas": [
        {"id": "source_coverage", "label": "Source coverage"},
        {"id": "timeline_anchors", "label": "Timeline anchors"},
    ],
    "authoring": [
        {"id": "citation_placeholders", "label": "Citation placeholders"},
        {"id": "myth_vs_fact", "label": "Myth vs fact pass"},
    ],
    "review": [
        {"id": "claims_sourced", "label": "Claims sourced"},
        {"id": "repetition_check", "label": "Repetition/waffle check"},
    ],
}


def get_default_playbook(post_type: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Return static playbook definition for post type.
    Unknown post_type → empty dict.
    """
    if post_type == "themed":
        return dict(DEFAULT_PLAYBOOK_THEMED)
    if post_type == "recipe":
        return dict(DEFAULT_PLAYBOOK_RECIPE)
    if post_type == "profile":
        return dict(DEFAULT_PLAYBOOK_PROFILE)
    if post_type == "clan":
        return dict(DEFAULT_PLAYBOOK_CLAN)
    if post_type == "generated":
        return dict(DEFAULT_PLAYBOOK_THEMED)  # same as themed
    return {}


def _get_extra_settings(post_id: int) -> Tuple[Optional[Dict], bool]:
    """Return (extra_settings dict, post_exists). Caller must not mutate stage."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
        row = cursor.fetchone()
    if not row:
        return None, False
    extra = row.get("extra_settings") if isinstance(row, dict) else getattr(row, "extra_settings", None)
    if extra is None:
        extra = {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            extra = {}
    if not isinstance(extra, dict):
        extra = {}
    return extra, True


def ensure_playbook_initialised(post_id: int, post_type: str) -> Tuple[Dict, Dict]:
    """
    Idempotent: if extra_settings.substage_playbook missing, set from get_default_playbook(post_type)
    and substage_state to {}. Does not overwrite existing. Does not mutate stage.
    Returns (playbook, state).
    """
    extra, exists = _get_extra_settings(post_id)
    if not exists:
        return {}, {}

    playbook = extra.get("substage_playbook")
    state = extra.get("substage_state")
    if playbook is None or not isinstance(playbook, dict):
        playbook = get_default_playbook(post_type)
        state = {}
        extra = dict(extra)
        extra["substage_playbook"] = playbook
        extra["substage_state"] = state
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "UPDATE post SET extra_settings = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (json.dumps(extra), post_id),
            )
            cursor.connection.commit()
    else:
        state = state if isinstance(state, dict) else {}
    return playbook, state


def get_playbook_and_state(post_id: int, post_type: str) -> Tuple[Dict, Dict]:
    """Return (playbook, state) for post. Ensures playbook initialised if missing."""
    return ensure_playbook_initialised(post_id, post_type)


def update_task_state(
    post_id: int,
    stage: str,
    task_id: str,
    status: str,
    note: Optional[str] = None,
) -> Tuple[bool, Optional[str], Dict, Dict]:
    """
    Update substage_state for one task. Validates stage/task_id/status.
    Does not mutate post.workflow_stage. Returns (success, error_message, playbook, state).
    """
    extra, exists = _get_extra_settings(post_id)
    if not exists:
        return False, "Post not found", {}, {}

    playbook = extra.get("substage_playbook")
    state = extra.get("substage_state")
    if not isinstance(playbook, dict):
        playbook = {}
    if not isinstance(state, dict):
        state = {}

    if stage not in playbook or not isinstance(playbook.get(stage), list):
        return False, f"Stage '{stage}' not in playbook", playbook, state
    task_ids = [t.get("id") for t in playbook[stage] if isinstance(t, dict) and t.get("id")]
    if task_id not in task_ids:
        return False, f"Task '{task_id}' not in stage '{stage}'", playbook, state

    allowed = PLAYBOOK_STATUSES_WITH_FAIL if stage == "review" else PLAYBOOK_STATUSES
    if status not in allowed:
        return False, f"Status must be one of {sorted(allowed)}", playbook, state

    extra = dict(extra)
    if "substage_state" not in extra or not isinstance(extra["substage_state"], dict):
        extra["substage_state"] = dict(state)
    state = extra["substage_state"]
    if stage not in state:
        state[stage] = {}
    state[stage] = dict(state[stage])
    state[stage][task_id] = {"status": status}
    if note is not None and note.strip():
        state[stage][task_id]["note"] = note.strip()[:500]
    extra["substage_state"] = state

    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "UPDATE post SET extra_settings = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (json.dumps(extra), post_id),
        )
        cursor.connection.commit()

    playbook = extra.get("substage_playbook", playbook)
    return True, None, playbook, state
