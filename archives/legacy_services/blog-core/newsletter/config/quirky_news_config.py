"""Configuration for quirky news harvesting and selection."""

from __future__ import annotations

# Heuristic scoring
HEURISTIC_SCORE_THRESHOLD = 3.0  # Minimum heuristic score to proceed to LLM classification

# LLM classification
LLM_QUIRKY_SCORE_THRESHOLD = 60  # Minimum quirky score (0-100) for selection

# Weekly selection
MAX_ITEMS_PER_WEEK = 8  # Maximum total items per week
MAX_ITEMS_PER_REGION = 2  # Maximum items per region

# Safety flags to exclude
EXCLUDED_SAFETY_FLAGS = ['death', 'serious_illness', 'crime']

# Image extraction
IMAGE_EXTRACTION_ENABLED = True
MAX_IMAGES_PER_ARTICLE = 10
IMAGE_EXTRACTION_TIMEOUT = 10  # seconds
IMAGE_CACHE_TTL_DAYS = 30
REMOTE_IMAGE_BASE_URL = '/newsletter/images/'

# Classification batch processing
CLASSIFICATION_BATCH_SIZE = 10
CLASSIFICATION_DAYS_BACK = 14  # How many days back to look for articles to classify

