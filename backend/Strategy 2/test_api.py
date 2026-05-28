import requests
import json

API_URL = "http://localhost:8001/query"

def test_user(user_name, prompt):
    print(f"\n--- Strategy 2: Testing for User: {user_name} ---")
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
    # Test 1: Monish (Access to both)
    test_user("monish", "What are Monish's skills?")
    
    # Test 2: Bob (Access only to presentation)
    test_user("bob", "What are Monish's skills?")
    test_user("bob", "What is the main topic of the presentation?")
    
    # Test 3: Guest (Access to nothing)
    test_user("guest", "Tell me about everything.")
