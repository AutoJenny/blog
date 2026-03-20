from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional


def _projects_config_path() -> Path:
    """
    ai-hub/config/projects.json lives alongside this blog repo under /Users/autojenny/Documents/.
    """
    # /.../Documents/projects/blog/utils/germination_engine.py -> /.../Documents
    return Path(__file__).resolve().parents[3] / "ai-hub" / "config" / "projects.json"


def _load_projects_config() -> Dict[str, Any]:
    cfg_path = _projects_config_path()
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_global_project_mission(*, project_id: str) -> Dict[str, str]:
    """
    Returns { historical_rigor, brand_tone } for a given project_id.

    Primary source: docs/project/PROJECT_CHARTER.md at the project's configured root_dir.
    """
    cfg = _load_projects_config()
    proj = (cfg.get("projects") or [])
    project = next((p for p in proj if str(p.get("project_id")).strip() == str(project_id).strip()), None) or {}
    root_dir = Path(project.get("root_dir") or "")
    if not root_dir:
        return {"historical_rigor": "", "brand_tone": ""}

    charter_path = root_dir / "docs" / "project" / "PROJECT_CHARTER.md"
    if not charter_path.exists():
        return {"historical_rigor": "", "brand_tone": ""}

    text = charter_path.read_text(encoding="utf-8")

    # Example markdown lines:
    # * **Primary Objective**: To ...
    # * **Tone**: Highly technical ...
    obj_match = re.search(r"\\*\\s*\\*\\*Primary Objective\\*\\*\\s*:\\s*(.+)", text)
    tone_match = re.search(r"\\*\\s*\\*\\*Tone\\*\\*\\s*:\\s*(.+)", text)

    historical_rigor = (obj_match.group(1).strip() if obj_match else "").replace("\r", "")
    brand_tone = (tone_match.group(1).strip() if tone_match else "").replace("\r", "")

    return {"historical_rigor": historical_rigor, "brand_tone": brand_tone}


def merge_mission(
    *,
    global_mission: Dict[str, str],
    local_override: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Merge global mission with local override.
    local_override keys are expected to include:
      - historical_rigor
      - brand_tone
    """
    merged: Dict[str, str] = {
        "historical_rigor": str(global_mission.get("historical_rigor") or ""),
        "brand_tone": str(global_mission.get("brand_tone") or ""),
    }
    if not local_override or not isinstance(local_override, dict):
        return merged

    for k in ["historical_rigor", "brand_tone"]:
        if k in local_override and local_override[k] is not None:
            merged[k] = str(local_override.get(k) or "")
    return merged


def build_expansion_prompt(
    *,
    seed_text: str,
    seed_metadata: Optional[Dict[str, Any]],
    merged_mission: Dict[str, str],
) -> str:
    seed_metadata = seed_metadata or {}
    if not isinstance(seed_metadata, dict):
        seed_metadata = {}

    source = str(seed_metadata.get("source") or "").strip() or "—"
    post_type = str(seed_metadata.get("post_type") or "").strip() or "—"

    historical_rigor = merged_mission.get("historical_rigor") or ""
    brand_tone = merged_mission.get("brand_tone") or ""

    seed_text = seed_text or ""
    seed_text = str(seed_text).strip()

    return (
        "You are the BlogForge Germination Studio (Seed-to-Brief).\n\n"
        "Mission Constraints (deterministic):\n"
        f"- Historical Rigor: {historical_rigor or '—'}\n"
        f"- Brand Tone: {brand_tone or '—'}\n\n"
        "Seed Metadata:\n"
        f"- Seed Source: {source}\n"
        f"- Post Type: {post_type}\n\n"
        "Seed Text:\n"
        f"{seed_text}\n\n"
        "Produce an Expansion Brief suitable for downstream LLM drafting.\n"
        "Return the result in a structured, auditable format that includes:\n"
        "1) Research Focus (bullet points)\n"
        "2) Proposed Section Skeleton (headings only)\n"
        "3) Required Fact Checks (list)\n"
        "4) Tone Notes (short)\n"
    )

