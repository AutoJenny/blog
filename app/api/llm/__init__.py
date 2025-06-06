from app.api.base import APIBlueprint

bp = APIBlueprint('llm_api', __name__)

from app.api.llm import routes 