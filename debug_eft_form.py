#!/usr/bin/env python3
"""
Debug EFT Form Field Visibility
Check if Federal Tax ID field is visible on the deployed form
"""

from playwright.sync_api import sync_playwright
import time

def debug_eft_form():
    """Debug the EFT form to see what fields are visible"""
    print("🔍 Debugging EFT Form Field Visibility")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to EFT form
            print(f"🌐 Navigating to EFT form...")
            page.goto("https://loi-automation-api.onrender.com/eft_form.html")
            page.wait_for_load_state('networkidle')
            
            # Check for federal tax ID field
            print("🔍 Checking for Federal Tax ID field...")
            federal_tax_field = page.locator('#federal-tax-id')
            
            if federal_tax_field.count() > 0:
                print("✅ Federal Tax ID field found in DOM")
                
                # Check if it's visible
                is_visible = federal_tax_field.is_visible()
                print(f"👁️ Federal Tax ID field visible: {is_visible}")
                
                # Get its properties
                if is_visible:
                    value = federal_tax_field.input_value()
                    print(f"📝 Current value: '{value}'")
                else:
                    # Check CSS properties
                    display = page.evaluate("document.getElementById('federal-tax-id').style.display")
                    print(f"🎨 CSS display: {display}")
                    
                    # Check if parent is visible
                    parent_visible = federal_tax_field.locator('..').is_visible()
                    print(f"👁️ Parent container visible: {parent_visible}")
            else:
                print("❌ Federal Tax ID field NOT found in DOM")
            
            # List all form fields
            print("\n📋 All form fields found:")
            form_fields = page.locator('form input, form select')
            count = form_fields.count()
            
            for i in range(count):
                field = form_fields.nth(i)
                field_id = field.get_attribute('id')
                field_name = field.get_attribute('name')
                is_required = field.get_attribute('required') is not None
                is_visible = field.is_visible()
                
                status = "✅" if is_visible else "❌"
                req_marker = " (REQUIRED)" if is_required else ""
                print(f"   {status} {field_id}: {field_name}{req_marker}")
            
            # Keep browser open for inspection
            print("\n🔍 Browser will stay open for 30 seconds for inspection...")
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    debug_eft_form()