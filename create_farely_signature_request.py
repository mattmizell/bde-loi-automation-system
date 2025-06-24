#!/usr/bin/env python3
"""
Create Signature Request for Farely Barnhart

Generate a DocuSign-like signature request for Farely Barnhart's LOI and send
the signature routing email with the web interface link.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for the signature request (shared with signature server)
signature_requests = {}

async def create_farely_signature_request():
    """Create signature request for Farely Barnhart"""
    
    try:
        logger.info("📝 Creating signature request for Farely Barnhart...")
        
        # Generate IDs
        request_id = str(uuid.uuid4())
        signature_token = str(uuid.uuid4())
        transaction_id = f"LOI-FARELY-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create signature request data
        signature_request = {
            'request_id': request_id,
            'transaction_id': transaction_id,
            'signer_name': 'Farely Barnhart',
            'signer_email': 'matt.mizell@gmail.com',
            'company_name': "Farley's Gas and Go",
            'document_name': 'LOI_Farleys_Gas_and_Go_Fuel_Supply_Agreement.pdf',
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
            'status': 'pending',
            'signature_token': signature_token,
            'signature_url': f"http://localhost:8001/sign/{signature_token}",
            'monthly_gasoline_volume': 85000,
            'monthly_diesel_volume': 25000,
            'total_monthly_volume': 110000,
            'annual_volume': 1320000,
            'image_funding_amount': 75000,
            'incentive_funding_amount': 50000,
            'total_estimated_incentives': 125000,
            'estimated_conversion_date': '2025-08-01'
        }
        
        # Store signature request (in production, this would be in PostgreSQL)
        signature_requests[request_id] = signature_request
        
        logger.info(f"✅ Signature request created:")
        logger.info(f"   Request ID: {request_id}")
        logger.info(f"   Transaction ID: {transaction_id}")
        logger.info(f"   Signer: {signature_request['signer_name']}")
        logger.info(f"   Email: {signature_request['signer_email']}")
        logger.info(f"   Company: {signature_request['company_name']}")
        logger.info(f"   Signature URL: {signature_request['signature_url']}")
        logger.info(f"   Expires: {datetime.fromisoformat(signature_request['expires_at']).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Send signature request email
        email_success = await send_signature_request_email(signature_request)
        
        if email_success:
            logger.info("📧 Signature request email sent successfully!")
            return signature_request
        else:
            logger.error("❌ Failed to send signature request email")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to create signature request: {e}")
        return None

async def send_signature_request_email(signature_request):
    """Send DocuSign-like signature request email"""
    
    try:
        # Gmail SMTP configuration
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "transaction.coordinator.agent@gmail.com"
        smtp_password = "xmvi xvso zblo oewe"
        
        # Create comprehensive signature request email
        msg = MIMEMultipart()
        msg['From'] = f"Better Day Energy LOI Team <{smtp_username}>"
        msg['To'] = signature_request['signer_email']
        msg['Subject'] = f"🖊️ SIGNATURE REQUIRED: {signature_request['company_name']} Fuel Supply Agreement"
        
        # DocuSign-style email body
        body = f"""
{signature_request['signer_name']}, please sign your Letter of Intent

You have been requested to review and sign the following document:

📄 DOCUMENT TO SIGN:
{signature_request['document_name']}
Better Day Energy Fuel Supply Agreement

👤 SIGNER INFORMATION:
Name: {signature_request['signer_name']}
Company: {signature_request['company_name']}
Email: {signature_request['signer_email']}

📋 AGREEMENT SUMMARY:
• Monthly Gasoline Volume: {signature_request['monthly_gasoline_volume']:,} gallons
• Monthly Diesel Volume: {signature_request['monthly_diesel_volume']:,} gallons
• Total Monthly Volume: {signature_request['total_monthly_volume']:,} gallons
• Annual Volume: {signature_request['annual_volume']:,} gallons

💰 FINANCIAL PACKAGE:
• Image Program Funding: ${signature_request['image_funding_amount']:,}
• Annual Volume Incentives: ${signature_request['incentive_funding_amount']:,}
• Total First Year Value: ${signature_request['total_estimated_incentives']:,}

