#!/usr/bin/env python3
"""
Test signature workflow as end user
Simulate receiving email and clicking signature link
"""

import requests
import time
from datetime import datetime

BASE_URL = "https://loi-automation-api.onrender.com"

# Transaction IDs from recent tests
TRANSACTION_IDS = [
    "55071680-be2f-40dc-88b9-6e3e9c439b2e",  # Customer Setup
    "10e884f9-c69f-4d2a-a865-84985dcefdc1"   # EFT Sales
]

def test_signature_page(transaction_id):
    """Test signature page loading and functionality"""
    print(f"\n{'='*50}")
    print(f"🔗 Testing Signature Page: {transaction_id}")
    
    signature_url = f"{BASE_URL}/api/v1/loi/sign/{transaction_id}"
    print(f"📄 URL: {signature_url}")
    
    try:
        response = requests.get(signature_url, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ Page loaded successfully ({len(content)} characters)")
            
            # Check for key elements
            if "signature" in content.lower():
                print("✅ Signature elements found")
            if "esign" in content.lower():
                print("✅ ESIGN compliance found")
            if "canvas" in content.lower():
                print("✅ Canvas element found")
            if "submit" in content.lower():
                print("✅ Submit button found")
                
            return True
            
        elif response.status_code == 404:
            print("❌ Transaction not found (404)")
            return False
            
        elif response.status_code == 500:
            print("❌ Server error (500)")
            print(f"📋 Response: {response.text[:200]}")
            return False
            
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def check_transaction_status(transaction_id):
    """Check transaction status in database"""
    print(f"\n🔍 Checking transaction status: {transaction_id}")
    
    status_url = f"{BASE_URL}/api/v1/loi/status/{transaction_id}"
    
    try:
        response = requests.get(status_url, timeout=10)
        print(f"📊 Status Check Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Transaction Status: {data}")
            return data
        else:
            print(f"❌ Status check failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Status check error: {str(e)}")
        return None

def test_email_generation():
    """Test if signature emails are being generated properly"""
    print(f"\n📧 Testing Email Generation Process")
    
    # Check if there's an admin endpoint to view sent emails
    admin_urls = [
        f"{BASE_URL}/api/v1/admin/loi/list",
        f"{BASE_URL}/api/v1/admin/emails",
        f"{BASE_URL}/admin/transactions"
    ]
    
    for url in admin_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Admin endpoint available: {url}")
                content = response.text[:300]
                print(f"📋 Preview: {content}...")
                return url
        except:
            pass
    
    print("⚠️ No admin endpoints accessible")
    return None

def main():
    """Main test execution"""
    print(f"🚀 Starting Signature Workflow Test")
    print(f"🌐 Target: {BASE_URL}")
    print(f"📧 Email: transaction.coordinator.agent@gmail.com")
    print(f"⏰ Time: {datetime.now()}")
    
    # Test email generation process
    test_email_generation()
    
    # Test each transaction signature page
    for transaction_id in TRANSACTION_IDS:
        # Check transaction status first
        status = check_transaction_status(transaction_id)
        
        # Test signature page
        signature_works = test_signature_page(transaction_id)
        
        print(f"📊 Summary for {transaction_id[:8]}...")
        print(f"   Status Check: {'✅' if status else '❌'}")
        print(f"   Signature Page: {'✅' if signature_works else '❌'}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Check transaction.coordinator.agent@gmail.com inbox")
    print(f"   2. Look for signature links in recent emails")
    print(f"   3. Test signature completion workflow")
    print(f"   4. Verify ESIGN compliance requirements")

if __name__ == "__main__":
    main()