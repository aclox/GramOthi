#!/usr/bin/env python3
"""
Simple API testing script for GramOthi backend
Run this after starting the server to test basic functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_health_check():
    """Test health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint."""
    print("🔍 Testing root endpoint...")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint working: {data.get('message', 'Unknown')}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_docs_endpoint():
    """Test API documentation endpoint."""
    print("🔍 Testing API docs...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation accessible")
            return True
        else:
            print(f"❌ API documentation failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API documentation failed: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints."""
    print("🔍 Testing authentication endpoints...")
    
    # Test registration
    test_user = {
        "name": "Test Teacher",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "teacher"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=test_user)
        if response.status_code == 200:
            print("✅ User registration working")
            user_data = response.json()
            user_id = user_data.get('id')
        else:
            print(f"❌ User registration failed: {response.status_code}")
            if response.status_code == 400 and "already registered" in response.text:
                print("   User already exists, continuing with login test")
                user_id = None
            else:
                return False
    except requests.exceptions.RequestException as e:
        print(f"❌ User registration failed: {e}")
        return False
    
    # Test login
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", data=login_data)
        if response.status_code == 200:
            print("✅ User login working")
            token_data = response.json()
            access_token = token_data.get('access_token')
            return access_token
        else:
            print(f"❌ User login failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ User login failed: {e}")
        return False

def test_protected_endpoints(access_token):
    """Test protected endpoints with authentication."""
    print("🔍 Testing protected endpoints...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test getting user info
    try:
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        if response.status_code == 200:
            print("✅ Protected endpoint (me) working")
        else:
            print(f"❌ Protected endpoint (me) failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Protected endpoint (me) failed: {e}")
        return False
    
    # Test creating a class
    class_data = {
        "title": "Test Class - API Testing"
    }
    
    try:
        response = requests.post(f"{API_BASE}/classes/", json=class_data, headers=headers)
        if response.status_code == 200:
            print("✅ Class creation working")
            class_info = response.json()
            class_id = class_info.get('id')
        else:
            print(f"❌ Class creation failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Class creation failed: {e}")
        return False
    
    # Test getting classes
    try:
        response = requests.get(f"{API_BASE}/classes/", headers=headers)
        if response.status_code == 200:
            print("✅ Class listing working")
        else:
            print(f"❌ Class listing failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Class listing failed: {e}")
        return False
    
    return True

def main():
    """Run all API tests."""
    print("🚀 GramOthi API Testing")
    print("=" * 40)
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Server is running")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the server first:")
        print("   ./start.sh")
        print("   or")
        print("   python -m app.main")
        return 1
    
    tests = [
        test_health_check,
        test_root_endpoint,
        test_docs_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Basic Tests: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🔍 Testing authentication and protected endpoints...")
        
        # Test authentication
        access_token = test_auth_endpoints()
        if access_token:
            # Test protected endpoints
            if test_protected_endpoints(access_token):
                print("\n🎉 All API tests passed!")
                print("\n📖 Full API documentation available at:")
                print(f"   {BASE_URL}/docs")
                print(f"\n🔍 Health check: {BASE_URL}/health")
            else:
                print("\n❌ Some protected endpoint tests failed")
                return 1
        else:
            print("\n❌ Authentication tests failed")
            return 1
    else:
        print("\n❌ Some basic tests failed")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
