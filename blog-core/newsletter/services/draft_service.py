"""Draft builder service.

Composes the weekly issue by invoking selectors and assembling blocks.
"""

from __future__ import annotations

from typing import Dict, List
from datetime import date
from newsletter.db.queries_issue import create_issue, upsert_block
from newsletter.selectors.blog_feature import select_feature_article
from newsletter.selectors.snapshot import select_snapshot, fallback_snapshot
from newsletter.selectors.intro import select_intro_content
from newsletter.selectors.products import select_new_products, select_spotlight_product, group_variants
from newsletter.selectors.category import select_category_feature
from newsletter.selectors.evergreen import select_evergreen
from newsletter.selectors.theme import select_default_theme
from newsletter.services.block_suggestion_service import auto_select_for_block


def build_weekly_issue(*, target_week: str | None = None) -> Dict:
    """Create an issue and populate initial blocks (placeholders allowed)."""
    if not target_week:
        iso_year, iso_week, _ = date.today().isocalendar()
        target_week = f"{iso_year}W{iso_week:02d}"

    # Select theme based on week
    theme = select_default_theme(target_week=target_week)
    theme_id = theme.get('id') if theme else None
    
    # Generate subject and preheader from theme
    if theme:
        subject = f"{theme.get('idea_title', 'This week in Scotland')} — {target_week}"
        preheader = theme.get('seasonal_context') or theme.get('idea_description') or "A quick wander through culture & craft."
    else:
        subject = f"This week in Scotland — {target_week}"
        preheader = "A quick wander through culture & craft."
    
    issue_id = create_issue(target_week=target_week, subject=subject, preheader=preheader, theme_id=theme_id)

    # Automatically select weekly highlights for Round Scotland component
    try:
        from newsletter.services.weekly_highlights_selection import select_weekly_highlights
        from newsletter.config.quirky_news_config import (
            LLM_QUIRKY_SCORE_THRESHOLD,
            MAX_ITEMS_PER_REGION,
            MAX_ITEMS_PER_WEEK
        )
        highlights_result = select_weekly_highlights(
            issue_id=issue_id,
            target_week=target_week,
            quirky_score_threshold=LLM_QUIRKY_SCORE_THRESHOLD,
            max_per_region=MAX_ITEMS_PER_REGION,
            max_total=MAX_ITEMS_PER_WEEK
        )
        if highlights_result.get('success'):
            import logging
            logging.getLogger(__name__).info(
                f"Selected {highlights_result.get('selected_count', 0)} weekly highlights for issue {issue_id}"
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to select weekly highlights: {e}", exc_info=True)
        # Don't fail issue creation if highlights selection fails

    position = 0

    # Build all blocks using unified suggestion service
    block_types = [
        "intro",
        "feature",
        "snapshot",
        "new_products",
        "spotlight",
        "category",
        "evergreen",
        "closing",
    ]

    for block_type in block_types:
        if block_type == "closing":
            # Closing is simple, no suggestions
            payload = {"text": "Warmly, from Scotland"}
        else:
            # Use unified auto-select service
            payload = auto_select_for_block(block_type=block_type, issue_id=issue_id, target_week=target_week)
            # Ensure suggestions are stored in payload for all blocks that use them
            if block_type in ("intro", "snapshot"):
                # These already have suggestions from select_intro_content/select_snapshot
                pass
            else:
                # For other blocks, get suggestions and store them
                from newsletter.services.block_suggestion_service import get_suggestions_for_block
                suggestions_result = get_suggestions_for_block(block_type=block_type, issue_id=issue_id, target_week=target_week)
                if suggestions_result.get('suggestions'):
                    payload['suggestions'] = suggestions_result['suggestions']
                if suggestions_result.get('current'):
                    payload['selected'] = suggestions_result['current']
        
        upsert_block(issue_id=issue_id, block_type=block_type, position=position, enabled=True, payload=payload)
        position += 1

    return {"issue_id": issue_id, "target_week": target_week}


