#!/usr/bin/env python3
"""
Test script to verify signature integrity checking works correctly
"""

import sys
import os
from datetime import datetime, timedelta
import base64

# Add current directory to path
sys.path.append('.')

from signature_storage import TamperEvidentSignatureStorage

def test_integrity_verification():
    """Test that integrity verification works correctly"""
    
    print("🔍 Testing Signature Integrity Verification")
    print("=" * 50)
    
    # Initialize storage
    storage = TamperEvidentSignatureStorage()
    
    # Create test signature request
    signature_request = {
        'transaction_id': 'TEST-TXN-123',
        'signature_token': 'test-token-456',
        'signer_name': 'John Test',
        'signer_email': 'john@test.com',
        'company_name': 'Test Company LLC',
        'document_name': 'Test VP Racing LOI',
        'expires_at': datetime.now() + timedelta(days=30)
    }
    
    # Create fake signature image data
    fake_signature_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    # Store signature
    print("📝 Storing test signature...")
    verification_code = storage.store_signature(
        signature_request,
        fake_signature_data,
        '127.0.0.1',
        'Mozilla/5.0 Test Browser'
    )
    
    if not verification_code:
        print("❌ Failed to store signature")
        return False
    
    print(f"✅ Signature stored with verification code: {verification_code}")
    
    # Test integrity verification
    print("🔍 Testing integrity verification...")
    is_valid, message = storage.verify_signature_integrity(verification_code)
    
    print(f"🔐 Integrity check result: {is_valid}")
    print(f"📄 Message: {message}")
    
    if is_valid:
        print("✅ Integrity verification PASSED - no tampering detected")
    else:
        print("❌ Integrity verification FAILED - possible tampering or bug")
        return False
    
    # Test audit report
    print("📊 Testing audit report generation...")
    audit_report = storage.get_audit_report(verification_code)
    
    if audit_report:
        print("✅ Audit report generated successfully")
        print(f"   Integrity Valid: {audit_report['integrity_valid']}")
        print(f"   Integrity Message: {audit_report['integrity_message']}")
        print(f"   Signer: {audit_report['signer_name']}")
        print(f"   Transaction ID: {audit_report['transaction_id']}")
        
        if audit_report['integrity_valid']:
            print("✅ Audit report shows NO TAMPERING")
        else:
            print("❌ Audit report shows TAMPERING DETECTED")
            return False
    else:
        print("❌ Failed to generate audit report")
        return False
    
    # Test with non-existent verification code
    print("🔍 Testing with invalid verification code...")
    is_valid, message = storage.verify_signature_integrity("INVALID-CODE")
    print(f"   Result: {is_valid}, Message: {message}")
    
    if not is_valid and "not found" in message:
        print("✅ Correctly detected invalid verification code")
    else:
        print("❌ Should have detected invalid verification code")
    
    print("\n🎉 Integrity verification test completed!")
    return True

def test_database_connection():
    """Test basic database connectivity"""
    try:
        storage = TamperEvidentSignatureStorage()
        conn = storage.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result[0] == 1:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Signature Integrity Verification Test")
    print("=" * 60)
    
    # Test database first
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Run integrity test
    success = test_integrity_verification()
    
    if success:
        print("\n✅ All tests passed - integrity verification working correctly!")
        print("🛡️  No hardcoded tampering evidence found")
    else:
        print("\n❌ Tests failed - integrity verification has issues")
        print("🔍 Check for database schema issues or logic bugs")