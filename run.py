from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    host = os.getenv('HOST', '127.0.0.1')
    app.run(host=host, port=port, debug=True) 