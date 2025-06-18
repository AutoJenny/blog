from flask import render_template, jsonify
from app.main import bp

@bp.route('/')
def index():
    return render_template('main/index.html')

@bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

@bp.route('/health/detailed')
def detailed_health_check():
    return jsonify({"status": "healthy", "details": "llm-actions branch"})

@bp.route('/dashboard')
def dashboard():
    return render_template('main/dashboard.html')

@bp.route('/modern')
def modern_index():
    return render_template('main/modern_index.html')

@bp.route('/docs/')
@bp.route('/docs/<path:req_path>')
def docs(req_path=''):
    return render_template('main/docs_content.html')

@bp.route('/docs/nav/')
def docs_nav():
    return render_template('main/docs_nav.html')

@bp.route('/docs/view/<path:file_path>')
def docs_content(file_path):
    return render_template('main/docs_content.html')

@bp.route('/mermaid-standalone')
def mermaid_standalone():
    return render_template('main/mermaid_standalone.html')

@bp.route('/llm/')
def llm_dashboard():
    return render_template('main/llm_dashboard.html')

@bp.route('/llm/providers')
def llm_providers():
    return render_template('main/llm_providers.html')

@bp.route('/llm/models')
def llm_models():
    return render_template('main/llm_models.html')

@bp.route('/llm/prompts')
def llm_prompts():
    return render_template('main/llm_prompts.html')

@bp.route('/llm/logs')
def llm_logs():
    return render_template('main/llm_logs.html')

@bp.route('/llm/settings')
def llm_settings():
    return render_template('main/llm_settings.html')

@bp.route('/preview/')
def preview_stub():
    return render_template('preview/landing.html')

@bp.route('/structure/')
def structure_stub():
    return render_template('preview/structure.html') 