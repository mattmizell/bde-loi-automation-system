#!/usr/bin/env python3
"""
HTML-to-PDF Generator for Signed LOI Documents
Uses browser-based PDF generation (like most e-signature platforms)
"""

import json
import base64
from datetime import datetime
import requests
from pathlib import Path

class HTMLLOIPDFGenerator:
    """Generate PDF-ready HTML for signed LOI documents"""
    
    def __init__(self, crm_api_key):
        self.crm_api_key = crm_api_key
        self.base_url = "https://api.lessannoyingcrm.com"
        # Parse the API key to get user code
        if '-' in crm_api_key:
            self.user_code = crm_api_key.split('-')[0]
        else:
            self.user_code = "1073223"
    
    def create_signed_loi_html(self, signature_data, audit_report):
        """Create print-ready HTML for PDF conversion"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Signed LOI - {audit_report['verification_code']}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 0.75in;
                }}
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #1f4e79;
                    padding-bottom: 15px;
                }}
                .company-name {{
                    font-size: 28pt;
                    font-weight: bold;
                    color: #1f4e79;
                    margin-bottom: 5px;
                }}
                .document-title {{
                    font-size: 18pt;
                    color: #1f4e79;
                    margin-bottom: 10px;
                }}
                .metadata {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .metadata table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .metadata td {{
                    padding: 5px 10px;
                    border: 1px solid #dee2e6;
                }}
                .metadata td:first-child {{
                    background: #e9ecef;
                    font-weight: bold;
                    width: 30%;
                }}
                .section {{
                    margin-bottom: 25px;
                    page-break-inside: avoid;
                }}
                .section-title {{
                    font-size: 16pt;
                    font-weight: bold;
                    color: #1f4e79;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #1f4e79;
                    padding-bottom: 5px;
                }}
                .info-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 15px;
                }}
                .info-table th {{
                    background: #1f4e79;
                    color: white;
                    padding: 10px;
                    text-align: center;
                    font-weight: bold;
                }}
                .info-table td {{
                    padding: 8px 10px;
                    border: 1px solid #1f4e79;
                    text-align: center;
                }}
                .info-table tr:nth-child(even) td {{
                    background: #f8f9fa;
                }}
                .financial-highlight {{
                    background: #e8f5e8;
                    border: 2px solid #28a745;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .financial-highlight .total-row {{
                    background: #28a745;
                    color: white;
                    font-weight: bold;
                }}
                .terms-list {{
                    margin-left: 20px;
                    margin-bottom: 15px;
                }}
                .terms-list li {{
                    margin-bottom: 8px;
                    list-style-type: disc;
                }}
                .signature-section {{
                    border: 2px solid #007bff;
                    padding: 20px;
                    border-radius: 8px;
                    background: #f0f8ff;
                    page-break-inside: avoid;
                }}
                .signature-image {{
                    max-width: 300px;
                    max-height: 150px;
                    border: 1px solid #ccc;
                    padding: 10px;
                    background: white;
                    margin: 15px 0;
                }}
                .signature-details {{
                    background: #fff3cd;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #ffeaa7;
                    margin-top: 15px;
                }}
                .security-section {{
                    background: #e7f3ff;
                    border: 1px solid #007bff;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .compliance-notice {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 15px;
                    font-style: italic;
                }}
                .page-break {{
                    page-break-before: always;
                }}
                @media print {{
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body>
            <!-- Header -->
            <div class="header">
                <div class="company-name">Better Day Energy</div>
                <div class="document-title">Letter of Intent - VP Racing Fuel Supply Agreement</div>
                <div style="font-size: 12pt; color: #666;">Electronically Executed Document</div>
            </div>
            
            <!-- Document Metadata -->
            <div class="metadata">
                <table>
                    <tr>
                        <td>Document Type:</td>
                        <td>Letter of Intent</td>
                    </tr>
                    <tr>
                        <td>Transaction ID:</td>
                        <td>{audit_report['transaction_id']}</td>
                    </tr>
                    <tr>
                        <td>Verification Code:</td>
                        <td>{audit_report['verification_code']}</td>
                    </tr>
                    <tr>
                        <td>Generated:</td>
                        <td>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</td>
                    </tr>
                </table>
            </div>
            
            <!-- Customer Information -->
            <div class="section">
                <div class="section-title">Customer Information</div>
                <table class="info-table">
                    <tr>
                        <td><strong>Business Name:</strong></td>
                        <td>{audit_report['company_name']}</td>
                    </tr>
                    <tr>
                        <td><strong>Owner/Contact:</strong></td>
                        <td>{audit_report['signer_name']}</td>
                    </tr>
                    <tr>
                        <td><strong>Email Address:</strong></td>
                        <td>{audit_report['signer_email']}</td>
                    </tr>
                    <tr>
                        <td><strong>Business Type:</strong></td>
                        <td>Independent Gas Station</td>
                    </tr>
                </table>
            </div>
            
            <!-- Fuel Volume Commitments -->
            <div class="section">
                <div class="section-title">Fuel Volume Commitments</div>
                <table class="info-table">
                    <tr>
                        <th>Product</th>
                        <th>Monthly Volume</th>
                        <th>Annual Volume</th>
                    </tr>
                    <tr>
                        <td>Gasoline</td>
                        <td>85,000 gallons</td>
                        <td>1,020,000 gallons</td>
                    </tr>
                    <tr>
                        <td>Diesel</td>
                        <td>25,000 gallons</td>
                        <td>300,000 gallons</td>
                    </tr>
                    <tr style="background: #e8f5e8; font-weight: bold;">
                        <td>Total</td>
                        <td>110,000 gallons</td>
                        <td>1,320,000 gallons</td>
                    </tr>
                </table>
            </div>
            
            <!-- Financial Incentive Package -->
            <div class="section">
                <div class="section-title">Financial Incentive Package</div>
                <div class="financial-highlight">
                    <table class="info-table">
                        <tr>
                            <th>Incentive Type</th>
                            <th>Amount</th>
                        </tr>
                        <tr>
                            <td>Image Program Funding</td>
                            <td>$75,000</td>
                        </tr>
                        <tr>
                            <td>Volume Incentives (Annual)</td>
                            <td>$50,000</td>
                        </tr>
                        <tr class="total-row">
                            <td><strong>Total First Year Value</strong></td>
                            <td><strong>$125,000</strong></td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <!-- Key Terms & Conditions -->
            <div class="section">
                <div class="section-title">Key Terms & Conditions</div>
                <ul class="terms-list">
                    <li>Contract Duration: 36 months</li>
                    <li>Exclusive fuel purchasing agreement</li>
                    <li>Minimum monthly volume: 110,000 gallons</li>
                    <li>Target conversion date: August 1, 2025</li>
                    <li>Dedicated account management</li>
                    <li>24/7 emergency fuel supply</li>
                    <li>Competitive pricing with quarterly reviews</li>
                </ul>
            </div>
            
            <!-- Electronic Signature Section -->
            <div class="section signature-section">
                <div class="section-title">Electronic Signature</div>
                
                <p><strong>Electronically Signed By:</strong> {audit_report['signer_name']}</p>
                
                {self._get_signature_image_html(signature_data)}
                
                <div class="signature-details">
                    <table style="width: 100%; border: none;">
                        <tr>
                            <td style="border: none; padding: 5px 0;"><strong>Date & Time:</strong></td>
                            <td style="border: none; padding: 5px 0;">{audit_report['signed_at'].strftime('%B %d, %Y at %I:%M %p')}</td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px 0;"><strong>IP Address:</strong></td>
                            <td style="border: none; padding: 5px 0;">{audit_report['ip_address']}</td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px 0;"><strong>Verification Code:</strong></td>
                            <td style="border: none; padding: 5px 0;">{audit_report['verification_code']}</td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px 0;"><strong>Browser Fingerprint:</strong></td>
                            <td style="border: none; padding: 5px 0;">{audit_report['browser_fingerprint'][:32]}...</td>
                        </tr>
                    </table>
                </div>
                
                <div class="compliance-notice">
                    <strong>Legal Notice:</strong> This document has been electronically signed in accordance with the 
                    Electronic Signatures in Global and National Commerce Act (ESIGN Act). The electronic signature 
                    is legally binding and has the same legal effect as a handwritten signature.
                </div>
            </div>
            
            <!-- Security & Integrity Information -->
            <div class="section security-section">
                <div class="section-title">Document Security & Integrity</div>
                <table class="info-table">
                    <tr>
                        <td><strong>Storage Method:</strong></td>
                        <td>PostgreSQL with tamper-evident hashing</td>
                    </tr>
                    <tr>
                        <td><strong>Integrity Status:</strong></td>
                        <td>{audit_report['integrity_message']}</td>
                    </tr>
                    <tr>
                        <td><strong>Compliance:</strong></td>
                        <td>ESIGN Act Compliant ✓</td>
                    </tr>
                    <tr>
                        <td><strong>Audit Trail:</strong></td>
                        <td>Complete IP and timestamp logging</td>
                    </tr>
                    <tr>
                        <td><strong>Document Hash:</strong></td>
                        <td>{audit_report.get('document_hash', 'N/A')[:64]}...</td>
                    </tr>
                </table>
            </div>
            
            <!-- Print Instructions (hidden when printed) -->
            <div class="no-print" style="margin-top: 30px; padding: 15px; background: #e9ecef; border-radius: 5px;">
                <h3>To Save as PDF:</h3>
                <ol>
                    <li>Press <strong>Ctrl+P</strong> (or Cmd+P on Mac)</li>
                    <li>Select "Save as PDF" as destination</li>
                    <li>Choose "More settings" if needed</li>
                    <li>Click "Save"</li>
                </ol>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _get_signature_image_html(self, signature_data):
        """Generate HTML for signature image if available"""
        if signature_data and signature_data.get('signature_image'):
            try:
                # Convert binary signature data to base64
                image_base64 = base64.b64encode(signature_data['signature_image']).decode('utf-8')
                return f'''
                <div style="margin: 15px 0;">
                    <p><strong>Digital Signature:</strong></p>
                    <img src="data:image/png;base64,{image_base64}" 
                         class="signature-image" 
                         alt="Electronic Signature" />
                </div>
                '''
            except Exception as e:
                print(f"Warning: Could not include signature image: {e}")
        
        return '<p><em>Signature image not available</em></p>'
    
    def create_pdf_endpoint(self, verification_code):
        """Create HTML endpoint for PDF generation"""
        html_file = f"signed_loi_{verification_code}.html"
        
        # This would integrate with the signature storage to get real data
        # For now, return the HTML file path
        return html_file
    
    def store_in_crm_with_pdf_link(self, contact_id, audit_report, pdf_url=None):
        """Store comprehensive LOI information in CRM with PDF generation instructions"""
        
        try:
            # Create detailed CRM note
            note_content = f"""
