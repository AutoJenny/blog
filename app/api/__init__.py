from app.api.base import APIBlueprint

bp = APIBlueprint('api', __name__)

from app.api import routes 