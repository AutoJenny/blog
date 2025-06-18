from flask import Flask, render_template
import os

app = Flask(__name__, 
           template_folder='app/templates',
           static_folder='app/static')

# Register the nav module templates
from modules.nav import bp as nav_bp
app.register_blueprint(nav_bp)

@app.route("/")
def index():
    # Provide context variables for the navigation
    context = {
        'current_stage': 'planning',
        'current_substage': 'idea',
        'current_step': 'basic_idea',
        'post_id': 1,
        'all_posts': [
            {'id': 1, 'title': 'Sample Post'},
            {'id': 2, 'title': 'Another Post'}
        ]
    }
    return render_template("main/index.html", **context)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)