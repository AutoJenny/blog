"""
Canonical authoring substage registry (Instruction Set 16 / W2 Phase 1).
Single server-side authority for substages aligned to:
  metadata → ideas → structure → titling → authoring → imaging → review

Registry-only. No runner functions. No execution.
"""

from typing import List, Dict, Any, Tuple, Optional

CANONICAL_STAGE_ORDER = [
    "metadata",
    "ideas",
    "structure",
    "titling",
    "authoring",
    "imaging",
    "review",
]

# Each substage: id, title, description, min_stage, post_types, artefacts_written, supports_web_research
# Runner not implemented; no function pointer.
CANONICAL_SUBSTAGES: Dict[str, List[Dict[str, Any]]] = {
    "metadata": [
        {
            "id": "edit_metadata",
            "title": "Edit metadata",
            "description": "Set title, subtitle, and basic post metadata.",
            "min_stage": "metadata",
            "post_types": ["themed", "recipe", "profile", "clan", "generated"],
            "artefacts_written": ["post.title", "post.subtitle", "post.summary"],
            "supports_web_research": False,
        },
    ],
    "ideas": [
        {
            "id": "generate_idea_set",
            "title": "Generate Idea Set",
            "description": "Generate or curate required ideas for the post (research-backed for themed).",
            "min_stage": "ideas",
            "post_types": ["themed", "recipe", "profile", "clan", "generated"],
            "artefacts_written": ["post_required_idea"],
            "supports_web_research": True,
            "nav_key": "ideas",  # legacy navbar key for lookup
        },
    ],
    "structure": [
        {
            "id": "topic_brainstorming",
            "title": "Topic brainstorming",
            "description": "Generate and cluster topics for sections.",
            "min_stage": "ideas",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_development"],
            "supports_web_research": True,
            "nav_key": "topic_brainstorming",
        },
        {
            "id": "section_structure",
            "title": "Section structure",
            "description": "Define section outline and structure.",
            "min_stage": "structure",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section"],
            "supports_web_research": False,
            "nav_key": "section_structure",
        },
        {
            "id": "topic_allocation",
            "title": "Section ideas",
            "description": "Allocate ideas to sections.",
            "min_stage": "structure",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_development", "post_section"],
            "supports_web_research": False,
            "nav_key": "topic_allocation",
        },
        {
            "id": "section_titling",
            "title": "Section titling",
            "description": "Create section titles and briefs.",
            "min_stage": "structure",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section"],
            "supports_web_research": False,
            "nav_key": "section_titling",
        },
    ],
    "titling": [
        {
            "id": "section_titling_final",
            "title": "Section titling (final)",
            "description": "Finalise section titles and order.",
            "min_stage": "titling",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section"],
            "supports_web_research": False,
        },
    ],
    "authoring": [
        {
            "id": "author_first_drafts",
            "title": "First drafts",
            "description": "Draft section content.",
            "min_stage": "titling",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section.draft"],
            "supports_web_research": True,
            "nav_key": "drafting",
        },
        {
            "id": "image_concepts",
            "title": "Image concepts",
            "description": "Define image concepts per section.",
            "min_stage": "authoring",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section.image_concepts"],
            "supports_web_research": False,
            "nav_key": "image_concepts",
        },
        {
            "id": "image_prompts",
            "title": "Image prompts",
            "description": "Generate image prompts per section.",
            "min_stage": "authoring",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section.image_prompts"],
            "supports_web_research": False,
            "nav_key": "image_prompts",
        },
        {
            "id": "image_captions",
            "title": "Image captions",
            "description": "Write image captions and alt text.",
            "min_stage": "authoring",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section.image_captions"],
            "supports_web_research": False,
            "nav_key": "image_captions",
        },
    ],
    "imaging": [
        {
            "id": "image_generation",
            "title": "Image generation",
            "description": "Generate section images.",
            "min_stage": "authoring",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": ["post_section images", "image_archive"],
            "supports_web_research": False,
            "nav_key": "image_generation",
        },
        {
            "id": "optimise",
            "title": "Optimise",
            "description": "Resize, compress, watermark images.",
            "min_stage": "imaging",
            "post_types": ["themed", "recipe", "profile", "generated"],
            "artefacts_written": [],
            "supports_web_research": False,
            "nav_key": "optimise",
        },
    ],
    "review": [
        {
            "id": "final_review",
            "title": "Final review",
            "description": "Review and finalise before publish.",
            "min_stage": "review",
            "post_types": ["themed", "recipe", "profile", "clan", "generated"],
            "artefacts_written": [],
            "supports_web_research": False,
            "nav_key": "final_review",
        },
    ],
}


def get_canonical_substages_for_post(
    post_id: int,
    post_type: str,
    current_stage: str,
    stage_index_fn,
) -> Dict[str, Any]:
    """
    Build canonical substages response for a post. Filters by post_type, sets available_now by min_stage.
    No execution. Registry-only.
    """
    stages_out = []
    for stage in CANONICAL_STAGE_ORDER:
        substages_raw = CANONICAL_SUBSTAGES.get(stage, [])
        current_idx = stage_index_fn(current_stage)
        stage_available = current_idx >= stage_index_fn(stage)
        substages_out = []
        for s in substages_raw:
            if post_type not in (s.get("post_types") or []):
                continue
            min_stage = s.get("min_stage") or stage
            available_now = current_idx >= stage_index_fn(min_stage)
            substages_out.append({
                "id": s["id"],
                "title": s["title"],
                "description": s.get("description", ""),
                "min_stage": min_stage,
                "available_now": available_now,
                "nav_key": s.get("nav_key"),
                "supports_web_research": s.get("supports_web_research", False),
            })
        if substages_out:
            stages_out.append({
                "stage": stage,
                "available": stage_available,
                "substages": substages_out,
            })
    return {
        "post_id": post_id,
        "post_type": post_type,
        "current_stage": current_stage,
        "stages": stages_out,
    }


def find_substage_by_nav(stage: str, substage_key: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Find a canonical substage by (stage, substage_key). Returns (canonical_stage, substage_dict) or None.
    Handles legacy navbar: e.g. (planning, ideas) -> (ideas, generate_idea_set substage).
    """
    substage_key_normalized = (substage_key or "").replace("-", "_").strip()
    # Direct match in given stage
    for s in CANONICAL_SUBSTAGES.get(stage, []):
        if s.get("id") == substage_key or s.get("id") == substage_key_normalized:
            return (stage, s)
        if s.get("nav_key") == substage_key or s.get("nav_key") == substage_key_normalized:
            return (stage, s)
    # Legacy: planning + ideas -> canonical ideas stage, generate_idea_set
    if stage == "planning" and (substage_key == "ideas" or substage_key_normalized == "ideas"):
        for s in CANONICAL_SUBSTAGES.get("ideas", []):
            if s.get("nav_key") == "ideas" or s.get("id") == "generate_idea_set":
                return ("ideas", s)
    # Search all stages
    for canon_stage, substages in CANONICAL_SUBSTAGES.items():
        for s in substages:
            if s.get("nav_key") == substage_key or s.get("nav_key") == substage_key_normalized:
                return (canon_stage, s)
            if s.get("id") == substage_key or s.get("id") == substage_key_normalized:
                return (canon_stage, s)
    return None
