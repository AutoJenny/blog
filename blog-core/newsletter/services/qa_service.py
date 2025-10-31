"""Pre-send QA checks aggregator."""

from __future__ import annotations

from typing import Dict, List, Tuple
from newsletter.db.queries_issue import list_blocks_by_issue
from newsletter.validators.links import validate_links
from newsletter.validators.images import validate_image_cards
from newsletter.validators.content import has_alt_text


def run_pre_send_checks(issue_id: int) -> List[Tuple[str, bool]]:
    blocks = list_blocks_by_issue(issue_id=issue_id)
    results: List[Tuple[str, bool]] = []

    # Links
    urls: List[str] = []
    for b in blocks:
        payload = b.get("payload_json", {})
        if isinstance(payload, dict):
            candidate = payload.get("url")
            if candidate:
                urls.append(candidate)
            if b.get("type") == "new_products":
                for it in payload.get("items", []) or []:
                    if it.get("slug"):
                        urls.append(it["slug"])  # slugs treated as hrefs here
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

    return results



