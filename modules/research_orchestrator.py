from __future__ import annotations

import logging
from dataclasses import dataclass

from config.database import db_manager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResearchOrchestrator:
    """
    Domain 2 (Library): Minimal research readiness gate.

    Contract:
    - If the post has no research substage rows, treat research as not required (ready=True).
    - If research substage rows exist, require a "complete" status.
    """

    complete_statuses: tuple[str, ...] = (
        "research_complete",
        "complete",
        "completed",
        "done",
        "ready",
    )

    def is_research_ready(self, post_id: int) -> bool:
        if not isinstance(post_id, int) or post_id <= 0:
            return False

        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pws.status, wsse.name AS substage_name
                    FROM post_workflow_sub_stage pws
                    JOIN workflow_sub_stage_entity wsse ON wsse.id = pws.sub_stage_id
                    WHERE pws.post_id = %s
                      AND wsse.name ILIKE '%%research%%'
                    """,
                    (post_id,),
                )
                rows = cursor.fetchall() or []
        except Exception as e:
            logger.warning("Research readiness check failed for post_id=%s: %s", post_id, e)
            return False

        # No research substages attached => no requirement.
        if not rows:
            return True

        for r in rows:
            status = (r.get("status") if isinstance(r, dict) else None) or ""
            if status.strip().lower() in self.complete_statuses:
                return True

        return False

