#!/usr/bin/env python3
"""
Automated Blog Post Creator (Domain 4 "Factory Boss" shell)

This is the governed entrypoint for future post-generation automation.
For now it enforces Framework Rule IV.1 (Pre-Flight Dependency):
no generation proceeds unless Research is ready.
"""

from __future__ import annotations

import argparse
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from modules.research_orchestrator import ResearchOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _extract_surname_candidate(post_title: str) -> str:
    """
    Best-effort surname extraction from a post title.

    We intentionally keep this conservative: use the first token only.
    """
    if not post_title:
        return ""
    title = post_title.strip()
    if not title:
        return ""
    return title.split()[0].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed blog post creator (shell).")
    parser.add_argument("--post-id", type=int, required=True, help="Target post ID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No-op execution (still enforces research gate).",
    )
    args = parser.parse_args()

    orchestrator = ResearchOrchestrator()
    if not orchestrator.is_research_ready(args.post_id):
        logger.error("Research gate failed: post_id=%s is not research-ready.", args.post_id)
        return 2

    logger.info("Research gate passed: post_id=%s", args.post_id)

    # Domain 4 pre-flight: internal intelligence (Domain 2) before any generation steps.
    post_title = ""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT title FROM post WHERE id = %s", (args.post_id,))
            row = cursor.fetchone() or {}
            post_title = (row.get("title") or "").strip()
    except Exception as e:
        logger.warning("Could not load post title for post_id=%s: %s", args.post_id, e)

    surname_candidate = _extract_surname_candidate(post_title)
    internal_intelligence = None
    primary_truth_text = ""
    if surname_candidate:
        logger.info("Fetching internal intelligence for surname token=%s", surname_candidate)
        internal_intelligence = orchestrator.fetch_internal_intelligence(surname_candidate)
        primary_truth_text = internal_intelligence.get("primary_truth_text") or ""
        if internal_intelligence.get("found_internal_data"):
            logger.info(
                "Internal intelligence found (kb_hits=%d, semantic_chunks=%d, links=%d).",
                len(internal_intelligence.get("kb_hits") or []),
                len(internal_intelligence.get("semantic_chunks") or []),
                len(internal_intelligence.get("privileged_links") or []),
            )
        else:
            logger.info("No internal intelligence found for surname=%s (proceeding without Primary Truth).", surname_candidate)

    # This shell currently does not perform LLM generation yet; however, we now
    # enforce the 'Primary Truth' retrieval contract ahead of future generation logic.
    if args.dry_run:
        logger.info("[DRY-RUN] No generation performed.")
        if primary_truth_text:
            logger.info("Primary Truth preview (first 600 chars):\n%s", primary_truth_text[:600])
        return 0

    # Future: orchestrate Domain 4 writing steps here, respecting workflow state engine.
    logger.info("Creator shell ready. No generation steps implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

