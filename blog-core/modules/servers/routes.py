import subprocess
import requests
import json
from flask import render_template, jsonify, request, current_app
from . import bp

# Server configurations
SERVERS = {
    5000: {
        'name': 'Blog Core',
        'description': 'Main blog application with workflow and navigation',
        'path': '/Users/nickfiddes/Code/projects/blog/blog-core',
        'start_cmd': 'PORT=5000 python3 app.py',
        'health_url': 'http://localhost:5000/',
        'home_url': 'http://localhost:5000',
        'status': 'unknown'
    },
    5001: {
        'name': 'Blog Launchpad',
        'description': 'Project management and launch interface',
        'path': '/Users/nickfiddes/Code/projects/blog/blog-launchpad',
        'start_cmd': 'PORT=5001 python3 app.py',
        'health_url': 'http://localhost:5001/',
        'home_url': 'http://localhost:5001',
        'status': 'unknown'
    },
    5002: {
        'name': 'Blog LLM Actions',
        'description': 'AI-powered content generation and LLM interactions',
        'path': '/Users/nickfiddes/Code/projects/blog/blog-llm-actions',
        'start_cmd': 'PORT=5002 python3 app.py',
        'health_url': 'http://localhost:5002/',
        'home_url': 'http://localhost:5002',
        'status': 'unknown'
    },
    5003: {
        'name': 'Blog Post Sections',
        'description': 'Section management and content organization',
        'path': '/Users/nickfiddes/Code/projects/blog/blog-post-sections',
        'start_cmd': 'python3 app.py',
        'health_url': 'http://localhost:5003/sections',
        'home_url': 'http://localhost:5003',
        'status': 'unknown'
    },
    5004: {
        'name': 'Blog Post Info',
        'description': 'Post metadata and information management',
        'path': '/Users/nickfiddes/Code/projects/blog/blog-post-info',
        'start_cmd': 'PORT=5004 python3 app.py',
        'health_url': 'http://localhost:5004/',
        'home_url': 'http://localhost:5004',
        'status': 'unknown'
    },
    5005: {
        'name': 'Blog Images',
        'description': 'Image generation and management interface',
        'path': '/Users/nickfiddes/Code/projects/blog/blog-images',
        'start_cmd': 'PORT=5005 python3 app.py',
        'health_url': 'http://localhost:5005/',
        'home_url': 'http://localhost:5005',
        'status': 'unknown'
    }
}

def check_server_status(port):
    """Check if a server is running on the specified port."""
    try:
        server = SERVERS[port]
        response = requests.get(server['health_url'], timeout=3)
        return response.status_code == 200
    except:
        return False

def get_server_status():
    """Get status of all servers."""
    for port in SERVERS:
        SERVERS[port]['status'] = 'running' if check_server_status(port) else 'stopped'
    return SERVERS

@bp.route('/')
def servers_index():
    """Main servers management page."""
    servers = get_server_status()
    return render_template('servers/index.html', servers=servers)

@bp.route('/api/status')
def api_status():
    """API endpoint to get server status."""
    servers = get_server_status()
    return jsonify(servers)

@bp.route('/api/start/<int:port>')
def api_start_server(port):
    """Start a specific server."""
    if port not in SERVERS:
        return jsonify({'error': 'Invalid port'}), 400
    
    server = SERVERS[port]
    try:
        # Stop any existing process on the port
        subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True)
        subprocess.run(['pkill', '-f', f'python.*{port}'], capture_output=True)
        
        # Start the server
        cmd = f"cd {server['path']} && nohup {server['start_cmd']} > app.log 2>&1 &"
        subprocess.run(cmd, shell=True, cwd=server['path'])
        
        return jsonify({'success': True, 'message': f'Started {server["name"]} on port {port}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/stop/<int:port>')
def api_stop_server(port):
    """Stop a specific server."""
    if port not in SERVERS:
        return jsonify({'error': 'Invalid port'}), 400
    
    try:
        # Find and kill processes on the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(['kill', '-9', pid])
        
        return jsonify({'success': True, 'message': f'Stopped server on port {port}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/restart-all')
def api_restart_all():
    """Restart all servers using the restart script."""
    try:
        script_path = '/Users/nickfiddes/Code/projects/restart_projects.sh'
        subprocess.run(['bash', script_path], cwd='/Users/nickfiddes/Code/projects')
        return jsonify({'success': True, 'message': 'Restarting all servers...'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/stop-all')
def api_stop_all():
    """Stop all servers."""
    try:
        for port in SERVERS:
            subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True)
            subprocess.run(['pkill', '-f', f'python.*{port}'], capture_output=True)
        
        return jsonify({'success': True, 'message': 'Stopped all servers'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500