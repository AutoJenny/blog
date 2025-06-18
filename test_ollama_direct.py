import requests

payload = {
    "model": "llama3.1:70b",
    "prompt": 'Start every response with "TITLE: NONSENSE". Write entirely in French. Write a short poem. Data for this operation as follows: dog breakfasts',
    "temperature": 0.7,
    "max_tokens": 1000,
    "stream": False
}

response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
print("Status:", response.status_code)
print("Response:", response.json()) 