#!/usr/bin/env python3
"""
Debug script to examine form elements
"""

from playwright.sync_api import sync_playwright
import time

BASE_URL = "https://loi-automation-api.onrender.com"

def debug_form_elements():
    """Debug what elements are actually on each form"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("🔍 DEBUGGING FORM ELEMENTS")
        print("=" * 60)
        
        try:
            # 1. Debug EFT Form
            print("\n📋 EFT FORM DEBUG")
            page.goto(f"{BASE_URL}")
            page.wait_for_load_state('networkidle')
            
            # Click EFT link
            eft_link = page.locator('a:has-text("EFT")')
            if eft_link.count() > 0:
                eft_link.first.click()
                page.wait_for_load_state('networkidle')
                print(f"URL: {page.url}")
                
                # List all input fields
                inputs = page.locator('input')
                print(f"Found {inputs.count()} input fields:")
                for i in range(inputs.count()):
                    input_el = inputs.nth(i)
                    input_id = input_el.get_attribute('id')
                    input_name = input_el.get_attribute('name')
                    input_type = input_el.get_attribute('type')
                    print(f"  {i+1}. ID: {input_id}, Name: {input_name}, Type: {input_type}")
                
                # List all select fields
                selects = page.locator('select')
                print(f"Found {selects.count()} select fields:")
                for i in range(selects.count()):
                    select_el = selects.nth(i)
                    select_id = select_el.get_attribute('id')
                    select_name = select_el.get_attribute('name')
                    print(f"  {i+1}. ID: {select_id}, Name: {select_name}")
            
            time.sleep(2)
            
            # 2. Debug P66 LOI Form
            print("\n⛽ P66 LOI FORM DEBUG")
            page.goto(f"{BASE_URL}")
            page.wait_for_load_state('networkidle')
            
            # Click P66 link
            p66_link = page.locator('a:has-text("Phillips 66")')
            if p66_link.count() > 0:
                p66_link.first.click()
                page.wait_for_load_state('networkidle')
                print(f"URL: {page.url}")
                
                # List submit buttons
                buttons = page.locator('button')
                print(f"Found {buttons.count()} buttons:")
                for i in range(buttons.count()):
                    button_el = buttons.nth(i)
                    button_text = button_el.text_content()
                    button_type = button_el.get_attribute('type')
                    print(f"  {i+1}. Text: '{button_text}', Type: {button_type}")
                
                # Check for checkboxes
                checkboxes = page.locator('input[type="checkbox"]')
                print(f"Found {checkboxes.count()} checkboxes:")
                for i in range(checkboxes.count()):
                    checkbox_el = checkboxes.nth(i)
                    checkbox_id = checkbox_el.get_attribute('id')
                    checkbox_name = checkbox_el.get_attribute('name')
                    print(f"  {i+1}. ID: {checkbox_id}, Name: {checkbox_name}")
            
            time.sleep(5)  # Keep browser open to see results
            
        finally:
            browser.close()

if __name__ == "__main__":
    debug_form_elements()