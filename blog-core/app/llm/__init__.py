from flask import Blueprint

bp = Blueprint('llm', __name__)

from app.llm import routes 