#!/usr/bin/env python3
"""
AI Checkout Automation - Backend Test Script
Tests the local Python Flask server to ensure it's working correctly
"""

import requests
import json
import sys
import time

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_TIMEOUT = 10

def test_health_endpoint():
    """Test the health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_form_analysis_endpoint():
    """Test the form analysis endpoint"""
    print("\nTesting form analysis endpoint...")
    
    test_data = {
        "form_data": {
            "url": "https://example-store.com/checkout",
            "page_title": "Checkout - Example Store",
            "form_fields": [
                {"id": "email", "type": "email", "name": "email", "required": True},
                {"id": "first_name", "type": "text", "name": "first_name", "required": True},
                {"id": "last_name", "type": "text", "name": "last_name", "required": True}
            ]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-form", 
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Form analysis passed: Found {len(data.get('form_fields', []))} fields")
            return True
        else:
            print(f"❌ Form analysis failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Form analysis failed: {e}")
        return False

def test_checkout_processing_endpoint():
    """Test the checkout processing endpoint"""
    print("\nTesting checkout processing endpoint...")
    
    test_data = {
        "form_data": {
            "url": "https://example-store.com/checkout",
            "page_title": "Checkout - Example Store",
            "form_fields": [
                {"id": "email", "type": "email", "name": "email", "required": True},
                {"id": "shipping_name", "type": "text", "name": "shipping_name", "required": True},
                {"id": "card_number", "type": "text", "name": "card_number", "required": True}
            ]
        },
        "user_profile": {
            "name": "Test User",
            "email": "test@example.com",
            "address": "123 Test St",
            "city": "Test City",
            "state": "CA",
            "zip": "12345",
            "country": "US",
            "card_number": "4111111111111111",
            "card_expiry": "12/25",
            "card_cvv": "123"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/process-checkout", 
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            actions = data.get('actions', [])
            print(f"✅ Checkout processing passed: Generated {len(actions)} actions")
            
            # Show first few actions as example
            if actions:
                print("Sample actions:")
                for i, action in enumerate(actions[:3]):
                    print(f"  {i+1}. {action.get('description', 'No description')}")
            
            return True
        else:
            print(f"❌ Checkout processing failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Checkout processing failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI Checkout Automation - Backend Test Suite")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        test_health_endpoint,
        test_form_analysis_endpoint,
        test_checkout_processing_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Python backend is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the server logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
