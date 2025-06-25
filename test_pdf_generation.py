#!/usr/bin/env python3
"""
Test script for PDF generation functionality
"""

import tempfile
import os
from integrated_pdf_signature_server import IntegratedSignatureHandler

def test_pdf_generation():
    """Test the PDF generation functionality"""
    
    # Create a sample signature request
    signature_request = {
        'transaction_id': 'TEST-12345',
        'signer_name': 'John Test',
        'signer_email': 'john@example.com',
        'company_name': 'Test Company LLC',
        'business_address': '123 Test St, Test City, TS 12345',
        'deal_terms': {
            'total_gallons': 50000,
            'price_per_gallon': 2.45,
            'signing_incentive': 2500,
            'contract_duration': 24
        }
    }
    
    verification_code = 'TEST-VERIFY-123'
    
    # Create handler instance
    handler = IntegratedSignatureHandler()
    
    # Test HTML generation
    print("🔍 Testing HTML generation...")
    html_content = handler.generate_signed_document_html(signature_request, verification_code)
    print(f"✅ HTML generated ({len(html_content)} characters)")
    
    # Test PDF generation
    print("🔍 Testing PDF generation...")
    pdf_path = "/tmp/test_signed_document.pdf"
    pdf_success = handler.html_to_pdf(html_content, pdf_path)
    
    if pdf_success:
        print(f"✅ PDF generated successfully: {pdf_path}")
        if os.path.exists(pdf_path):
            print(f"   File size: {os.path.getsize(pdf_path)} bytes")
        else:
            # Check for HTML fallback
            html_path = pdf_path.replace('.pdf', '.html')
            if os.path.exists(html_path):
                print(f"   HTML fallback created: {html_path}")
                print(f"   File size: {os.path.getsize(html_path)} bytes")
    else:
        print("❌ PDF generation failed")
        # Check for HTML fallback
        html_path = pdf_path.replace('.pdf', '.html')
        if os.path.exists(html_path):
            print(f"✅ HTML fallback created: {html_path}")
            print(f"   File size: {os.path.getsize(html_path)} bytes")
    
    # Test email preparation (without actually sending)
    print("🔍 Testing email preparation...")
    
    # Mock the email sending function
    def mock_email_test():
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        
        # Check if file exists
        file_path = pdf_path
        file_extension = ".pdf"
        file_type = "PDF"
        
        if not os.path.exists(pdf_path):
            html_path = pdf_path.replace('.pdf', '.html')
            if os.path.exists(html_path):
                file_path = html_path
                file_extension = ".html"
                file_type = "HTML"
            else:
                print("❌ No file found for email attachment")
                return False
        
        # Create email (without sending)
        msg = MIMEMultipart()
        msg['Subject'] = f"Your Signed LOI Document - {signature_request['company_name']}"
        msg['From'] = "test@betterdayenergy.com"
        msg['To'] = signature_request['signer_email']
        
        # Attach the document file
        with open(file_path, 'rb') as f:
            if file_extension == '.pdf':
                part = MIMEBase('application', 'pdf')
            else:
                part = MIMEBase('text', 'html')
            
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="Signed_LOI_{verification_code}{file_extension}"'
            )
            msg.attach(part)
        
        print(f"✅ Email prepared with {file_type} attachment")
        print(f"   Subject: {msg['Subject']}")
        print(f"   To: {msg['To']}")
        print(f"   Attachment: Signed_LOI_{verification_code}{file_extension}")
        return True
    
    mock_email_test()
    
    print("\n🎉 PDF generation test completed!")
    print(f"📄 Document available at: {pdf_path}")
    
    # Clean up
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    html_path = pdf_path.replace('.pdf', '.html')
    if os.path.exists(html_path):
        os.remove(html_path)

if __name__ == "__main__":
    test_pdf_generation()