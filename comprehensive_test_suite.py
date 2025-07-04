#!/usr/bin/env python3
"""
Comprehensive Test Suite with Database Verification
Iterative testing until 100% success rate
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
import time
import json
import psycopg2
from log_test_issue import log_test_issue, get_open_issues

# Configuration
BASE_URL = "https://loi-automation-api.onrender.com"
HEADLESS = False  # Visible browser for debugging

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

# Database connection
def get_db_connection():
    """Connect to production database"""
    try:
        return psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
    except:
        return psycopg2.connect("postgresql://mattmizell:training1@localhost:5432/loi_automation")

class ComprehensiveTestSuite:
    def __init__(self):
        self.test_run_id = f"COMPREHENSIVE_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.browser = None
        self.page = None
        self.issues = []
        self.test_results = {}
        self.transaction_ids = {}
        
    def start_browser(self):
        """Start browser session"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=HEADLESS)
        self.page = self.browser.new_page()
        print(f"🌐 Browser started for test run: {self.test_run_id}")
        
    def stop_browser(self):
        """Stop browser session"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🛑 Browser stopped")
        
    def log_issue(self, test_name, category, description, error="", severity="HIGH"):
        """Log issue for tracking"""
        issue = {
            "test_name": test_name,
            "category": category,
            "description": description,
            "error": error,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(issue)
        
        log_test_issue(
            test_run_id=self.test_run_id,
            form_type=test_name,
            issue_category=category,
            issue_description=description,
            error_message=error,
            severity=severity
        )
        
    def safe_fill(self, selector, value, test_name=""):
        """Safely fill form field"""
        try:
            self.page.wait_for_selector(selector, timeout=5000)
            self.page.fill(selector, str(value))
            return True
        except Exception as e:
            self.log_issue(test_name, "Frontend", f"Failed to fill {selector}: {str(e)}", str(e))
            return False
            
    def safe_select(self, selector, value, test_name=""):
        """Safely select option"""
        try:
            self.page.wait_for_selector(selector, timeout=5000)
            self.page.select_option(selector, value)
            return True
        except Exception as e:
            self.log_issue(test_name, "Frontend", f"Failed to select {selector}: {str(e)}", str(e))
            return False
            
    def safe_click(self, selector, test_name=""):
        """Safely click element"""
        try:
            self.page.wait_for_selector(selector, timeout=5000)
            self.page.click(selector)
            return True
        except Exception as e:
            self.log_issue(test_name, "Frontend", f"Failed to click {selector}: {str(e)}", str(e))
            return False
            
    def check_database_record(self, table, conditions, test_name):
        """Verify record exists in database"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            where_clause = " AND ".join([f"{k} = %s" for k in conditions.keys()])
            query = f"SELECT * FROM {table} WHERE {where_clause}"
            
            cur.execute(query, list(conditions.values()))
            result = cur.fetchone()
            
            conn.close()
            
            if result:
                print(f"✅ Database record found in {table}")
                return True
            else:
                self.log_issue(test_name, "Database", f"No record found in {table} with conditions {conditions}")
                return False
                
        except Exception as e:
            self.log_issue(test_name, "Database", f"Database check failed for {table}: {str(e)}", str(e))
            return False
            
    def test_customer_setup_sales_initiation(self):
        """Test Customer Setup Sales Initiation"""
        test_name = "Customer_Setup_Sales_Initiation"
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        
        try:
            # Navigate from dashboard
            self.page.goto(f"{BASE_URL}")
            self.page.wait_for_load_state('networkidle')
            
            # Click Customer Setup link
            customer_link = self.page.locator('a:has-text("Customer Setup")')
            if customer_link.count() > 0:
                customer_link.first.click()
                self.page.wait_for_load_state('networkidle')
            else:
                self.page.goto(f"{BASE_URL}/customer-setup/initiate")
                self.page.wait_for_load_state('networkidle')
                
            # Fill form
            success = all([
                self.safe_fill('input[name="legal_business_name"]', TEST_DATA["company"], test_name),
                self.safe_fill('input[name="primary_contact_name"]', TEST_DATA["contact"], test_name),
                self.safe_fill('input[name="primary_contact_email"]', TEST_DATA["email"], test_name),
                self.safe_fill('input[name="primary_contact_phone"]', TEST_DATA["phone"], test_name),
                self.safe_fill('textarea[name="notes"]', f"Test run: {self.test_run_id}", test_name)
            ])
            
            if not success:
                self.test_results[test_name] = "FAILED - Form filling"
                return
                
            # Submit
            self.safe_click('button[type="submit"]', test_name)
            time.sleep(3)
            
            # Check response
            try:
                success_msg = self.page.locator('.alert-success').text_content()
                if "successfully" in success_msg and "Transaction ID:" in success_msg:
                    transaction_id = success_msg.split("Transaction ID:")[1].strip().split()[0]
                    self.transaction_ids[test_name] = transaction_id
                    print(f"✅ Success! Transaction ID: {transaction_id}")
                    
                    # Verify in database
                    self.check_database_record("customers", {"email": TEST_DATA["email"]}, test_name)
                    
                    self.test_results[test_name] = "PASSED"
                else:
                    self.log_issue(test_name, "Backend", f"Invalid success message: {success_msg}")
                    self.test_results[test_name] = "FAILED - Invalid response"
                    
            except Exception as e:
                self.log_issue(test_name, "Frontend", f"No success message found: {str(e)}", str(e))
                self.test_results[test_name] = "FAILED - No response"
                
        except Exception as e:
            self.log_issue(test_name, "Test", f"Test execution failed: {str(e)}", str(e))
            self.test_results[test_name] = "ERROR"
            
    def test_eft_sales_initiation(self):
        """Test EFT Sales Initiation"""
        test_name = "EFT_Sales_Initiation"
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        
        try:
            # Navigate from dashboard
            self.page.goto(f"{BASE_URL}")
            self.page.wait_for_load_state('networkidle')
            
            # Click EFT link
            eft_link = self.page.locator('a:has-text("EFT")')
            if eft_link.count() > 0:
                eft_link.first.click()
                self.page.wait_for_load_state('networkidle')
            else:
                self.page.goto(f"{BASE_URL}/eft/initiate")
                self.page.wait_for_load_state('networkidle')
                
            # Fill form
            success = all([
                self.safe_fill('#company-name', TEST_DATA["company"], test_name),
                self.safe_fill('#customer-email', TEST_DATA["email"], test_name),
                self.safe_fill('#customer-phone', TEST_DATA["phone"], test_name),
                self.safe_fill('#federal-tax-id', TEST_DATA["tax_id"], test_name),
                self.safe_fill('#authorized-name', TEST_DATA["contact"], test_name),
                self.safe_fill('#authorized-title', "General Manager", test_name),
                self.safe_fill('#bank-name', TEST_DATA["bank_name"], test_name),
                self.safe_fill('#account-holder', TEST_DATA["contact"], test_name),
                self.safe_select('#account-type', "checking", test_name),
                self.safe_fill('#initiated-by', "Claude Test Sales Rep", test_name)
            ])
            
            if not success:
                self.test_results[test_name] = "FAILED - Form filling"
                return
                
            # Submit
            self.safe_click('button[type="submit"]', test_name)
            time.sleep(3)
            
            # Check response
            try:
                success_msg = self.page.locator('.alert-success').text_content()
                if "successfully" in success_msg:
                    if "Transaction ID:" in success_msg:
                        transaction_id = success_msg.split("Transaction ID:")[1].strip().split()[0]
                        self.transaction_ids[test_name] = transaction_id
                        print(f"✅ Success! Transaction ID: {transaction_id}")
                    else:
                        print(f"✅ Success! {success_msg}")
                    
                    self.test_results[test_name] = "PASSED"
                else:
                    self.log_issue(test_name, "Backend", f"Invalid success message: {success_msg}")
                    self.test_results[test_name] = "FAILED - Invalid response"
                    
            except Exception as e:
                self.log_issue(test_name, "Frontend", f"No success message found: {str(e)}", str(e))
                self.test_results[test_name] = "FAILED - No response"
                
        except Exception as e:
            self.log_issue(test_name, "Test", f"Test execution failed: {str(e)}", str(e))
            self.test_results[test_name] = "ERROR"
            
    def test_p66_loi_submission(self):
        """Test P66 LOI Direct Submission with detailed debugging"""
        test_name = "P66_LOI_Submission"
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        
        try:
            # Navigate to P66 form
            self.page.goto(f"{BASE_URL}/p66_loi_form.html")
            self.page.wait_for_load_state('networkidle')
            
            # Fill all fields systematically
            fields_success = all([
                # Station Information
                self.safe_fill('#station-name', "Claude's Test Phillips 66", test_name),
                self.safe_fill('#station-address', TEST_DATA["address"], test_name),
                self.safe_fill('#station-city', TEST_DATA["city"], test_name),
                self.safe_fill('#station-state', TEST_DATA["state"], test_name),
                self.safe_fill('#station-zip', TEST_DATA["zip"], test_name),
                
                # Fuel volumes  
                self.safe_fill('#gasoline-volume', "50000", test_name),
                self.safe_fill('#diesel-volume', "20000", test_name),
                self.safe_fill('#current-brand', "Independent", test_name),
                self.safe_fill('#brand-expiration', "2025-12-31", test_name),
                
                # Contract details
                self.safe_fill('#start-date', "2025-08-01", test_name),
                self.safe_select('#contract-term', "10", test_name),
                self.safe_fill('#volume-incentive', "25000", test_name),
                self.safe_fill('#image-funding', "15000", test_name),
                self.safe_fill('#equipment-funding', "10000", test_name),
                
                # Special requirements
                self.safe_fill('#special-requirements', f"Test: {self.test_run_id}", test_name),
                
                # Contact info
                self.safe_fill('#representative-name', TEST_DATA["contact"], test_name),
                self.safe_fill('#representative-title', "General Manager", test_name),
                self.safe_fill('#contact-email', TEST_DATA["email"], test_name),
                self.safe_fill('#contact-phone', TEST_DATA["phone"], test_name)
            ])
            
            if not fields_success:
                self.test_results[test_name] = "FAILED - Form filling"
                return
                
            # Check equipment boxes
            try:
                self.page.check('#canopy')
                self.page.check('#dispensers')
            except Exception as e:
                self.log_issue(test_name, "Frontend", f"Equipment checkboxes failed: {str(e)}", str(e))
                
            # Capture form data before submit for debugging
            form_data = {}
            try:
                form_data['station_name'] = self.page.locator('#station-name').input_value()
                form_data['contact_email'] = self.page.locator('#contact-email').input_value()
                form_data['representative_name'] = self.page.locator('#representative-name').input_value()
                print(f"📋 Form data preview: {form_data}")
            except Exception as e:
                print(f"⚠️ Could not capture form data: {e}")
                
            # Submit form
            print("🚀 Submitting P66 LOI form...")
            self.safe_click('#submit-btn', test_name)
            time.sleep(5)  # Wait longer for backend processing
            
            # Check response with detailed analysis
            try:
                alert = self.page.locator('.alert').first
                if alert.is_visible():
                    alert_text = alert.text_content().strip()
                    print(f"📋 Response received: {alert_text}")
                    
                    if "successfully" in alert_text.lower():
                        if "transaction id:" in alert_text.lower():
                            # Extract transaction ID
                            parts = alert_text.lower().split("transaction id:")
                            if len(parts) > 1:
                                transaction_id = parts[1].strip().split()[0]
                                self.transaction_ids[test_name] = transaction_id
                                print(f"✅ Success! Transaction ID: {transaction_id}")
                                
                                # Verify in database
                                self.check_database_record("p66_loi_form_data", {"email": TEST_DATA["email"]}, test_name)
                                
                                self.test_results[test_name] = "PASSED"
                                return
                                
                        print(f"✅ Success response but no transaction ID found")
                        self.test_results[test_name] = "PARTIAL - Success but no transaction ID"
                        return
                        
                    elif "this letter of intent begins" in alert_text.lower():
                        # This is the intro message, not a response - backend issue
                        self.log_issue(test_name, "Backend", "Form submission returned intro message instead of processing response", alert_text, "CRITICAL")
                        self.test_results[test_name] = "FAILED - Backend not processing"
                        return
                        
                    else:
                        # Some other error message
                        self.log_issue(test_name, "Backend", f"Form submission failed: {alert_text}", alert_text, "CRITICAL")
                        self.test_results[test_name] = "FAILED - Backend error"
                        return
                        
                else:
                    self.log_issue(test_name, "Frontend", "No response message displayed after submission", "", "CRITICAL")
                    self.test_results[test_name] = "FAILED - No response"
                    
            except Exception as e:
                self.log_issue(test_name, "Test", f"Response checking failed: {str(e)}", str(e), "CRITICAL")
                self.test_results[test_name] = "ERROR - Response check failed"
                
        except Exception as e:
            self.log_issue(test_name, "Test", f"Test execution failed: {str(e)}", str(e), "CRITICAL")
            self.test_results[test_name] = "ERROR"
            
    def test_signature_workflow(self, transaction_id, test_name_prefix):
        """Test signature workflow for a given transaction"""
        test_name = f"{test_name_prefix}_Signature"
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        
        if not transaction_id:
            print("⏭️ Skipping signature test - no transaction ID")
            self.test_results[test_name] = "SKIPPED - No transaction ID"
            return
            
        try:
            # Navigate to signature page
            signature_url = f"{BASE_URL}/api/v1/loi/sign/{transaction_id}"
            print(f"📄 Signature URL: {signature_url}")
            
            self.page.goto(signature_url)
            self.page.wait_for_load_state('networkidle')
            
            # Check for ESIGN compliance
            esign_section = self.page.locator('.esign-disclosure')
            if esign_section.is_visible():
                print("✅ ESIGN disclosure found")
            else:
                self.log_issue(test_name, "ESIGN", "ESIGN disclosure section not visible")
                
            # Check for consent checkbox
            consent_checkbox = self.page.locator('#esign-consent')
            if consent_checkbox.is_visible():
                consent_checkbox.check()
                print("✅ ESIGN consent checked")
            else:
                self.log_issue(test_name, "ESIGN", "ESIGN consent checkbox not found")
                
            # Test signature pad
            canvas = self.page.locator('#signature-pad')
            if canvas.is_visible():
                # Draw signature
                box = canvas.bounding_box()
                if box:
                    self.page.mouse.move(box['x'] + 50, box['y'] + 50)
                    self.page.mouse.down()
                    self.page.mouse.move(box['x'] + 150, box['y'] + 100)
                    self.page.mouse.move(box['x'] + 250, box['y'] + 50)
                    self.page.mouse.up()
                    print("✅ Signature drawn")
                    
                    # Submit signature
                    submit_btn = self.page.locator('#submit-signature')
                    if submit_btn.is_visible() and submit_btn.is_enabled():
                        submit_btn.click()
                        time.sleep(3)
                        
                        # Check for success
                        success_alert = self.page.locator('.alert-success')
                        if success_alert.is_visible():
                            print("✅ Signature completed successfully!")
                            self.test_results[test_name] = "PASSED"
                            
                            # Verify in database
                            self.check_database_record("electronic_signatures", {"transaction_id": transaction_id}, test_name)
                            
                        else:
                            self.log_issue(test_name, "Backend", "No success message after signature submission")
                            self.test_results[test_name] = "FAILED - No success response"
                    else:
                        self.log_issue(test_name, "Frontend", "Submit signature button not available")
                        self.test_results[test_name] = "FAILED - Submit button unavailable"
                else:
                    self.log_issue(test_name, "Frontend", "Could not get signature pad dimensions")
                    self.test_results[test_name] = "FAILED - Canvas dimensions"
            else:
                self.log_issue(test_name, "Frontend", "Signature pad not visible")
                self.test_results[test_name] = "FAILED - No signature pad"
                
        except Exception as e:
            if "404" in str(e) or "500" in str(e):
                self.log_issue(test_name, "Backend", f"Signature page not accessible: {str(e)}", str(e), "CRITICAL")
                self.test_results[test_name] = "FAILED - Page not accessible"
            else:
                self.log_issue(test_name, "Test", f"Signature test failed: {str(e)}", str(e))
                self.test_results[test_name] = "ERROR"
                
    def test_customer_setup_completion(self):
        """Test Customer Setup Completion (multi-step customer form)"""
        test_name = "Customer_Setup_Completion"
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        
        try:
            # Navigate to customer setup form
            self.page.goto(f"{BASE_URL}/customer_setup_form.html")
            self.page.wait_for_load_state('networkidle')
            
            # Step 1: Business Information
            print("📝 Step 1: Business Information")
            step1_success = all([
                self.safe_fill('#legal-business-name', TEST_DATA["company"], test_name),
                self.safe_select('#business-type', "LLC", test_name),
                self.safe_fill('#federal-tax-id', TEST_DATA["tax_id"], test_name),
                self.safe_fill('#years-in-business', "5", test_name)
            ])
            
            if step1_success:
                self.safe_click('#next-to-step-2', test_name)
                time.sleep(2)
                print("✅ Step 1 completed")
            else:
                self.test_results[test_name] = "FAILED - Step 1"
                return
                
            # Step 2: Contact Details  
            print("📝 Step 2: Contact Details")
            step2_success = all([
                self.safe_fill('#primary-contact-name', TEST_DATA["contact"], test_name),
                self.safe_fill('#primary-contact-title', "General Manager", test_name),
                self.safe_fill('#primary-contact-phone', TEST_DATA["phone"], test_name),
                self.safe_fill('#primary-contact-email', TEST_DATA["email"], test_name),
                self.safe_fill('#ap-contact-name', "Claude Accounting", test_name),
                self.safe_fill('#ap-contact-phone', "(555) 123-ACCT", test_name),
                self.safe_fill('#ap-contact-email', "accounting@claudesgas.com", test_name)
            ])
            
            if step2_success:
                self.safe_click('#next-to-step-3', test_name)
                time.sleep(2)
                print("✅ Step 2 completed")
            else:
                self.test_results[test_name] = "FAILED - Step 2"
                return
                
            # Step 3: Location & Equipment
            print("📝 Step 3: Location & Equipment")
            step3_success = all([
                self.safe_fill('#physical-address', TEST_DATA["address"], test_name),
                self.safe_fill('#physical-city', TEST_DATA["city"], test_name),
                self.safe_fill('#physical-state', TEST_DATA["state"], test_name),
                self.safe_fill('#physical-zip', TEST_DATA["zip"], test_name),
                self.safe_fill('#annual-fuel-volume', "600000", test_name),
                self.safe_fill('#number-dispensers', "8", test_name),
                self.safe_fill('#number-tanks', "3", test_name)
            ])
            
            # Check "same as physical address"
            try:
                self.page.check('#same-as-physical')
            except Exception as e:
                self.log_issue(test_name, "Frontend", f"Same as physical checkbox failed: {str(e)}")
            
            if step3_success:
                self.safe_click('#next-to-step-4', test_name)
                time.sleep(2)
                print("✅ Step 3 completed")
            else:
                self.test_results[test_name] = "FAILED - Step 3"
                return
                
            # Step 4: Financial References
            print("📝 Step 4: Financial References")
            step4_success = all([
                self.safe_fill('#bank-name', TEST_DATA["bank_name"], test_name),
                self.safe_fill('#bank-contact', "John Banker", test_name),
                self.safe_fill('#bank-phone', "(555) 123-BANK", test_name),
                self.safe_fill('#trade-company', "Test Fuel Distributors", test_name),
                self.safe_fill('#trade-contact', "Jane Supplier", test_name),
                self.safe_fill('#trade-phone', "(555) 123-FUEL", test_name)
            ])
            
            if step4_success:
                self.safe_click('#next-to-step-5', test_name)
                time.sleep(2)
                print("✅ Step 4 completed")
            else:
                self.test_results[test_name] = "FAILED - Step 4"
                return
                
            # Step 5: Authorization (no signature required)
            print("📝 Step 5: Authorization")
            
            # Submit final form
            self.safe_click('#submit-customer-setup', test_name)
            time.sleep(5)
            
            # Check for success response
            try:
                success_msg = self.page.locator('.alert-success').text_content()
                if "successfully" in success_msg.lower():
                    print(f"✅ Customer Setup Completion successful!")
                    self.test_results[test_name] = "PASSED"
                    
                    # Verify in database
                    self.check_database_record("customers", {"email": TEST_DATA["email"]}, test_name)
                else:
                    self.log_issue(test_name, "Backend", f"Invalid success message: {success_msg}")
                    self.test_results[test_name] = "FAILED - Invalid response"
                    
            except Exception as e:
                self.log_issue(test_name, "Frontend", f"No success message found: {str(e)}", str(e))
                self.test_results[test_name] = "FAILED - No response"
                
        except Exception as e:
            self.log_issue(test_name, "Test", f"Test execution failed: {str(e)}", str(e))
            self.test_results[test_name] = "ERROR"
            
    def test_vp_racing_loi_submission(self):
        """Test VP Racing LOI Direct Submission"""
        test_name = "VP_Racing_LOI_Submission"
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        
        try:
            # Navigate from dashboard
            self.page.goto(f"{BASE_URL}")
            self.page.wait_for_load_state('networkidle')
            
            # Look for VP Racing link
            vp_link = self.page.locator('a:has-text("VP Racing")')
            if vp_link.count() > 0:
                vp_link.first.click()
                self.page.wait_for_load_state('networkidle')
            else:
                # Try direct navigation
                self.page.goto(f"{BASE_URL}/forms/vp-racing-loi")
                self.page.wait_for_load_state('networkidle')
                
            print(f"📄 VP Racing form URL: {self.page.url}")
            
            # Fill VP Racing LOI form (corrected field selectors)
            fields_success = all([
                # Station Information
                self.safe_fill('#station-name', "Claude's VP Racing Station", test_name),
                self.safe_fill('#station-address', TEST_DATA["address"], test_name),
                self.safe_fill('#station-city', TEST_DATA["city"], test_name),
                self.safe_fill('#station-state', TEST_DATA["state"], test_name),
                self.safe_fill('#station-zip', TEST_DATA["zip"], test_name),
                
                # Fuel volumes - CORRECTED SELECTORS
                self.safe_fill('#gasoline-volume', "40000", test_name),
                self.safe_fill('#diesel-volume', "15000", test_name),
                self.safe_fill('#current-brand', "Shell", test_name),
                
                # Contact info - CORRECTED SELECTORS
                self.safe_fill('#representative-name', TEST_DATA["contact"], test_name),
                self.safe_fill('#representative-title', "General Manager", test_name),
                self.safe_fill('#contact-email', TEST_DATA["email"], test_name),
                self.safe_fill('#contact-phone', TEST_DATA["phone"], test_name),
                
                # Comments - CORRECTED SELECTOR
                self.safe_fill('#special-requirements', f"VP Racing test: {self.test_run_id}", test_name)
            ])
            
            if not fields_success:
                self.test_results[test_name] = "FAILED - Form filling"
                return
                
            # Submit form
            self.safe_click('button[type="submit"]', test_name)
            time.sleep(5)
            
            # Check response
            try:
                alert = self.page.locator('.alert').first
                if alert.is_visible():
                    alert_text = alert.text_content()
                    print(f"📋 VP Racing response: {alert_text}")
                    
                    if "successfully" in alert_text.lower():
                        if "transaction id:" in alert_text.lower():
                            parts = alert_text.lower().split("transaction id:")
                            if len(parts) > 1:
                                transaction_id = parts[1].strip().split()[0]
                                self.transaction_ids[test_name] = transaction_id
                                print(f"✅ Success! Transaction ID: {transaction_id}")
                                
                        self.test_results[test_name] = "PASSED"
                        
                        # Verify in database
                        self.check_database_record("vp_racing_loi_form_data", {"email": TEST_DATA["email"]}, test_name)
                        
                    else:
                        self.log_issue(test_name, "Backend", f"VP Racing submission failed: {alert_text}", alert_text)
                        self.test_results[test_name] = "FAILED - Backend error"
                else:
                    self.log_issue(test_name, "Frontend", "No response message after VP Racing submission")
                    self.test_results[test_name] = "FAILED - No response"
                    
            except Exception as e:
                self.log_issue(test_name, "Test", f"VP Racing response check failed: {str(e)}", str(e))
                self.test_results[test_name] = "ERROR"
                
        except Exception as e:
            self.log_issue(test_name, "Test", f"VP Racing test failed: {str(e)}", str(e))
            self.test_results[test_name] = "ERROR"
            
    def test_eft_customer_completion(self, eft_transaction_id):
        """Test EFT Customer Completion with ESIGN signature"""
        test_name = "EFT_Customer_Completion"
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {test_name}")
        print(f"📄 Using EFT Transaction ID: {eft_transaction_id}")
        
        try:
            # Navigate to EFT customer form
            self.page.goto(f"{BASE_URL}/eft_form.html")
            self.page.wait_for_load_state('networkidle')
            
            # Fill EFT customer completion form
            fields_success = all([
                # Company information (may be pre-filled)
                self.safe_fill('#company-name', TEST_DATA["company"], test_name),
                self.safe_fill('#customer-email', TEST_DATA["email"], test_name),
                
                # Bank account details  
                self.safe_fill('#bank-name', TEST_DATA["bank_name"], test_name),
                self.safe_fill('#account-holder-name', TEST_DATA["contact"], test_name),
                self.safe_select('#account-type', "checking", test_name),
                self.safe_fill('#routing-number', TEST_DATA["routing"], test_name),
                self.safe_fill('#account-number', TEST_DATA["account"], test_name),
                
                # Authorization details
                self.safe_fill('#authorization-amount', "50000", test_name),
                self.safe_select('#frequency', "Monthly", test_name)
            ])
            
            if not fields_success:
                self.test_results[test_name] = "FAILED - Form filling"
                return
                
            # Check for ESIGN compliance section
            esign_section = self.page.locator('.esign-disclosure')
            if esign_section.is_visible():
                print("✅ ESIGN disclosure found")
            else:
                self.log_issue(test_name, "ESIGN", "ESIGN disclosure section not visible")
                
            # Check for consent checkbox
            consent_checkbox = self.page.locator('#esign-consent')
            if consent_checkbox.is_visible():
                consent_checkbox.check()
                print("✅ ESIGN consent checked")
            else:
                self.log_issue(test_name, "ESIGN", "ESIGN consent checkbox not found")
                
            # Test signature pad
            canvas = self.page.locator('#signature-pad')
            if canvas.is_visible():
                # Draw signature
                box = canvas.bounding_box()
                if box:
                    self.page.mouse.move(box['x'] + 50, box['y'] + 50)
                    self.page.mouse.down()
                    self.page.mouse.move(box['x'] + 150, box['y'] + 100)
                    self.page.mouse.move(box['x'] + 250, box['y'] + 50)
                    self.page.mouse.up()
                    print("✅ EFT signature drawn")
                else:
                    self.log_issue(test_name, "Frontend", "Could not get signature pad dimensions")
            else:
                self.log_issue(test_name, "Frontend", "Signature pad not visible")
                
            # Submit EFT form
            self.safe_click('#submit-eft', test_name)
            time.sleep(5)
            
            # Check for success
            try:
                success_alert = self.page.locator('.alert-success')
                if success_alert.is_visible():
                    success_text = success_alert.text_content()
                    print(f"✅ EFT completion successful: {success_text}")
                    self.test_results[test_name] = "PASSED"
                    
                    # Verify in database
                    self.check_database_record("eft_form_data", {"customer_email": TEST_DATA["email"]}, test_name)
                    self.check_database_record("electronic_signatures", {"transaction_id": eft_transaction_id}, test_name)
                    
                else:
                    self.log_issue(test_name, "Frontend", "No success message after EFT completion")
                    self.test_results[test_name] = "FAILED - No success response"
                    
            except Exception as e:
                self.log_issue(test_name, "Test", f"EFT completion response check failed: {str(e)}", str(e))
                self.test_results[test_name] = "ERROR"
                
        except Exception as e:
            self.log_issue(test_name, "Test", f"EFT completion test failed: {str(e)}", str(e))
            self.test_results[test_name] = "ERROR"

    def run_comprehensive_tests(self):
        """Run all tests in sequence"""
        print(f"\n🚀 Starting Comprehensive Test Suite: {self.test_run_id}")
        print(f"🌐 Target URL: {BASE_URL}")
        print(f"📧 Test Email: {TEST_DATA['email']}")
        print("=" * 80)
        
        try:
            self.start_browser()
            
            # Test 1: Customer Setup Sales Initiation
            self.test_customer_setup_sales_initiation()
            
            # Test 2: Customer Setup Completion (multi-step)
            self.test_customer_setup_completion()
            
            # Test 3: EFT Sales Initiation
            self.test_eft_sales_initiation()
            
            # Test 3.5: EFT Customer Completion (if we have transaction ID)
            if "EFT_Sales_Initiation" in self.transaction_ids:
                self.test_eft_customer_completion(self.transaction_ids["EFT_Sales_Initiation"])
            else:
                print("⚠️ Skipping EFT customer completion - no transaction ID from sales initiation")
            
            # Test 4: P66 LOI Direct Submission
            self.test_p66_loi_submission()
            
            # Test 5: VP Racing LOI Direct Submission
            self.test_vp_racing_loi_submission()
            
            # Test 6: P66 Signature Flow (if we have transaction ID)
            if "P66_LOI_Submission" in self.transaction_ids:
                self.test_signature_workflow(self.transaction_ids["P66_LOI_Submission"], "P66_LOI")
            else:
                print("⚠️ Skipping P66 signature test - no transaction ID from submission")
                
            # Test 7: VP Racing Signature Flow (if we have transaction ID)
            if "VP_Racing_LOI_Submission" in self.transaction_ids:
                self.test_signature_workflow(self.transaction_ids["VP_Racing_LOI_Submission"], "VP_Racing_LOI")
            else:
                print("⚠️ Skipping VP Racing signature test - no transaction ID from submission")
                
        finally:
            self.stop_browser()
            
        # Print comprehensive results
        self.print_results()
        
    def print_results(self):
        """Print comprehensive test results and issues"""
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE TEST RESULTS")
        print(f"{'='*80}")
        
        passed = sum(1 for result in self.test_results.values() if result == "PASSED")
        failed = sum(1 for result in self.test_results.values() if "FAILED" in result)
        errors = sum(1 for result in self.test_results.values() if "ERROR" in result)
        skipped = sum(1 for result in self.test_results.values() if "SKIPPED" in result)
        partial = sum(1 for result in self.test_results.values() if "PARTIAL" in result)
        
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Errors: {errors}")
        print(f"⏭️ Skipped: {skipped}")
        print(f"🔄 Partial: {partial}")
        print(f"📊 Success Rate: {(passed / total * 100):.1f}%" if total > 0 else "0%")
        
        print(f"\n{'='*80}")
        print("📋 DETAILED TEST RESULTS")
        print(f"{'='*80}")
        
        for test_name, result in self.test_results.items():
            status_icon = {
                "PASSED": "✅",
                "FAILED": "❌", 
                "ERROR": "⚠️",
                "SKIPPED": "⏭️",
                "PARTIAL": "🔄"
            }
            
            # Find appropriate icon
            icon = "❓"
            for status, status_icon_val in status_icon.items():
                if status in result:
                    icon = status_icon_val
                    break
                    
            print(f"{icon} {test_name}: {result}")
            if test_name in self.transaction_ids:
                print(f"   📄 Transaction ID: {self.transaction_ids[test_name]}")
                
        # Show issues
        if self.issues:
            print(f"\n{'='*80}")
            print(f"🐛 ISSUES FOUND: {len(self.issues)}")
            print(f"{'='*80}")
            
            for issue in self.issues:
                print(f"[{issue['severity']}] {issue['test_name']} - {issue['category']}: {issue['description']}")
                if issue['error']:
                    print(f"   Error: {issue['error']}")
                    
        # Save results
        results_file = f"comprehensive_test_results_{self.test_run_id}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_run_id": self.test_run_id,
                "timestamp": datetime.now().isoformat(),
                "test_results": self.test_results,
                "transaction_ids": self.transaction_ids,
                "issues": self.issues,
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "skipped": skipped,
                    "partial": partial,
                    "success_rate": (passed / total * 100) if total > 0 else 0
                }
            }, f, indent=2)
            
        print(f"\n💾 Results saved to: {results_file}")

def main():
    """Main execution"""
    suite = ComprehensiveTestSuite()
    suite.run_comprehensive_tests()

if __name__ == "__main__":
    main()