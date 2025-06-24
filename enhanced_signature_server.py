#!/usr/bin/env python3
"""
Enhanced Signature Server with PostgreSQL Tamper-Evident Storage
Combines the clean UI with secure database storage
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import base64
import logging
from pathlib import Path
from signature_storage import TamperEvidentSignatureStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize PostgreSQL storage
signature_storage = TamperEvidentSignatureStorage()

# Load signature request data
def load_signature_requests():
    """Load signature requests from JSON file"""
    data_file = Path("./signature_request_data.json")
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}

# Storage
signature_requests = load_signature_requests()

class EnhancedSignatureHandler(BaseHTTPRequestHandler):
    """Handle signature requests with PostgreSQL storage"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/":
            self.serve_home()
        elif path.startswith("/sign/"):
            token = path.split("/sign/")[1]
            self.serve_signature_page(token)
        elif path.startswith("/signature-complete/"):
            verification_code = path.split("/signature-complete/")[1]
            self.serve_completion_page(verification_code)
        elif path.startswith("/signature-image/"):
            verification_code = path.split("/signature-image/")[1]
            self.serve_signature_image(verification_code)
        elif path.startswith("/audit-report/"):
            verification_code = path.split("/audit-report/")[1]
            self.serve_audit_report(verification_code)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/api/submit-signature":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_signature_submission(post_data)
        else:
            self.send_error(404)
    
    def serve_home(self):
        """Serve home page"""
        html = """
        <html>
        <head>
            <title>Better Day Energy Signature System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }
                .header { text-align: center; color: #1f4e79; margin-bottom: 30px; }
                .features { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Better Day Energy</h1>
                    <h2>Enhanced Electronic Signature System</h2>
                    <p>PostgreSQL-powered signature routing with tamper-evident storage</p>
                </div>
                <div class="features">
                    <h3>🔐 Security Features</h3>
                    <ul>
                        <li>✅ PostgreSQL BLOB storage for signature images</li>
                        <li>✅ Cryptographic integrity hashing (HMAC-SHA256)</li>
                        <li>✅ Complete audit trail with IP logging</li>
                        <li>✅ Tamper detection and verification</li>
                        <li>✅ ESIGN Act compliance flags</li>
                        <li>✅ Browser fingerprinting</li>
                    </ul>
                </div>
                <p style="text-align: center;">Click the signature link in your email to sign your document.</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_signature_page(self, token):
        """Serve the signature page"""
        # Find signature request by token
        signature_request = None
        for req_id, req_data in signature_requests.items():
            if req_data.get('signature_token') == token:
                signature_request = req_data
                break
        
        if not signature_request:
            self.send_error(404, "Signature request not found")
            return
        
        # Check if already signed (check PostgreSQL)
        # For now, use same logic as before
        if signature_request.get('status') == 'completed':
            self.serve_already_signed(signature_request)
            return
        
        # Generate signature page HTML (same as clean version)
        html = self.create_signature_page_html(signature_request)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def create_signature_page_html(self, signature_request):
        """Create the signature page (same as clean version but enhanced)"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sign Document - {signature_request['document_name']}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f8f9fa;
                }}
                .header {{
                    background: white;
                    border-bottom: 1px solid #e9ecef;
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .logo {{
                    color: #1f4e79;
                    font-weight: bold;
                    font-size: 18px;
                }}
                .status {{
                    background: #fff3cd;
                    color: #856404;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 20px auto;
                    padding: 0 20px;
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 20px;
                }}
                .document-panel {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 30px;
                }}
                .signature-panel {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 20px;
                    height: fit-content;
                }}
                .document-content {{
                    max-height: 600px;
                    overflow-y: auto;
                    border: 2px solid #007bff;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 8px;
                    background: #f8f9fa;
                }}
                .signature-area {{
                    border: 2px dashed #dee2e6;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                    background: #f8f9fa;
                }}
                #signature-canvas {{
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    cursor: crosshair;
                    background: white;
                    touch-action: none;
                }}
                .btn {{
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: 500;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    text-align: center;
                }}
                .btn-primary {{
                    background: #007bff;
                    color: white;
                }}
                .btn-secondary {{
                    background: #6c757d;
                    color: white;
                }}
                .btn-success {{
                    background: #28a745;
                    color: white;
                    font-size: 18px;
                    padding: 15px 30px;
                    width: 100%;
                }}
                .info-box {{
                    background: #e7f3ff;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }}
                .warning-box {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }}
                .security-box {{
                    background: #e8f5e8;
                    border: 1px solid #c3e6c3;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }}
                h1, h2, h3 {{ color: #1f4e79; margin: 20px 0 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .financial-highlight {{
                    background: #e8f5e8;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                @media (max-width: 768px) {{
                    .container {{ grid-template-columns: 1fr; }}
                }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>
        </head>
        <body>
            <div class="header">
                <div class="logo">Better Day Energy - Enhanced Electronic Signature</div>
                <div class="status">Expires {datetime.fromisoformat(signature_request['expires_at']).strftime('%B %d, %Y')}</div>
            </div>
            
            <div class="container">
                <div class="document-panel">
                    <h2>[Document] {signature_request['document_name']}</h2>
                    <p>Please review this Letter of Intent carefully before signing</p>
                    
                    <div class="document-content">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1>Better Day Energy</h1>
                            <h2>Letter of Intent</h2>
                            <h3>VP Racing Fuel Supply Agreement</h3>
                        </div>
                        
                        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                        <p><strong>Transaction ID:</strong> {signature_request['transaction_id']}</p>
                        
                        <h3>[Building] Customer Information</h3>
                        <table>
                            <tr><th>Business Name</th><td>{signature_request['company_name']}</td></tr>
                            <tr><th>Owner/Contact</th><td>{signature_request['signer_name']}</td></tr>
                            <tr><th>Email</th><td>{signature_request['signer_email']}</td></tr>
                            <tr><th>Business Type</th><td>Independent Gas Station</td></tr>
                        </table>
                        
                        <h3>[Fuel] Fuel Volume Commitments</h3>
                        <table>
                            <tr><th>Product</th><th>Monthly Volume</th><th>Annual Volume</th></tr>
                            <tr><td>Gasoline</td><td>85,000 gallons</td><td>1,020,000 gallons</td></tr>
                            <tr><td>Diesel</td><td>25,000 gallons</td><td>300,000 gallons</td></tr>
                            <tr><td><strong>Total</strong></td><td><strong>110,000 gallons</strong></td><td><strong>1,320,000 gallons</strong></td></tr>
                        </table>
                        
                        <div class="financial-highlight">
                            <h3>[Money] Financial Incentive Package</h3>
                            <table>
                                <tr><th>Incentive Type</th><th>Amount</th></tr>
                                <tr><td>Image Program Funding</td><td>$75,000</td></tr>
                                <tr><td>Volume Incentives (Annual)</td><td>$50,000</td></tr>
                                <tr><td><strong>Total First Year Value</strong></td><td><strong>$125,000</strong></td></tr>
                            </table>
                        </div>
                        
                        <h3>[Clipboard] Key Terms & Conditions</h3>
                        <ul>
                            <li>Contract Duration: 36 months</li>
                            <li>Exclusive fuel purchasing agreement</li>
                            <li>Minimum monthly volume: 110,000 gallons</li>
                            <li>Target conversion date: August 1, 2025</li>
                            <li>Dedicated account management</li>
                            <li>24/7 emergency fuel supply</li>
                            <li>Competitive pricing with quarterly reviews</li>
                        </ul>
                        
                        <div class="warning-box">
                            <h3>[Sign] Electronic Signature Authorization</h3>
                            <p>By signing this Letter of Intent electronically, you acknowledge:</p>
                            <ul>
                                <li>Understanding and agreement to all terms stated above</li>
                                <li>Commitment to proceed with formal contract negotiation</li>
                                <li>Authorization to begin implementation planning</li>
                                <li>Legal binding nature of this agreement</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="signature-panel">
                    <div class="info-box">
                        <h3>[Note] Signer Information</h3>
                        <p><strong>Name:</strong> {signature_request['signer_name']}</p>
                        <p><strong>Email:</strong> {signature_request['signer_email']}</p>
                        <p><strong>Company:</strong> {signature_request['company_name']}</p>
                    </div>
                    
                    <div class="security-box">
                        <h3>[Lock] Enhanced Security</h3>
                        <ul style="font-size: 12px; margin: 0;">
                            <li>✅ PostgreSQL tamper-evident storage</li>
                            <li>✅ Cryptographic integrity verification</li>
                            <li>✅ Complete audit trail logging</li>
                            <li>✅ ESIGN Act compliance</li>
                        </ul>
                    </div>
                    
                    <div class="warning-box">
                        <h3>[Sign] Your Signature Required</h3>
                        <p>Please sign below to electronically execute this agreement.</p>
                    </div>
                    
                    <div class="signature-area">
                        <p><strong>Sign Here:</strong></p>
                        <canvas id="signature-canvas" width="300" height="150"></canvas>
                        <div style="margin-top: 10px;">
                            <button type="button" class="btn btn-secondary" onclick="clearSignature()">[Trash] Clear</button>
                        </div>
                    </div>
                    
                    <button type="button" class="btn btn-success" onclick="submitSignature()" id="sign-button">
                        [Checkmark] Sign Document
                    </button>
                    
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px; color: #666; margin-top: 20px;">
                        [Lock] <strong>Security:</strong> This signature will be stored in PostgreSQL with tamper-evident cryptographic hashing. 
                        IP: {self.client_address[0]}
                    </div>
                </div>
            </div>
            
            <script>
                // Initialize signature pad
                const canvas = document.getElementById('signature-canvas');
                const signaturePad = new SignaturePad(canvas);
                
                // Clear signature
                function clearSignature() {{
                    signaturePad.clear();
                }}
                
                // Submit signature
                async function submitSignature() {{
                    if (signaturePad.isEmpty()) {{
                        alert('Please provide your signature before submitting.');
                        return;
                    }}
                    
                    const signButton = document.getElementById('sign-button');
                    signButton.disabled = true;
                    signButton.innerHTML = '[Hourglass] Processing...';
                    
                    try {{
                        const signatureData = signaturePad.toDataURL('image/png');
                        
                        const response = await fetch('/api/submit-signature', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                signature_token: '{signature_request['signature_token']}',
                                signature_data: signatureData,
                                signed_at: new Date().toISOString()
                            }})
                        }});
                        
                        if (response.ok) {{
                            const result = await response.json();
                            window.location.href = '/signature-complete/' + result.verification_code;
                        }} else {{
                            throw new Error('Failed to submit signature');
                        }}
                    }} catch (error) {{
                        alert('Error submitting signature. Please try again.');
                        signButton.disabled = false;
                        signButton.innerHTML = '[Checkmark] Sign Document';
                    }}
                }}
            </script>
        </body>
        </html>
        """
    
    def handle_signature_submission(self, post_data):
        """Handle signature submission with PostgreSQL storage"""
        try:
            data = json.loads(post_data.decode())
            signature_token = data.get('signature_token')
            
            # Find signature request
            signature_request = None
            for req_id, req_data in signature_requests.items():
                if req_data.get('signature_token') == signature_token:
                    signature_request = req_data
                    break
            
            if not signature_request:
                self.send_error(404, "Signature request not found")
                return
            
            # Get client info
            ip_address = self.client_address[0]
            user_agent = self.headers.get('User-Agent', 'Unknown')
            
            # Store signature in PostgreSQL with tamper-evident features
            verification_code = signature_storage.store_signature(
                signature_request,
                data.get('signature_data'),
                ip_address,
                user_agent
            )
            
            if not verification_code:
                self.send_error(500, "Failed to store signature")
                return
            
            # Update in-memory status
            signature_request['status'] = 'completed'
            signature_request['verification_code'] = verification_code
            
            logger.info(f"[Checkmark] Enhanced signature completed for {signature_request['signer_name']}")
            logger.info(f"[Database] Stored in PostgreSQL with verification code: {verification_code}")
            
            # Send response
            response_data = {
                'success': True,
                'verification_code': verification_code
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"[X] Error handling signature: {e}")
            self.send_error(500, str(e))
    
    def serve_completion_page(self, verification_code):
        """Serve enhanced completion page with PostgreSQL data"""
        # Get signature data from PostgreSQL
        audit_report = signature_storage.get_audit_report(verification_code)
        
        if not audit_report:
            self.send_error(404, "Signed document not found")
            return
        
        html = f"""
        <html>
        <head>
            <title>Signature Complete - Better Day Energy</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 700px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; text-align: center; }}
                .success {{ color: #28a745; font-size: 48px; margin-bottom: 20px; }}
                .verification {{ background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: left; }}
                .security {{ background: #e7f3ff; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: left; }}
                .links {{ margin: 20px 0; }}
                .btn {{ padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">[Checkmark]</div>
                <h1>Document Signed Successfully!</h1>
                <p>Your Letter of Intent has been electronically executed with enhanced security.</p>
                
                <div class="verification">
                    <h3>[Key] Verification Code</h3>
                    <code style="font-size: 18px; font-weight: bold;">{verification_code}</code>
                    <p>Keep this code for your records</p>
                </div>
                
                <div class="details">
                    <h3>[Clipboard] Signature Details</h3>
                    <p><strong>Signer:</strong> {audit_report['signer_name']}</p>
                    <p><strong>Company:</strong> {audit_report['company_name']}</p>
                    <p><strong>Document:</strong> {audit_report['document_name']}</p>
                    <p><strong>Signed:</strong> {audit_report['signed_at'].strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>Transaction ID:</strong> {audit_report['transaction_id']}</p>
                </div>
                
                <div class="security">
                    <h3>[Lock] Security & Compliance</h3>
                    <p><strong>Storage:</strong> PostgreSQL with BLOB data</p>
                    <p><strong>Integrity:</strong> {audit_report['integrity_message']}</p>
                    <p><strong>IP Address:</strong> {audit_report['ip_address']}</p>
                    <p><strong>Browser:</strong> {audit_report['browser_fingerprint'][:16]}...</p>
                    <p><strong>Compliance:</strong> ESIGN Act compliant ✅</p>
                </div>
                
                <div class="links">
                    <a href="/signature-image/{verification_code}" class="btn">[Image] View Signature</a>
                    <a href="/audit-report/{verification_code}" class="btn">[Report] Full Audit Report</a>
                </div>
                
                <p style="margin-top: 30px; color: #666;">
                    Thank you for choosing Better Day Energy!<br>
                    Our team will contact you within 2 business days.
                </p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_signature_image(self, verification_code):
        """Serve signature image from PostgreSQL"""
        image_data = signature_storage.get_signature_image(verification_code)
        
        if not image_data:
            self.send_error(404, "Signature image not found")
            return
        
        # Extract base64 data
        image_base64 = image_data['image_data'].split(',')[1]
        image_binary = base64.b64decode(image_base64)
        
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.send_header('Content-length', str(len(image_binary)))
        self.end_headers()
        self.wfile.write(image_binary)
    
    def serve_audit_report(self, verification_code):
        """Serve complete audit report"""
        audit_report = signature_storage.get_audit_report(verification_code)
        
        if not audit_report:
            self.send_error(404, "Audit report not found")
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(audit_report, indent=2, default=str).encode('utf-8'))
    
    def serve_already_signed(self, signature_request):
        """Serve already signed page"""
        html = f"""
        <html>
        <head>
            <title>Document Already Signed</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; text-align: center; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>[Checkmark] Document Already Signed</h1>
                <p>This document has already been signed by {signature_request['signer_name']}.</p>
                <p><strong>Verification Code:</strong> {signature_request.get('verification_code', 'N/A')}</p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

def main():
    """Start the enhanced signature server"""
    server_address = ('', 8002)  # Different port to avoid conflict
    httpd = HTTPServer(server_address, EnhancedSignatureHandler)
    
    print("[Lock] Better Day Energy Enhanced Signature Server Started!")
    print("[Database] PostgreSQL tamper-evident storage enabled")
    print("[Globe] Access at: http://localhost:8002")
    print("[Email] Ready for signature requests with enhanced security")
    print("\n[Clipboard] Features:")
    print("- PostgreSQL BLOB storage for signature images")
    print("- Cryptographic integrity hashing (HMAC-SHA256)")
    print("- Complete audit trail with IP logging")  
    print("- Tamper detection and verification")
    print("- ESIGN Act compliance flags")
    print("- Signature image viewing (/signature-image/CODE)")
    print("- Full audit reports (/audit-report/CODE)")
    
    httpd.serve_forever()

if __name__ == "__main__":
    main()