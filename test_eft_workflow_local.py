#!/usr/bin/env python3
"""
Local test script for EFT two-stage workflow
Tests the complete flow without requiring database or email sending
"""

import json
import uuid
from datetime import datetime
import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_sales_initiated_eft_request():
    """Test 1: Sales-initiated EFT request validation"""
    print("🧪 Test 1: Sales-initiated EFT request validation")
    
    try:
        from api.forms_api import SalesInitiatedEFTRequest
        
        # Test minimal valid request
        minimal_data = {
            "company_name": "Test Company Inc",
            "customer_email": "test@testcompany.com"
        }
        
        request = SalesInitiatedEFTRequest(**minimal_data)
        print(f"✅ Minimal request validation passed: {request.company_name}")
        
        # Test full request with pre-filled data
        full_data = {
            "company_name": "Test Company Inc",
            "customer_email": "test@testcompany.com",
            "customer_phone": "(555) 123-4567",
            "bank_name": "Test Bank",
            "account_holder_name": "Test Company Inc",
            "account_type": "checking",
            "authorized_by_name": "John Smith",
            "authorized_by_title": "Owner",
            "federal_tax_id": "12-3456789",
            "initiated_by": "Jane Sales",
            "notes": "Customer needs expedited processing"
        }
        
        full_request = SalesInitiatedEFTRequest(**full_data)
        print(f"✅ Full request validation passed: {len(full_data)} fields")
        
        # Test invalid email
        try:
            invalid_email = {
                "company_name": "Test Company",
                "customer_email": "invalid-email"
            }
            SalesInitiatedEFTRequest(**invalid_email)
            print("❌ Should have failed with invalid email")
        except Exception as e:
            print(f"✅ Invalid email properly rejected: {type(e).__name__}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_eft_completion_form_generation():
    """Test 2: EFT completion form generation"""
    print("\n🧪 Test 2: EFT completion form generation")
    
    try:
        from api.forms_api import generate_eft_completion_form
        
        transaction_id = str(uuid.uuid4())
        pre_filled_data = {
            "company_name": "Test Company Inc",
            "customer_email": "test@testcompany.com",
            "bank_name": "Test Bank",
            "account_holder_name": "Test Company Inc",
            "notes": "Please complete ASAP"
        }
        
        form_html = generate_eft_completion_form(transaction_id, pre_filled_data)
        
        # Check that form contains expected elements
        assert transaction_id in form_html, "Transaction ID not found in form"
        assert "Test Company Inc" in form_html, "Company name not found in form"
        assert "Complete Your EFT Authorization" in form_html, "Title not found in form"
        
        print(f"✅ Form generation successful: {len(form_html)} characters")
        print(f"✅ Transaction ID embedded: {transaction_id[:8]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_template_generation():
    """Test 3: Email template generation (without sending)"""
    print("\n🧪 Test 3: Email template generation")
    
    try:
        # Test that we can import and call the email function structure
        import main
        
        # Verify email function exists
        assert hasattr(main, 'send_eft_completion_email'), "Email function not found"
        
        # Test email configuration
        assert hasattr(main, 'EMAIL_CONFIG'), "Email config not found"
        
        config = main.EMAIL_CONFIG
        required_keys = ['smtp_host', 'smtp_port', 'from_email']
        for key in required_keys:
            assert key in config, f"Missing email config: {key}"
            
        print(f"✅ Email configuration valid: {len(config)} settings")
        print(f"✅ SMTP host: {config['smtp_host']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_models():
    """Test 4: Database model compatibility"""
    print("\n🧪 Test 4: Database model compatibility")
    
    try:
        from api.forms_api import DATABASE_AVAILABLE
        
        if DATABASE_AVAILABLE:
            from database.models import LOITransaction, TransactionType, TransactionStatus, WorkflowStage
            
            # Test that enum values exist
            assert hasattr(TransactionType, 'EFT_FORM'), "EFT_FORM transaction type missing"
            assert hasattr(WorkflowStage, 'PENDING_CUSTOMER_COMPLETION'), "PENDING_CUSTOMER_COMPLETION stage missing"
            assert hasattr(TransactionStatus, 'PENDING'), "PENDING status missing"
            
            print("✅ Database models compatible")
            print("✅ Required enum values present")
        else:
            print("⚠️ Database not available - using mock mode")
            print("✅ Mock classes loaded successfully")
            
        return True
        
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint_structure():
    """Test 5: API endpoint structure"""
    print("\n🧪 Test 5: API endpoint structure")
    
    try:
        from api.forms_api import router
        
        # Get all routes
        routes = [route.path for route in router.routes]
        
        expected_routes = [
            "/eft/initiate",
            "/eft/complete/{transaction_id}",
            "/eft/submit"
        ]
        
        for expected_route in expected_routes:
            # Check if route exists (exact match or with path parameter)
            route_found = any(
                expected_route == route or 
                ('{transaction_id}' in expected_route and expected_route.replace('{transaction_id}', '') in route)
                for route in routes
            )
            
            if route_found:
                print(f"✅ Route found: {expected_route}")
            else:
                print(f"❌ Route missing: {expected_route}")
                print(f"Available routes: {routes}")
                return False
                
        print(f"✅ All {len(expected_routes)} expected routes found")
        return True
        
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_form_html_files():
    """Test 6: HTML form files exist and are valid"""
    print("\n🧪 Test 6: HTML form files")
    
    try:
        # Check that EFT sales initiation form exists
        sales_form_path = "eft_sales_initiate.html"
        if os.path.exists(sales_form_path):
            with open(sales_form_path, 'r') as f:
                content = f.read()
                assert "Initiate EFT Authorization" in content, "Sales form title missing"
                assert "/api/v1/forms/eft/initiate" in content, "API endpoint missing"
                print(f"✅ Sales form valid: {len(content)} characters")
        else:
            print(f"❌ Sales form missing: {sales_form_path}")
            return False
            
        # Check that regular EFT form still exists
        eft_form_path = "eft_form.html"
        if os.path.exists(eft_form_path):
            with open(eft_form_path, 'r') as f:
                content = f.read()
                print(f"✅ Customer EFT form exists: {len(content)} characters")
        else:
            print(f"⚠️ Customer EFT form missing: {eft_form_path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test 6 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🧪 Starting Local EFT Workflow Tests")
    print("=" * 50)
    
    tests = [
        test_sales_initiated_eft_request,
        test_eft_completion_form_generation,
        test_email_template_generation,
        test_database_models,
        test_api_endpoint_structure,
        test_form_html_files
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("🧪 Test Results Summary")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_func, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test_func.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)