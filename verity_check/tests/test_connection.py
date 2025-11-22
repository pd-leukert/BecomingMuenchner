import requests
import json
import sys

def test_connection():
    url = "http://localhost:8000/v1/chat/completions"
    model = "Qwen/Qwen2-VL-7B-Instruct"
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Hello, are you ready to process documents?"
            }
        ],
        "max_tokens": 50
    }
    
    print(f"📡 Testing connection to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"✅ Connection Successful!")
        print(f"🤖 Model Response: {content}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is 'serve.sh' running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
