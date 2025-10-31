"""Universal block service: shared suggestion and override helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from newsletter.services.suggestion_service import generate_suggestions
from newsletter.db.queries_issue import update_block_payload, get_block


def get_content_options(*, block_type: str, issue_id: int, block_id: int, target_week: str) -> Dict[str, Any]:
  """Return suggestions and current selection for a block type.
  This is a thin wrapper to enable reuse by future editors (feature/products/etc.).
  """
  block = get_block(block_id=block_id)
  current_payload = block.get('payload_json', {}) if block else {}
  suggestions = generate_suggestions(block_type=block_type, target_week=target_week, count=3)
  return {
    'suggestions': suggestions,
    'current': current_payload.get('selected') or current_payload,
  }


def apply_override(*, block_id: int, override_payload: Dict[str, Any]) -> Dict[str, Any]:
  """Save manual JSON override to the block payload."""
  update_block_payload(block_id=block_id, payload={**override_payload, 'manual_override': True})
  return {'success': True}
