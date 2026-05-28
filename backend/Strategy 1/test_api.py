import requests
import json
import time

API_URL = "http://localhost:8000/query"

def test_user(user_name, prompt):
    print(f"\n--- Testing for User: {user_name} ---")
    print(f"Prompt: {prompt}")
    payload = {
        "user_name": user_name,
        "user_prompt": prompt
    }
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['response']}")
            print(f"Sources: {data['sources']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    # Wait for server to start if run in same script, but we'll run it separately
    print("Starting tests. Ensure the FastAPI server is running.")
    
    # Test 1: Monish (Access to both)
    test_user("monish", "What is the main topic of the presentation?")
    test_user("monish", "What are Monish's skills?")
    
    # Test 2: Bob (Access to only presentation)
    test_user("bob", "What is the main topic of the presentation?")
    test_user("bob", "What are Monish's skills?")
    
    # Test 3: Guest (Access to nothing)
    test_user("guest", "Tell me about everything.")
