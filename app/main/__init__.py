from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return "Main index - stub"

@bp.route('/health')
def health_check():
    return "OK"

@bp.route('/health/detailed')
def detailed_health_check():
    return "Detailed health check - stub"

@bp.route('/dashboard')
def dashboard():
    return "Dashboard - stub"

@bp.route('/modern')
def modern_index():
    return "Modern index - stub"

@bp.route('/docs/')
def docs():
    return "Docs - stub"

@bp.route('/docs/<path:req_path>')
def docs_path(req_path):
    return f"Docs path: {req_path} - stub"

@bp.route('/docs/nav/')
def docs_nav():
    return "Docs nav - stub"

@bp.route('/docs/view/<path:file_path>')
def docs_content(file_path):
    return f"Docs content: {file_path} - stub"

@bp.route('/mermaid-standalone')
def mermaid_standalone():
    return "Mermaid standalone - stub"

@bp.route('/llm/')
def llm_dashboard():
    return "LLM dashboard - stub"

@bp.route('/llm/providers')
def llm_providers():
    return "LLM providers - stub"

@bp.route('/llm/models')
def llm_models():
    return "LLM models - stub"

@bp.route('/llm/prompts')
def llm_prompts():
    return "LLM prompts - stub"

@bp.route('/llm/logs')
def llm_logs():
    return "LLM logs - stub"

@bp.route('/llm/settings')
def llm_settings():
    return "LLM settings - stub"

@bp.route('/preview/')
def preview_stub():
    return "Preview stub"

@bp.route('/structure/')
def structure_stub():
    return "Structure stub" 