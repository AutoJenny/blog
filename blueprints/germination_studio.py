from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, jsonify, render_template, request

from config.database import db_manager
from utils.germination_engine import (
    build_expansion_prompt,
    get_global_project_mission,
    merge_mission,
)

bp = Blueprint("germination_studio", __name__)
logger = logging.getLogger(__name__)


def _parse_extra_settings(extra_settings: Any) -> Dict[str, Any]:
    if extra_settings is None:
        return {}
    if isinstance(extra_settings, dict):
        return extra_settings
    if isinstance(extra_settings, str):
        try:
            return json.loads(extra_settings) if extra_settings else {}
        except Exception:
            return {}
    return {}


def _get_post_row(post_id: int) -> Optional[Dict[str, Any]]:
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, extra_settings
            FROM post
            WHERE id = %s
            """,
            (post_id,),
        )
        row = cursor.fetchone()
    return row


@bp.route("/create/germination", methods=["GET"])
def create_germination_deck():
    post_id = request.args.get("post_id", type=int)
    if not post_id:
        return jsonify({"success": False, "error": "post_id is required"}), 400

    post = _get_post_row(post_id)
    if not post:
        return jsonify({"success": False, "error": "post not found"}), 404

    extra = _parse_extra_settings(post.get("extra_settings"))
    mission_override = extra.get("mission_override") if isinstance(extra.get("mission_override"), dict) else {}
    seed_metadata = extra.get("seed_metadata") if isinstance(extra.get("seed_metadata"), dict) else {}

    seed_text = str(post.get("title") or "").strip()

    global_mission = get_global_project_mission(project_id="blog")
    merged_mission = merge_mission(global_mission=global_mission, local_override=mission_override)
    expansion_prompt = build_expansion_prompt(
        seed_text=seed_text,
        seed_metadata=seed_metadata,
        merged_mission=merged_mission,
    )

    return render_template(
        "germination/germination.html",
        blueprint_name="germination",
        post_id=post_id,
        project_id="blog",
        project_mission=global_mission,
        mission_override=mission_override,
        seed_metadata=seed_metadata,
        seed_text=seed_text,
        expansion_prompt=expansion_prompt,
    )


@bp.route("/api/create/germination/build", methods=["POST"])
def api_create_germination_build():
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    try:
        post_id = int(post_id)
    except Exception:
        return jsonify({"success": False, "error": "post_id must be an integer"}), 400

    post = _get_post_row(post_id)
    if not post:
        return jsonify({"success": False, "error": "post not found"}), 404

    extra = _parse_extra_settings(post.get("extra_settings"))

    seed_text = str(data.get("seed_text") or "").strip()
    if not seed_text:
        seed_text = str(post.get("title") or "").strip()

    mission_override = data.get("mission_override")
    if not isinstance(mission_override, dict):
        mission_override = {}

    seed_metadata = data.get("seed_metadata")
    if not isinstance(seed_metadata, dict):
        seed_metadata = {}

    # Persist only the requested local override keys to post.extra_settings.
    extra = dict(extra)
    extra["mission_override"] = mission_override
    extra["seed_metadata"] = seed_metadata

    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            UPDATE post
            SET extra_settings = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (json.dumps(extra), post_id),
        )
        cursor.connection.commit()

    global_mission = get_global_project_mission(project_id="blog")
    merged_mission = merge_mission(global_mission=global_mission, local_override=mission_override)
    expansion_prompt = build_expansion_prompt(
        seed_text=seed_text,
        seed_metadata=seed_metadata,
        merged_mission=merged_mission,
    )

    return jsonify(
        {
            "success": True,
            "post_id": post_id,
            "expansion_prompt": expansion_prompt,
            "mission_override": mission_override,
            "seed_metadata": seed_metadata,
        }
    )

