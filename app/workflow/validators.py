from typing import List
from app.models import Post


class ValidationError(Exception):
    """Raised when validation fails"""

    pass


def validate_stage(post: Post, stage: str, sub_stage: str, rules: List[str]) -> None:
    """
    Validate a stage using the specified rules
    Raises ValidationError if validation fails
    """
    for rule in rules:
        validator = VALIDATORS.get(rule)
        if validator:
            validator(post)
        else:
            raise ValueError(f"Unknown validation rule: {rule}")


def basic_idea_not_empty(post: Post) -> None:
    """Validate that the post has a basic idea"""
    if not post.basic_idea or not post.basic_idea.strip():
        raise ValidationError("Basic idea is required")


def audience_defined(post: Post) -> None:
    """Validate that the audience is defined in metadata"""
    if not post.llm_metadata or "audience" not in post.llm_metadata:
        raise ValidationError("Target audience must be defined")


def value_prop_defined(post: Post) -> None:
    """Validate that the value proposition is defined"""
    if not post.llm_metadata or "value_proposition" not in post.llm_metadata:
        raise ValidationError("Value proposition must be defined")


def research_notes_added(post: Post) -> None:
    """Validate that research notes are added"""
    if not post.llm_metadata or "research_notes" not in post.llm_metadata:
        raise ValidationError("Research notes are required")


def expert_notes_added(post: Post) -> None:
    """Validate that expert consultation notes are added"""
    if not post.llm_metadata or "expert_notes" not in post.llm_metadata:
        raise ValidationError("Expert consultation notes are required")


def facts_verified(post: Post) -> None:
    """Validate that facts have been verified"""
    if not post.llm_metadata or "fact_verification" not in post.llm_metadata:
        raise ValidationError("Fact verification is required")


def sections_defined(post: Post) -> None:
    """Validate that post sections are defined"""
    if not post.sections:
        raise ValidationError("Post sections must be defined")


def flow_reviewed(post: Post) -> None:
    """Validate that content flow has been reviewed"""
    if not post.llm_metadata or "flow_review" not in post.llm_metadata:
        raise ValidationError("Content flow review is required")


def resources_listed(post: Post) -> None:
    """Validate that required resources are listed"""
    if not post.llm_metadata or "required_resources" not in post.llm_metadata:
        raise ValidationError("Required resources must be listed")


def content_not_empty(post: Post) -> None:
    """Validate that post has content"""
    if not post.content or not post.content.strip():
        raise ValidationError("Post content is required")


def tech_reviewed(post: Post) -> None:
    """Validate that technical review is complete"""
    if not post.llm_metadata or "technical_review" not in post.llm_metadata:
        raise ValidationError("Technical review is required")


def readability_checked(post: Post) -> None:
    """Validate that readability has been checked"""
    if not post.llm_metadata or "readability_check" not in post.llm_metadata:
        raise ValidationError("Readability check is required")


def image_plan_complete(post: Post) -> None:
    """Validate that image plan is complete"""
    if not post.llm_metadata or "image_plan" not in post.llm_metadata:
        raise ValidationError("Image plan is required")


def images_generated(post: Post) -> None:
    """Validate that required images are generated"""
    if not post.header_image:
        raise ValidationError("Header image is required")
    for section in post.sections:
        if section.image_id is None:
            raise ValidationError(f"Image missing for section: {section.title}")


def images_optimized(post: Post) -> None:
    """Validate that images are optimized"""
    if not post.header_image or not post.header_image.image_metadata.get("optimized"):
        raise ValidationError("Header image not optimized")
    for section in post.sections:
        if section.image and not section.image.image_metadata.get("optimized"):
            raise ValidationError(f"Image not optimized for section: {section.title}")


def images_watermarked(post: Post) -> None:
    """Validate that images are watermarked"""
    if not post.header_image or not post.header_image.watermarked:
        raise ValidationError("Header image not watermarked")
    for section in post.sections:
        if section.image and not section.image.watermarked:
            raise ValidationError(f"Image not watermarked for section: {section.title}")


def basic_meta_complete(post: Post) -> None:
    """Validate that basic metadata is complete"""
    if not post.seo_metadata or not all(
        k in post.seo_metadata for k in ["title", "description"]
    ):
        raise ValidationError("Basic metadata (title, description) is required")


