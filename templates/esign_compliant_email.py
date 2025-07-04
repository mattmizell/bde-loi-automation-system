def get_esign_compliant_email_template(customer_name: str, company_name: str, transaction_id: str, loi_type: str, signature_url: str) -> tuple[str, str]:
    """
    Generate ESIGN Act compliant email templates (HTML and plain text)
    Returns: (html_body, text_body)
    """
    
    # HTML Email Template
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1f4e79; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1>🏢 Better Day Energy</h1>
                <h2>Letter of Intent - Electronic Signature Required</h2>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                <p>Dear {customer_name},</p>
                
                <p>Your <strong>{loi_type}</strong> Letter of Intent for <strong>{company_name}</strong> has been prepared and requires your electronic signature.</p>
                
                <!-- ESIGN Act Disclosure -->
                <div style="background: #fff3cd; border: 2px solid #ffeeba; padding: 20px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="color: #856404; margin-top: 0;">📋 Important Legal Notice - Electronic Signatures</h3>
                    <p style="color: #856404;"><strong>Federal law (ESIGN Act) requires we inform you about electronic signatures:</strong></p>
                    <ul style="color: #856404; margin: 10px 0;">
                        <li>You have the right to receive this document in paper form</li>
                        <li>You may withdraw consent to use electronic signatures at any time</li>
                        <li>Your electronic signature will be legally binding</li>
                        <li>You must have access to view and download PDF documents</li>
                    </ul>
                    <p style="color: #856404; margin-bottom: 0;"><strong>By clicking the link below, you consent to use electronic signatures for this transaction.</strong></p>
                </div>
                
                <div style="background: #e8f5e9; border: 1px solid #4caf50; padding: 20px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="color: #2e7d32; margin-top: 0;">📋 Next Steps:</h3>
                    <ol>
                        <li>Click the signature link below</li>
                        <li>Review and consent to electronic signature use</li>
                        <li>Review your LOI details carefully</li>
                        <li>Sign electronically using your mouse or touch screen</li>
                        <li>Submit your signature to complete the process</li>
                    </ol>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{signature_url}" 
                       style="background: #28a745; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 6px; font-weight: bold; 
                              display: inline-block; font-size: 16px;">
                        ✍️ Review and Sign Your LOI
                    </a>
                </div>
                
                <!-- Paper Copy Option -->
                <div style="background: #e3f2fd; border: 1px solid #bbdefb; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>📄 Prefer Paper Documents?</strong><br>
                    If you would like to receive paper copies instead of signing electronically, please contact us at:<br>
                    📧 documents@betterdayenergy.com<br>
                    📞 (888) 555-0123</p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⚠️ Important:</strong> This signature link will expire in 30 days. 
                    Please complete your signature as soon as possible to avoid delays in processing.</p>
                </div>
                
                <!-- System Requirements -->
                <div style="background: #f0f4f8; border: 1px solid #d0d8e0; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>💻 System Requirements:</strong><br>
                    To sign electronically, you need:<br>
                    • Internet access and a modern web browser<br>
                    • Ability to view and download PDF files<br>
                    • Valid email address for document delivery</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                    <p><strong>Transaction Details:</strong></p>
                    <p style="margin: 5px 0;"><strong>Transaction ID:</strong> {transaction_id}</p>
                    <p style="margin: 5px 0;"><strong>Company:</strong> {company_name}</p>
                    <p style="margin: 5px 0;"><strong>LOI Type:</strong> {loi_type}</p>
                    <p style="margin: 5px 0;"><strong>Your Email:</strong> {customer_name}</p>
                </div>
                
                <p>If you have any questions about the electronic signature process or need assistance, please contact our team.</p>
                
                <p>Thank you for choosing Better Day Energy!</p>
                
                <div style="margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
                    <p>Better Day Energy LOI Automation System<br>
                    123 Energy Way, Houston, TX 77001<br>
                    This is an automated message - please do not reply to this email.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain Text Email Template
    text_body = f"""
Better Day Energy - Letter of Intent Electronic Signature Required

Dear {customer_name},

Your {loi_type} Letter of Intent for {company_name} has been prepared and requires your electronic signature.

IMPORTANT LEGAL NOTICE - ELECTRONIC SIGNATURES
===============================================
Federal law (ESIGN Act) requires we inform you about electronic signatures:
• You have the right to receive this document in paper form
• You may withdraw consent to use electronic signatures at any time  
• Your electronic signature will be legally binding
• You must have access to view and download PDF documents

By clicking the link below, you consent to use electronic signatures for this transaction.

NEXT STEPS:
1. Click the signature link below
2. Review and consent to electronic signature use
3. Review your LOI details carefully
4. Sign electronically using your mouse or touch screen
5. Submit your signature to complete the process

SIGN YOUR LOI NOW:
{signature_url}

PREFER PAPER DOCUMENTS?
If you would like to receive paper copies instead of signing electronically, please contact us at:
Email: documents@betterdayenergy.com
Phone: (888) 555-0123

SYSTEM REQUIREMENTS:
To sign electronically, you need:
• Internet access and a modern web browser
• Ability to view and download PDF files
• Valid email address for document delivery

IMPORTANT: This signature link will expire in 30 days. Please complete your signature as soon as possible to avoid delays in processing.

Transaction Details:
Transaction ID: {transaction_id}
Company: {company_name}
LOI Type: {loi_type}
Your Email: {customer_name}

If you have any questions about the electronic signature process or need assistance, please contact our team.

Thank you for choosing Better Day Energy!

--
Better Day Energy LOI Automation System
123 Energy Way, Houston, TX 77001
This is an automated message - please do not reply to this email.
    """
    
    return html_body, text_body