from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/test-llm')
def test_llm():
    payload = {
        "model": "llama3.1:70b",
        "prompt": 'Start every response with "TITLE: NONSENSE". Write entirely in French. Write a short poem. Data for this operation as follows: dog breakfasts',
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }
    r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
    return jsonify(r.json())

if __name__ == '__main__':
    app.run(port=5050) 