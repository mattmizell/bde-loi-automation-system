#!/usr/bin/env python3
"""
Debug P66 form response timing and JavaScript execution
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

def debug_p66_response_handling():
    """Debug P66 form response timing and JavaScript"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Listen to console logs
        def handle_console(msg):
            print(f"🖥️ Console: {msg.text}")
            
        page.on("console", handle_console)
        
        # Listen to network requests
        def handle_response(response):
            if "/api/v1/loi/submit" in response.url:
                print(f"🌐 API Response: {response.status} - {response.url}")
                if response.status == 200:
                    try:
                        response_data = response.json()
                        print(f"📄 API Data: {response_data}")
                    except:
                        print(f"📄 API Text: {response.text()}")
                        
        page.on("response", handle_response)
        
        print("🔍 DEBUGGING P66 RESPONSE HANDLING")
        print("=" * 60)
        
        try:
            # Navigate to P66 form
            page.goto(f"{BASE_URL}/p66_loi_form.html")
            page.wait_for_load_state('networkidle')
            print(f"📄 Loaded P66 form")
            
            # Fill form quickly
            print("📝 Filling form...")
            page.fill('#station-name', "Claude's Test Phillips 66")
            page.fill('#station-address', TEST_DATA["address"])
            page.fill('#station-city', TEST_DATA["city"])
            page.fill('#station-state', TEST_DATA["state"])
            page.fill('#station-zip', TEST_DATA["zip"])
            page.fill('#gasoline-volume', "50000")
            page.fill('#diesel-volume', "20000")
            page.fill('#current-brand', "Independent")
            page.fill('#brand-expiration', "2025-12-31")
            page.fill('#start-date', "2025-08-01")
            page.select_option('#contract-term', "10")
            page.fill('#volume-incentive', "25000")
            page.fill('#image-funding', "15000")
            page.fill('#equipment-funding', "10000")
            page.check('#canopy')
            page.check('#dispensers')
            page.fill('#special-requirements', "Debug response timing test")
            page.fill('#representative-name', TEST_DATA["contact"])
            page.fill('#representative-title', "General Manager")
            page.fill('#contact-email', TEST_DATA["email"])
            page.fill('#contact-phone', TEST_DATA["phone"])
            print("✅ Form filled")
            
            # Take screenshot before submit
            page.screenshot(path="before_submit.png")
            print("📸 Screenshot taken: before_submit.png")
            
            # Submit and monitor closely
            print("🚀 Submitting form...")
            page.click('#submit-btn')
            
            # Wait and take multiple screenshots to see what happens
            for i in range(15):
                time.sleep(1)
                page.screenshot(path=f"after_submit_{i+1}s.png")
                
                # Check current state
                alert = page.locator('.alert').first
                if alert.is_visible():
                    alert_text = alert.text_content()
                    print(f"📋 Alert at {i+1}s: {alert_text[:100]}...")
                    
                    if "successfully" in alert_text.lower():
                        print(f"✅ Success message found at {i+1} seconds!")
                        break
                    elif "transaction id" in alert_text.lower():
                        print(f"✅ Transaction ID found at {i+1} seconds!")
                        break
                else:
                    print(f"⏳ No alert visible at {i+1}s")
                    
            # Final state check
            print("\n📊 Final state check:")
            all_alerts = page.locator('.alert')
            alert_count = all_alerts.count()
            print(f"Total alerts: {alert_count}")
            
            for i in range(alert_count):
                alert_text = all_alerts.nth(i).text_content()
                alert_class = all_alerts.nth(i).get_attribute('class')
                print(f"Alert {i+1}: {alert_class} - {alert_text[:100]}...")
                
            # Check form visibility
            form = page.locator('#loi-form')
            form_visible = form.is_visible()
            print(f"Form visible: {form_visible}")
            
            # Keep browser open for manual inspection
            print("\n⏰ Keeping browser open for 10 seconds for manual inspection...")
            time.sleep(10)
            
        finally:
            browser.close()

if __name__ == "__main__":
    debug_p66_response_handling()