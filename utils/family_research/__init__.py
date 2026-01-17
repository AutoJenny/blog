"""
Family Research Utilities
Modular components for family story facts research and narrative generation.
"""

from .prompts import (
    FACT_EXTRACTION_PROMPT,
    SYSTEM_PROMPT,
    STORY_WRITING_SYSTEM_PROMPT,
    STORY_WRITING_USER_PROMPT
)
from .web_utils import (
    perform_web_search,
    fetch_page_content,
    chunk_text
)
from .story_facts import (
    extract_facts_from_chunk,
    post_process_story_facts
)
from .narrative import generate_narrative
from .db_utils import (
    get_family_context,
    load_template
)

__all__ = [
    'FACT_EXTRACTION_PROMPT',
    'SYSTEM_PROMPT',
    'STORY_WRITING_SYSTEM_PROMPT',
    'STORY_WRITING_USER_PROMPT',
    'perform_web_search',
    'fetch_page_content',
    'chunk_text',
    'extract_facts_from_chunk',
    'post_process_story_facts',
    'generate_narrative',
    'get_family_context',
    'load_template'
]


