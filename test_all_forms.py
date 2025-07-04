#!/usr/bin/env python3
"""
Comprehensive E2E Test Suite for LOI Automation System
Runs all test cases and logs issues for batch fixing
"""

from playwright.sync_api import sync_playwright, Page, expect
from datetime import datetime
import time
import json
from log_test_issue import log_test_issue, get_open_issues

# Configuration
BASE_URL = "https://loi-automation-api.onrender.com"
HEADLESS = True  # Set to False to see browser

# Test Data
TEST_DATA = {
    "company": "Claude's Test Gas Station LLC",
    "contact": "Claude Test Manager",
    "email": "transaction.coordinator.agent@gmail.com",
    "phone": "(555) 123-TEST",
    "address": "123 Test Station Drive",
    "city": "St. Louis",
    "state": "MO",
    "zip": "63101",
    "tax_id": "12-3456789",
    "bank_name": "First National Test Bank",
    "routing": "021000021",
    "account": "123456789012"
}

class TestResult:
    def __init__(self, test_id, name):
        self.test_id = test_id
        self.name = name
        self.status = "NOT_RUN"
        self.transaction_id = None
        self.error = None
        self.issues = []
        
    def to_dict(self):
        return {
            "test_id": self.test_id,
            "name": self.name,
            "status": self.status,
            "transaction_id": self.transaction_id,
            "error": self.error,
            "issues": self.issues
        }

