#!/usr/bin/env python3
"""
Send signature email for the new LOI
"""

import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Load the signature request data
with open("signature_request_data.json", "r") as f:
    signature_data = json.load(f)

request_data = signature_data["request_001"]

# Email configuration (from Fathom project)
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "transaction.coordinator.agent@gmail.com"
smtp_password = "xmvi xvso zblo oewe"

# Email content
def create_signature_email(request_data):
    """Create professional signature request email"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: #1f4e79; color: white; padding: 20px; text-align: center; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; }}
            .content {{ padding: 30px; }}
            .signature-button {{ 
                display: inline-block; 
                background: #28a745; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 5px; 
                font-weight: bold; 
                margin: 20px 0;
            }}
            .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            .urgent {{ color: #dc3545; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Better Day Energy</h1>
                <h2>Electronic Signature Required</h2>
            </div>
            
            <div class="content">
                <p>Dear {request_data['signer_name']},</p>
                
                <p>Your <strong>Letter of Intent</strong> for the VP Racing Fuel Supply Agreement is ready for your electronic signature.</p>
                
                <div class="details">
                    <h3>Document Details:</h3>
                    <p><strong>Document:</strong> {request_data['document_name']}</p>
                    <p><strong>Company:</strong> {request_data['company_name']}</p>
                    <p><strong>Transaction ID:</strong> {request_data['transaction_id']}</p>
                    <p><strong>Expires:</strong> {datetime.fromisoformat(request_data['expires_at']).strftime('%B %d, %Y')}</p>
                </div>
                
                <p class="urgent">⏰ Action Required: Please sign within 30 days</p>
                
                <center>
                    <a href="http://localhost:8003/sign/{request_data['signature_token']}" class="signature-button">
                        🖊️ SIGN DOCUMENT NOW
                    </a>
                </center>
                
                <div style="margin: 30px 0; padding: 15px; background: #e7f3ff; border-radius: 5px;">
                    <h3>What happens next?</h3>
                    <ol>
                        <li>Click the "Sign Document Now" button above</li>
                        <li>Review the complete Letter of Intent</li>
                        <li>Provide your electronic signature</li>
                        <li>Receive confirmation with verification code</li>
                        <li>Our team will contact you within 2 business days</li>
                    </ol>
                </div>
                
                <p><strong>Questions?</strong> Reply to this email or contact our team.</p>
                
                <p>Thank you for choosing Better Day Energy!</p>
                
                <p>Best regards,<br>
                <strong>Better Day Energy Team</strong><br>
                VP Racing Fuel Supply Division</p>
            </div>
            
            <div class="footer">
                <p>🔒 This signature request is secure and legally binding under the ESIGN Act</p>
                <p>📧 This email was sent to: {request_data['signer_email']}</p>
                <p>Transaction Reference: {request_data['transaction_id']}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
Better Day Energy - Electronic Signature Required

Dear {request_data['signer_name']},

Your Letter of Intent for the VP Racing Fuel Supply Agreement is ready for your electronic signature.

Document Details:
- Document: {request_data['document_name']}
- Company: {request_data['company_name']}
- Transaction ID: {request_data['transaction_id']}
- Expires: {datetime.fromisoformat(request_data['expires_at']).strftime('%B %d, %Y')}

⏰ ACTION REQUIRED: Please sign within 30 days

SIGN DOCUMENT: http://localhost:8003/sign/{request_data['signature_token']}

What happens next?
1. Click the signature link above
2. Review the complete Letter of Intent
3. Provide your electronic signature
4. Receive confirmation with verification code
5. Our team will contact you within 2 business days

Questions? Reply to this email or contact our team.

Thank you for choosing Better Day Energy!

Best regards,
Better Day Energy Team
VP Racing Fuel Supply Division

---
🔒 This signature request is secure and legally binding under the ESIGN Act
📧 This email was sent to: {request_data['signer_email']}
Transaction Reference: {request_data['transaction_id']}
    """
    
    return html_content, text_content

def send_signature_email():
    """Send the signature request email"""
    
    try:
        # Create email content
        html_content, text_content = create_signature_email(request_data)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_username
        msg['To'] = request_data['signer_email']
        msg['Subject'] = f"🖊️ Signature Required: {request_data['document_name']} - {request_data['transaction_id']}"
        
        # Add both plain text and HTML versions
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        print("📧 Connecting to Gmail SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        print(f"📤 Sending signature email to {request_data['signer_email']}...")
        server.send_message(msg)
        server.quit()
        
        print("✅ Signature email sent successfully!")
        print(f"📧 Sent to: {request_data['signer_email']}")
        print(f"📄 Document: {request_data['document_name']}")
        print(f"🔗 Signature Link: http://localhost:8001/sign/{request_data['signature_token']}")
        print(f"🆔 Transaction ID: {request_data['transaction_id']}")
        print("\n🎯 Check your email to experience the full signature workflow!")
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print("\n🔗 Direct signature link: http://localhost:8001/sign/" + request_data['signature_token'])

if __name__ == "__main__":
    send_signature_email()