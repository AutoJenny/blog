"""
Publishing validators for Clan publish flow.
W2-FIX-2: validate_post_for_clan_publish(post_id) returns { ok, errors, warnings, required_fields_snapshot }.
Requirements (W2-FIX-3): title, subtitle, header image; status in {in_process, published}.
"""

import logging
from config.database import db_manager

logger = logging.getLogger(__name__)

# Statuses that allow publishing (Mark Ready sets in_process)
PUBLISHABLE_POST_STATUSES = ('in_process', 'published')


def validate_post_for_clan_publish(post_id: int) -> dict:
    """
    Validate post is ready for Clan publish.
    Returns: { ok, errors, warnings, required_fields_snapshot }
    """
    errors = []
    warnings = []
    snapshot = {}

    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, title, subtitle, summary, status FROM post WHERE id = %s",
                (post_id,),
            )
            row = cursor.fetchone()
        if not row:
            return {
                "ok": False,
                "errors": ["Post not found"],
                "warnings": [],
                "required_fields_snapshot": {},
            }

        post = dict(row)
        snapshot["title"] = bool(post.get("title") and str(post.get("title", "")).strip())
        snapshot["subtitle"] = bool(post.get("subtitle") or post.get("summary"))
        status = (post.get("status") or "").strip().lower()
        snapshot["status"] = status
        snapshot["status_ok"] = status in PUBLISHABLE_POST_STATUSES

        # Header image - use same finder as publishing
        from blueprints.launchpad.publishing_helpers import find_header_image

        header_path = find_header_image(post_id)
        snapshot["header_image"] = bool(header_path)

        if not snapshot["title"]:
            errors.append("Title is required")
        if not snapshot["subtitle"]:
            errors.append("Subtitle or summary is required")
        if not snapshot["header_image"]:
            errors.append("Header image is required")
        if not snapshot["status_ok"]:
            errors.append(
                f"Status must be one of: {', '.join(PUBLISHABLE_POST_STATUSES)}. Current: {status}"
            )

        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "required_fields_snapshot": snapshot,
        }
    except Exception as e:
        logger.error(f"validate_post_for_clan_publish({post_id}): {e}")
        return {
            "ok": False,
            "errors": [str(e)],
            "warnings": [],
            "required_fields_snapshot": {},
        }
