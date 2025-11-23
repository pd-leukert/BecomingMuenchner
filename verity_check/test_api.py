import httpx
import asyncio
import json
import sys

async def test_api():
    base_url = "http://35.184.144.165:8001"
    
    print(f"🔍 Testing API at {base_url}...")
    
    # 1. Test Health Endpoint
    try:
        print("\n1️⃣  Testing Health Check (GET /)...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return

    # 2. Test Verification Endpoint
    print("\n2️⃣  Testing Verification (POST /check)...")
    payload = {"applicationId": "dummy-123"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"Sending payload: {payload}")
            response = await client.post(f"{base_url}/check", json=payload)
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Success!")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"⚠️  Request returned status {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Verification request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
