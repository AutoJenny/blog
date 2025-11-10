"""
Imaging Blueprint - Modular Version
Main blueprint that imports and orchestrates all imaging modules
"""

from flask import Blueprint
from dotenv import load_dotenv
import logging
import os

# Load environment variables (ensure .env is loaded)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, '.env')
env_absolute = '/Users/autojenny/Documents/projects/blog/.env'
if os.path.exists(env_absolute):
    load_dotenv(dotenv_path=env_absolute, override=True)
elif os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('imaging', __name__, url_prefix='/imaging')

# Import and register all modules
try:
    # Page routes
    from blueprints.imaging_routes import register_routes as register_page_routes
    register_page_routes(bp)
    logger.info("✅ Registered imaging page routes")
except Exception as e:
    logger.error(f"Failed to register imaging page routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Image generation API endpoints
    from blueprints.imaging_api_generation import register_routes as register_generation_routes
    register_generation_routes(bp)
    logger.info("✅ Registered imaging generation API routes")
except Exception as e:
    logger.error(f"Failed to register imaging generation API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Image optimization API endpoints
    from blueprints.imaging_api_optimization import register_routes as register_optimization_routes
    register_optimization_routes(bp)
    logger.info("✅ Registered imaging optimization API routes")
except Exception as e:
    logger.error(f"Failed to register imaging optimization API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Data API endpoints
    from blueprints.imaging_api_data import register_routes as register_data_routes
    register_data_routes(bp)
    logger.info("✅ Registered imaging data API routes")
except Exception as e:
    logger.error(f"Failed to register imaging data API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Prompt management API endpoints
    from blueprints.imaging_api_prompts import register_routes as register_prompts_routes
    register_prompts_routes(bp)
    logger.info("✅ Registered imaging prompts API routes")
except Exception as e:
    logger.error(f"Failed to register imaging prompts API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    # Model configuration API endpoints
    from blueprints.imaging_api_config import register_routes as register_config_routes
    register_config_routes(bp)
    logger.info("✅ Registered imaging config API routes")
except Exception as e:
    logger.error(f"Failed to register imaging config API routes: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Photo-harvesting endpoints are DEPRECATED and have been removed
# All Photo-harvesting routes now redirect to image generation

logger.info("✅ Imaging blueprint initialized successfully")
