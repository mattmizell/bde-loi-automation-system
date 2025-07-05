#!/usr/bin/env python3
"""
Browser test for EFT form initiation workflow
"""

from playwright.sync_api import sync_playwright
import time

def test_eft_initiate_browser():
    """Test the EFT form initiation via browser"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to EFT sales initiation form
            print("🌐 Navigating to EFT sales initiation form...")
            page.goto("https://loi-automation-api.onrender.com/eft/initiate")
            page.wait_for_load_state('networkidle')
            
            # Fill out the form
            print("📝 Filling out EFT initiation form...")
            page.fill('#company-name', 'Test Gas Station LLC')
            page.fill('#customer-email', 'transaction.coordinator.agent@gmail.com')
            page.fill('#customer-phone', '(555) 123-4567')
            page.fill('#federal-tax-id', '12-3456789')
            page.fill('#bank-name', 'First National Bank')
            page.fill('#authorized-name', 'John Smith')
            page.fill('#authorized-title', 'Owner')
            page.fill('#initiated-by', 'Sales Team Test')
            
            # Submit the form
            print("📤 Submitting form...")
            page.click('button[type="submit"]')
            
            # Wait for response
            time.sleep(3)
            
            # Check for success message
            success_element = page.locator('#success-alert')
            if success_element.is_visible():
                success_text = page.locator('#success-message').text_content()
                print(f"✅ SUCCESS: {success_text}")
            else:
                # Check for error
                error_text = page.evaluate("document.body.innerText")
                print(f"❌ Error or unexpected response")
                print(error_text[:500])
            
            # Keep browser open for inspection
            print("\n🔍 Browser will stay open for 10 seconds...")
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_eft_initiate_browser()