#!/usr/bin/env python3
"""
Simple test for EFT form initiation endpoint
"""

import requests
import json

def test_eft_initiate():
    """Test the EFT form initiation endpoint"""
    
    url = "https://loi-automation-api.onrender.com/api/v1/forms/eft/initiate"
    
    # Test data
    payload = {
        "company_name": "Test Company LLC",
        "customer_email": "transaction.coordinator.agent@gmail.com",
        "customer_phone": "(555) 123-4567",
        "federal_tax_id": "12-3456789",
        "bank_name": "First National Bank",
        "authorized_by_name": "John Doe",
        "authorized_by_title": "CFO",
        "initiated_by": "Sales Team"
    }
    
    print(f"🔄 Testing EFT initiate endpoint...")
    print(f"📍 URL: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📨 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS! Response:")
            print(json.dumps(result, indent=2))
            
            if result.get('transaction_id'):
                print(f"\n🎉 Transaction ID: {result['transaction_id']}")
                print(f"📧 Email sent to: {result.get('customer_email')}")
                print(f"🔗 Form URL: {result.get('form_url')}")
        else:
            print(f"\n❌ ERROR Response:")
            try:
                error_detail = response.json()
                print(json.dumps(error_detail, indent=2))
            except:
                print(response.text)
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_eft_initiate()