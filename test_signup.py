import requests
import json

url = "http://localhost:8000/api/auth/signup"
data = {
    "full_name": "Test User",
    "email": "testuser123@example.com",
    "password": "test123",
    "phone_number": "+251912345678",
    "location": "Addis Ababa",
    "age": 25,
    "sex": "Male"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
