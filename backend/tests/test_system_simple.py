"""
Simple system endpoint test
Tests individual endpoints one at a time
"""
import sys
import os
import requests
import time
import subprocess
import signal

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_with_curl():
    """Test endpoints using curl commands"""
    print("Testing System API Endpoints with curl")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    print("1. Testing /api/status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            # Verify Next.js format
            if all(key in data for key in ["status", "user", "llm_configured"]):
                if data["status"] == "operational":
                    print("✅ /api/status endpoint matches Next.js format")
                    status_passed = True
                else:
                    print("❌ Status field incorrect")
                    status_passed = False
            else:
                print("❌ Response format doesn't match Next.js")
                status_passed = False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            status_passed = False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        status_passed = False
    
    print()
    
    print("2. Testing /api/init endpoint...")
    try:
        user_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = requests.post(f"{base_url}/api/init", json=user_data, timeout=10)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            # Verify Next.js format
            if "message" in data and "user" in data:
                if data["message"] in ["User created", "User already initialized"]:
                    print("✅ /api/init endpoint matches Next.js format")
                    init_passed = True
                else:
                    print("❌ Message field incorrect")
                    init_passed = False
            else:
                print("❌ Response format doesn't match Next.js")
                init_passed = False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            init_passed = False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        init_passed = False
    
    print()
    
    print("3. Testing /api/status after init...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            # Should now have user data
            if data["status"] == "operational":
                print("✅ /api/status still working after init")
                status_after_passed = True
            else:
                print("❌ Status changed unexpectedly")
                status_after_passed = False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            status_after_passed = False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        status_after_passed = False
    
    print()
    print("=" * 50)
    
    total_tests = 3
    passed_tests = sum([status_passed, init_passed, status_after_passed])
    
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All system endpoint tests passed!")
        print("✅ FastAPI system endpoints match Next.js behavior")
        return True
    else:
        print("❌ Some tests failed")
        return False

def check_server_running():
    """Check if FastAPI server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("System Endpoint Testing")
    print("Checking if FastAPI server is running on port 8000...")
    
    if check_server_running():
        print("✓ Server is running")
        success = test_with_curl()
    else:
        print("❌ Server is not running on port 8000")
        print("Please start the server with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        success = False
    
    exit(0 if success else 1)