def seo_optimized(post: Post) -> None:
    """Validate that SEO optimization is complete"""
    required_seo = ["keywords", "meta_title", "meta_description", "canonical_url"]
    if not post.seo_metadata or not all(k in post.seo_metadata for k in required_seo):
        raise ValidationError("SEO optimization is incomplete")


def social_preview_complete(post: Post) -> None:
    """Validate that social preview is complete"""
    required_social = ["og_title", "og_description", "og_image", "twitter_card"]
    if not post.seo_metadata or not all(
        k in post.seo_metadata for k in required_social
    ):
        raise ValidationError("Social preview metadata is incomplete")


def self_reviewed(post: Post) -> None:
    """Validate that self-review is complete"""
    if not post.llm_metadata or "self_review" not in post.llm_metadata:
        raise ValidationError("Self-review is required")


def peer_reviewed(post: Post) -> None:
    """Validate that peer review is complete"""
    if not post.llm_metadata or "peer_review" not in post.llm_metadata:
        raise ValidationError("Peer review is required")


def final_checked(post: Post) -> None:
    """Validate that final check is complete"""
    if not post.llm_metadata or "final_check" not in post.llm_metadata:
        raise ValidationError("Final check is required")


def schedule_set(post: Post) -> None:
    """Validate that publication schedule is set"""
    if not post.published_at:
        raise ValidationError("Publication date must be set")


def deployed(post: Post) -> None:
    """Validate that post is deployed"""
    if not post.published:
        raise ValidationError("Post must be published")


def verified_live(post: Post) -> None:
    """Validate that post is verified live"""
    if not post.llm_metadata or "verified_live" not in post.llm_metadata:
        raise ValidationError("Post must be verified live")


def feedback_collected(post: Post) -> None:
    """Validate that feedback is collected"""
    if not post.llm_metadata or "feedback" not in post.llm_metadata:
        raise ValidationError("Feedback collection is required")


def updates_applied(post: Post) -> None:
    """Validate that updates are applied"""
    if not post.llm_metadata or "updates" not in post.llm_metadata:
        raise ValidationError("Content updates must be tracked")


def version_tracked(post: Post) -> None:
    """Validate that version is tracked"""
    if not post.llm_metadata or "version_history" not in post.llm_metadata:
        raise ValidationError("Version history must be tracked")


def platforms_selected(post: Post) -> None:
    """Validate that syndication platforms are selected"""
    if not post.syndication_status or "platforms" not in post.syndication_status:
        raise ValidationError("Syndication platforms must be selected")


def content_adapted(post: Post) -> None:
    """Validate that content is adapted for platforms"""
    if not post.syndication_status or "adaptations" not in post.syndication_status:
        raise ValidationError("Content must be adapted for platforms")


def distributed(post: Post) -> None:
    """Validate that content is distributed"""
    if not post.syndication_status or "distribution" not in post.syndication_status:
        raise ValidationError("Content must be distributed to platforms")


def tracking_setup(post: Post) -> None:
    """Validate that engagement tracking is set up"""
    if not post.syndication_status or "tracking" not in post.syndication_status:
        raise ValidationError("Engagement tracking must be set up")


# Map validation rule names to their functions
VALIDATORS = {
    "basic_idea_not_empty": basic_idea_not_empty,
    "audience_defined": audience_defined,
    "value_prop_defined": value_prop_defined,
    "research_notes_added": research_notes_added,
    "expert_notes_added": expert_notes_added,
    "facts_verified": facts_verified,
    "sections_defined": sections_defined,
    "flow_reviewed": flow_reviewed,
    "resources_listed": resources_listed,
    "content_not_empty": content_not_empty,
    "tech_reviewed": tech_reviewed,
    "readability_checked": readability_checked,
    "image_plan_complete": image_plan_complete,
    "images_generated": images_generated,
    "images_optimized": images_optimized,
    "images_watermarked": images_watermarked,
    "basic_meta_complete": basic_meta_complete,
    "seo_optimized": seo_optimized,
    "social_preview_complete": social_preview_complete,
    "self_reviewed": self_reviewed,
    "peer_reviewed": peer_reviewed,
    "final_checked": final_checked,
    "schedule_set": schedule_set,
    "deployed": deployed,
    "verified_live": verified_live,
    "feedback_collected": feedback_collected,
    "updates_applied": updates_applied,
    "version_tracked": version_tracked,
    "platforms_selected": platforms_selected,
    "content_adapted": content_adapted,
    "distributed": distributed,
    "tracking_setup": tracking_setup,
}
