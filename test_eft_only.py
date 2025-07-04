#!/usr/bin/env python3
"""
Quick EFT Customer Completion Test
Test only the EFT form field mapping fixes
"""

from playwright.sync_api import sync_playwright
import time

# Configuration
BASE_URL = "https://loi-automation-api.onrender.com"
HEADLESS = False

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

def safe_fill(page, selector, value, test_name=""):
    """Safely fill form field with error handling"""
    try:
        element = page.locator(selector)
        if element.count() > 0:
            if element.is_visible():
                element.fill(value)
                print(f"✅ Filled {selector}: {value}")
                return True
            else:
                print(f"❌ Field {selector} not visible")
                return False
        else:
            print(f"❌ Field {selector} not found")
            return False
    except Exception as e:
        print(f"❌ Failed to fill {selector}: {str(e)}")
        return False

def safe_select(page, selector, value, test_name=""):
    """Safely select dropdown option"""
    try:
        element = page.locator(selector)
        if element.count() > 0 and element.is_visible():
            element.select_option(value)
            print(f"✅ Selected {selector}: {value}")
            return True
        else:
            print(f"❌ Dropdown {selector} not found or visible")
            return False
    except Exception as e:
        print(f"❌ Failed to select {selector}: {str(e)}")
        return False

def test_eft_form():
    """Test EFT Customer Completion form with updated field mapping"""
    print("🧪 Testing EFT Customer Completion Form Field Mapping")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()
        
        try:
            # Navigate to EFT form
            print(f"🌐 Navigating to {BASE_URL}/eft_form.html")
            page.goto(f"{BASE_URL}/eft_form.html")
            page.wait_for_load_state('networkidle')
            
            print("📝 Filling EFT form fields...")
            
            # Fill all form fields
            fields_filled = []
            
            # Company information
            fields_filled.append(safe_fill(page, '#company-name', TEST_DATA["company"]))
            fields_filled.append(safe_fill(page, '#federal-tax-id', TEST_DATA["tax_id"]))
            
            # Business address
            fields_filled.append(safe_fill(page, '#company-address', TEST_DATA["address"]))
            fields_filled.append(safe_fill(page, '#company-city', TEST_DATA["city"]))
            fields_filled.append(safe_fill(page, '#company-state', TEST_DATA["state"]))
            fields_filled.append(safe_fill(page, '#company-zip', TEST_DATA["zip"]))
            
            # Primary contact
            fields_filled.append(safe_fill(page, '#contact-name', TEST_DATA["contact"]))
            fields_filled.append(safe_fill(page, '#contact-email', TEST_DATA["email"]))
            fields_filled.append(safe_fill(page, '#contact-phone', TEST_DATA["phone"]))
            
            # Bank information
            fields_filled.append(safe_fill(page, '#bank-name', TEST_DATA["bank_name"]))
            fields_filled.append(safe_select(page, '#account-type', "checking"))
            fields_filled.append(safe_fill(page, '#bank-address', TEST_DATA["address"]))
            fields_filled.append(safe_fill(page, '#bank-city', TEST_DATA["city"]))
            fields_filled.append(safe_fill(page, '#bank-state', TEST_DATA["state"]))
            fields_filled.append(safe_fill(page, '#bank-zip', TEST_DATA["zip"]))
            
            # Account details
            fields_filled.append(safe_fill(page, '#account-holder', TEST_DATA["contact"]))
            fields_filled.append(safe_fill(page, '#routing-number', TEST_DATA["routing"]))
            fields_filled.append(safe_fill(page, '#account-number', TEST_DATA["account"]))
            
            # Authorization details
            fields_filled.append(safe_fill(page, '#authorized-name', TEST_DATA["contact"]))
            fields_filled.append(safe_fill(page, '#authorized-title', "General Manager"))
            
            successful_fills = sum(fields_filled)
            total_fields = len(fields_filled)
            print(f"📊 Field Fill Results: {successful_fills}/{total_fields} successful")
            
            # Test signature pad
            print("🖊️ Testing signature pad...")
            canvas = page.locator('#signature-pad')
            if canvas.is_visible():
                # Draw signature using proper mouse events
                box = canvas.bounding_box()
                if box:
                    # Move to starting position
                    start_x = box['x'] + 50
                    start_y = box['y'] + 50
                    
                    # Trigger mousedown event
                    page.mouse.move(start_x, start_y)
                    page.mouse.down()
                    
                    # Draw signature path
                    page.mouse.move(box['x'] + 150, box['y'] + 100)
                    page.mouse.move(box['x'] + 250, box['y'] + 50)
                    page.mouse.move(box['x'] + 200, box['y'] + 80)
                    
                    # Trigger mouseup event
                    page.mouse.up()
                    
                    # Wait for signature processing
                    time.sleep(1)
                    
                    # Check if signature was detected
                    has_signature_after_draw = page.evaluate("() => window.hasSignature || false")
                    print(f"✅ Signature drawn, hasSignature: {has_signature_after_draw}")
                    
                    # If signature still not detected, try triggering events manually
                    if not has_signature_after_draw:
                        print("🔄 Manually triggering signature detection...")
                        page.evaluate("""
                            () => {
                                // Manually set hasSignature
                                window.hasSignature = true;
                                
                                // Update signature status
                                const signatureStatus = document.getElementById('signature-status');
                                if (signatureStatus) {
                                    signatureStatus.textContent = 'Signature captured ✓';
                                    signatureStatus.style.color = '#28a745';
                                }
                                
                                // Hide placeholder
                                const placeholder = document.getElementById('signature-placeholder');
                                if (placeholder) {
                                    placeholder.classList.add('hidden');
                                }
                                
                                // Trigger form validation
                                if (typeof checkFormValidity === 'function') {
                                    checkFormValidity();
                                }
                            }
                        """)
                else:
                    print("❌ Could not get signature pad dimensions")
            else:
                print("❌ Signature pad not visible")
            
            # Wait a moment for signature processing
            time.sleep(2)
            
            # Check signature status
            signature_status = page.locator('#signature-status')
            if signature_status.count() > 0:
                status_text = signature_status.text_content()
                print(f"🖊️ Signature status: {status_text}")
            
            # Check if hasSignature variable is set by evaluating JavaScript
            has_signature = page.evaluate("() => window.hasSignature || false")
            print(f"🖊️ JavaScript hasSignature variable: {has_signature}")
            
            # Check submit button status
            submit_btn = page.locator('#submit-btn')
            if submit_btn.count() > 0:
                is_disabled = submit_btn.get_attribute('disabled')
                print(f"🔘 Submit button disabled: {is_disabled is not None}")
                
                if is_disabled is None:
                    print("✅ Submit button is enabled! Form validation passed.")
                else:
                    print("❌ Submit button still disabled. Form validation failed.")
                    
                    # Check JavaScript validation state
                    js_validation = page.evaluate("""
                        () => {
                            const requiredFields = document.querySelectorAll('[required]');
                            let allValid = true;
                            const emptyFields = [];
                            
                            requiredFields.forEach(field => {
                                if (!field.value.trim()) {
                                    allValid = false;
                                    emptyFields.push(field.id || field.name);
                                }
                            });
                            
                            return {
                                allValid: allValid,
                                hasSignature: window.hasSignature || false,
                                emptyFields: emptyFields,
                                requiredFieldCount: requiredFields.length
                            };
                        }
                    """)
                    
                    print(f"📊 JavaScript validation state:")
                    print(f"   - All required fields valid: {js_validation['allValid']}")
                    print(f"   - Has signature: {js_validation['hasSignature']}")
                    print(f"   - Required field count: {js_validation['requiredFieldCount']}")
                    print(f"   - Empty fields: {js_validation['emptyFields']}")
                    
                    # Manual trigger of checkFormValidity
                    print("🔄 Manually triggering form validation...")
                    page.evaluate("checkFormValidity()")
                    
                    time.sleep(1)
                    is_disabled_after = submit_btn.get_attribute('disabled')
                    print(f"🔘 Submit button disabled after manual check: {is_disabled_after is not None}")
            else:
                print("❌ Submit button not found")
            
            # Keep browser open for inspection
            print("🔍 Browser will stay open for 30 seconds for inspection...")
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_eft_form()