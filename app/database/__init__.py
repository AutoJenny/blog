from flask import Blueprint

bp = Blueprint("db", __name__, url_prefix="/db")

# Do NOT import routes here to avoid circular import

# Global replicator instance
replicator = None
