import requests
import json

def test_auth():
    url = "http://127.0.0.1:8001/api/token/"
    data = {
        "username": "heist",
        "password": "1234567vampire"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"Token received: {token_data.get('token', 'No token in response')}")
            return token_data.get('token')
        else:
            print("Authentication failed!")
            return None
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server!")
        print("Make sure server is running on http://127.0.0.1:8001/")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_auth() 