from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'llm-actions-test'})

@app.route('/test')
def test():
    """Test endpoint."""
    return jsonify({'message': 'Test endpoint working'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True) 