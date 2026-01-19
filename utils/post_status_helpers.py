"""
Post Status Helpers
Utility functions for post status validation and management
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Valid workflow statuses that allow post reuse
# Note: These must match the post_status enum in the database
WORKFLOW_STATUSES = ['draft', 'in_process']

# Statuses that should never be reused
FINAL_STATUSES = ['published', 'deleted', 'archived']


def can_reuse_post(status: Optional[str]) -> bool:
    """
    Check if a post with the given status can be reused.
    
    Args:
        status: Post status from database
        
    Returns:
        True if post can be reused, False otherwise
    """
    if not status:
        return False
    
    status_lower = status.lower().strip()
    
    # Never reuse published, failed, or deleted posts
    if status_lower in FINAL_STATUSES:
        return False
    
    # Only reuse posts in workflow states
    return status_lower in WORKFLOW_STATUSES


def get_reusable_status_filter() -> str:
    """
    Get SQL filter condition for reusable post statuses.
    
    Returns:
        SQL condition string: "status IN ('draft', 'in_progress', 'needs_review', 'ready')"
    """
    status_list = "', '".join(WORKFLOW_STATUSES)
    return f"status IN ('{status_list}')"


def normalize_status_for_display(status: Optional[str]) -> str:
    """
    Normalize status for display (no modification, just return as-is).
    This is kept for backward compatibility but just returns the raw status.
    
    Args:
        status: Raw status from database
        
    Returns:
        Status as-is (no normalization)
    """
    return status or 'Unknown'
