#!/usr/bin/env python3
"""
AI Checkout Automation - Complete Integration Test
Tests the entire system end-to-end to ensure everything works together
"""

import requests
import json
import sys
import time
import subprocess
import threading
import webbrowser
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"
TEST_TIMEOUT = 15
SERVER_START_TIMEOUT = 30

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a test step"""
    print(f"\n[{step}] {description}")

def check_server_running():
    """Check if the Flask server is already running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_server(timeout=SERVER_START_TIMEOUT):
    """Wait for server to become available"""
    print(f"   Waiting for server to start (max {timeout}s)...")
    
    for i in range(timeout):
        if check_server_running():
            print(f"   ✅ Server is running after {i+1}s")
            return True
        time.sleep(1)
        if i % 5 == 4:  # Print progress every 5 seconds
            print(f"   Still waiting... ({i+1}s)")
    
    return False

def test_complete_checkout_flow():
    """Test a complete checkout automation flow"""
    print_step("4", "Testing complete checkout automation flow")
    
    # Simulate a realistic checkout form
    test_form_data = {
        "form_data": {
            "url": "https://demo-store.example.com/checkout",
            "page_title": "Checkout - Demo Store",
            "form_fields": [
                {"id": "email", "type": "email", "name": "email", "required": True, "placeholder": "Enter your email"},
                {"id": "first_name", "type": "text", "name": "first_name", "required": True, "placeholder": "First name"},
                {"id": "last_name", "type": "text", "name": "last_name", "required": True, "placeholder": "Last name"},
                {"id": "address1", "type": "text", "name": "address1", "required": True, "placeholder": "Street address"},
                {"id": "city", "type": "text", "name": "city", "required": True, "placeholder": "City"},
                {"id": "state", "type": "text", "name": "state", "required": True, "placeholder": "State"},
                {"id": "zip", "type": "text", "name": "zip", "required": True, "placeholder": "ZIP code"},
                {"id": "card_number", "type": "text", "name": "card_number", "required": True, "placeholder": "Card number"},
                {"id": "card_expiry", "type": "text", "name": "card_expiry", "required": True, "placeholder": "MM/YY"},
                {"id": "card_cvv", "type": "password", "name": "card_cvv", "required": True, "placeholder": "CVV"}
            ]
        },
        "user_profile": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "address": "123 Main Street",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
            "country": "US",
            "card_number": "4111111111111111",
            "card_expiry": "12/25",
            "card_cvv": "123"
        }
    }
    
    try:
        print("   Sending realistic checkout form for processing...")
        response = requests.post(
            f"{BASE_URL}/process-checkout",
            json=test_form_data,
            headers={'Content-Type': 'application/json'},
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            actions = result.get('actions', [])
            
            print(f"   ✅ Checkout processing successful!")
            print(f"   📊 Generated {len(actions)} form filling actions")
            
            # Validate the response structure
            if 'strategy_summary' in result:
                print(f"   📋 Strategy: {result['strategy_summary'][:100]}...")
            
            # Show some sample actions
            if actions:
                print(f"   🎯 Sample actions:")
                for i, action in enumerate(actions[:5]):  # Show first 5 actions
                    element_id = action.get('element_id', 'unknown')
                    action_type = action.get('action_type', 'unknown')
                    value = action.get('value', 'unknown')
                    print(f"      {i+1}. {element_id} -> {action_type}: {value}")
                
                if len(actions) > 5:
                    print(f"      ... and {len(actions) - 5} more actions")
            
            # Validate that key fields are filled
            filled_fields = {action.get('element_id') for action in actions}
            expected_fields = {'email', 'first_name', 'last_name', 'address1', 'card_number'}
            missing_fields = expected_fields - filled_fields
            
            if missing_fields:
                print(f"   ⚠️  Warning: Some expected fields not filled: {missing_fields}")
            else:
                print(f"   ✅ All critical fields covered by automation")
            
            return True
            
        else:
            print(f"   ❌ Request failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during checkout flow test: {e}")
        return False

def test_browser_extension_compatibility():
    """Test browser extension compatibility"""
    print_step("5", "Testing browser extension compatibility")
    
    # Test CORS headers
    try:
        print("   Testing CORS headers...")
        response = requests.options(f"{BASE_URL}/process-checkout")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        if cors_headers['Access-Control-Allow-Origin']:
            print(f"   ✅ CORS properly configured")
            return True
        else:
            print(f"   ❌ CORS headers missing")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing CORS: {e}")
        return False

def open_test_browser():
    """Open browser to test the extension"""
    print_step("6", "Opening browser for manual extension test")
    
    test_urls = [
        "https://demo.stripe.com/",
        "https://checkout.stripe.com/",
        "chrome://extensions/"
    ]
    
    print("   🌐 Opening test URLs in browser...")
    print("   You can now test the extension manually on these pages:")
    
    for url in test_urls:
        print(f"      - {url}")
        try:
            webbrowser.open(url)
            time.sleep(1)  # Brief delay between openings
        except:
            print(f"        (Failed to auto-open {url})")
    
    print("\n   📝 Manual testing checklist:")
    print("      1. Ensure the extension is loaded in chrome://extensions/")
    print("      2. Navigate to a checkout page")
    print("      3. Click the extension icon")
    print("      4. Check that backend status shows '✅ Python backend running'")
    print("      5. Try the 'Automate Current Page' button")
    
    return True

def main():
    """Run the complete integration test suite"""
    print_header("🚀 AI Checkout Automation - Complete Integration Test")
    
    # Test summary
    tests_run = 0
    tests_passed = 0
    
    # Check if server is already running
    print_step("1", "Checking if Python backend is running")
    
    if check_server_running():
        print("   ✅ Server is already running")
        tests_passed += 1
    else:
        print("   ❌ Server is not running")
        print("   💡 Please start the server with: start_server.bat")
        print("   Then run this test again.")
        return 1
    
    tests_run += 1
    
    # Test health endpoint
    print_step("2", "Testing health endpoint")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TEST_TIMEOUT)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check passed: {health_data.get('status', 'OK')}")
            tests_passed += 1
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    tests_run += 1
    
    # Test form analysis endpoint
    print_step("3", "Testing form analysis endpoint")
    simple_form = {
        "form_data": {
            "url": "https://test.com/checkout",
            "form_fields": [
                {"id": "email", "type": "email", "required": True}
            ]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analyze-form", json=simple_form, timeout=TEST_TIMEOUT)
        if response.status_code == 200:
            print(f"   ✅ Form analysis working")
            tests_passed += 1
        else:
            print(f"   ❌ Form analysis failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Form analysis error: {e}")
    
    tests_run += 1
    
    # Test complete checkout flow
    if test_complete_checkout_flow():
        tests_passed += 1
    tests_run += 1
    
    # Test browser extension compatibility
    if test_browser_extension_compatibility():
        tests_passed += 1
    tests_run += 1
    
    # Open browser for manual testing
    if open_test_browser():
        tests_passed += 1
    tests_run += 1
    
    # Final results
    print_header("📊 Test Results Summary")
    print(f"Tests Run: {tests_run}")
    print(f"Tests Passed: {tests_passed}")
    print(f"Success Rate: {(tests_passed/tests_run)*100:.1f}%")
    
    if tests_passed == tests_run:
        print("\n🎉 All tests passed! Your AI Checkout Automation is ready to use!")
        print("\n📋 Next steps:")
        print("   1. Install the browser extension (if not already done)")
        print("   2. Test on real checkout pages")
        print("   3. Configure your personal profile in the extension")
        return 0
    else:
        print(f"\n⚠️  {tests_run - tests_passed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