SIGNED LOI DOCUMENT - {audit_report['verification_code']}

📄 Document: {audit_report['document_name']}
🏢 Company: {audit_report['company_name']}
✍️  Signer: {audit_report['signer_name']}
📅 Signed: {audit_report['signed_at'].strftime('%B %d, %Y at %I:%M %p')}
🆔 Transaction ID: {audit_report['transaction_id']}

💰 FINANCIAL PACKAGE:
• Image Program Funding: $75,000
• Volume Incentives (Annual): $50,000
• Total First Year Value: $125,000

⛽ VOLUME COMMITMENTS:
• Gasoline: 85,000 gallons/month (1,020,000/year)
• Diesel: 25,000 gallons/month (300,000/year)
• Total: 110,000 gallons/month (1,320,000/year)

🔐 SECURITY & COMPLIANCE:
• Verification Code: {audit_report['verification_code']}
• IP Address: {audit_report['ip_address']}
• Browser: {audit_report['browser_fingerprint'][:16]}...
• Integrity: {audit_report['integrity_message']}
• Compliance: ESIGN Act Compliant ✓

📋 CONTRACT TERMS:
• Duration: 36 months
• Exclusive fuel purchasing agreement
• Target conversion: August 1, 2025
• Dedicated account management
• 24/7 emergency fuel supply

