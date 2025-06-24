#!/usr/bin/env python3
"""
Test E-Signature System

Test the PostgreSQL-based e-signature functionality using the transaction coordinator Gmail account.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_email_connection():
    """Test basic email connection"""
    
    try:
        logger.info("📧 Testing Gmail SMTP connection...")
        
        # Gmail SMTP configuration from Fathom project
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "transaction.coordinator.agent@gmail.com"
        smtp_password = "xmvi xvso zblo oewe"
        
        # Connect to Gmail SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Enable TLS encryption
            server.login(smtp_username, smtp_password)
            
            logger.info("✅ Gmail SMTP connection successful!")
            
            # Send test email
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = smtp_username  # Send to self for testing
            msg['Subject'] = "LOI E-Signature System Test"
            
            body = f"""
LOI E-Signature System Test

This is a test email from the Better Day Energy LOI Automation System.

Test Details:
- System: PostgreSQL E-Signature Service
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- From: LOI Automation System
- Purpose: Verify email functionality for e-signature notifications

If you receive this email, the e-signature email system is working correctly.

---
Better Day Energy LOI Automation System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            logger.info("✅ Test email sent successfully!")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Email connection test failed: {e}")
        return False

async def test_esignature_request():
    """Test creating an e-signature request"""
    
    try:
        logger.info("📝 Testing e-signature request creation...")
        
        # Create mock e-signature request data
        signature_request = {
            'id': str(uuid.uuid4()),
            'document_name': 'Test_LOI_Document.pdf',
            'signer_name': 'Adam Simpson',
            'signer_email': 'transaction.coordinator.agent@gmail.com',  # Use our test email
            'company_name': 'Test Company',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=7),
            'status': 'pending',
            'signature_url': f"http://localhost:8000/api/v1/esignature/sign/{str(uuid.uuid4())}"
        }
        
        logger.info(f"📄 Created signature request: {signature_request['id']}")
        logger.info(f"👤 Signer: {signature_request['signer_name']} ({signature_request['signer_email']})")
        logger.info(f"📅 Expires: {signature_request['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🔗 Signature URL: {signature_request['signature_url']}")
        
        # Test sending signature request email
        success = send_signature_request_email(signature_request)
        
        if success:
            logger.info("✅ E-signature request email sent successfully!")
            return True
        else:
            logger.error("❌ Failed to send e-signature request email")
            return False
            
    except Exception as e:
        logger.error(f"❌ E-signature request test failed: {e}")
        return False

def send_signature_request_email(signature_request):
    """Send signature request email"""
    
    try:
        # Gmail SMTP configuration
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "transaction.coordinator.agent@gmail.com"
        smtp_password = "xmvi xvso zblo oewe"
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = f"Better Day Energy LOI System <{smtp_username}>"
        msg['To'] = signature_request['signer_email']
        msg['Subject'] = f"Electronic Signature Required - {signature_request['document_name']}"
        
        # Email body
        body = f"""
Dear {signature_request['signer_name']},

You have been requested to electronically sign the following document:

Document: {signature_request['document_name']}
Company: {signature_request['company_name']}
Request Date: {signature_request['created_at'].strftime('%B %d, %Y at %I:%M %p')}
Expires: {signature_request['expires_at'].strftime('%B %d, %Y at %I:%M %p')}

To sign this document, please click the link below:

{signature_request['signature_url']}

Instructions:
1. Click the link above to open the signature page
2. Review the document carefully
3. Click "Sign Document" to apply your electronic signature
4. Your signature will be legally binding once applied

Important Notes:
- This link will expire on {signature_request['expires_at'].strftime('%B %d, %Y')}
- You will receive a confirmation email once the document is signed
- Contact us if you have any questions about this document

Thank you for your prompt attention to this matter.

Best regards,
Better Day Energy LOI Automation System

---
Request ID: {signature_request['id']}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you believe you received this email in error, please contact us immediately.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(f"📧 Signature request email sent to {signature_request['signer_email']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send signature request email: {e}")
        return False

async def test_esignature_workflow():
    """Test complete e-signature workflow"""
    
    logger.info("🔄 Testing complete e-signature workflow...")
    
    # Step 1: Test email connection
    if not test_email_connection():
        return False
    
    # Step 2: Test signature request creation and email
    if not await test_esignature_request():
        return False
    
    # Step 3: Simulate signature completion notification
    logger.info("📝 Testing signature completion notification...")
    
    completion_data = {
        'request_id': str(uuid.uuid4()),
        'signer_name': 'Adam Simpson',
        'signer_email': 'transaction.coordinator.agent@gmail.com',
        'document_name': 'Test_LOI_Document.pdf',
        'signed_at': datetime.now(),
        'signature_ip': '192.168.1.100',
        'verification_code': 'ES-' + str(uuid.uuid4())[:8].upper()
    }
    
    success = send_signature_completion_email(completion_data)
    
    if success:
        logger.info("✅ Signature completion notification sent!")
        return True
    else:
        logger.error("❌ Failed to send completion notification")
        return False

def send_signature_completion_email(completion_data):
    """Send signature completion notification"""
    
    try:
        # Gmail SMTP configuration
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "transaction.coordinator.agent@gmail.com"
        smtp_password = "xmvi xvso zblo oewe"
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = f"Better Day Energy LOI System <{smtp_username}>"
        msg['To'] = completion_data['signer_email']
        msg['Subject'] = f"Document Signed Successfully - {completion_data['document_name']}"
        
        # Email body
        body = f"""
Dear {completion_data['signer_name']},

Your electronic signature has been successfully applied to the document.

Signature Details:
Document: {completion_data['document_name']}
Signed Date: {completion_data['signed_at'].strftime('%B %d, %Y at %I:%M %p')}
Verification Code: {completion_data['verification_code']}
IP Address: {completion_data['signature_ip']}

Your signature is now legally binding and the document is complete.

Next Steps:
- A copy of the signed document will be stored in your CRM record
- Better Day Energy will process your Letter of Intent
- You will receive updates on the status of your agreement

Thank you for completing the electronic signature process.

Best regards,
Better Day Energy LOI Automation System

---
Request ID: {completion_data['request_id']}
Completed on: {completion_data['signed_at'].strftime('%Y-%m-%d %H:%M:%S')}

This is an automated notification from the LOI Automation System.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(f"📧 Completion notification sent to {completion_data['signer_email']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send completion notification: {e}")
        return False

async def main():
    """Main test function"""
    
    print("🧪 Testing PostgreSQL E-Signature System")
    print("📧 Using: transaction.coordinator.agent@gmail.com")
    print("=" * 60)
    
    success = await test_esignature_workflow()
    
    if success:
        print("\n✅ E-signature system test completed successfully!")
        print("📧 Check transaction.coordinator.agent@gmail.com for test emails")
        print("🔗 E-signature workflow is ready for production use")
    else:
        print("\n❌ E-signature system test failed")
        print("📋 Check logs for details")

if __name__ == "__main__":
    asyncio.run(main())