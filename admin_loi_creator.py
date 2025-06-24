#!/usr/bin/env python3
"""
Admin LOI Creator - Simple interface for Adam to create new LOI signature requests
"""

import json
import uuid
from datetime import datetime, timedelta
import os

def create_new_loi():
    """Interactive LOI creator for Adam"""
    
    print("🎯 Better Day Energy - LOI Creator")
    print("=" * 50)
    
    # Get customer information
    print("\n📋 Customer Information:")
    signer_name = input("Customer Name: ").strip()
    if not signer_name:
        signer_name = "Customer Name"
    
    signer_email = input("Customer Email: ").strip()
    if not signer_email:
        signer_email = "customer@example.com"
    
    company_name = input("Company Name: ").strip()
    if not company_name:
        company_name = f"{signer_name}'s Business"
    
    # Generate unique identifiers
    transaction_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"
    signature_token = str(uuid.uuid4())
    
    # Create LOI request
    new_request = {
        "transaction_id": transaction_id,
        "signature_token": signature_token,
        "signer_name": signer_name,
        "signer_email": signer_email,
        "company_name": company_name,
        "document_name": "VP Racing Fuel Supply Agreement - Letter of Intent",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    # Load existing requests
    data_file = "signature_request_data.json"
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            signature_data = json.load(f)
    else:
        signature_data = {}
    
    # Add new request
    request_key = f"request_{len(signature_data) + 1:03d}"
    signature_data[request_key] = new_request
    
    # Save updated data
    with open(data_file, 'w') as f:
        json.dump(signature_data, f, indent=2)
    
    # Generate URLs
    local_url = f"http://localhost:8001/sign/{signature_token}"
    production_url = f"https://loi-automation-api.onrender.com/sign/{signature_token}"
    
    print("\n✅ LOI Created Successfully!")
    print("=" * 50)
    print(f"📧 Customer: {signer_name}")
    print(f"🏢 Company: {company_name}")
    print(f"📮 Email: {signer_email}")
    print(f"🆔 Transaction ID: {transaction_id}")
    print(f"🎫 Signature Token: {signature_token}")
    print(f"📅 Expires: {new_request['expires_at'][:10]}")
    print()
    print("🔗 Signature URLs:")
    print(f"   Local: {local_url}")
    print(f"   Production: {production_url}")
    print()
    
    # Email template
    print("📧 Email Template for Adam:")
    print("-" * 30)
    email_template = f"""
Subject: VP Racing Fuel Supply Agreement - Electronic Signature Required

Dear {signer_name},

Thank you for your interest in partnering with Better Day Energy for your fuel supply needs.

Please review and electronically sign the attached Letter of Intent for our VP Racing Fuel Supply Agreement by clicking the link below:

🔗 Sign Document: {production_url}

Key Benefits:
• $125,000 first-year incentive package
• Competitive pricing with quarterly reviews
• 24/7 emergency fuel supply support
• Dedicated account management

This document expires in 30 days. Please complete your signature at your earliest convenience.

If you have any questions, please contact Adam Simpson directly.

Best regards,
Better Day Energy Team

Transaction ID: {transaction_id}
"""
    print(email_template)
    
    return new_request

def list_existing_lois():
    """Show all existing LOI requests"""
    
    data_file = "signature_request_data.json"
    if not os.path.exists(data_file):
        print("❌ No LOI requests found.")
        return
    
    with open(data_file, 'r') as f:
        signature_data = json.load(f)
    
    print("\n📋 Existing LOI Requests:")
    print("=" * 80)
    
    for key, request in signature_data.items():
        status = request.get('status', 'unknown')
        created = request.get('created_at', 'unknown')[:10]
        expires = request.get('expires_at', 'unknown')[:10]
        
        print(f"🆔 {request.get('transaction_id', 'N/A')}")
        print(f"   👤 {request.get('signer_name', 'N/A')} - {request.get('company_name', 'N/A')}")
        print(f"   📧 {request.get('signer_email', 'N/A')}")
        print(f"   📊 Status: {status} | Created: {created} | Expires: {expires}")
        print(f"   🔗 https://loi-automation-api.onrender.com/sign/{request.get('signature_token', '')}")
        print()

def main():
    """Main menu for LOI management"""
    
    while True:
        print("\n🎯 Better Day Energy - LOI Management")
        print("=" * 40)
        print("1. Create New LOI")
        print("2. List Existing LOIs")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            create_new_loi()
        elif choice == "2":
            list_existing_lois()
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()