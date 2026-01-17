"""
Weekly Content Image Generation Configuration
Styling knobs for square image generation (tweakable without code changes)
"""

import os

# Canvas Settings
CANVAS_SIZE = 1080  # Square 1080×1080

# Colors
BG_COLOR = "#1e3a5f"  # Deep blue (example - adjust to match brand)
TEXT_COLOR = "#f5f1e8"  # Warm ivory for main content (Scots phrase and translation)
HEADER_FOOTER_COLOR = "#8fa8c4"  # Pale blue for header and footer (recedes, makes main content stand out)

# Typography
# Note: These font names should match system fonts or ImageMagick font paths
# Using system fonts that are commonly available:
# - Baskerville is available on macOS
# - Arial/Helvetica are universal fallbacks
# - If specific fonts not found, ImageMagick will use defaults
HEADER_FONT = "Arial-Bold"  # Bold sans for header (fallback: Helvetica-Bold)
BODY_FONT = "Baskerville-Italic"  # Serif italic for Scots phrase (available on macOS)
ACCENT_FONT = "Arial"  # Clean sans for translation/footer (fallback: Helvetica)

# Logo Settings
# Resolve logo path relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(PROJECT_ROOT, "static", "images", "site", "clan-watermark.png")
LOGO_CORNER = "bottom-right"  # or "top-left", "top-right", "bottom-left"
LOGO_SCALE = 0.20  # 20% of canvas width (increased from 15%)
LOGO_PADDING = 40  # pixels from edge

# Layout Margins
TOP_MARGIN = 90  # pixels
BOTTOM_MARGIN = 90  # pixels
SAFE_MARGIN = 90  # pixels (all text within this inset)

# Text Settings
PHRASE_MAX_WIDTH = 800  # pixels (wraps if longer)
LINE_SPACING = 1.2  # line height multiplier
TEXTURE_STRENGTH = 0.05  # 0-1, subtle noise/texture

# Series Footer Text
SERIES_FOOTER_TEXT = "Scots Language Series"  # or your brand series name

# Category-Specific Titles
CATEGORY_TITLES = {
    'weekly_word': 'SCOTS WORD OF THE WEEK',
    'weekly_phrase': 'SCOTS PHRASE OF THE WEEK',
    'weekly_insult': 'SCOTS INSULT OF THE WEEK'
}

# Output Directory Structure
OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "static", "content", "weekly_posts")