class LOITestSuite:
    def __init__(self, test_run_id):
        self.test_run_id = test_run_id
        self.results = []
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        
    def start_browser(self):
        """Initialize browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=HEADLESS)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        print(f"🌐 Browser started ({'headless' if HEADLESS else 'headed'} mode)")
        
    def stop_browser(self):
        """Clean up browser"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🛑 Browser stopped")
        
    def log_issue(self, test_id, issue_type, description, error="", steps="", severity="MEDIUM"):
        """Log issue to database"""
        log_test_issue(
            test_run_id=self.test_run_id,
            form_type=test_id,
            issue_category=issue_type,
            issue_description=description,
            error_message=error,
            reproduction_steps=steps,
            severity=severity
        )
        
    def wait_for_element(self, selector, timeout=10000):
        """Wait for element with timeout"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
            
    def safe_fill(self, selector, value, test_id=""):
        """Safely fill form field"""
        try:
            if self.wait_for_element(selector, 5000):
                self.page.fill(selector, str(value))
                return True
            else:
                self.log_issue(test_id, "Frontend", f"Field not found: {selector}", 
                              severity="HIGH")
                return False
        except Exception as e:
            self.log_issue(test_id, "Frontend", f"Failed to fill {selector}: {str(e)}", 
                          str(e), severity="HIGH")
            return False
            
    def safe_select(self, selector, value, test_id=""):
        """Safely select option from dropdown"""
        try:
            if self.wait_for_element(selector, 5000):
                self.page.select_option(selector, value)
                return True
            else:
                self.log_issue(test_id, "Frontend", f"Select element not found: {selector}", 
                              severity="HIGH")
                return False
        except Exception as e:
            self.log_issue(test_id, "Frontend", f"Failed to select {selector}: {str(e)}", 
                          str(e), severity="HIGH")
            return False
            
    def safe_click(self, selector, test_id=""):
        """Safely click element"""
        try:
            if self.wait_for_element(selector, 5000):
                self.page.click(selector)
                return True
            else:
                self.log_issue(test_id, "Frontend", f"Button not found: {selector}", 
                              severity="HIGH")
                return False
        except Exception as e:
            self.log_issue(test_id, "Frontend", f"Failed to click {selector}: {str(e)}", 
                          str(e), severity="HIGH")
            return False
            
    # TEST CASE TC-001: Customer Setup Sales Initiation
    def test_customer_setup_initiation(self):
        """TC-001: Customer Setup Sales Initiation"""
        test = TestResult("TC-001", "Customer Setup Sales Initiation")
        print(f"\n{'='*60}")
        print(f"🧪 {test.test_id}: {test.name}")
        
        try:
            # Start from dashboard like a real user
            self.page.goto(f"{BASE_URL}")
            self.page.wait_for_load_state('networkidle')
            print(f"📍 Started at dashboard: {self.page.url}")
            
            # Click on Customer Setup link from dashboard
            customer_link = self.page.locator('a:has-text("Customer Setup")')
            if customer_link.count() > 0:
                customer_link.first.click()
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Navigated to: {self.page.url}")
            else:
                # Try alternative navigation
                self.page.goto(f"{BASE_URL}/customer-setup/initiate")
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Direct navigation to: {self.page.url}")
            
            # Fill form - note the actual field names from browser test
            filled = all([
                self.safe_fill('input[name="legal_business_name"]', TEST_DATA["company"], test.test_id),
                self.safe_fill('input[name="primary_contact_name"]', TEST_DATA["contact"], test.test_id),
                self.safe_fill('input[name="primary_contact_email"]', TEST_DATA["email"], test.test_id),
                self.safe_fill('input[name="primary_contact_phone"]', TEST_DATA["phone"], test.test_id),
                self.safe_fill('textarea[name="notes"]', f"{test.test_id}: Testing customer setup", test.test_id)
            ])
            
            if not filled:
                test.status = "FAILED"
                test.error = "Could not fill all required fields"
                return test
                
            # Submit form
            if not self.safe_click('button[type="submit"]', test.test_id):
                test.status = "FAILED"
                test.error = "Could not click submit button"
                return test
                
            # Wait for response
            time.sleep(3)
            
            # Check for success
            if self.wait_for_element('.alert-success', 5000):
                success_text = self.page.locator('.alert-success').text_content()
                print(f"✅ Success: {success_text}")
                
                # Extract transaction ID if present
                if "Transaction ID:" in success_text:
                    test.transaction_id = success_text.split("Transaction ID:")[1].strip().split()[0]
                    print(f"📄 Transaction ID: {test.transaction_id}")
                    
                test.status = "PASSED"
            else:
                # Check for error
                if self.wait_for_element('.alert-danger', 2000):
                    error_text = self.page.locator('.alert-danger').text_content()
                    test.error = error_text
                    self.log_issue(test.test_id, "Backend", f"Form submission error: {error_text}", 
                                  error_text, severity="CRITICAL")
                else:
                    test.error = "No success or error message found"
                    self.log_issue(test.test_id, "Frontend", "No response after submission", 
                                  severity="HIGH")
                test.status = "FAILED"
                
        except Exception as e:
            test.status = "ERROR"
            test.error = str(e)
            self.log_issue(test.test_id, "Test", f"Unexpected error: {str(e)}", 
                          str(e), severity="CRITICAL")
            
        self.results.append(test)
        return test
        
    # TEST CASE TC-003: EFT Sales Initiation
    def test_eft_initiation(self):
        """TC-003: EFT Sales Initiation"""
        test = TestResult("TC-003", "EFT Sales Initiation")
        print(f"\n{'='*60}")
        print(f"🧪 {test.test_id}: {test.name}")
        
        try:
            # Start from dashboard like a real user
            self.page.goto(f"{BASE_URL}")
            self.page.wait_for_load_state('networkidle')
            
            # Click on EFT link from dashboard
            eft_link = self.page.locator('a:has-text("EFT")')
            if eft_link.count() > 0:
                eft_link.first.click()
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Navigated to: {self.page.url}")
            else:
                # Try alternative navigation
                self.page.goto(f"{BASE_URL}/eft/initiate")
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Direct navigation to: {self.page.url}")
            
            # Fill form - EFT Sales Initiation (not customer completion)
            filled = all([
                self.safe_fill('#company-name', TEST_DATA["company"], test.test_id),
                self.safe_fill('#customer-email', TEST_DATA["email"], test.test_id),
                self.safe_fill('#customer-phone', TEST_DATA["phone"], test.test_id),
                self.safe_fill('#federal-tax-id', TEST_DATA["tax_id"], test.test_id),
                self.safe_fill('#authorized-name', TEST_DATA["contact"], test.test_id),
                self.safe_fill('#authorized-title', "General Manager", test.test_id),
                self.safe_fill('#bank-name', TEST_DATA["bank_name"], test.test_id),
                self.safe_fill('#account-holder', TEST_DATA["contact"], test.test_id),
                self.safe_select('#account-type', "checking", test.test_id),
                self.safe_fill('#initiated-by', "Claude Test Sales Rep", test.test_id)
            ])
            
            if not filled:
                test.status = "FAILED"
                test.error = "Could not fill all required fields"
                return test
                
            # Submit
            if not self.safe_click('button[type="submit"]', test.test_id):
                test.status = "FAILED"
                test.error = "Could not click submit button"
                return test
                
            # Wait and check response
            time.sleep(3)
            
            if self.wait_for_element('.alert-success', 5000):
                success_text = self.page.locator('.alert-success').text_content()
                print(f"✅ Success: {success_text}")
                test.status = "PASSED"
            else:
                test.status = "FAILED"
                test.error = "No success message found"
                
        except Exception as e:
            test.status = "ERROR"
            test.error = str(e)
            self.log_issue(test.test_id, "Test", f"Unexpected error: {str(e)}", 
                          str(e), severity="CRITICAL")
            
        self.results.append(test)
        return test
        
    # TEST CASE TC-005: P66 LOI Direct Submission
    def test_p66_loi_submission(self):
        """TC-005: P66 LOI Direct Submission"""
        test = TestResult("TC-005", "P66 LOI Direct Submission")
        print(f"\n{'='*60}")
        print(f"🧪 {test.test_id}: {test.name}")
        
        try:
            # Start from dashboard like a real user
            self.page.goto(f"{BASE_URL}")
            self.page.wait_for_load_state('networkidle')
            
            # Click on P66 LOI link from dashboard
            p66_link = self.page.locator('a:has-text("Phillips 66")')
            if p66_link.count() > 0:
                p66_link.first.click()
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Navigated to: {self.page.url}")
            else:
                # Try alternative navigation
                self.page.goto(f"{BASE_URL}/p66_loi_form.html")
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Direct navigation to: {self.page.url}")
            
            # Fill Station Information
            filled = all([
                self.safe_fill('#station-name', "Claude's Phillips 66", test.test_id),
                self.safe_fill('#station-address', TEST_DATA["address"], test.test_id),
                self.safe_fill('#station-city', TEST_DATA["city"], test.test_id),
                self.safe_fill('#station-state', TEST_DATA["state"], test.test_id),
                self.safe_fill('#station-zip', TEST_DATA["zip"], test.test_id),
                
                # Fuel volumes
                self.safe_fill('#gasoline-volume', "50000", test.test_id),
                self.safe_fill('#diesel-volume', "20000", test.test_id),
                self.safe_fill('#current-brand', "Independent", test.test_id),
                self.safe_fill('#brand-expiration', "2025-12-31", test.test_id),
                
                # Contract details
                self.safe_fill('#start-date', "2025-08-01", test.test_id),
                self.safe_select('#contract-term', "10", test.test_id),
                self.safe_fill('#volume-incentive', "25000", test.test_id),
                self.safe_fill('#image-funding', "15000", test.test_id),
                self.safe_fill('#equipment-funding', "10000", test.test_id),
                
                # Special requirements
                self.safe_fill('#special-requirements', f"{test.test_id}: Testing P66 submission", test.test_id),
                
                # Contact info - using correct field IDs from actual form
                self.safe_fill('#representative-name', TEST_DATA["contact"], test.test_id),
                self.safe_fill('#representative-title', "General Manager", test.test_id),
                self.safe_fill('#contact-email', TEST_DATA["email"], test.test_id),
                self.safe_fill('#contact-phone', TEST_DATA["phone"], test.test_id)
            ])
            
            if not filled:
                test.status = "FAILED"
                test.error = "Could not fill all required fields"
                return test
                
            # Check equipment boxes - using correct IDs
            self.page.check('#canopy')
            self.page.check('#dispensers')
            
            # Submit form
            if not self.safe_click('#submit-btn', test.test_id):
                test.status = "FAILED"
                test.error = "Could not click submit button"
                return test
                
            # Wait for response
            time.sleep(3)
            
            # Check for success
            if self.wait_for_element('.alert', 5000):
                alert_text = self.page.locator('.alert').first.text_content()
                print(f"📋 Response: {alert_text}")
                
                if "successfully" in alert_text.lower():
                    # Extract transaction ID
                    if "transaction id:" in alert_text.lower():
                        parts = alert_text.lower().split("transaction id:")
                        if len(parts) > 1:
                            test.transaction_id = parts[1].strip().split()[0]
                            print(f"📄 Transaction ID: {test.transaction_id}")
                    test.status = "PASSED"
                else:
                    test.status = "FAILED"
                    test.error = alert_text
                    self.log_issue(test.test_id, "Backend", f"Submission failed: {alert_text}", 
                                  alert_text, severity="CRITICAL")
            else:
                test.status = "FAILED"
                test.error = "No response message"
                
        except Exception as e:
            test.status = "ERROR"
            test.error = str(e)
            self.log_issue(test.test_id, "Test", f"Unexpected error: {str(e)}", 
                          str(e), severity="CRITICAL")
            
        self.results.append(test)
        return test
        
    # TEST CASE TC-006: P66 LOI Signature Flow
    def test_p66_signature_flow(self, transaction_id=None):
        """TC-006: P66 LOI Signature Flow"""
        test = TestResult("TC-006", "P66 LOI Signature Flow")
        print(f"\n{'='*60}")
        print(f"🧪 {test.test_id}: {test.name}")
        
        if not transaction_id:
            test.status = "SKIPPED"
            test.error = "No transaction ID provided"
            self.results.append(test)
            return test
            
        try:
            url = f"{BASE_URL}/api/v1/loi/sign/{transaction_id}"
            print(f"📄 Testing signature URL: {url}")
            self.page.goto(url)
            self.page.wait_for_load_state('networkidle')
            
            # Check for ESIGN disclosure
            if self.wait_for_element('.esign-disclosure', 5000):
                print("✅ ESIGN disclosure found")
            else:
                self.log_issue(test.test_id, "ESIGN", "ESIGN disclosure section not found", 
                              severity="HIGH")
                              
            # Check for consent checkbox
            consent_found = False
            if self.wait_for_element('#esign-consent', 2000):
                print("✅ ESIGN consent checkbox found")
                self.page.check('#esign-consent')
                consent_found = True
            else:
                self.log_issue(test.test_id, "ESIGN", "ESIGN consent checkbox not found", 
                              severity="HIGH")
                              
            # Check for signature pad
            if self.wait_for_element('#signature-pad', 5000):
                print("✅ Signature pad found")
                
                # Draw signature
                canvas = self.page.locator('#signature-pad')
                box = canvas.bounding_box()
                if box:
                    # Simple signature drawing
                    self.page.mouse.move(box['x'] + 50, box['y'] + 50)
                    self.page.mouse.down()
                    self.page.mouse.move(box['x'] + 150, box['y'] + 80)
                    self.page.mouse.move(box['x'] + 250, box['y'] + 50)
                    self.page.mouse.move(box['x'] + 350, box['y'] + 80)
                    self.page.mouse.up()
                    print("✅ Signature drawn")
                    
                    # Try to submit
                    if self.safe_click('#submit-signature', test.test_id):
                        time.sleep(3)
                        
                        # Check for success
                        if self.wait_for_element('.alert-success', 5000):
                            print("✅ Signature submitted successfully")
                            test.status = "PASSED"
                        else:
                            test.status = "FAILED"
                            test.error = "No success message after signature"
                    else:
                        test.status = "FAILED"
                        test.error = "Could not submit signature"
                else:
                    test.status = "FAILED"
                    test.error = "Could not get signature pad dimensions"
            else:
                test.status = "FAILED"
                test.error = "Signature pad not found"
                self.log_issue(test.test_id, "Frontend", "Signature pad not found", 
                              severity="CRITICAL")
                              
        except Exception as e:
            # Check if it's a 404/500 error
            if "500" in str(e) or "404" in str(e):
                test.status = "FAILED"
                test.error = f"Signature page error: {str(e)}"
                self.log_issue(test.test_id, "Backend", f"Signature page not accessible: {str(e)}", 
                              str(e), severity="CRITICAL")
            else:
                test.status = "ERROR"
                test.error = str(e)
                self.log_issue(test.test_id, "Test", f"Unexpected error: {str(e)}", 
                              str(e), severity="CRITICAL")
                              
        self.results.append(test)
        return test
        
    # TEST CASE TC-009: Paper Copy Request
    def test_paper_copy_request(self):
        """TC-009: Paper Copy Request"""
        test = TestResult("TC-009", "Paper Copy Request")
        print(f"\n{'='*60}")
        print(f"🧪 {test.test_id}: {test.name}")
        
        try:
            # Start from dashboard like a real user
            self.page.goto(f"{BASE_URL}")
            self.page.wait_for_load_state('networkidle')
            
            # Look for paper copy link or navigate directly
            paper_link = self.page.locator('a:has-text("Paper Copy")')
            if paper_link.count() > 0:
                paper_link.first.click()
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Navigated to: {self.page.url}")
            else:
                # Try direct navigation
                self.page.goto(f"{BASE_URL}/api/v1/paper-copy/form")
                self.page.wait_for_load_state('networkidle')
                print(f"📍 Direct navigation to: {self.page.url}")
            
            # Use a test transaction ID
            test_transaction_id = "TEST_TRANS_123"
            
            filled = all([
                self.safe_fill('#transaction_id', test_transaction_id, test.test_id),
                self.safe_fill('#customer_name', TEST_DATA["contact"], test.test_id),
                self.safe_fill('#customer_email', TEST_DATA["email"], test.test_id),
                self.safe_fill('#reason', f"{test.test_id}: Testing paper copy request", test.test_id)
            ])
            
            if not filled:
                test.status = "FAILED"
                test.error = "Could not fill required fields"
                return test
                
            # Select document type
            self.page.select_option('#document_type', "P66 LOI")
            
            # Submit
            if self.safe_click('button[type="submit"]', test.test_id):
                time.sleep(2)
                
                # Check for success
                if self.wait_for_element('#result', 3000):
                    result_text = self.page.locator('#result').text_content()
                    if "successfully" in result_text.lower():
                        print("✅ Paper copy request submitted")
                        test.status = "PASSED"
                    else:
                        test.status = "FAILED"
                        test.error = result_text
                else:
                    test.status = "FAILED"
                    test.error = "No result message"
            else:
                test.status = "FAILED"
                test.error = "Could not submit form"
                
        except Exception as e:
            test.status = "ERROR"
            test.error = str(e)
            self.log_issue(test.test_id, "Test", f"Unexpected error: {str(e)}", 
                          str(e), severity="MEDIUM")
                          
        self.results.append(test)
        return test
        
    def run_all_tests(self):
        """Execute all test cases"""
        print(f"\n🚀 Starting Test Run: {self.test_run_id}")
        print(f"🌐 Base URL: {BASE_URL}")
        print(f"📧 Test Email: {TEST_DATA['email']}")
        
        try:
            self.start_browser()
            
            # Run tests in sequence
            tc001 = self.test_customer_setup_initiation()
            tc003 = self.test_eft_initiation()
            tc005 = self.test_p66_loi_submission()
            
            # Test signature flow if we got a transaction ID
            if tc005.transaction_id:
                self.test_p66_signature_flow(tc005.transaction_id)
            else:
                print("⚠️ Skipping signature test - no transaction ID from P66 submission")
                
            # Always test paper copy form
            self.test_paper_copy_request()
            
        finally:
            self.stop_browser()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test execution summary"""
        print(f"\n{'='*60}")
        print("📊 TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIPPED")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Errors: {errors}")
        print(f"⏭️ Skipped: {skipped}")
        
        print(f"\n{'='*60}")
        print("📋 DETAILED RESULTS")
        print(f"{'='*60}")
        
        for result in self.results:
            status_icon = {
                "PASSED": "✅",
                "FAILED": "❌",
                "ERROR": "⚠️",
                "SKIPPED": "⏭️",
                "NOT_RUN": "⭕"
            }.get(result.status, "❓")
            
            print(f"{status_icon} {result.test_id}: {result.name}")
            print(f"   Status: {result.status}")
            if result.transaction_id:
                print(f"   Transaction ID: {result.transaction_id}")
            if result.error:
                print(f"   Error: {result.error}")
            print()
            
        # Show logged issues
        issues = get_open_issues(self.test_run_id)
        if issues:
            print(f"\n{'='*60}")
            print(f"🐛 ISSUES LOGGED: {len(issues)}")
            print(f"{'='*60}")
            
            for issue in issues:
                print(f"[{issue[5]}] {issue[1]} - {issue[2]}: {issue[3]}")
                
        # Save results to file
        with open(f"test_results_{self.test_run_id}.json", "w") as f:
            json.dump([r.to_dict() for r in self.results], f, indent=2)
        print(f"\n💾 Results saved to: test_results_{self.test_run_id}.json")

def main():
    """Main test execution"""
    test_run_id = f"FULL_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    suite = LOITestSuite(test_run_id)
    suite.run_all_tests()

if __name__ == "__main__":
    main()