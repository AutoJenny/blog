from app.api.base import APIBlueprint

bp = APIBlueprint('llm_api_modern', __name__)

from app.api.llm import routes 

# Import the deprecated blueprint from app/api/llm.py
from app.api.llm import bp as llm_api_deprecated_bp

__all__ = ['bp', 'llm_api_deprecated_bp'] 