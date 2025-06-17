from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def llm_actions():
    return render_template('llm_actions.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000) 