import requests
import json

def test_allocate_content():
    # Test data
    data = {
        "sections": [
            {
                "id": "1",
                "heading": "Introduction to AI",
                "description": "Overview of artificial intelligence and its basic concepts"
            },
            {
                "id": "2",
                "heading": "Machine Learning Basics",
                "description": "Fundamental principles and types of machine learning"
            },
            {
                "id": "3",
                "heading": "Deep Learning",
                "description": "Neural networks and deep learning architectures"
            }
        ],
        "facts": [
            "Artificial Intelligence was first coined as a term in 1956 at the Dartmouth Conference",
            "Machine learning is a subset of AI that focuses on training algorithms to learn from data",
            "Deep learning uses neural networks with multiple layers to process complex patterns",
            "The first neural network, the Perceptron, was created in 1957",
            "Supervised learning requires labeled training data",
            "Unsupervised learning finds patterns in unlabeled data",
            "Reinforcement learning uses rewards to guide learning",
            "Convolutional Neural Networks are particularly good at image recognition",
            "Recurrent Neural Networks are designed for sequential data",
            "Transfer learning allows models to use knowledge from one task for another"
        ]
    }

    # Make the request
    response = requests.post(
        'http://localhost:5000/api/v1/structure/allocate/22',
        json=data
    )

    # Print the response
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_allocate_content() 