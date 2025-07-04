#!/usr/bin/env python3
"""
End-to-End Browser Testing with Playwright
Tests all forms with actual browser interactions
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
import time
from log_test_issue import log_test_issue

# Base URL for testing
BASE_URL = "https://loi-automation-api.onrender.com"

# Test customer data
TEST_CUSTOMER = {
    "company": "Claude's Test Gas Station LLC",
    "contact": "Claude Test Manager",
    "email": "transaction.coordinator.agent@gmail.com",
    "phone": "(555) 123-TEST",
    "address": "123 Test Station Drive",
    "city": "St. Louis",
    "state": "MO",
    "zip": "63101"
}

class E2EFormTester:
    def __init__(self, test_run_id):
        self.test_run_id = test_run_id
        self.browser = None
        self.page = None
        
    def start_browser(self, headless=True):
        """Start browser session"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        print(f"🌐 Browser started in {'headless' if headless else 'headed'} mode")
        
    def stop_browser(self):
        """Stop browser session"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🛑 Browser stopped")
        
    def test_customer_setup_sales_initiation(self):
        """Test Customer Setup sales initiation form"""
        print("\n📋 Testing Customer Setup Sales Initiation...")
        
        try:
            # Navigate to form
            self.page.goto(f"{BASE_URL}/customer-setup/initiate")
            self.page.wait_for_load_state('networkidle')
            
            # Fill form fields
            self.page.fill('input[name="legal_business_name"]', TEST_CUSTOMER["company"])
            self.page.fill('input[name="primary_contact_name"]', TEST_CUSTOMER["contact"])
            self.page.fill('input[name="primary_contact_email"]', TEST_CUSTOMER["email"])
            self.page.fill('input[name="primary_contact_phone"]', TEST_CUSTOMER["phone"])
            self.page.fill('textarea[name="notes"]', f"E2E Test Run: {self.test_run_id}")
            
            # Submit form
            self.page.click('button[type="submit"]')
            
            # Wait for response
            time.sleep(2)
            
            # Check for success message
            success_msg = self.page.locator('.alert-success').text_content()
            if "successfully" in success_msg:
                print(f"✅ Form submitted successfully!")
                # Extract transaction ID if present
                if "Transaction ID:" in success_msg:
                    transaction_id = success_msg.split("Transaction ID:")[1].strip()
                    print(f"📄 Transaction ID: {transaction_id}")
                    return transaction_id
            else:
                raise Exception("Success message not found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            log_test_issue(
                test_run_id=self.test_run_id,
                form_type="CUSTOMER_SETUP_SALES",
                issue_category="Frontend",
                issue_description=f"Form submission failed: {str(e)}",
                error_message=str(e),
                reproduction_steps="1. Navigate to /customer-setup/initiate 2. Fill form 3. Submit",
                severity="CRITICAL"
            )
            return None
            
    def test_p66_loi_form(self):
        """Test P66 LOI form submission"""
        print("\n⛽ Testing P66 LOI Form...")
        
        try:
            # Navigate to form
            self.page.goto(f"{BASE_URL}/p66_loi_form.html")
            self.page.wait_for_load_state('networkidle')
            
            # Fill station information
            self.page.fill('input[name="station_name"]', "Claude's Test Phillips 66")
            self.page.fill('input[name="station_address"]', TEST_CUSTOMER["address"])
            self.page.fill('input[name="station_city"]', TEST_CUSTOMER["city"])
            self.page.fill('input[name="station_state"]', TEST_CUSTOMER["state"])
            self.page.fill('input[name="station_zip"]', TEST_CUSTOMER["zip"])
            
            # Fill contact information
            self.page.fill('input[name="contact_name"]', TEST_CUSTOMER["contact"])
            self.page.fill('input[name="email"]', TEST_CUSTOMER["email"])
            self.page.fill('input[name="phone"]', TEST_CUSTOMER["phone"])
            
            # Fill fuel volume
            self.page.fill('input[name="monthly_gasoline_gallons"]', "50000")
            self.page.fill('input[name="monthly_diesel_gallons"]', "20000")
            
            # Fill contract details
            self.page.fill('input[name="current_brand"]', "Independent")
            self.page.fill('input[name="brand_expiration_date"]', "2025-12-31")
            self.page.fill('input[name="contract_start_date"]', "2025-08-01")
            self.page.fill('input[name="contract_term_years"]', "10")
            
            # Fill incentives
            self.page.fill('input[name="volume_incentive_requested"]', "25000")
            self.page.fill('input[name="image_funding_requested"]', "15000")
            self.page.fill('input[name="equipment_funding_requested"]', "10000")
            
            # Fill additional details
            self.page.fill('textarea[name="special_requirements"]', f"E2E Test: {self.test_run_id}")
            self.page.fill('input[name="authorized_representative"]', TEST_CUSTOMER["contact"])
            self.page.fill('input[name="representative_title"]', "General Manager")
            
            # Submit form
            self.page.click('button[type="submit"]')
            
            # Wait for response
            time.sleep(3)
            
            # Check for success
            alert = self.page.locator('.alert').first
            if alert.is_visible():
                alert_text = alert.text_content()
                print(f"📋 Response: {alert_text}")
                
                if "successfully" in alert_text.lower():
                    print("✅ P66 LOI submitted successfully!")
                    return True
                else:
                    raise Exception(f"Form submission failed: {alert_text}")
            else:
                raise Exception("No response message found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            log_test_issue(
                test_run_id=self.test_run_id,
                form_type="P66_LOI",
                issue_category="Frontend",
                issue_description=f"P66 LOI submission failed: {str(e)}",
                error_message=str(e),
                reproduction_steps="1. Navigate to /p66_loi_form.html 2. Fill all fields 3. Submit",
                severity="CRITICAL"
            )
            return False
            
    def test_signature_page(self, transaction_id):
        """Test signature page with ESIGN compliance"""
        print(f"\n✍️ Testing Signature Page for transaction: {transaction_id}")
        
        try:
            # Navigate to signature page
            self.page.goto(f"{BASE_URL}/api/v1/loi/sign/{transaction_id}")
            self.page.wait_for_load_state('networkidle')
            
            # Check for ESIGN compliance section
            esign_section = self.page.locator('.esign-disclosure')
            if not esign_section.is_visible():
                log_test_issue(
                    test_run_id=self.test_run_id,
                    form_type="SIGNATURE_PAGE",
                    issue_category="ESIGN",
                    issue_description="ESIGN disclosure section not visible",
                    reproduction_steps=f"1. Navigate to /api/v1/loi/sign/{transaction_id}",
                    severity="HIGH"
                )
                
            # Check for consent checkbox
            consent_checkbox = self.page.locator('#esign-consent')
            if consent_checkbox.is_visible():
                print("✅ ESIGN consent checkbox found")
                # Check the consent box
                consent_checkbox.check()
            else:
                log_test_issue(
                    test_run_id=self.test_run_id,
                    form_type="SIGNATURE_PAGE",
                    issue_category="ESIGN",
                    issue_description="ESIGN consent checkbox not found",
                    reproduction_steps=f"1. Navigate to signature page 2. Look for #esign-consent",
                    severity="HIGH"
                )
                
            # Test signature pad
            canvas = self.page.locator('#signature-pad')
            if canvas.is_visible():
                print("✅ Signature pad found")
                # Simulate drawing signature
                box = canvas.bounding_box()
                if box:
                    # Draw a simple signature
                    self.page.mouse.move(box['x'] + 50, box['y'] + 50)
                    self.page.mouse.down()
                    self.page.mouse.move(box['x'] + 150, box['y'] + 100)
                    self.page.mouse.move(box['x'] + 250, box['y'] + 50)
                    self.page.mouse.up()
                    print("✅ Signature drawn")
            else:
                log_test_issue(
                    test_run_id=self.test_run_id,
                    form_type="SIGNATURE_PAGE",
                    issue_category="Frontend",
                    issue_description="Signature pad not visible",
                    reproduction_steps=f"1. Navigate to signature page 2. Look for #signature-pad",
                    severity="CRITICAL"
                )
                
            # Submit signature
            submit_btn = self.page.locator('#submit-signature')
            if submit_btn.is_visible() and submit_btn.is_enabled():
                submit_btn.click()
                print("✅ Signature submitted")
                
                # Wait for response
                time.sleep(3)
                
                # Check for success
                success_alert = self.page.locator('.alert-success')
                if success_alert.is_visible():
                    print("✅ Signature completed successfully!")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"❌ Signature page error: {str(e)}")
            log_test_issue(
                test_run_id=self.test_run_id,
                form_type="SIGNATURE_PAGE",
                issue_category="Frontend",
                issue_description=f"Signature page failed: {str(e)}",
                error_message=str(e),
                reproduction_steps=f"1. Navigate to /api/v1/loi/sign/{transaction_id}",
                severity="CRITICAL"
            )
            return False

def run_full_test():
    """Run complete E2E test suite"""
    test_run_id = f"BROWSER_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n🧪 Starting Browser Test Run: {test_run_id}")
    print("=" * 60)
    
    tester = E2EFormTester(test_run_id)
    
    try:
        # Start browser (set headless=False to see the browser)
        tester.start_browser(headless=True)
        
        # Test 1: Customer Setup Sales Initiation
        transaction_id = tester.test_customer_setup_sales_initiation()
        
        # Test 2: P66 LOI Form
        tester.test_p66_loi_form()
        
        # Test 3: Test a known transaction signature page
        # tester.test_signature_page("LOI_1751632591_71ef539f")
        
        print("\n" + "=" * 60)
        print("🏁 Test run completed!")
        
    finally:
        tester.stop_browser()

if __name__ == "__main__":
    run_full_test()