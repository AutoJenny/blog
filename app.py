from flask import Flask, render_template
from dotenv import load_dotenv
from modules.nav import bp as workflow_nav_bp

def create_app():
    app = Flask(__name__, 
                template_folder='modules/nav/templates',
                static_folder='modules/nav/static')
    app.config['SECRET_KEY'] = 'dev'

    # Register blueprints
    app.register_blueprint(workflow_nav_bp)

    # Test route to view navigation
    @app.route('/test')
    def test():
        # Mock data that would normally come from the database
        context = {
            'current_stage': 'planning',
            'current_substage': 'idea',
            'current_step': 'basic_idea',
            'post_id': 1,
            'all_posts': [
                {'id': 1, 'title': 'Test Post 1'},
                {'id': 2, 'title': 'Test Post 2'},
            ]
        }
        return render_template('test.html', **context)

    return app

if __name__ == '__main__':
    load_dotenv()
    app = create_app()
    app.run(debug=True, port=5000)