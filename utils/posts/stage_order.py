"""
Canonical authoring stage order. W2 Phase 2.
Single source of truth for stage ordering. All stage comparisons must use stage_index().
"""

STAGE_ORDER = [
    "metadata",
    "ideas",
    "structure",
    "titling",
    "authoring",
    "imaging",
    "review",
]


def stage_index(stage: str) -> int:
    """Return 0-based index of stage in STAGE_ORDER. Unknown stage returns 0."""
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return 0
