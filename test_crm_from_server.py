#!/usr/bin/env python3
"""
Test CRM API directly from server to check if LACRM blocks server requests
"""

import requests
import json

def test_crm_api():
    """Test CRM API call from server"""
    
    api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
    search_url = "https://api.lessannoyingcrm.com"
    
    # Test payload
    search_payload = {
        "UserCode": api_key,
        "Function": "SearchContacts",
        "Parameters": {
            "SearchTerm": "Adam"
        }
    }
    
    print("🧪 Testing CRM API from server...")
    print(f"🔗 URL: {search_url}")
    print(f"📤 Payload: {search_payload}")
    
    try:
        # Test 1: Simple request
        print("\n1️⃣ Testing basic request...")
        response = requests.post(search_url, json=search_payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        # Test 2: With browser headers
        print("\n2️⃣ Testing with browser headers...")
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*'
        }
        
        response2 = requests.post(search_url, json=search_payload, headers=headers, timeout=10)
        print(f"Status: {response2.status_code}")
        print(f"Response: {response2.text[:200]}...")
        
        # Test 3: Try the working format from check_crm_record.py
        print("\n3️⃣ Testing working format...")
        working_headers = {
            "Content-Type": "application/json",
            "Authorization": api_key
        }
        
        working_payload = {
            "Function": "SearchContacts",
            "Parameters": {
                "SearchTerm": "Adam"
            }
        }
        
        response3 = requests.post(search_url, headers=working_headers, json=working_payload, timeout=10)
        print(f"Status: {response3.status_code}")
        print(f"Response: {response3.text[:200]}...")
        
        if response3.status_code == 200:
            try:
                result = json.loads(response3.text)
                print(f"✅ Success! Found {len(result.get('Result', []))} contacts")
                return True
            except:
                print("❌ JSON parsing failed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    test_crm_api()