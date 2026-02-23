"""
Canonical Post Factory — ensure post_development and default sections exist.

W2-FIX-1: Canonical Draft Post Contract (Create + Ensure Sections)
After ANY post creation path, the post is authorable immediately:
- post_development row exists
- at least 1 post_section exists with numeric id and non-null section_order
"""

import logging
from typing import Optional

from config.database import db_manager

logger = logging.getLogger(__name__)

# Section templates: list of (section_order, section_heading, section_description, section_type)
DEFAULT_GENERIC_TEMPLATE = [
    (1, 'Main', '', 'body'),
]

DEFAULT_EDITORIAL_TEMPLATE = [
    (1, 'Intro', 'Introduction and hook', 'intro'),
    (2, 'Body', 'Main content', 'body'),
    (3, 'Outro', 'Conclusion and call to action', 'outro'),
]

DEFAULT_PROFILE_TEMPLATE = [
    (1, 'Standfirst', 'Summary/standfirst', 'standfirst'),
    (2, 'Key facts', 'Key facts and highlights', 'key_facts'),
    (3, 'Main', 'Main content', 'body'),
    (4, 'CTA', 'Call to action', 'cta'),
]


def _get_recipe_template():
    """Recipe template uses standard recipe sections from section_headings."""
    try:
        from utils.section_headings import get_standard_recipe_sections
        sections = get_standard_recipe_sections()
        return [(i + 1, sh, sd, st) for i, (st, sh, sd) in enumerate(sections)]
    except Exception:
        return DEFAULT_GENERIC_TEMPLATE


TEMPLATES = {
    'default_generic': DEFAULT_GENERIC_TEMPLATE,
    'default_editorial': DEFAULT_EDITORIAL_TEMPLATE,
    'default_profile': DEFAULT_PROFILE_TEMPLATE,
}


def ensure_post_development(post_id: int, idea_seed: str = '') -> None:
    """
    Ensure a post_development row exists for the given post.
    Idempotent: no-op if row already exists.

    Args:
        post_id: Post ID
        idea_seed: Optional idea seed (used when creating new row)
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT 1 FROM post_development WHERE post_id = %s LIMIT 1", (post_id,))
        if cursor.fetchone():
            return

        cursor.execute("""
            INSERT INTO post_development (post_id, idea_seed, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (post_id) DO NOTHING
        """, (post_id, idea_seed))
        cursor.connection.commit()
        logger.info(f"Ensured post_development for post {post_id}")


def ensure_default_sections(
    post_id: int,
    variant: str = 'generic',
    template_name: Optional[str] = None,
) -> int:
    """
    If post has 0 post_section rows, INSERT minimal template sections.
    Uses numeric ids (DB PK), sets section_order = 1..n (not null).

    Args:
        post_id: Post ID
        variant: Post variant ('generic', 'recipe', 'editorial', 'profile', 'generated')
        template_name: Template to use ('default_generic', 'default_editorial', 'default_profile').
                       If None, derived from variant: profile->default_profile, generic->default_generic.

    Returns:
        Number of sections created (0 if post already had sections)
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM post_section WHERE post_id = %s", (post_id,))
        row = cursor.fetchone()
        count = row['c'] if isinstance(row, dict) else row[0]

        if count > 0:
            return 0

        # Resolve template
        if variant == 'recipe':
            sections_def = _get_recipe_template()
        elif template_name and template_name in TEMPLATES:
            sections_def = TEMPLATES[template_name]
        elif variant == 'profile':
            sections_def = TEMPLATES.get('default_profile', DEFAULT_GENERIC_TEMPLATE)
        elif variant in ('editorial', 'generated'):
            sections_def = TEMPLATES.get('default_editorial', DEFAULT_GENERIC_TEMPLATE)
        else:
            sections_def = DEFAULT_GENERIC_TEMPLATE

        for section_order, section_heading, section_description, section_type in sections_def:
            cursor.execute("""
                INSERT INTO post_section (
                    post_id, section_order, section_type, section_heading,
                    section_description, status
                )
                VALUES (%s, %s, %s, %s, %s, 'draft')
            """, (post_id, section_order, section_type, section_heading, section_description))

        cursor.connection.commit()
        logger.info(f"Created {len(sections_def)} default sections for post {post_id} (variant={variant})")
        return len(sections_def)
