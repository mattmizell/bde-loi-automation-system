#!/usr/bin/env python3
"""
Test production LOI generation for Farley Barnhart
"""

import requests
import json
import uuid
from datetime import datetime, timedelta

# Production server URL
PRODUCTION_URL = "https://loi-automation-api.onrender.com"

def test_production_loi():
    """Generate new LOI request for Farley in production"""
    
    # Generate new signature request data
    signature_token = str(uuid.uuid4())
    transaction_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"
    
    loi_data = {
        "transaction_id": transaction_id,
        "signature_token": signature_token,
        "signer_name": "Farely Barnhart",
        "signer_email": "matt.mizell@gmail.com",
        "company_name": "Farley's Gas and Go",
        "document_name": "VP Racing Fuel Supply Agreement - Letter of Intent",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
        "loi_details": {
            "fuel_type": "VP Racing Fuel",
            "supplier": "Better Day Energy",
            "customer": "Farley's Gas and Go",
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "pricing": "Market competitive rates",
            "delivery_terms": "Standard delivery schedule",
            "payment_terms": "Net 30 days"
        }
    }
    
    print(f"🚀 Testing Production LOI System")
    print(f"📍 Production URL: {PRODUCTION_URL}")
    print(f"👤 Signer: {loi_data['signer_name']}")
    print(f"🏢 Company: {loi_data['company_name']}")
    print(f"📧 Email: {loi_data['signer_email']}")
    print(f"🔗 Transaction ID: {transaction_id}")
    print(f"🎫 Signature Token: {signature_token}")
    print()
    
    try:
        # Test 1: Check if server is alive
        print("1️⃣ Testing server connectivity...")
        response = requests.get(f"{PRODUCTION_URL}/", timeout=10)
        print(f"   ✅ Server response: {response.status_code}")
        print(f"   📄 Response preview: {response.text[:100]}...")
        print()
        
        # Test 2: Create signature request
        print("2️⃣ Creating signature request...")
        create_response = requests.post(
            f"{PRODUCTION_URL}/create-signature-request",
            json=loi_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   📨 Create request status: {create_response.status_code}")
        if create_response.status_code == 200:
            print(f"   ✅ Signature request created successfully!")
            result = create_response.json()
            print(f"   🔗 Signature URL: {result.get('signature_url', 'Not provided')}")
        else:
            print(f"   ❌ Error creating request: {create_response.text}")
        print()
        
        # Test 3: Send email notification
        print("3️⃣ Sending email notification...")
        email_data = {
            "signature_token": signature_token,
            "signer_name": loi_data["signer_name"],
            "signer_email": loi_data["signer_email"],
            "company_name": loi_data["company_name"],
            "signature_url": f"{PRODUCTION_URL}/sign/{signature_token}"
        }
        
        email_response = requests.post(
            f"{PRODUCTION_URL}/send-signature-email",
            json=email_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   📧 Email send status: {email_response.status_code}")
        if email_response.status_code == 200:
            print(f"   ✅ Email sent successfully to {loi_data['signer_email']}")
        else:
            print(f"   ❌ Error sending email: {email_response.text}")
        print()
        
        # Test 4: Check signature page accessibility
        print("4️⃣ Testing signature page...")
        signature_url = f"{PRODUCTION_URL}/sign/{signature_token}"
        page_response = requests.get(signature_url, timeout=10)
        print(f"   🖊️  Signature page status: {page_response.status_code}")
        if page_response.status_code == 200:
            print(f"   ✅ Signature page accessible")
            print(f"   🔗 Direct link: {signature_url}")
        else:
            print(f"   ❌ Signature page error: {page_response.text}")
        print()
        
        print("🎯 PRODUCTION TEST SUMMARY:")
        print(f"   📧 Email sent to: {loi_data['signer_email']}")
        print(f"   🔗 Signature URL: {signature_url}")
        print(f"   🆔 Transaction ID: {transaction_id}")
        print(f"   ⏰ Expires: {loi_data['expires_at']}")
        print()
        print("✅ Production test completed! Check your email for the LOI signature request.")
        
        return signature_token, transaction_id
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server may be slow to respond")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to production server")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        
    return None, None

if __name__ == "__main__":
    test_production_loi()