from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_cors import CORS
import os
from database import test_db_connection
from api.sections import bp as sections_bp

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins=['http://localhost:5000', 'http://localhost:5001', 'http://localhost:5002', 'http://localhost:5003'])

# Register blueprints
app.register_blueprint(sections_bp)

@app.route('/')
def index():
    # Get query parameters for post context
    post_id = request.args.get('post_id')
    stage = request.args.get('stage')
    substage = request.args.get('substage')
    step = request.args.get('step')
    
    # If we have post context, render sections panel directly
    if post_id:
        return render_template('sections_panel.html', 
                             post_id=post_id, 
                             stage=stage, 
                             substage=substage, 
                             step=step)
    
    # Otherwise redirect to sections
    return redirect(url_for('sections_panel'))

@app.route('/sections')
def sections_panel():
    return render_template('sections_panel.html')

@app.route('/sections-static/<int:post_id>')
def sections_static(post_id):
    """Server-side rendered sections page for testing"""
    try:
        from api.sections import get_sections_by_post_id
        sections = get_sections_by_post_id(post_id)
        return render_template('sections_static.html', sections=sections, post_id=post_id)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/test-sections')
def test_sections():
    return render_template('test_sections.html')

@app.route('/test-minimal')
def test_minimal():
    return send_file('test_minimal.html')

@app.route('/test-debug')
def test_debug():
    return send_file('test_debug.html')



@app.route('/test-db')
def test_db():
    if test_db_connection():
        return 'DB connection OK', 200
    else:
        return 'DB connection FAILED', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True) 