🔗 NEXT STEPS:
1. Contact customer within 2 business days
2. Schedule site visit for tank assessment
3. Begin image program planning
4. Prepare formal contract documents
5. Coordinate conversion timeline

📄 PDF GENERATION:
• View/Print: http://localhost:8002/signed-loi/{audit_report['verification_code']}
• Use browser "Save as PDF" function
• Document stored in PostgreSQL tamper-evident system

Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            """
            
            # Add note to CRM
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.crm_api_key
            }
            
            body = {
                "Function": "CreateNote",
                "Parameters": {
                    "ContactId": contact_id,
                    "Note": note_content
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=body,
                timeout=30
            )
            
            if response.status_code == 200:
                response_text = response.text
                try:
                    result = json.loads(response_text)
                    if result.get('Success'):
                        print(f"✅ Signed LOI information stored in CRM for contact {contact_id}")
                        print(f"📝 Note ID: {result.get('Result', 'Unknown')}")
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
            print(f"❌ Error storing in CRM: {e}")
            return False

def test_html_generation():
    """Test HTML generation"""
    
    # Sample audit report
    sample_audit = {
        'verification_code': 'LOI-SAMPLE123',
        'transaction_id': 'TXN-SAMPLE456',
        'signer_name': 'Farely Barnhart',
        'signer_email': 'matt.mizell@gmail.com',
        'company_name': "Farley's Gas and Go",
        'document_name': 'VP Racing Fuel Supply Agreement - Letter of Intent',
        'signed_at': datetime.now(),
        'ip_address': '192.168.1.100',
        'browser_fingerprint': 'abc123def456ghi789',
        'integrity_message': 'Signature integrity verified ✅',
        'document_hash': 'sha256:abcdef123456789'
    }
    
    # Generate HTML
    generator = HTMLLOIPDFGenerator("test-api-key")
    html_content = generator.create_signed_loi_html(None, sample_audit)
    
    # Save test HTML
    with open('test_signed_loi.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Test HTML generated: test_signed_loi.html")
    print("📄 Open in browser and use Ctrl+P -> Save as PDF")
    return html_content

if __name__ == "__main__":
    print("📄 HTML-to-PDF LOI Generator")
    print("=" * 50)
    
    # Test HTML generation
    test_html_generation()
    
    print("\n✅ Features implemented:")
    print("- Print-ready HTML with proper CSS")
    print("- Complete LOI document content")
    print("- Signature image embedding")
    print("- Security and audit information")
    print("- Browser-based PDF generation")
    print("- CRM integration with PDF links")
    print("- Professional document layout")
    print("\n🖨️  Use browser 'Save as PDF' for final PDF generation")