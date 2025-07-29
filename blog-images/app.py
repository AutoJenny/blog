#!/usr/bin/env python3
"""
Blog Images - Image Generation and Management Application
"""

import os
from flask import Flask, render_template, request

app = Flask(__name__)

# Configure port
port = int(os.environ.get('PORT', 5005))

@app.route('/')
def index():
    post_id = request.args.get('post_id', '1')
    return render_template('index.html', post_id=post_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port) 