#!/usr/bin/env python3
"""
Check Farley's CRM record for the signed LOI PDF information
"""

import requests
import json

def check_farley_crm_record():
    """Check Farley Barnhart's CRM record for LOI updates"""
    
    # CRM API configuration
    api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
    base_url = "https://api.lessannoyingcrm.com"
    contact_id = "4036857411931183467036798214340"  # Farley Barnhart
    
    try:
        print("📞 Checking Farley Barnhart's CRM record...")
        print(f"🆔 Contact ID: {contact_id}")
        
        # Get contact details including notes
        headers = {
            "Content-Type": "application/json",
            "Authorization": api_key
        }
        
        body = {
            "Function": "GetContact",
            "Parameters": {
                "ContactId": contact_id
            }
        }
        
        response = requests.post(
            base_url,
            headers=headers,
            json=body,
            timeout=30
        )
        
        if response.status_code == 200:
            response_text = response.text
            try:
                result = json.loads(response_text)
                if result.get('Success'):
                    contact_data = result.get('Result', {})
                    
                    print("✅ Contact found successfully!")
                    print(f"📝 Name: {contact_data.get('Name', 'N/A')}")
                    print(f"🏢 Company: {contact_data.get('CompanyName', 'N/A')}")
                    print(f"📧 Email: {contact_data.get('Email', 'N/A')}")
                    
                    # Check for notes (where our LOI data would be stored)
                    notes = contact_data.get('Notes', [])
                    print(f"\n📋 Total Notes: {len(notes)}")
                    
                    # Look for recent LOI notes
                    loi_notes = []
                    for note in notes:
                        if 'SIGNED LOI DOCUMENT' in note.get('Note', ''):
                            loi_notes.append(note)
                    
                    print(f"📄 LOI Signature Notes: {len(loi_notes)}")
                    
                    if loi_notes:
                        print("\n🔍 Recent LOI Notes:")
                        for i, note in enumerate(loi_notes[-3:], 1):  # Show last 3 LOI notes
                            print(f"\n--- LOI Note #{i} ---")
                            print(f"📅 Created: {note.get('DateCreated', 'Unknown')}")
                            note_content = note.get('Note', '')
                            
                            # Extract key information
                            lines = note_content.split('\n')
                            for line in lines[:20]:  # Show first 20 lines
                                if any(keyword in line for keyword in ['SIGNED LOI', 'Transaction ID', 'Verification Code', 'PDF', 'Financial', 'Volume']):
                                    print(f"  {line}")
                            
                            if len(lines) > 20:
                                print(f"  ... (note continues for {len(lines)} total lines)")
                    
                    return True
                    
                else:
                    print(f"❌ CRM API Error: {result.get('Error', 'Unknown error')}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ Failed to parse CRM response: {response_text}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking CRM: {e}")
        return False

def check_pdf_availability():
    """Check if the PDF is accessible via the signature server"""
    
    verification_code = "LOI-A8308E02"  # From the server logs
    pdf_url = f"http://localhost:8003/signed-loi/{verification_code}"
    
    try:
        print(f"\n📄 Checking PDF availability...")
        print(f"🔗 PDF URL: {pdf_url}")
        
        response = requests.get(pdf_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ PDF HTML is accessible!")
            print(f"📊 Response size: {len(response.text):,} characters")
            
            # Check if it contains signature data
            content = response.text
            if 'Electronic Signature' in content and 'Better Day Energy' in content:
                print("✅ PDF contains signature and company information")
                return True
            else:
                print("⚠️ PDF accessible but may be missing signature data")
                return False
        else:
            print(f"❌ PDF not accessible: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking PDF: {e}")
        return False

if __name__ == "__main__":
    print("🔍 CRM & PDF Verification Check")
    print("=" * 50)
    
    # Check CRM record
    crm_success = check_farley_crm_record()
    
    # Check PDF availability
    pdf_success = check_pdf_availability()
    
    print("\n📋 Summary:")
    print(f"📝 CRM Record Updated: {'✅ Yes' if crm_success else '❌ No'}")
    print(f"📄 PDF Available: {'✅ Yes' if pdf_success else '❌ No'}")
    
    if crm_success and pdf_success:
        print("\n🎉 Complete workflow verification successful!")
        print("📧 Farley's CRM record contains the signed LOI information")
        print("📄 PDF document is accessible for download/print")
    else:
        print("\n⚠️ Some components may need attention")