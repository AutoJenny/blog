"""
Output Readiness - DB-backed, explicit, observable validation for substage/output-channel.

W2-FIX-8: Formalises substage/output-channel validation as an explicit "Output Readiness" layer.
Purely diagnostic — does NOT modify workflow_stage. Used before One-Click execute and start_automation.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from config.database import db_manager
from config.output_channel_stages import get_stages_for_output, get_substages_for_output
from utils.taxonomy_helpers import get_post_type

logger = logging.getLogger(__name__)


def _get_pipeline_ordered(post_type: str, output_channel: str) -> List[Tuple[str, str]]:
    """
    Build ordered list of (stage, substage) for the pipeline.
    Returns empty list if pipeline cannot be determined.
    """
    config = get_stages_for_output(post_type, output_channel)
    if not config:
        return []
    if config.get("use_post_type_config"):
        from utils.substage_config import get_substages_for_post_type
        substages_by_stage = get_substages_for_post_type(post_type)
        if not substages_by_stage:
            return []
        # Order stages: planning, research, authoring, imaging, header (exclude calendar, content)
        stage_order = ["planning", "research", "authoring", "imaging", "header"]
        result = []
        for stage in stage_order:
            for substage in substages_by_stage.get(stage, []):
                result.append((stage, substage))
        return result
    stages = config.get("stages", [])
    substages = config.get("substages", {})
    result = []
    for stage in stages:
        for substage in substages.get(stage, []):
            result.append((stage, substage))
    return result


def _is_substage_complete(post_id: int, post: Dict[str, Any], section_stats: Dict, stage: str, substage: str) -> bool:
    """
    Check if a substage is complete for a post.
    Mirrors automation_pipeline completion logic for blog pipeline substages.
    """
    if not post:
        return False

    # Planning
    if substage == "ideas":
        return bool(post.get("expanded_idea") and str(post.get("expanded_idea", "")).strip())
    if substage == "taxonomy":
        return (
            post.get("theme_id") is not None
            and post.get("content_type_id") is not None
            and post.get("format_id") is not None
        )
    if substage == "topic_brainstorming":
        return bool(post.get("idea_scope") and str(post.get("idea_scope", "")).strip())
    if substage == "section_structure":
        return bool(post.get("section_structure"))
    if substage == "topic_allocation":
        return bool(post.get("topic_allocation"))
    if substage == "section_titling":
        return bool(post.get("sections") and str(post.get("sections", "")).strip())

    # Authoring
    if substage in ("drafting", "author_first_drafts"):
        if section_stats and section_stats.get("total", 0) > 0:
            return section_stats.get("drafted", 0) == section_stats["total"]
        return False
    if substage == "image_concepts":
        if section_stats and section_stats.get("total", 0) > 0:
            return section_stats.get("image_concepts_count", 0) == section_stats["total"]
        return False
    if substage == "image_prompts":
        if section_stats and section_stats.get("total", 0) > 0:
            return section_stats.get("image_prompts_count", 0) == section_stats["total"]
        return False
    if substage == "image_captions":
        if section_stats and section_stats.get("total", 0) > 0:
            return section_stats.get("image_captions_count", 0) == section_stats["total"]
        return False

    # Imaging
    if substage == "image_generation":
        if section_stats and section_stats.get("total", 0) > 0:
            return section_stats.get("image_generated_count", 0) == section_stats["total"]
        return False
    if substage == "optimise":
        if section_stats and section_stats.get("optimized_sections", 0) > 0:
            return section_stats.get("optimized_sections") == section_stats.get("total_sections")
        return section_stats.get("total_sections", 0) == 0

    # Header
    if substage == "title_summary":
        return bool(
            post.get("title") and str(post.get("title", "")).strip()
            and post.get("summary") and str(post.get("summary", "")).strip()
        )
    if substage == "header_image":
        return post.get("header_image_id") is not None
    if substage == "seo_meta":
        return bool(
            post.get("meta_title") and str(post.get("meta_title", "")).strip()
            and post.get("meta_description") and str(post.get("meta_description", "")).strip()
            and post.get("slug") and str(post.get("slug", "")).strip()
        )
    if substage == "product_match":
        return (
            post.get("profile_product_id") is not None
            or post.get("cross_promotion_product_id") is not None
        )
    if substage == "final_review":
        return (
            _is_substage_complete(post_id, post, section_stats, "header", "title_summary")
            and _is_substage_complete(post_id, post, section_stats, "header", "header_image")
            and _is_substage_complete(post_id, post, section_stats, "header", "seo_meta")
        )

    # Syndication / channel-specific: not tracked in post — assume not complete
    if stage in ("syndication", "content", "publish"):
        return False

    return False


def _load_post_and_stats(post_id: int) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Load post and section/optimization stats for completion checks."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, p.summary, p.header_image_id,
                       p.meta_title, p.meta_description, p.slug,
                       p.theme_id, p.content_type_id, p.format_id,
                       p.profile_product_id, p.cross_promotion_product_id,
                       pd.idea_seed, pd.section_structure, pd.topic_allocation, pd.sections
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            if not post:
                return None, None
            post = dict(post)

            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted,
                       SUM(CASE WHEN image_concepts IS NOT NULL AND image_concepts != '' THEN 1 ELSE 0 END) as image_concepts_count,
                       SUM(CASE WHEN image_prompts IS NOT NULL AND image_prompts != '' THEN 1 ELSE 0 END) as image_prompts_count,
                       SUM(CASE WHEN image_captions IS NOT NULL AND image_captions != '' THEN 1 ELSE 0 END) as image_captions_count,
                       SUM(CASE WHEN image_filename IS NOT NULL AND image_filename != '' THEN 1 ELSE 0 END) as image_generated_count
                FROM post_section
                WHERE post_id = %s AND section_order <= 7
            """, (post_id,))
            sec = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(DISTINCT ps.id) as total_sections,
                       COUNT(DISTINCT pi.section_id) as optimized_sections
                FROM post_section ps
                LEFT JOIN post_images pi ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
                WHERE ps.post_id = %s AND ps.section_order <= 7
            """, (post_id,))
            opt = cursor.fetchone()

            section_stats = dict(sec) if sec else {}
            if opt:
                section_stats["optimized_sections"] = opt.get("optimized_sections", 0)
                section_stats["total_sections"] = opt.get("total_sections", 0)

            return post, section_stats
    except Exception as e:
        logger.error(f"Error loading post {post_id} for output readiness: {e}")
        return None, None


def get_output_readiness(post_id: int, output_channel: str = "blog") -> Dict[str, Any]:
    """
    Evaluate output readiness for a post and output channel.
    Purely diagnostic — does NOT modify workflow_stage.

    Returns:
        {
            ok: bool,
            required_substage: str,
            required_stage: str,
            current_substage: str,
            current_stage: str,
            errors: [...],
            warnings: [...]
        }

    Rules:
        - Evaluates validate_substage_for_output / output-channel requirements.
        - ok=True only when the required (last) substage in the pipeline is complete.
    """
    errors: List[str] = []
    warnings: List[str] = []

    post, section_stats = _load_post_and_stats(post_id)
    if not post:
        return {
            "ok": False,
            "required_substage": "",
            "required_stage": "",
            "current_substage": "",
            "current_stage": "",
            "errors": ["Post not found"],
            "warnings": [],
        }

    post_type = get_post_type(post_id)
    if not post_type:
        post_type = "themed"

    pipeline = _get_pipeline_ordered(post_type, output_channel)
    if not pipeline:
        return {
            "ok": False,
            "required_substage": "",
            "required_stage": "",
            "current_substage": "",
            "current_stage": "",
            "errors": [f"No pipeline configured for post_type={post_type} output_channel={output_channel}"],
            "warnings": [],
        }

    required_stage, required_substage = pipeline[-1]
    current_stage, current_substage = "", ""

    for stage, substage in pipeline:
        if _is_substage_complete(post_id, post, section_stats or {}, stage, substage):
            current_stage, current_substage = stage, substage
        else:
            break

    ok = _is_substage_complete(post_id, post, section_stats or {}, required_stage, required_substage)

    if not ok:
        errors.append(
            f"Missing substage '{required_substage}' (stage: {required_stage}). "
            f"Current: '{current_substage or 'none'}' (stage: {current_stage or 'none'})."
        )

    return {
        "ok": ok,
        "required_substage": required_substage,
        "required_stage": required_stage,
        "current_substage": current_substage,
        "current_stage": current_stage,
        "errors": errors,
        "warnings": warnings,
        "post_type": post_type,
        "output_channel": output_channel,
    }
