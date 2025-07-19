from flask import Flask

app = Flask(__name__)

@app.route('/')
def test_page():
    return "Blog Core Test Page - Port 5000"

if __name__ == '__main__':
    app.run(port=5000, debug=True) 