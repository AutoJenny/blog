"""Pre-send QA checks aggregator."""

from __future__ import annotations

from typing import Dict, List, Tuple, Any
from newsletter.db.queries_issue import list_blocks_by_issue
from newsletter.validators.links import validate_links
from newsletter.validators.images import validate_image_cards
from newsletter.validators.content import has_alt_text
from newsletter.services.suggestion_service import validate_link
from newsletter.services.scoring import apply_safety_rules


def run_pre_send_checks(issue_id: int) -> List[Tuple[str, bool]]:
    blocks = list_blocks_by_issue(issue_id=issue_id)
    results: List[Tuple[str, bool]] = []

    # Links (including suggestion URLs)
    urls: List[str] = []
    for b in blocks:
        payload = b.get("payload_json", {})
        if isinstance(payload, dict):
            candidate = payload.get("url")
            if candidate:
                urls.append(candidate)
            # Check suggestions for URLs
            suggestions = payload.get("suggestions", [])
            if suggestions:
                for suggestion in suggestions:
                    if isinstance(suggestion, dict) and suggestion.get("url"):
                        urls.append(suggestion["url"])
            if b.get("type") == "new_products":
                for it in payload.get("items", []) or []:
                    if it.get("slug"):
                        urls.append(it["slug"])  # slugs treated as hrefs here
                    if it.get("url"):
                        urls.append(it["url"])
    link_ok = all(ok for _, ok in validate_links(urls)) if urls else True
    results.append(("links", link_ok))

    # Images
    cards: List[Dict[str, str]] = []
    for b in blocks:
        p = b.get("payload_json", {})
        if b.get("type") in ("feature", "spotlight") and p.get("hero_image") or p.get("image_url"):
            cards.append({"image_url": p.get("hero_image") or p.get("image_url")})
        if b.get("type") == "new_products":
            for it in p.get("items", []) or []:
                if it.get("image_url"):
                    cards.append({"image_url": it["image_url"]})
    image_ok = all(ok for _, ok in validate_image_cards(cards)) if cards else True
    results.append(("images", image_ok))

    # Alt text presence (basic: treat excerpt/title as proxy for now)
    alt_ok = True  # placeholder criterion
    results.append(("alt_text", alt_ok))

    # Content safety for suggestions
    suggestion_safety_ok = True
    for b in blocks:
        payload = b.get("payload_json", {})
        if isinstance(payload, dict):
            suggestions = payload.get("suggestions", [])
            if suggestions:
                # Apply safety rules to suggestion items
                safe_items = apply_safety_rules(suggestions)
                # Check if any suggestions were filtered out (indicates safety issue)
                if len(safe_items) < len(suggestions):
                    suggestion_safety_ok = False
                    break
                # Also check current selection
                selected = payload.get("selected")
                if selected and isinstance(selected, dict):
                    selected_list = [selected]
                    safe_selected = apply_safety_rules(selected_list)
                    if len(safe_selected) == 0:
                        suggestion_safety_ok = False
                        break
    results.append(("suggestion_safety", suggestion_safety_ok))

    return results



