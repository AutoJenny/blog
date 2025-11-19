"""
Header Blueprint - Modular Version
Main blueprint that imports and orchestrates all header modules
"""

from flask import Blueprint
import logging

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('header', __name__, url_prefix='/header')

# Re-export LLMService for backward compatibility
from .llm_service import LLMService

# Import and register all modules
try:
    # Page routes
    from .routes import register_routes as register_page_routes
    register_page_routes(bp)
    logger.info("✅ Registered header page routes")
except Exception as e:
    logger.error(f"Failed to register header page routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Prompt compilation API endpoints
    from .api_prompt_compilation import register_routes as register_prompt_compilation_routes
    register_prompt_compilation_routes(bp)
    logger.info("✅ Registered header prompt compilation API routes")
except Exception as e:
    logger.error(f"Failed to register header prompt compilation API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Prompt management API endpoints
    from .api_prompts import register_routes as register_prompts_routes
    register_prompts_routes(bp)
    logger.info("✅ Registered header prompts API routes")
except Exception as e:
    logger.error(f"Failed to register header prompts API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # UI preferences API endpoints
    from .api_ui_preferences import register_routes as register_ui_preferences_routes
    register_ui_preferences_routes(bp)
    logger.info("✅ Registered header UI preferences API routes")
except Exception as e:
    logger.error(f"Failed to register header UI preferences API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Image generation API endpoints
    from .api_image_generation import register_routes as register_image_generation_routes
    register_image_generation_routes(bp)
    logger.info("✅ Registered header image generation API routes")
except Exception as e:
    logger.error(f"Failed to register header image generation API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # SEO meta API endpoints
    from .api_seo_meta import register_routes as register_seo_meta_routes
    register_seo_meta_routes(bp)
    logger.info("✅ Registered header SEO meta API routes")
except Exception as e:
    logger.error(f"Failed to register header SEO meta API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Title generation API endpoints
    from .api_title_generation import register_routes as register_title_generation_routes
    register_title_generation_routes(bp)
    logger.info("✅ Registered header title generation API routes")
except Exception as e:
    logger.error(f"Failed to register header title generation API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Summary generation API endpoints
    from .api_summary_generation import register_routes as register_summary_generation_routes
    register_summary_generation_routes(bp)
    logger.info("✅ Registered header summary generation API routes")
except Exception as e:
    logger.error(f"Failed to register header summary generation API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Title/summary data API endpoints
    from .api_title_summary_data import register_routes as register_title_summary_data_routes
    register_title_summary_data_routes(bp)
    logger.info("✅ Registered header title/summary data API routes")
except Exception as e:
    logger.error(f"Failed to register header title/summary data API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Photo-harvesting API endpoints
    from .api_photo_harvesting import register_routes as register_photo_harvesting_routes
    register_photo_harvesting_routes(bp)
    logger.info("✅ Registered header photo-harvesting API routes")
except Exception as e:
    logger.error(f"Failed to register header photo-harvesting API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Test/utility API endpoints
    from .api_test import register_routes as register_test_routes
    register_test_routes(bp)
    logger.info("✅ Registered header test/utility API routes")
except Exception as e:
    logger.error(f"Failed to register header test/utility API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

logger.info("✅ Header blueprint initialized successfully")

