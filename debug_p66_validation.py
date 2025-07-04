#!/usr/bin/env python3
"""
Debug P66 form validation to see what's preventing submission
"""

from playwright.sync_api import sync_playwright
import time

BASE_URL = "https://loi-automation-api.onrender.com"

TEST_DATA = {
    "company": "Claude's Test Gas Station LLC",
    "contact": "Claude Test Manager", 
    "email": "transaction.coordinator.agent@gmail.com",
    "phone": "(555) 123-TEST",
    "address": "123 Test Station Drive",
    "city": "St. Louis",
    "state": "MO",
    "zip": "63101"
}

def debug_p66_validation():
    """Debug P66 form validation to find what's stopping submission"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("🔍 DEBUGGING P66 FORM VALIDATION")
        print("=" * 60)
        
        try:
            # Navigate to P66 form
            page.goto(f"{BASE_URL}/p66_loi_form.html")
            page.wait_for_load_state('networkidle')
            print(f"📄 Loaded P66 form: {page.url}")
            
            # Fill all fields one by one and check for validation
            print("\n📝 Filling form fields...")
            
            # Station Information
            page.fill('#station-name', "Claude's Test Phillips 66")
            page.fill('#station-address', TEST_DATA["address"])
            page.fill('#station-city', TEST_DATA["city"])
            page.fill('#station-state', TEST_DATA["state"])
            page.fill('#station-zip', TEST_DATA["zip"])
            print("✅ Station info filled")
            
            # Fuel volumes
            page.fill('#gasoline-volume', "50000")
            page.fill('#diesel-volume', "20000")
            page.fill('#current-brand', "Independent")
            page.fill('#brand-expiration', "2025-12-31")
            print("✅ Fuel volumes filled")
            
            # Contract details
            page.fill('#start-date', "2025-08-01")
            page.select_option('#contract-term', "10")
            page.fill('#volume-incentive', "25000")
            page.fill('#image-funding', "15000")
            page.fill('#equipment-funding', "10000")
            print("✅ Contract details filled")
            
            # Equipment checkboxes
            page.check('#canopy')
            page.check('#dispensers')
            print("✅ Equipment options checked")
            
            # Special requirements
            page.fill('#special-requirements', "Debug test: checking validation")
            print("✅ Special requirements filled")
            
            # Contact info
            page.fill('#representative-name', TEST_DATA["contact"])
            page.fill('#representative-title', "General Manager")
            page.fill('#contact-email', TEST_DATA["email"])
            page.fill('#contact-phone', TEST_DATA["phone"])
            print("✅ Contact info filled")
            
            # Check if submit button is enabled
            submit_btn = page.locator('#submit-btn')
            is_enabled = submit_btn.is_enabled()
            is_visible = submit_btn.is_visible()
            print(f"\n🎯 Submit button - Visible: {is_visible}, Enabled: {is_enabled}")
            
            # Check for any validation errors
            validation_errors = page.locator('.invalid-feedback, .error, .alert-danger')
            error_count = validation_errors.count()
            print(f"⚠️ Validation errors found: {error_count}")
            
            if error_count > 0:
                for i in range(error_count):
                    error_text = validation_errors.nth(i).text_content()
                    print(f"  Error {i+1}: {error_text}")
            
            # Check required fields
            required_fields = page.locator('input[required], select[required], textarea[required]')
            required_count = required_fields.count()
            print(f"📋 Required fields: {required_count}")
            
            unfilled_required = []
            for i in range(required_count):
                field = required_fields.nth(i)
                field_id = field.get_attribute('id')
                field_value = field.input_value() if field.get_attribute('type') != 'checkbox' else field.is_checked()
                if not field_value:
                    unfilled_required.append(field_id)
            
            if unfilled_required:
                print(f"❌ Unfilled required fields: {unfilled_required}")
            else:
                print("✅ All required fields filled")
            
            # Try to submit
            print("\n🚀 Attempting submission...")
            submit_btn.click()
            
            # Wait for response
            time.sleep(3)
            
            # Check response
            alert = page.locator('.alert').first
            if alert.is_visible():
                alert_text = alert.text_content()
                print(f"📋 Response: {alert_text}")
            else:
                print("❌ No response message found")
            
            # Check browser console for errors
            print("\n📊 Browser console logs:")
            # Note: Console logs would require additional setup in Playwright
            
            time.sleep(5)  # Keep browser open to examine
            
        except Exception as e:
            print(f"❌ Error during debugging: {str(e)}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    debug_p66_validation()