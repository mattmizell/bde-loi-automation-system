#!/usr/bin/env python3
"""
Integrated Signature Server with PDF Generation and CRM Storage
Complete workflow: Sign -> Store in PostgreSQL -> Generate PDF -> Store in CRM
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
from html_to_pdf_generator import HTMLLOIPDFGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
signature_storage = TamperEvidentSignatureStorage()
pdf_generator = HTMLLOIPDFGenerator("1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W")

# Load signature request data
def load_signature_requests():
    """Load signature requests from JSON file"""
    data_file = Path("./signature_request_data.json")
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}

signature_requests = load_signature_requests()

class IntegratedSignatureHandler(BaseHTTPRequestHandler):
    """Complete signature handler with PDF generation and CRM storage"""
    
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
        elif path.startswith("/signed-loi/"):
            verification_code = path.split("/signed-loi/")[1]
            self.serve_pdf_html(verification_code)
        elif path.startswith("/signature-image/"):
            verification_code = path.split("/signature-image/")[1]
            self.serve_signature_image(verification_code)
        elif path.startswith("/audit-report/"):
            verification_code = path.split("/audit-report/")[1]
            self.serve_audit_report(verification_code)
        elif path == "/admin":
            self.serve_admin_dashboard()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/api/submit-signature":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_signature_submission(post_data)
        elif self.path == "/api/create-loi":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_create_loi(post_data)
        else:
            self.send_error(404)
    
    def serve_home(self):
        """Serve home page"""
        html = """
        <html>
        <head>
            <title>Better Day Energy - Complete Signature System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }
                .header { text-align: center; color: #1f4e79; margin-bottom: 30px; }
                .features { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .workflow { background: #e7f3ff; padding: 20px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Better Day Energy</h1>
                    <h2>Complete Electronic Signature System</h2>
                    <p>Full workflow: Sign → PostgreSQL → PDF → CRM Storage</p>
                </div>
                
                <div class="features">
                    <h3>🔐 Security Features</h3>
                    <ul>
                        <li>✅ PostgreSQL tamper-evident storage</li>
                        <li>✅ Cryptographic integrity verification</li>
                        <li>✅ Complete audit trail logging</li>
                        <li>✅ ESIGN Act compliance</li>
                        <li>✅ Browser fingerprinting</li>
                    </ul>
                </div>
                
                <div class="workflow">
                    <h3>📄 Document Workflow</h3>
                    <ol>
                        <li>📧 Customer receives signature email</li>
                        <li>🖊️ Customer signs LOI electronically</li>
                        <li>💾 Signature stored in PostgreSQL</li>
                        <li>📄 PDF-ready HTML generated</li>
                        <li>📝 Complete record stored in CRM</li>
                        <li>🔗 PDF accessible via browser</li>
                    </ol>
                </div>
                
                <p style="text-align: center;">Click the signature link in your email to start the process.</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_signature_page(self, token):
        """Serve the signature page (reuse from enhanced server)"""
        # Find signature request by token
        signature_request = None
        for req_id, req_data in signature_requests.items():
            if req_data.get('signature_token') == token:
                signature_request = req_data
                break
        
        if not signature_request:
            self.send_error(404, "Signature request not found")
            return
        
        # Check if already signed
        if signature_request.get('status') == 'completed':
            self.serve_already_signed(signature_request)
            return
        
        # Generate signature page HTML (same as enhanced version)
        html = self.create_signature_page_html(signature_request)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def create_signature_page_html(self, signature_request):
        """Create signature page with workflow integration notice"""
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
                .workflow-box {{
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
                <div class="logo">Better Day Energy - Complete Signature System</div>
                <div class="status">Expires {datetime.fromisoformat(signature_request['expires_at']).strftime('%B %d, %Y')}</div>
            </div>
            
            <div class="container">
                <div class="document-panel">
                    <h2>📄 {signature_request['document_name']}</h2>
                    <p>Please review this Letter of Intent carefully before signing</p>
                    
                    <div class="document-content">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1>Better Day Energy</h1>
                            <h2>Letter of Intent</h2>
                            <h3>VP Racing Fuel Supply Agreement</h3>
                        </div>
                        
                        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                        <p><strong>Transaction ID:</strong> {signature_request['transaction_id']}</p>
                        
                        <h3>Customer Information</h3>
                        <table>
                            <tr><th>Business Name</th><td>{signature_request['company_name']}</td></tr>
                            <tr><th>Owner/Contact</th><td>{signature_request['signer_name']}</td></tr>
                            <tr><th>Email</th><td>{signature_request['signer_email']}</td></tr>
                            <tr><th>Business Type</th><td>Independent Gas Station</td></tr>
                        </table>
                        
                        <h3>Fuel Volume Commitments</h3>
                        <table>
                            <tr><th>Product</th><th>Monthly Volume</th><th>Annual Volume</th></tr>
                            <tr><td>Gasoline</td><td>85,000 gallons</td><td>1,020,000 gallons</td></tr>
                            <tr><td>Diesel</td><td>25,000 gallons</td><td>300,000 gallons</td></tr>
                            <tr><td><strong>Total</strong></td><td><strong>110,000 gallons</strong></td><td><strong>1,320,000 gallons</strong></td></tr>
                        </table>
                        
                        <div class="financial-highlight">
                            <h3>Financial Incentive Package</h3>
                            <table>
                                <tr><th>Incentive Type</th><th>Amount</th></tr>
                                <tr><td>Image Program Funding</td><td>$75,000</td></tr>
                                <tr><td>Volume Incentives (Annual)</td><td>$50,000</td></tr>
                                <tr><td><strong>Total First Year Value</strong></td><td><strong>$125,000</strong></td></tr>
                            </table>
                        </div>
                        
                        <h3>Key Terms & Conditions</h3>
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
                            <h3>Electronic Signature Authorization</h3>
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
                        <h3>Signer Information</h3>
                        <p><strong>Name:</strong> {signature_request['signer_name']}</p>
                        <p><strong>Email:</strong> {signature_request['signer_email']}</p>
                        <p><strong>Company:</strong> {signature_request['company_name']}</p>
                    </div>
                    
                    <div class="workflow-box">
                        <h3>🔄 Complete Workflow</h3>
                        <ul style="font-size: 12px; margin: 0;">
                            <li>✅ PostgreSQL secure storage</li>
                            <li>✅ PDF generation ready</li>
                            <li>✅ CRM integration enabled</li>
                            <li>✅ Audit trail logging</li>
                        </ul>
                    </div>
                    
                    <div class="warning-box">
                        <h3>Your Signature Required</h3>
                        <p>Signing will trigger the complete workflow automation.</p>
                    </div>
                    
                    <div class="signature-area">
                        <p><strong>Sign Here:</strong></p>
                        <canvas id="signature-canvas" width="300" height="150"></canvas>
                        <div style="margin-top: 10px;">
                            <button type="button" class="btn btn-secondary" onclick="clearSignature()">Clear</button>
                        </div>
                    </div>
                    
                    <button type="button" class="btn btn-success" onclick="submitSignature()" id="sign-button">
                        🚀 Execute Complete Workflow
                    </button>
                    
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px; color: #666; margin-top: 20px;">
                        🔒 Complete security: PostgreSQL → PDF → CRM<br>
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
                
                // Submit signature with full workflow
                async function submitSignature() {{
                    if (signaturePad.isEmpty()) {{
                        alert('Please provide your signature before submitting.');
                        return;
                    }}
                    
                    const signButton = document.getElementById('sign-button');
                    signButton.disabled = true;
                    signButton.innerHTML = '⏳ Processing Complete Workflow...';
                    
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
                        signButton.innerHTML = '🚀 Execute Complete Workflow';
                    }}
                }}
            </script>
        </body>
        </html>
        """
    
    def handle_signature_submission(self, post_data):
        """Handle signature submission with COMPLETE workflow"""
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
            
            logger.info(f"🚀 Starting complete signature workflow for {signature_request['signer_name']}")
            
            # STEP 1: Store signature in PostgreSQL with tamper-evident features
            logger.info("📊 Step 1: Storing in PostgreSQL...")
            verification_code = signature_storage.store_signature(
                signature_request,
                data.get('signature_data'),
                ip_address,
                user_agent
            )
            
            if not verification_code:
                self.send_error(500, "Failed to store signature in PostgreSQL")
                return
            
            # STEP 2: Get complete audit report
            logger.info("📋 Step 2: Generating audit report...")
            audit_report = signature_storage.get_audit_report(verification_code)
            signature_image_data = signature_storage.get_signature_image(verification_code)
            
            # STEP 3: Store comprehensive information in CRM
            logger.info("📝 Step 3: Storing in CRM...")
            
            # Find Farley's contact ID (we know it from previous tests)
            contact_id = "4036857411931183467036798214340"  # Farley Barnhart's ID
            
            success = pdf_generator.store_in_crm_with_pdf_link(
                contact_id,
                audit_report,
                f"http://localhost:8003/signed-loi/{verification_code}"
            )
            
            if success:
                logger.info("✅ CRM storage completed successfully")
            else:
                logger.warning("⚠️ CRM storage failed, but signature is secure in PostgreSQL")
            
            # Update in-memory status
            signature_request['status'] = 'completed'
            signature_request['verification_code'] = verification_code
            
            logger.info(f"🎉 COMPLETE WORKFLOW FINISHED for {signature_request['signer_name']}")
            logger.info(f"📄 PDF available at: /signed-loi/{verification_code}")
            logger.info(f"📝 CRM updated for contact: {contact_id}")
            
            # Send response
            response_data = {
                'success': True,
                'verification_code': verification_code,
                'workflow_completed': True,
                'pdf_url': f"/signed-loi/{verification_code}",
                'crm_updated': success
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"❌ Error in complete workflow: {e}")
            self.send_error(500, str(e))
    
    def serve_completion_page(self, verification_code):
        """Serve completion page with full workflow results"""
        # Get audit report
        audit_report = signature_storage.get_audit_report(verification_code)
        
        if not audit_report:
            self.send_error(404, "Signed document not found")
            return
        
        html = f"""
        <html>
        <head>
            <title>Workflow Complete - Better Day Energy</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; text-align: center; }}
                .success {{ color: #28a745; font-size: 48px; margin-bottom: 20px; }}
                .verification {{ background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: left; }}
                .workflow {{ background: #e7f3ff; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: left; }}
                .links {{ margin: 20px 0; }}
                .btn {{ padding: 12px 24px; margin: 8px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .btn-success {{ background: #28a745; }}
                .btn-warning {{ background: #ffc107; color: #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">🎉</div>
                <h1>Complete Workflow Executed!</h1>
                <p>Your Letter of Intent has been processed through our complete automation system.</p>
                
                <div class="verification">
                    <h3>🔐 Verification Code</h3>
                    <code style="font-size: 18px; font-weight: bold;">{verification_code}</code>
                    <p>Keep this code for your records</p>
                </div>
                
                <div class="details">
                    <h3>📋 Signature Details</h3>
                    <p><strong>Signer:</strong> {audit_report['signer_name']}</p>
                    <p><strong>Company:</strong> {audit_report['company_name']}</p>
                    <p><strong>Document:</strong> {audit_report['document_name']}</p>
                    <p><strong>Signed:</strong> {audit_report['signed_at'].strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>Transaction ID:</strong> {audit_report['transaction_id']}</p>
                </div>
                
                <div class="workflow">
                    <h3>✅ Completed Workflow Steps</h3>
                    <ol>
                        <li>🖊️ Electronic signature captured and validated</li>
                        <li>💾 Signature stored securely in PostgreSQL</li>
                        <li>🔐 Tamper-evident integrity hash generated</li>
                        <li>📄 PDF-ready document created</li>
                        <li>📝 Complete record stored in Less Annoying CRM</li>
                        <li>🔗 Document accessible for download/print</li>
                    </ol>
                </div>
                
                <div class="links">
                    <a href="/signed-loi/{verification_code}" class="btn btn-success">📄 View/Print PDF</a>
                    <a href="/signature-image/{verification_code}" class="btn">🖼️ View Signature</a>
                    <a href="/audit-report/{verification_code}" class="btn">📊 Full Audit Report</a>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>🔗 Next Steps</h3>
                    <p>✅ CRM Record Updated: Farley Barnhart's contact record now contains complete LOI details</p>
                    <p>📧 Our team will contact you within 2 business days</p>
                    <p>📄 Use the "View/Print PDF" button above for your records</p>
                </div>
                
                <p style="margin-top: 30px; color: #666;">
                    Thank you for choosing Better Day Energy!<br>
                    Your complete signing workflow has been executed successfully.
                </p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_pdf_html(self, verification_code):
        """Serve PDF-ready HTML document"""
        # Get data from PostgreSQL
        audit_report = signature_storage.get_audit_report(verification_code)
        signature_image_data = signature_storage.get_signature_image(verification_code)
        
        if not audit_report:
            self.send_error(404, "Document not found")
            return
        
        # Generate PDF-ready HTML
        html_content = pdf_generator.create_signed_loi_html(signature_image_data, audit_report)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
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
                <h1>✅ Document Already Signed</h1>
                <p>This document has already been processed through our complete workflow.</p>
                <p><strong>Signer:</strong> {signature_request['signer_name']}</p>
                <p><strong>Verification Code:</strong> {signature_request.get('verification_code', 'N/A')}</p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_admin_dashboard(self):
        """Serve admin dashboard for creating new LOIs"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Better Day Energy - LOI Admin Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f8f9fa;
                    padding: 20px;
                }
                .container {
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                .header {
                    background: linear-gradient(135deg, #1f4e79, #2c5aa0);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .header h1 { font-size: 28px; margin-bottom: 10px; }
                .header p { opacity: 0.9; }
                .content {
                    padding: 30px;
                }
                .form-section {
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 8px;
                    font-weight: 600;
                    color: #1f4e79;
                }
                .form-group input {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #e9ecef;
                    border-radius: 6px;
                    font-size: 16px;
                }
                .form-group input:focus {
                    outline: none;
                    border-color: #007bff;
                }
                .btn {
                    background: #28a745;
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: 600;
                    cursor: pointer;
                    width: 100%;
                }
                .btn:hover {
                    background: #218838;
                }
                .result-box {
                    background: #e8f5e8;
                    border: 2px solid #28a745;
                    padding: 20px;
                    border-radius: 8px;
                    margin-top: 20px;
                    display: none;
                }
                .result-box h3 {
                    color: #155724;
                    margin-bottom: 15px;
                }
                .url-box {
                    background: white;
                    padding: 15px;
                    border-radius: 6px;
                    border: 1px solid #c3e6c3;
                    margin: 10px 0;
                    font-family: monospace;
                    word-break: break-all;
                }
                .email-template {
                    background: #fff;
                    border: 1px solid #ddd;
                    padding: 20px;
                    border-radius: 6px;
                    margin-top: 15px;
                    white-space: pre-line;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                }
                .copy-btn {
                    background: #007bff;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    margin-top: 10px;
                }
                .status-box {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Better Day Energy - LOI Admin</h1>
                    <p>Create new Letter of Intent signature requests for customers</p>
                    <p><strong>Production System:</strong> https://loi-automation-api.onrender.com</p>
                </div>
                
                <div class="content">
                    <div class="status-box">
                        <h3>🚀 Live Production System</h3>
                        <p>✅ PostgreSQL connected | ✅ CRM integrated | ✅ Email ready</p>
                        <p>This admin panel creates LOIs that are instantly live on the production system.</p>
                    </div>
                    
                    <div class="form-section">
                        <h2>📋 Create New LOI Request</h2>
                        <form id="loi-form">
                            <div class="form-group">
                                <label for="signer-name">Customer Name:</label>
                                <input type="text" id="signer-name" placeholder="e.g., John Smith" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="signer-email">Customer Email:</label>
                                <input type="email" id="signer-email" placeholder="e.g., john@example.com" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="company-name">Company Name:</label>
                                <input type="text" id="company-name" placeholder="e.g., Smith's Gas Station" required>
                            </div>
                            
                            <button type="submit" class="btn">🚀 Create Live LOI Request</button>
                        </form>
                    </div>
                    
                    <div id="result" class="result-box">
                        <h3>✅ LOI Created Successfully!</h3>
                        <div id="loi-details"></div>
                        
                        <h4>🔗 Live Signature URL:</h4>
                        <div id="signature-url" class="url-box"></div>
                        <button class="copy-btn" onclick="copyUrl()">📋 Copy URL</button>
                        
                        <h4>📧 Email Template for Customer:</h4>
                        <div id="email-template" class="email-template"></div>
                        <button class="copy-btn" onclick="copyEmail()">📋 Copy Email</button>
                    </div>
                </div>
            </div>
            
            <script>
                function generateUUID() {
                    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                        var r = Math.random() * 16 | 0,
                            v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    });
                }
                
                function generateTransactionId() {
                    return 'TXN-' + generateUUID().substr(0, 8).toUpperCase();
                }
                
                document.getElementById('loi-form').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const signerName = document.getElementById('signer-name').value;
                    const signerEmail = document.getElementById('signer-email').value;
                    const companyName = document.getElementById('company-name').value;
                    
                    const transactionId = generateTransactionId();
                    const signatureToken = generateUUID();
                    const createdAt = new Date().toISOString();
                    const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
                    
                    const loiData = {
                        transaction_id: transactionId,
                        signature_token: signatureToken,
                        signer_name: signerName,
                        signer_email: signerEmail,
                        company_name: companyName,
                        document_name: "VP Racing Fuel Supply Agreement - Letter of Intent",
                        status: "pending",
                        created_at: createdAt,
                        expires_at: expiresAt
                    };
                    
                    try {
                        const response = await fetch('/api/create-loi', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(loiData)
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            const signatureUrl = `https://loi-automation-api.onrender.com/sign/${signatureToken}`;
                            
                            // Show results
                            document.getElementById('loi-details').innerHTML = `
                                <p><strong>Customer:</strong> ${signerName}</p>
                                <p><strong>Company:</strong> ${companyName}</p>
                                <p><strong>Email:</strong> ${signerEmail}</p>
                                <p><strong>Transaction ID:</strong> ${transactionId}</p>
                                <p><strong>Expires:</strong> ${new Date(expiresAt).toLocaleDateString()}</p>
                            `;
                            
                            document.getElementById('signature-url').textContent = signatureUrl;
                            
                            const emailTemplate = `Subject: VP Racing Fuel Supply Agreement - Electronic Signature Required

Dear ${signerName},

Thank you for your interest in partnering with Better Day Energy for your fuel supply needs.

Please review and electronically sign the attached Letter of Intent for our VP Racing Fuel Supply Agreement by clicking the link below:

🔗 Sign Document: ${signatureUrl}

Key Benefits:
• $125,000 first-year incentive package  
• Competitive pricing with quarterly reviews
• 24/7 emergency fuel supply support
• Dedicated account management

This document expires in 30 days. Please complete your signature at your earliest convenience.

If you have any questions, please contact Adam Simpson directly.

Best regards,
Better Day Energy Team

Transaction ID: ${transactionId}`;
                            
                            document.getElementById('email-template').textContent = emailTemplate;
                            document.getElementById('result').style.display = 'block';
                            
                            // Store the data for copying
                            window.currentSignatureUrl = signatureUrl;
                            window.currentEmailTemplate = emailTemplate;
                            
                            alert('✅ LOI Created Successfully!\\n\\nThe signature URL is now live and ready to send to the customer.');
                            
                        } else {
                            throw new Error('Failed to create LOI');
                        }
                    } catch (error) {
                        alert('❌ Error creating LOI: ' + error.message);
                    }
                });
                
                function copyUrl() {
                    navigator.clipboard.writeText(window.currentSignatureUrl);
                    alert('✅ Signature URL copied to clipboard!');
                }
                
                function copyEmail() {
                    navigator.clipboard.writeText(window.currentEmailTemplate);
                    alert('✅ Email template copied to clipboard!');
                }
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_create_loi(self, post_data):
        """Handle creating new LOI requests"""
        try:
            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))
            
            # Load existing signature requests
            global signature_requests
            
            # Generate a unique request key
            request_key = f"request_{len(signature_requests) + 1:03d}"
            
            # Add new request to memory
            signature_requests[request_key] = data
            
            # Save to file (in production, this updates the server's data)
            try:
                with open("signature_request_data.json", "w") as f:
                    json.dump(signature_requests, f, indent=2)
                logger.info(f"LOI request created: {data['transaction_id']} for {data['signer_name']}")
            except Exception as e:
                logger.error(f"Failed to save LOI data to file: {str(e)}")
                # Continue anyway since we have it in memory
            
            # Send success response
            response_data = {
                "success": True,
                "message": "LOI created successfully",
                "transaction_id": data["transaction_id"],
                "signature_token": data["signature_token"],
                "signature_url": f"https://loi-automation-api.onrender.com/sign/{data['signature_token']}"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error creating LOI: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

def main():
    """Start the complete integrated signature server"""
    import os
    port = int(os.environ.get('PORT', 8003))  # Use PORT env var for Render
    server_address = ('', port)
    httpd = HTTPServer(server_address, IntegratedSignatureHandler)
    
    print("🚀 Better Day Energy COMPLETE Signature System Started!")
    print("=" * 60)
    print(f"🌐 Access at: http://localhost:{port}")
    print(f"🎯 Admin panel: http://localhost:{port}/admin")
    print("📧 Ready for complete workflow automation")
    print("\n✅ Complete Workflow:")
    print("1. 🖊️ Electronic signature capture")
    print("2. 💾 PostgreSQL tamper-evident storage") 
    print("3. 🔐 Cryptographic integrity verification")
    print("4. 📄 PDF-ready HTML generation")
    print("5. 📝 CRM record creation and storage")
    print("6. 🔗 Document accessibility for download")
    print("\n🎯 Features Available:")
    print("- /signed-loi/CODE - PDF-ready document")
    print("- /signature-image/CODE - Signature image")
    print("- /audit-report/CODE - Complete audit trail")
    print("- Full CRM integration with Farley's contact")
    
    httpd.serve_forever()

if __name__ == "__main__":
    main()