⏰ IMPORTANT DEADLINE:
This signature request expires on {datetime.fromisoformat(signature_request['expires_at']).strftime('%B %d, %Y at %I:%M %p')}

🖊️ REVIEW AND SIGN:
Click here to review and sign your document:

{signature_request['signature_url']}

📋 SIGNING PROCESS:
1. Click the link above to open the signature interface
2. Review the complete Letter of Intent document
3. Verify all terms and conditions are accurate
4. Apply your electronic signature using your mouse or finger
5. Complete the signing process
6. Receive confirmation and verification code

🔒 SECURITY & LEGAL INFORMATION:
• Your electronic signature will be legally binding
• The signing process uses bank-grade security
• All signature events are logged with timestamps and IP addresses
• This agreement will have the same legal effect as a handwritten signature

📞 NEED ASSISTANCE?
If you have questions about the document or signing process:
• Reply to this email for document questions
• Call our LOI support team for technical assistance
• Contact your sales representative for term clarifications

⚠️ IMPORTANT REMINDERS:
• Do not share this signature link with others
• Review all terms carefully before signing
• Contact us immediately if any information is incorrect
• Save your verification code after signing for your records

🤝 PARTNERSHIP COMMITMENT:
This LOI represents the beginning of a valuable partnership between {signature_request['company_name']} and Better Day Energy. We're committed to providing exceptional service and competitive pricing for your fuel supply needs.

Thank you for choosing Better Day Energy as your fuel supply partner!

---
SIGNATURE REQUEST DETAILS:
Request ID: {signature_request['request_id']}
Transaction ID: {signature_request['transaction_id']}
Created: {datetime.fromisoformat(signature_request['created_at']).strftime('%B %d, %Y at %I:%M %p')}
Expires: {datetime.fromisoformat(signature_request['expires_at']).strftime('%B %d, %Y at %I:%M %p')}

🔐 SECURITY NOTICE:
This email contains a secure signature link. If you received this email in error, please notify us immediately and do not click the signature link.

Better Day Energy LOI Automation System
Professional Fuel Distribution Services
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

def save_signature_request_for_server(signature_request):
    """Save signature request data for the signature server to access"""
    
    import json
    from pathlib import Path
    
    # Save to JSON file for the signature server to read
    data_file = Path("./signature_request_data.json")
    
    with open(data_file, 'w') as f:
        json.dump({signature_request['request_id']: signature_request}, f, indent=2)
    
    logger.info(f"💾 Signature request data saved to {data_file}")

async def main():
    """Main function"""
    
    print("🖊️ Creating Signature Request for Farely Barnhart")
    print("🏢 Company: Farley's Gas and Go")
    print("📧 Email: matt.mizell@gmail.com")
    print("💰 Deal Value: $125,000 first year")
    print("=" * 70)
    
    # Create signature request
    signature_request = await create_farely_signature_request()
    
    if signature_request:
        # Save for signature server
        save_signature_request_for_server(signature_request)
        
        print("\n✅ SIGNATURE REQUEST CREATED SUCCESSFULLY!")
        print(f"📧 Email sent to: {signature_request['signer_email']}")
        print(f"🔗 Signature URL: {signature_request['signature_url']}")
        print(f"⏰ Expires: {datetime.fromisoformat(signature_request['expires_at']).strftime('%B %d, %Y at %I:%M %p')}")
        print(f"🆔 Request ID: {signature_request['request_id']}")
        print("\n📋 NEXT STEPS:")
        print("1. 🖥️ Start the signature server: python3 signature_server.py")
        print("2. 📧 Check matt.mizell@gmail.com for the signature request email")
        print("3. 🖊️ Click the signature link to review and sign the LOI")
        print("4. ✅ Complete the DocuSign-like signature experience")
        print("\n🎉 Ready for Farely to sign his LOI!")
    else:
        print("\n❌ Failed to create signature request")
        print("📋 Check logs for details")

if __name__ == "__main__":
    asyncio.run(main())