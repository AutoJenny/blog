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

from modules.research_orchestrator import ResearchOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
    if args.dry_run:
        logger.info("[DRY-RUN] No generation performed.")
        return 0

    # Future: orchestrate Domain 4 writing steps here, respecting workflow state engine.
    logger.info("Creator shell ready. No generation steps implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

