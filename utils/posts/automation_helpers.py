"""
Automation helpers for workflow_stage convergence (W2-FIX-7).
Per-stage toggles, automation.enabled, reconcile after execute.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any

from config.database import db_manager

logger = logging.getLogger(__name__)

# Stage keys for automation.stage_enabled (maps to workflow stages produced by automation)
AUTOMATION_STAGE_KEYS = frozenset({"drafted", "imaged", "essentials_complete"})


def _get_automation_config(post_id: int) -> Dict[str, Any]:
    """Load post.extra_settings.automation. Returns {} if missing."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
        row = cursor.fetchone()
    if not row:
        return {}
    extra = row.get("extra_settings") or {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            extra = {}
    if not isinstance(extra, dict):
        return {}
    return extra.get("automation") or {}


def is_automation_enabled(post_id: int) -> bool:
    """
    Check if automation is globally enabled for this post.
    Defaults to True if not set.
    """
    cfg = _get_automation_config(post_id)
    if "enabled" not in cfg:
        return True
    return bool(cfg.get("enabled"))


def is_automation_stage_enabled(post_id: int, stage_key: str) -> bool:
    """
    Check if automation is enabled for the given stage.
    stage_key: 'drafted' | 'imaged' | 'essentials_complete' | etc.
    Defaults to True if not set.
    """
    cfg = _get_automation_config(post_id)
    stage_enabled = cfg.get("stage_enabled") or {}
    if not isinstance(stage_enabled, dict):
        return True
    if stage_key not in stage_enabled:
        return True
    return bool(stage_enabled.get(stage_key))


def check_automation_blocked(post_id: int, stage_key: str) -> Tuple[bool, Optional[Dict], int]:
    """
    Check if automation is blocked for this stage.
    Returns (blocked, response_dict, status_code).
    If blocked, (True, {...}, 403). If allowed, (False, None, 0).
    """
    if not is_automation_enabled(post_id):
        return True, {
            "automation_blocked": True,
            "stage": stage_key,
            "message": "Automation is disabled for this post.",
        }, 403
    if not is_automation_stage_enabled(post_id, stage_key):
        return True, {
            "automation_blocked": True,
            "stage": stage_key,
            "message": f"Automation for stage '{stage_key}' is disabled. Enable in post extra_settings.automation.stage_enabled.",
        }, 403
    return False, None, 0


def reconcile_after_execute(post_id: int, substage: str, actor: str = "automation") -> None:
    """
    After successful execute, validate stage and advance if criteria met and stage enabled.
    W2-FIX-7 Part D.
    """
    from utils.posts.workflow_stage import (
        validate_workflow_stage,
        get_next_advanceable_stage,
        advance_stage,
    )
    validate_workflow_stage(post_id)
    next_stage = get_next_advanceable_stage(post_id)
    if not next_stage:
        return
    if not is_automation_stage_enabled(post_id, next_stage):
        logger.info("Automation reconcile: next stage %s disabled for post %s, not advancing", next_stage, post_id)
        return
    ok, err = advance_stage(post_id, next_stage, actor=actor)
    if ok:
        logger.info("Automation reconcile: advanced post %s to %s (actor=%s)", post_id, next_stage, actor)
    else:
        logger.debug("Automation reconcile: could not advance post %s to %s: %s", post_id, next_stage, err)


def _merge_automation_extra(post_id: int, updates: Dict[str, Any]) -> None:
    """Merge updates into post.extra_settings.automation."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
        row = cursor.fetchone()
    if not row:
        return
    extra = row.get("extra_settings") or {}
    if isinstance(extra, str):
        try:
            extra = json.loads(extra) if extra else {}
        except json.JSONDecodeError:
            extra = {}
    if not isinstance(extra, dict):
        extra = {}
    automation = extra.get("automation") or {}
    if not isinstance(automation, dict):
        automation = {}
    automation.update(updates)
    extra["automation"] = automation
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            "UPDATE post SET extra_settings = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (json.dumps(extra), post_id),
        )
        cursor.connection.commit()


def set_automation_last_run(post_id: int, stage: str) -> None:
    """Record last successful automation run."""
    _merge_automation_extra(post_id, {"last_run": datetime.now(timezone.utc).isoformat(), "last_run_stage": stage})


def set_automation_last_blocked(post_id: int, stage: str, message: str = "") -> None:
    """Record last blocked automation attempt."""
    _merge_automation_extra(
        post_id,
        {"last_blocked_stage": stage, "last_error": message or f"Blocked at {stage}"},
    )
