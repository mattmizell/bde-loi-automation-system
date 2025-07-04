#!/usr/bin/env python3
"""
Debug P66 backend submission issue
Investigate why form submission returns intro message instead of processing
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://loi-automation-api.onrender.com"

# Test data that matches what the form sends
test_data = {
    "loi_type": "phillips_66",
    "fuel_brand": "Phillips 66",
    "station_name": "Claude's Test Phillips 66",
    "station_address": "123 Test Station Drive",
    "station_city": "St. Louis", 
    "station_state": "MO",
    "station_zip": "63101",
    "monthly_gasoline_gallons": "50000",
    "monthly_diesel_gallons": "20000",
    "current_brand": "Independent",
    "brand_expiration_date": "2025-12-31",
    "contract_start_date": "2025-08-01",
    "contract_term_years": "10",
    "volume_incentive_requested": "25000",
    "image_funding_requested": "15000",
    "equipment_funding_requested": "10000",
    "canopy_replacement": True,
    "dispenser_replacement": True,
    "special_requirements": "Debug test submission",
    "authorized_representative": "Claude Test Manager",
    "representative_title": "General Manager",
    "email": "transaction.coordinator.agent@gmail.com",
    "phone": "(555) 123-TEST"
}

def test_p66_api_directly():
    """Test P66 LOI API endpoint directly"""
    print("🔍 DEBUGGING P66 BACKEND API")
    print("=" * 60)
    
    endpoint = f"{BASE_URL}/api/v1/loi/submit"
    print(f"🎯 Testing endpoint: {endpoint}")
    print(f"📋 Payload: {json.dumps(test_data, indent=2)}")
    
    try:
        # Send POST request
        response = requests.post(
            endpoint,
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"📄 Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"📄 Response Text: {response.text}")
            
        if response.status_code == 200:
            print("✅ API call successful")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_form_submission_path():
    """Test the exact path a browser form submission would take"""
    print("\n🌐 TESTING BROWSER FORM SUBMISSION PATH")
    print("=" * 60)
    
    # Test if the form endpoint exists
    form_url = f"{BASE_URL}/p66_loi_form.html"
    print(f"📄 Testing form page: {form_url}")
    
    try:
        response = requests.get(form_url)
        print(f"📊 Form page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ P66 form page accessible")
            
            # Check if the form has the correct action attribute
            content = response.text
            if '/api/v1/loi/submit' in content:
                print("✅ Form has correct action URL")
            else:
                print("❌ Form action URL not found or incorrect")
                
            # Check for JavaScript form submission handling
            if 'addEventListener' in content and 'submit' in content:
                print("✅ JavaScript form submission handler found")
            else:
                print("❌ JavaScript form submission handler missing")
                
        else:
            print(f"❌ Form page not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing form page: {str(e)}")

def check_backend_logs():
    """Check if we can get any backend log information"""
    print("\n📊 CHECKING BACKEND STATUS")
    print("=" * 60)
    
    # Test root endpoint
    try:
        response = requests.get(BASE_URL)
        print(f"🏠 Root endpoint status: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {str(e)}")
        
    # Test API health
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"🏥 Health endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"📄 Health response: {response.text}")
    except Exception as e:
        print(f"⚠️ Health endpoint not available: {str(e)}")

def simulate_browser_request():
    """Simulate exact browser request with all headers"""
    print("\n🌐 SIMULATING EXACT BROWSER REQUEST")
    print("=" * 60)
    
    # Headers that a browser would send
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/p66_loi_form.html",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    endpoint = f"{BASE_URL}/api/v1/loi/submit"
    
    try:
        response = requests.post(
            endpoint,
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Browser simulation status: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                if "transaction_id" in json_response:
                    print(f"✅ Success! Transaction ID: {json_response['transaction_id']}")
                else:
                    print(f"⚠️ Response missing transaction_id: {json_response}")
            except:
                print(f"⚠️ Non-JSON response: {response.text}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Browser simulation failed: {str(e)}")

def main():
    """Run all debugging tests"""
    print(f"🚀 P66 BACKEND DEBUG SESSION - {datetime.now()}")
    print("=" * 80)
    
    test_form_submission_path()
    test_p66_api_directly()
    simulate_browser_request()
    check_backend_logs()
    
    print("\n" + "=" * 80)
    print("🏁 DEBUG SESSION COMPLETE")

if __name__ == "__main__":
    main()