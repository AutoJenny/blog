from flask import Blueprint, render_template
from app.database import get_db_conn

bp = Blueprint('db', __name__)

@bp.route('/')
def index():
    return render_template('db/index.html')

@bp.route('/restore')
def restore():
    return render_template('db/restore.html')

@bp.route('/stats')
def stats():
    return render_template('db/stats.html')

@bp.route('/logs')
def logs():
    return render_template('db/logs.html')

@bp.route('/migrations')
def migrations():
    return render_template('db/migrations.html')

@bp.route('/replication')
def replication():
    return render_template('db/replication.html')

@bp.route('/tables')
def list_tables():
    return render_template('db/tables.html')

@bp.route('/debug')
def db_debug():
    return render_template('db/debug.html')

@bp.route('/raw')
def db_raw():
    return render_template('db/raw.html')

@bp.route('/backup', methods=['POST'])
def backup():
    return "Backup endpoint"

@bp.route('/debug/routes')
def debug_db_routes():
    return "Database routes debug" 