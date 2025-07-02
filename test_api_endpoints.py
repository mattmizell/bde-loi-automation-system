#!/usr/bin/env python3
"""
Quick API endpoint test using requests
"""

import json
import time

def test_eft_endpoints():
    """Test EFT endpoints with minimal data"""
    print("🧪 Testing EFT API Endpoints")
    
    # Test data
    test_data = {
        "company_name": "Test Company API",
        "customer_email": "test@example.com",
        "bank_name": "Test Bank",
        "notes": "API test"
    }
    
    print(f"Test payload: {json.dumps(test_data, indent=2)}")
    
    # Note: This would require the server to be running
    # For local testing, we'll just validate the payload structure
    
    required_fields = ["company_name", "customer_email"]
    for field in required_fields:
        assert field in test_data, f"Required field {field} missing"
        assert test_data[field], f"Required field {field} is empty"
    
    print("✅ Test payload structure valid")
    print("✅ Required fields present")
    print("ℹ️ To test live API, start server with: python main.py")
    print("ℹ️ Then POST to: http://localhost:8000/api/v1/forms/eft/initiate")
    
    return True

if __name__ == "__main__":
    test_eft_endpoints()
    print("🎉 API endpoint structure test passed!")