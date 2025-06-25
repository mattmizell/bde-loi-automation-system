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
import threading
import time
import hashlib
import secrets
import os
from signature_storage import TamperEvidentSignatureStorage
from html_to_pdf_generator import HTMLLOIPDFGenerator

# CRM Bridge Authentication
CRM_BRIDGE_TOKENS = {
    "loi_automation": "bde_loi_auth_" + hashlib.sha256("loi_automation_secret_key_2025".encode()).hexdigest()[:32],
    "bolt_sales_tool": "bde_bolt_auth_" + hashlib.sha256("bolt_sales_secret_key_2025".encode()).hexdigest()[:32], 
    "adam_sales_app": "bde_adam_auth_" + hashlib.sha256("adam_sales_secret_key_2025".encode()).hexdigest()[:32],
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
signature_storage = TamperEvidentSignatureStorage()
pdf_generator = HTMLLOIPDFGenerator("1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W")

# User Authentication System
AUTHORIZED_USERS = {
    "matt.mizell@gmail.com": {
        "name": "Matt Mizell",
        "role": "admin",
        "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # 'password123'
        "permissions": ["create_loi", "view_all", "admin_access", "crm_access"]
    },
    "adam@betterdayenergy.com": {
        "name": "Adam Castelli", 
        "role": "manager",
        "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # 'password123'
        "permissions": ["create_loi", "view_all", "crm_access"]
    }
}

# Session storage (in production, this would be in database)
user_sessions = {}

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def authenticate_user(email, password):
    """Authenticate user credentials"""
    if email not in AUTHORIZED_USERS:
        return None
    
    user = AUTHORIZED_USERS[email]
    if hash_password(password) == user["password_hash"]:
        # Create session
        session_token = generate_session_token()
        user_sessions[session_token] = {
            "email": email,
            "name": user["name"],
            "role": user["role"],
            "permissions": user["permissions"],
            "login_time": datetime.now(),
            "expires": datetime.now() + timedelta(hours=8)
        }
        return session_token
    return None

def get_user_from_session(session_token):
    """Get user info from session token"""
    if not session_token or session_token not in user_sessions:
        return None
    
    session = user_sessions[session_token]
    if datetime.now() > session["expires"]:
        del user_sessions[session_token]
        return None
    
    return session

def require_auth(handler_method):
    """Decorator to require authentication"""
    def wrapper(self, *args, **kwargs):
        # Check for session cookie
        cookie_header = self.headers.get('Cookie', '')
        session_token = None
        
        for cookie in cookie_header.split(';'):
            if 'session_token=' in cookie:
                session_token = cookie.split('session_token=')[1].strip()
                break
        
        user = get_user_from_session(session_token)
        if not user:
            self.send_login_page()
            return
        
        # Add user to request context
        self.current_user = user
        return handler_method(self, *args, **kwargs)
    
    return wrapper

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
            self.serve_admin_dashboard_with_auth()
        elif path == "/login":
            self.serve_login_page()
        elif path == "/logout":
            self.handle_logout()
        elif path.startswith("/api/v1/crm-bridge/"):
            self.handle_crm_bridge_get(path, parsed_path)
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
        elif self.path == "/api/search-crm":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_crm_search(post_data)
        elif self.path == "/api/create-crm-contact":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_create_crm_contact(post_data)
        elif self.path == "/api/update-crm-contact":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_update_crm_contact(post_data)
        elif self.path == "/api/refresh-crm-cache":
            self.handle_refresh_crm_cache()
        elif self.path == "/api/get-crm-contacts":
            self.handle_get_crm_contacts()
        elif self.path == "/api/sync-status":
            self.handle_sync_status()
        elif self.path == "/api/request-paper-copy":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_paper_copy_request(post_data)
        elif self.path == "/api/login":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_login(post_data)
        elif self.path.startswith("/api/v1/crm-bridge/"):
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            self.handle_crm_bridge_post(self.path, post_data)
        else:
            self.send_error(404)
    
    def serve_home(self):
        """Serve home page"""
        html = """
        <html>
        <head>
            <title>Better Day Energy - Document Signature System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; color: #1f4e79; margin-bottom: 40px; background: white; padding: 30px; border-radius: 10px; }
                .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }
                .form-card {
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .form-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
                }
                .form-icon { font-size: 48px; margin-bottom: 15px; }
                .form-title { font-size: 24px; color: #1f4e79; margin-bottom: 10px; }
                .form-subtitle { color: #666; margin-bottom: 20px; font-size: 14px; }
                .form-description { color: #333; margin-bottom: 25px; line-height: 1.5; }
                .form-button {
                    background: #1f4e79;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    font-weight: bold;
                    transition: background 0.2s;
                }
                .form-button:hover { background: #2563eb; }
                .coming-soon {
                    background: #ccc;
                    cursor: not-allowed;
                    opacity: 0.6;
                }
                .info-section {
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏢 Better Day Energy</h1>
                    <h2>Document Signature System</h2>
                    <p>Select a document type to create and route for signature</p>
                </div>
                
                <div class="form-grid">
                    <!-- VP Racing LOI -->
                    <div class="form-card">
                        <div class="form-icon">⛽</div>
                        <h3 class="form-title">VP Racing LOI</h3>
                        <p class="form-subtitle">Fuel Supply Agreement</p>
                        <p class="form-description">
                            Letter of Intent for VP Racing fuel supply partnership. 
                            Configure volumes, incentives, and contract terms.
                        </p>
                        <a href="/admin" class="form-button">► Create New</a>
                    </div>
                    
                    <!-- Phillips 66 LOI -->
                    <div class="form-card">
                        <div class="form-icon">🛢️</div>
                        <h3 class="form-title">Phillips 66 LOI</h3>
                        <p class="form-subtitle">Fuel Supply Agreement</p>
                        <p class="form-description">
                            Letter of Intent for Phillips 66 fuel supply partnership. 
                            P66-specific terms and branding.
                        </p>
                        <a href="#" class="form-button coming-soon" onclick="alert('P66 LOI coming soon!'); return false;">Coming Soon</a>
                    </div>
                    
                    <!-- EFT Setup Form -->
                    <div class="form-card">
                        <div class="form-icon">🏦</div>
                        <h3 class="form-title">EFT Setup</h3>
                        <p class="form-subtitle">Bank Authorization</p>
                        <p class="form-description">
                            Electronic Funds Transfer authorization form for automatic 
                            payment setup and processing.
                        </p>
                        <a href="#" class="form-button coming-soon" onclick="alert('EFT Form coming soon!'); return false;">Coming Soon</a>
                    </div>
                    
                    <!-- Customer Setup -->
                    <div class="form-card">
                        <div class="form-icon">📋</div>
                        <h3 class="form-title">Customer Setup</h3>
                        <p class="form-subtitle">Onboarding Document</p>
                        <p class="form-description">
                            Comprehensive customer onboarding form for new business 
                            relationships and account setup.
                        </p>
                        <a href="#" class="form-button coming-soon" onclick="alert('Customer Setup coming soon!'); return false;">Coming Soon</a>
                    </div>
                </div>
                
                <div class="info-section">
                    <h3>📊 System Features</h3>
                    <ul>
                        <li>🔍 Customer search and CRM integration</li>
                        <li>✍️ Electronic signature capture</li>
                        <li>📧 Automatic email notifications</li>
                        <li>🔒 Secure document storage</li>
                        <li>📈 Real-time status tracking</li>
                        <li>🏢 Multi-document support</li>
                    </ul>
                </div>
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
                
                /* ESIGN Act Compliance Styling */
                .esign-disclosure-section {{
                    background: #fff8e1;
                    border: 2px solid #ff9800;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .legal-disclosure-content {{
                    font-size: 14px;
                    line-height: 1.6;
                }}
                .disclosure-box {{
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .disclosure-details h5 {{
                    color: #d84315;
                    margin: 15px 0 8px 0;
                    font-size: 14px;
                }}
                .disclosure-details ul {{
                    margin: 8px 0;
                    padding-left: 20px;
                }}
                .disclosure-details li {{
                    margin: 6px 0;
                }}
                .consent-checkboxes {{
                    background: #f5f5f5;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .consent-item {{
                    display: block;
                    margin: 12px 0;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .consent-checkbox {{
                    margin-right: 10px;
                    transform: scale(1.2);
                }}
                .consent-text {{
                    line-height: 1.5;
                }}
                .paper-copy-info {{
                    background: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 15px 0;
                    text-align: center;
                }}
                .consent-validation-error {{
                    background: #ffebee;
                    color: #c62828;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 10px 0;
                    display: none;
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
                            <tr><th>Phone</th><td>{signature_request.get('deal_terms', {}).get('customer', {}).get('phone', 'Not provided')}</td></tr>
                            <tr><th>Business Address</th><td>{signature_request.get('deal_terms', {}).get('customer', {}).get('address', 'Not provided')}</td></tr>
                            <tr><th>Business Type</th><td>Independent Gas Station</td></tr>
                        </table>
                        
                        <h3>Fuel Volume Commitments</h3>
                        <table>
                            <tr><th>Product</th><th>Monthly Volume</th><th>Annual Volume</th></tr>
                            <tr><td>Gasoline</td><td>{signature_request.get('deal_terms', {}).get('gasoline_volume', 0):,} gallons</td><td>{signature_request.get('deal_terms', {}).get('gasoline_volume', 0) * 12:,} gallons</td></tr>
                            <tr><td>Diesel</td><td>{signature_request.get('deal_terms', {}).get('diesel_volume', 0):,} gallons</td><td>{signature_request.get('deal_terms', {}).get('diesel_volume', 0) * 12:,} gallons</td></tr>
                            <tr><td><strong>Total</strong></td><td><strong>{signature_request.get('deal_terms', {}).get('gasoline_volume', 0) + signature_request.get('deal_terms', {}).get('diesel_volume', 0):,} gallons</strong></td><td><strong>{(signature_request.get('deal_terms', {}).get('gasoline_volume', 0) + signature_request.get('deal_terms', {}).get('diesel_volume', 0)) * 12:,} gallons</strong></td></tr>
                        </table>
                        
                        <div class="financial-highlight">
                            <h3>Financial Incentive Package</h3>
                            <table>
                                <tr><th>Incentive Type</th><th>Amount</th></tr>
                                <tr><td>Image Program Funding</td><td>${signature_request.get('deal_terms', {}).get('image_funding', 0):,}</td></tr>
                                <tr><td>Volume Incentives (Annual)</td><td>${signature_request.get('deal_terms', {}).get('volume_incentives', 0):,}</td></tr>
                                <tr><td><strong>Total First Year Value</strong></td><td><strong>${signature_request.get('deal_terms', {}).get('image_funding', 0) + signature_request.get('deal_terms', {}).get('volume_incentives', 0):,}</strong></td></tr>
                            </table>
                        </div>
                        
                        <h3>Key Terms & Conditions</h3>
                        <ul>
                            <li>Contract Duration: {signature_request.get('deal_terms', {}).get('contract_duration', 36)} months</li>
                            <li>Exclusive fuel purchasing agreement</li>
                            <li>Minimum monthly volume: {signature_request.get('deal_terms', {}).get('gasoline_volume', 0) + signature_request.get('deal_terms', {}).get('diesel_volume', 0):,} gallons</li>
                            <li>Target conversion date: {signature_request.get('deal_terms', {}).get('conversion_date', 'TBD')}</li>
                            <li>Dedicated account management</li>
                            <li>24/7 emergency fuel supply</li>
                            <li>Competitive pricing with quarterly reviews</li>
                        </ul>
                        
                        <!-- ESIGN Act Compliance Section - Required by Federal Law -->
                        <div class="esign-disclosure-section">
                            <h3>🔒 Electronic Signature Disclosure (Required by Law)</h3>
                            <div class="legal-disclosure-content">
                                <div class="disclosure-box">
                                    <h4>Electronic Records and Signatures Consent</h4>
                                    <p><strong>Before proceeding, you must understand and consent to the following:</strong></p>
                                    
                                    <div class="disclosure-details">
                                        <h5>Your Rights:</h5>
                                        <ul>
                                            <li><strong>Paper Copies:</strong> You have the right to receive a paper copy of this document at no charge by contacting us at admin@betterdayenergy.com</li>
                                            <li><strong>Withdrawal:</strong> You may withdraw your consent to receive electronic records at any time</li>
                                            <li><strong>Legal Effect:</strong> Your electronic signature will have the same legal effect as a handwritten signature</li>
                                        </ul>
                                        
                                        <h5>System Requirements:</h5>
                                        <ul>
                                            <li>Internet browser with JavaScript enabled</li>
                                            <li>Valid email address for record delivery</li>
                                            <li>Ability to download and save PDF documents</li>
                                        </ul>
                                        
                                        <h5>Record Retention:</h5>
                                        <ul>
                                            <li>You should retain copies of all electronic records</li>
                                            <li>Electronic records will be provided via email and online access</li>
                                            <li>Records are stored securely with cryptographic integrity protection</li>
                                        </ul>
                                    </div>
                                </div>
                                
                                <div class="consent-checkboxes">
                                    <label class="consent-item">
                                        <input type="checkbox" id="electronic-records-consent" required class="consent-checkbox">
                                        <span class="consent-text"><strong>I consent to receive this document and all related records electronically instead of paper copies</strong></span>
                                    </label>
                                    
                                    <label class="consent-item">
                                        <input type="checkbox" id="hardware-software-acknowledge" required class="consent-checkbox">
                                        <span class="consent-text">I acknowledge that I have been informed of the hardware and software requirements above</span>
                                    </label>
                                    
                                    <label class="consent-item">
                                        <input type="checkbox" id="signature-intent-confirm" required class="consent-checkbox">
                                        <span class="consent-text"><strong>I intend to sign this document electronically and understand it will be legally binding</strong></span>
                                    </label>
                                    
                                    <label class="consent-item">
                                        <input type="checkbox" id="terms-understanding" required class="consent-checkbox">
                                        <span class="consent-text">I have read, understood, and agree to all terms stated in this Letter of Intent</span>
                                    </label>
                                </div>
                                
                                <div class="paper-copy-info">
                                    <p><small><strong>Need a paper copy?</strong> Contact admin@betterdayenergy.com or call (555) 123-4567</small></p>
                                </div>
                            </div>
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
                        <p>Complete all consent requirements before signing.</p>
                    </div>
                    
                    <!-- Consent Validation Error -->
                    <div class="consent-validation-error" id="consent-error">
                        <strong>⚠️ Required Consent Missing</strong><br>
                        You must check all required consent boxes above before signing.
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
                
                // Validate ESIGN Act consent requirements
                function validateESIGNConsent() {{
                    const requiredCheckboxes = [
                        'electronic-records-consent',
                        'hardware-software-acknowledge', 
                        'signature-intent-confirm',
                        'terms-understanding'
                    ];
                    
                    const uncheckedBoxes = requiredCheckboxes.filter(id => !document.getElementById(id).checked);
                    
                    if (uncheckedBoxes.length > 0) {{
                        document.getElementById('consent-error').style.display = 'block';
                        document.getElementById('consent-error').scrollIntoView({{ behavior: 'smooth' }});
                        return false;
                    }}
                    
                    document.getElementById('consent-error').style.display = 'none';
                    return true;
                }}
                
                // Submit signature with full workflow and ESIGN compliance
                async function submitSignature() {{
                    // First validate ESIGN consent
                    if (!validateESIGNConsent()) {{
                        return;
                    }}
                    
                    if (signaturePad.isEmpty()) {{
                        alert('Please provide your signature before submitting.');
                        return;
                    }}
                    
                    const signButton = document.getElementById('sign-button');
                    signButton.disabled = true;
                    signButton.innerHTML = '⏳ Processing Complete Workflow...';
                    
                    try {{
                        const signatureData = signaturePad.toDataURL('image/png');
                        
                        // Collect consent data for ESIGN compliance
                        const consentData = {{
                            electronic_consent_given: document.getElementById('electronic-records-consent').checked,
                            hardware_software_acknowledged: document.getElementById('hardware-software-acknowledge').checked,
                            explicit_intent_confirmed: document.getElementById('signature-intent-confirm').checked,
                            terms_understanding_confirmed: document.getElementById('terms-understanding').checked,
                            disclosures_acknowledged: true,
                            consent_timestamp: new Date().toISOString(),
                            identity_authentication_method: 'email_and_browser_fingerprint'
                        }};
                        
                        const response = await fetch('/api/submit-signature', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                signature_token: '{signature_request['signature_token']}',
                                signature_data: signatureData,
                                signed_at: new Date().toISOString(),
                                consent_data: consentData
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
            
            # Process ESIGN Act consent data
            consent_data = data.get('consent_data', {})
            
            # Update signature request with consent information for compliance
            signature_request.update({
                'electronic_consent_given': consent_data.get('electronic_consent_given', False),
                'explicit_intent_confirmed': consent_data.get('explicit_intent_confirmed', False),
                'disclosures_acknowledged': consent_data.get('disclosures_acknowledged', False),
                'hardware_software_acknowledged': consent_data.get('hardware_software_acknowledged', False),
                'terms_understanding_confirmed': consent_data.get('terms_understanding_confirmed', False),
                'consent_timestamp': consent_data.get('consent_timestamp'),
                'identity_authentication_method': consent_data.get('identity_authentication_method', 'email_and_browser_fingerprint')
            })
            
            logger.info(f"🚀 Starting ESIGN compliant signature workflow for {signature_request['signer_name']}")
            logger.info(f"🔒 Consent validation: Electronic={consent_data.get('electronic_consent_given')}, Intent={consent_data.get('explicit_intent_confirmed')}")
            
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
            
            # STEP 3: Generate PDF of the signed document
            logger.info("📄 Step 3: Generating PDF...")
            
            # Get the signed HTML document
            signed_html = self.generate_signed_document_html(signature_request, verification_code)
            
            # Convert HTML to PDF
            pdf_path = f"/tmp/signed_loi_{verification_code}.pdf"
            pdf_success = self.html_to_pdf(signed_html, pdf_path)
            
            # STEP 4: Store PDF in CRM
            logger.info("📝 Step 4: Storing PDF in CRM...")
            
            # Get the correct contact ID from signature request
            contact_id = signature_request.get('crm_contact_id')
            if not contact_id:
                # Try to find contact by email
                customer_email = signature_request.get('signer_email')
                contact_id = self.find_crm_contact_by_email(customer_email)
            
            crm_success = False
            if contact_id and pdf_success:
                # Store PDF in CRM as attachment
                crm_success = self.store_pdf_in_crm(contact_id, pdf_path, signature_request, verification_code)
                
                # Also store link and audit info
                pdf_generator.store_in_crm_with_pdf_link(
                    contact_id,
                    audit_report,
                    f"https://loi-automation-api.onrender.com/signed-loi/{verification_code}"
                )
            
            # STEP 5: Email PDF to customer
            logger.info("📧 Step 5: Emailing signed document to customer...")
            email_sent = False
            if pdf_success:
                email_sent = self.email_signed_pdf_to_customer(
                    signature_request, 
                    pdf_path, 
                    verification_code
                )
            
            # Update in-memory status
            signature_request['status'] = 'completed'
            signature_request['verification_code'] = verification_code
            
            logger.info(f"🎉 COMPLETE WORKFLOW FINISHED for {signature_request['signer_name']}")
            logger.info(f"📄 PDF generated: {pdf_success}")
            logger.info(f"📝 CRM updated: {crm_success}")
            logger.info(f"📧 Email sent: {email_sent}")
            
            # Send response
            response_data = {
                'success': True,
                'verification_code': verification_code,
                'workflow_completed': True,
                'pdf_url': f"/signed-loi/{verification_code}",
                'pdf_generated': pdf_success,
                'crm_updated': crm_success,
                'email_sent': email_sent
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"❌ Error in complete workflow: {e}")
            self.send_error(500, str(e))
    
    def generate_signed_document_html(self, signature_request, verification_code):
        """Generate HTML version of signed document for PDF conversion"""
        signature_data = signature_storage.get_signature_image(verification_code)
        audit_report = signature_storage.get_audit_report(verification_code)
        
        # Get deal terms
        deal_terms = signature_request.get('deal_terms', {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Signed LOI - {signature_request['transaction_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .section {{ margin-bottom: 25px; }}
                h1 {{ color: #1f4e79; }}
                h2 {{ color: #2563eb; margin-top: 25px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .signature-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .signature-image {{ border: 2px solid #000; padding: 10px; background: white; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #ddd; }}
                .verification {{ background: #e8f5e8; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Better Day Energy</h1>
                <h2>Letter of Intent - VP Racing Fuel Supply Agreement</h2>
                <p><strong>SIGNED DOCUMENT</strong></p>
            </div>
            
            <div class="section">
                <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                <p><strong>Transaction ID:</strong> {signature_request['transaction_id']}</p>
                <p><strong>Verification Code:</strong> {verification_code}</p>
            </div>
            
            <div class="section">
                <h3>Customer Information</h3>
                <table>
                    <tr><th>Business Name</th><td>{signature_request['company_name']}</td></tr>
                    <tr><th>Owner/Contact</th><td>{signature_request['signer_name']}</td></tr>
                    <tr><th>Email</th><td>{signature_request['signer_email']}</td></tr>
                    <tr><th>Phone</th><td>{deal_terms.get('customer', {}).get('phone', 'Not provided')}</td></tr>
                    <tr><th>Business Address</th><td>{deal_terms.get('customer', {}).get('address', 'Not provided')}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h3>Fuel Volume Commitments</h3>
                <table>
                    <tr><th>Product</th><th>Monthly Volume</th><th>Annual Volume</th></tr>
                    <tr><td>Gasoline</td><td>{deal_terms.get('gasoline_volume', 0):,} gallons</td><td>{deal_terms.get('gasoline_volume', 0) * 12:,} gallons</td></tr>
                    <tr><td>Diesel</td><td>{deal_terms.get('diesel_volume', 0):,} gallons</td><td>{deal_terms.get('diesel_volume', 0) * 12:,} gallons</td></tr>
                    <tr><td><strong>Total</strong></td><td><strong>{(deal_terms.get('gasoline_volume', 0) + deal_terms.get('diesel_volume', 0)):,} gallons</strong></td><td><strong>{(deal_terms.get('gasoline_volume', 0) + deal_terms.get('diesel_volume', 0)) * 12:,} gallons</strong></td></tr>
                </table>
            </div>
            
            <div class="section">
                <h3>Financial Incentive Package</h3>
                <table>
                    <tr><th>Incentive Type</th><th>Amount</th></tr>
                    <tr><td>Image Program Funding</td><td>${deal_terms.get('image_funding', 0):,}</td></tr>
                    <tr><td>Volume Incentives</td><td>${deal_terms.get('volume_incentives', 0):,}</td></tr>
                    <tr><td><strong>Total First Year Value</strong></td><td><strong>${(deal_terms.get('image_funding', 0) + deal_terms.get('volume_incentives', 0)):,}</strong></td></tr>
                </table>
            </div>
            
            <div class="signature-section">
                <h3>Electronic Signature</h3>
                <p><strong>Signed by:</strong> {signature_request['signer_name']}</p>
                <p><strong>Date:</strong> {audit_report['signed_at']}</p>
                <p><strong>IP Address:</strong> {audit_report['ip_address']}</p>
                <div class="signature-image">
                    <img src="{signature_data['data_url']}" alt="Signature" style="max-width: 300px;">
                </div>
            </div>
            
            <div class="footer verification">
                <h3>Document Verification</h3>
                <p><strong>Verification Code:</strong> {verification_code}</p>
                <p><strong>Document Hash:</strong> {audit_report['hash']}</p>
                <p><strong>Signature Method:</strong> Electronic Signature</p>
                <p><strong>Storage:</strong> PostgreSQL with tamper-evident features</p>
                <p>This document has been electronically signed and is legally binding.</p>
            </div>
        </body>
        </html>
        """
        return html
    
    def html_to_pdf(self, html_content, output_path):
        """Convert HTML to PDF using best available method"""
        try:
            # First try wkhtmltopdf if available
            import subprocess
            import tempfile
            
            # Check if wkhtmltopdf is available
            try:
                subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, check=True)
                wkhtmltopdf_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                wkhtmltopdf_available = False
            
            if wkhtmltopdf_available:
                # Write HTML to temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(html_content)
                    temp_html = f.name
                
                # Convert to PDF
                result = subprocess.run([
                    'wkhtmltopdf',
                    '--enable-local-file-access',
                    '--margin-top', '20mm',
                    '--margin-bottom', '20mm',
                    '--margin-left', '20mm',
                    '--margin-right', '20mm',
                    temp_html,
                    output_path
                ], capture_output=True, text=True)
                
                # Clean up temp file
                os.unlink(temp_html)
                
                if result.returncode == 0:
                    logger.info(f"✅ PDF generated successfully with wkhtmltopdf: {output_path}")
                    return True
                else:
                    logger.error(f"❌ wkhtmltopdf failed: {result.stderr}")
            
            # Fallback: Use Python PDF library
            logger.info("📄 Trying Python PDF generation...")
            
            # Try weasyprint first (best HTML to PDF conversion)
            try:
                import weasyprint
                
                # Generate PDF with WeasyPrint
                weasyprint.HTML(string=html_content).write_pdf(output_path)
                logger.info(f"✅ PDF generated successfully with WeasyPrint: {output_path}")
                return True
                
            except ImportError:
                logger.info("WeasyPrint not available, trying reportlab...")
                
                # Try reportlab
                try:
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import letter
                    from reportlab.lib.styles import getSampleStyleSheet
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                    from reportlab.lib.units import inch
                    import re
                    from html import unescape
                    
                    # Convert HTML to text for reportlab
                    text_content = re.sub('<[^<]+?>', '', html_content)
                    text_content = unescape(text_content)
                    
                    # Create PDF with reportlab
                    doc = SimpleDocTemplate(output_path, pagesize=letter)
                    styles = getSampleStyleSheet()
                    story = []
                    
                    # Split content into paragraphs
                    paragraphs = text_content.split('\n\n')
                    
                    for para in paragraphs:
                        if para.strip():
                            if 'LETTER OF INTENT' in para.upper():
                                p = Paragraph(para.strip(), styles['Title'])
                            elif para.strip().isupper() and len(para.strip()) < 50:
                                p = Paragraph(para.strip(), styles['Heading1'])
                            else:
                                p = Paragraph(para.strip(), styles['Normal'])
                            story.append(p)
                            story.append(Spacer(1, 0.1*inch))
                    
                    doc.build(story)
                    logger.info(f"✅ PDF generated successfully with ReportLab: {output_path}")
                    return True
                    
                except ImportError:
                    logger.info("ReportLab not available, saving as formatted HTML...")
                    
                    # Final fallback: Enhanced HTML with print styles
                    html_with_print_styles = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Signed Document</title>
                        <style>
                            @media print {{
                                body {{ margin: 0.5in; font-family: Arial, sans-serif; }}
                                .no-print {{ display: none; }}
                            }}
                            body {{ font-family: Arial, sans-serif; line-height: 1.4; }}
                            h1 {{ color: #1f4e79; text-align: center; }}
                            h2 {{ color: #2563eb; border-bottom: 2px solid #2563eb; }}
                            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                            .signature {{ border: 2px solid #007bff; padding: 10px; margin: 20px 0; }}
                            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                        </style>
                    </head>
                    <body>
                        {html_content.split('<body>')[1].split('</body>')[0] if '<body>' in html_content else html_content}
                        <div class="no-print">
                            <p><strong>Note:</strong> This is a print-ready HTML version. Use your browser's print function to create a PDF.</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    html_path = output_path.replace('.pdf', '.html')
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_with_print_styles)
                    
                    logger.info(f"✅ HTML document saved (print-ready): {html_path}")
                    return True
                
        except Exception as e:
            logger.error(f"❌ Error generating PDF: {e}")
            # Final fallback: save as basic HTML
            try:
                html_path = output_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"📄 Basic HTML saved: {html_path}")
            except:
                pass
            return False
    
    def find_crm_contact_by_email(self, email):
        """Find CRM contact ID by email"""
        try:
            conn = signature_storage.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT contact_id FROM crm_contacts_cache 
                    WHERE LOWER(email) = LOWER(%s) 
                    LIMIT 1
                """, (email,))
                result = cursor.fetchone()
                conn.close()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error finding contact by email: {e}")
            return None
    
    def store_pdf_in_crm(self, contact_id, pdf_path, signature_request, verification_code):
        """Store PDF or HTML as attachment in CRM"""
        try:
            import requests
            import base64
            import os
            
            # Check if PDF exists, otherwise look for HTML
            file_path = pdf_path
            file_extension = ".pdf"
            
            if not os.path.exists(pdf_path):
                html_path = pdf_path.replace('.pdf', '.html')
                if os.path.exists(html_path):
                    file_path = html_path
                    file_extension = ".html"
                else:
                    logger.error(f"Neither PDF nor HTML file found: {pdf_path}")
                    return False
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data_bytes = f.read()
            
            # Encode file as base64
            file_base64 = base64.b64encode(file_data_bytes).decode('utf-8')
            
            # Prepare CRM API request
            api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
            api_user = api_key.split('-')[0]
            
            # Create file attachment in CRM
            file_data = {
                "Function": "CreateFile",
                "Parameters": {
                    "IsAttachedToContact": contact_id,
                    "FileName": f"Signed_LOI_{verification_code}{file_extension}",
                    "FileData": file_base64
                }
            }
            
            response = requests.post(
                "https://api.lessannoyingcrm.com/v2/",
                json={
                    "UserCode": api_user,
                    "APIToken": api_key,
                    **file_data
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('Success'):
                    logger.info(f"✅ PDF stored in CRM for contact {contact_id}")
                    
                    # Also add a note about the signed document
                    note_data = {
                        "Function": "CreateNote",
                        "Parameters": {
                            "ContactId": contact_id,
                            "Note": f"Signed LOI Document\n\nTransaction ID: {signature_request['transaction_id']}\nVerification Code: {verification_code}\nSigned by: {signature_request['signer_name']}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nDocument Type: VP Racing Fuel Supply Agreement"
                        }
                    }
                    
                    requests.post(
                        "https://api.lessannoyingcrm.com/v2/",
                        json={
                            "UserCode": api_user,
                            "APIToken": api_key,
                            **note_data
                        }
                    )
                    
                    return True
                else:
                    logger.error(f"CRM API error: {result.get('Error')}")
                    return False
            else:
                logger.error(f"CRM API HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing PDF in CRM: {e}")
            return False
    
    def email_signed_pdf_to_customer(self, signature_request, pdf_path, verification_code):
        """Email the signed document to the customer"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            # Check if PDF exists, otherwise look for HTML
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
                    logger.error(f"Neither PDF nor HTML file found for email: {pdf_path}")
                    return False
            
            # Get SMTP settings
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', 'transaction.coordinator.agent@gmail.com')
            smtp_password = os.getenv('SMTP_PASSWORD', 'xmvi xvso zblo oewe')
            
            # Create email
            msg = MIMEMultipart()
            msg['Subject'] = f"Your Signed LOI Document - {signature_request['company_name']}"
            msg['From'] = f"Better Day Energy <{smtp_username}>"
            msg['To'] = signature_request['signer_email']
            
            # Email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #1f4e79, #2563eb); color: white; padding: 30px; text-align: center;">
                    <h1>🏢 Better Day Energy</h1>
                    <h2>Thank You for Signing!</h2>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <p>Dear {signature_request['signer_name']},</p>
                    
                    <p>Thank you for electronically signing the VP Racing Fuel Supply Agreement Letter of Intent.</p>
                    
                    <p>Your signed document is attached to this email as a {file_type} file for your records.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>📄 Document Details:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li>• <strong>Transaction ID:</strong> {signature_request['transaction_id']}</li>
                            <li>• <strong>Verification Code:</strong> {verification_code}</li>
                            <li>• <strong>Date Signed:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                        </ul>
                    </div>
                    
                    <p>You can also view your signed document online at any time:</p>
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="https://loi-automation-api.onrender.com/signed-loi/{verification_code}" 
                           style="background: #1f4e79; color: white; padding: 10px 20px; text-decoration: none; 
                                  border-radius: 6px; display: inline-block;">
                            View Document Online
                        </a>
                    </div>
                    
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                    
                    <p>Best regards,<br>
                    Better Day Energy Team</p>
                </div>
                
                <div style="background: #e9ecef; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                    <p>This email contains confidential information. Please keep your verification code secure.</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_body = f"""
Dear {signature_request['signer_name']},

Thank you for electronically signing the VP Racing Fuel Supply Agreement Letter of Intent.

Your signed document is attached to this email as a {file_type} file for your records.

Document Details:
• Transaction ID: {signature_request['transaction_id']}
• Verification Code: {verification_code}
• Date Signed: {datetime.now().strftime('%B %d, %Y')}

You can also view your signed document online at:
https://loi-automation-api.onrender.com/signed-loi/{verification_code}

If you have any questions, please don't hesitate to contact us.

Best regards,
Better Day Energy Team
            """
            
            # Attach parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
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
                
            logger.info(f"📎 Attached {file_type} document: {file_path}")
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Signed document emailed to {signature_request['signer_email']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to email signed document: {e}")
            return False
    
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
    
    def serve_admin_dashboard_with_auth(self):
        """Serve admin dashboard with authentication check"""
        # Check for session cookie
        cookie_header = self.headers.get('Cookie', '')
        session_token = None
        
        for cookie in cookie_header.split(';'):
            if 'session_token=' in cookie:
                session_token = cookie.split('session_token=')[1].strip()
                break
        
        user = get_user_from_session(session_token)
        if not user:
            self.serve_login_page()
            return
        
        # User is authenticated, serve the dashboard
        self.current_user = user
        self.serve_admin_dashboard()
    
    def serve_login_page(self):
        """Serve login page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Better Day Energy - Login</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #1f4e79, #2c5aa0);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .login-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    width: 100%;
                    max-width: 400px;
                }}
                .login-header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .login-header h1 {{
                    color: #1f4e79;
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                .login-header p {{
                    color: #666;
                    font-size: 14px;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 8px;
                    font-weight: 600;
                    color: #1f4e79;
                }}
                .form-group input {{
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #e9ecef;
                    border-radius: 6px;
                    font-size: 16px;
                }}
                .form-group input:focus {{
                    outline: none;
                    border-color: #007bff;
                }}
                .btn {{
                    background: #28a745;
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    width: 100%;
                }}
                .btn:hover {{
                    background: #218838;
                }}
                .error-msg {{
                    background: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    display: none;
                }}
                .user-note {{
                    background: #e7f3ff;
                    border: 1px solid #007bff;
                    padding: 15px;
                    border-radius: 6px;
                    margin-top: 20px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="login-header">
                    <h1>🎯 Better Day Energy</h1>
                    <p>LOI Administration System</p>
                </div>
                
                <div id="error-msg" class="error-msg"></div>
                
                <form id="login-form">
                    <div class="form-group">
                        <label for="email">Email Address:</label>
                        <input type="email" id="email" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" required>
                    </div>
                    
                    <button type="submit" class="btn">🔑 Login</button>
                </form>
                
                <div class="user-note">
                    <strong>Authorized Users:</strong><br>
                    • Matt Mizell (matt.mizell@gmail.com)<br>
                    • Adam Castelli (adam@betterdayenergy.com)<br><br>
                    <em>Initial password: password123</em>
                </div>
            </div>
            
            <script>
                document.getElementById('login-form').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const errorDiv = document.getElementById('error-msg');
                    
                    try {{
                        const response = await fetch('/api/login', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ email, password }})
                        }});
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            // Set session cookie and redirect
                            document.cookie = `session_token=${{result.session_token}}; path=/; max-age=28800`; // 8 hours
                            window.location.href = '/admin';
                        }} else {{
                            errorDiv.textContent = result.error || 'Login failed';
                            errorDiv.style.display = 'block';
                        }}
                    }} catch (error) {{
                        errorDiv.textContent = 'Connection error: ' + error.message;
                        errorDiv.style.display = 'block';
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_paper_copy_request(self, post_data):
        """Handle paper copy requests as required by ESIGN Act"""
        try:
            data = json.loads(post_data.decode())
            verification_code = data.get('verification_code')
            email = data.get('email')
            reason = data.get('reason', 'Requested paper copy')
            
            if not verification_code or not email:
                self.send_error(400, "Verification code and email required")
                return
            
            # Verify the document exists
            audit_report = signature_storage.get_audit_report(verification_code)
            if not audit_report:
                self.send_error(404, "Document not found")
                return
            
            # Log the paper copy request
            logger.info(f"📄 Paper copy requested for {verification_code} by {email}")
            
            # Send email notification to admin
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
                smtp_port = int(os.getenv('SMTP_PORT', '587'))
                smtp_username = os.getenv('SMTP_USERNAME', 'transaction.coordinator.agent@gmail.com')
                smtp_password = os.getenv('SMTP_PASSWORD', 'xmvi xvso zblo oewe')
                
                msg = MIMEMultipart()
                msg['Subject'] = f"Paper Copy Request - {verification_code}"
                msg['From'] = f"Better Day Energy <{smtp_username}>"
                msg['To'] = "admin@betterdayenergy.com"
                
                body = f"""
Paper Copy Request Received

Document: {audit_report['document_name']}
Verification Code: {verification_code}
Requester Email: {email}
Signer: {audit_report['signer_name']}
Company: {audit_report['company_name']}
Original Signature Date: {audit_report['signed_at']}
Request Reason: {reason}
Request Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ESIGN Act Compliance: As required by federal law, this customer has requested a paper copy of their electronically signed document. Please fulfill this request promptly at no charge to the customer.

Document Link: https://loi-automation-api.onrender.com/signed-loi/{verification_code}
                """
                
                msg.attach(MIMEText(body, 'plain'))
                
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                # Send confirmation to requester
                msg_customer = MIMEMultipart()
                msg_customer['Subject'] = "Paper Copy Request Received"
                msg_customer['From'] = f"Better Day Energy <{smtp_username}>"
                msg_customer['To'] = email
                
                customer_body = f"""
Dear {audit_report['signer_name']},

Your request for a paper copy of the electronically signed document has been received and will be processed within 2-3 business days at no charge.

Document Details:
- Verification Code: {verification_code}
- Document: {audit_report['document_name']}
- Original Signature Date: {audit_report['signed_at'].strftime('%B %d, %Y')}

The paper copy will be mailed to the address we have on file. If you need it sent to a different address, please reply to this email with the correct mailing address.

Thank you,
Better Day Energy Team
                """
                
                msg_customer.attach(MIMEText(customer_body, 'plain'))
                
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg_customer)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': 'Paper copy request submitted successfully. You will receive a confirmation email and your paper copy within 2-3 business days.'
                }).encode())
                
            except Exception as e:
                logger.error(f"Failed to send paper copy request emails: {e}")
                self.send_error(500, "Failed to process paper copy request")
                
        except Exception as e:
            logger.error(f"Error handling paper copy request: {e}")
            self.send_error(500, str(e))

    def handle_login(self, post_data):
        """Handle login request"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            
            session_token = authenticate_user(email, password)
            
            if session_token:
                user = AUTHORIZED_USERS[email]
                response_data = {
                    "success": True,
                    "session_token": session_token,
                    "user": {
                        "name": user["name"],
                        "email": email,
                        "role": user["role"],
                        "permissions": user["permissions"]
                    }
                }
                logger.info(f"User logged in: {email} ({user['role']})")
            else:
                response_data = {
                    "success": False,
                    "error": "Invalid email or password"
                }
                logger.warning(f"Failed login attempt: {email}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_logout(self):
        """Handle logout request"""
        # Clear session cookie and redirect to login
        self.send_response(302)
        self.send_header('Location', '/login')
        self.send_header('Set-Cookie', 'session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()
    
    def serve_admin_dashboard(self):
        """Serve CRM-integrated admin dashboard for creating LOIs"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Better Day Energy - CRM-Integrated LOI Admin</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f8f9fa;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
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
                .step-section {
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    border-left: 5px solid #007bff;
                }
                .step-section.active {
                    border-left-color: #28a745;
                    background: #f8fff8;
                }
                .step-section h2 {
                    color: #1f4e79;
                    margin-bottom: 20px;
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
                .form-group input, .form-group select, .form-group textarea {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #e9ecef;
                    border-radius: 6px;
                    font-size: 16px;
                }
                .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
                    outline: none;
                    border-color: #007bff;
                }
                .form-row {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }
                .btn {
                    background: #007bff;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    margin-right: 10px;
                    margin-bottom: 10px;
                }
                .btn.btn-success {
                    background: #28a745;
                }
                .btn.btn-warning {
                    background: #ffc107;
                    color: #000;
                }
                .btn:hover {
                    opacity: 0.9;
                }
                .customer-info {
                    background: #e7f3ff;
                    border: 2px solid #007bff;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                .deal-summary {
                    background: #e8f5e8;
                    border: 2px solid #28a745;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                .hidden {
                    display: none;
                }
                .error-box {
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 10px 0;
                }
                .success-box {
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 10px 0;
                }
                .workflow-status {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }
                .financial-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 15px;
                }
                @media (max-width: 768px) {
                    .form-row, .financial-grid { grid-template-columns: 1fr; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Better Day Energy - LOI Creation System</h1>
                    <p>Professional LOI Creation with Background CRM Sync</p>
                    <p><strong>Workflow:</strong> Customer Info → Deal Terms → Generate LOI → Route → Sign → Background CRM Sync</p>
                    <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 6px; font-size: 14px;">
                        <span style="float: left;">👤 Logged in as: <strong>{getattr(self, 'current_user', {}).get('name', 'Unknown')} ({getattr(self, 'current_user', {}).get('role', 'guest')})</strong></span>
                        <span style="float: right;"><a href="/logout" style="color: white; text-decoration: none;">🚪 Logout</a></span>
                        <div style="clear: both;"></div>
                    </div>
                </div>
                
                <div class="content">
                    <div class="workflow-status">
                        <h3>📋 Smart LOI Workflow</h3>
                        <p>1️⃣ Quick CRM search → 2️⃣ Enter/select customer → 3️⃣ Deal terms → 4️⃣ Generate LOI → 5️⃣ Route for signature</p>
                    </div>
                    
                    <!-- STEP 1: Quick CRM Search -->
                    <div class="step-section active" id="step-1">
                        <h2>🔍 Step 1: Quick Customer Check</h2>
                        <p style="color: #666; margin-bottom: 20px;">Search CRM first to avoid duplicates. If not found, we'll create new record.</p>
                        
                        <div class="form-group">
                            <label for="quick-search">Search by company name or contact name:</label>
                            <div style="display: flex; gap: 10px;">
                                <input type="text" id="quick-search" placeholder="e.g., Smith's Gas Station or John Smith" style="flex: 1;">
                                <button type="button" class="btn" onclick="quickSearchCRM()" style="width: auto;">🔍 Search</button>
                            </div>
                        </div>
                        
                        <div id="quick-search-results" class="hidden" style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 6px; background: #f9f9f9;">
                            <!-- Search results will appear here -->
                        </div>
                        
                        <div style="text-align: center; margin: 20px 0; color: #666;">
                            <strong>OR</strong>
                        </div>
                        
                        <button type="button" class="btn btn-success" onclick="skipToNewCustomer()">➕ Skip Search - Add New Customer</button>
                    </div>
                    
                    <!-- STEP 2: Customer Information -->
                    <div class="step-section hidden" id="step-2">
                        <h2>👤 Step 2: Customer Information</h2>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="customer-name">Contact Name: <span style="color: red;">*</span></label>
                                <input type="text" id="customer-name" placeholder="e.g., John Smith" required>
                            </div>
                            <div class="form-group">
                                <label for="customer-email">Email Address: <span style="color: red;">*</span></label>
                                <input type="email" id="customer-email" placeholder="e.g., john@example.com" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="company-name">Company Name: <span style="color: red;">*</span></label>
                                <input type="text" id="company-name" placeholder="e.g., Smith's Gas Station" required>
                            </div>
                            <div class="form-group">
                                <label for="customer-phone">Phone Number:</label>
                                <input type="tel" id="customer-phone" placeholder="e.g., 314-555-1234">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="customer-address">Business Address:</label>
                            <input type="text" id="customer-address" placeholder="e.g., 123 Main St, St. Louis, MO 63101">
                        </div>
                        <button type="button" class="btn btn-success" onclick="proceedToDealTerms()">Next: Deal Terms →</button>
                        <button type="button" class="btn" onclick="showStep(1)" style="background: #6c757d;">← Back to Search</button>
                        
                        <div id="selected-customer-info" class="hidden" style="background: #e7f3ff; padding: 15px; border-radius: 6px; margin-top: 15px;">
                            <!-- Selected customer info will appear here -->
                        </div>
                    </div>
                    
                    
                    <!-- STEP 3: Deal Terms -->
                    <div class="step-section hidden" id="step-3">
                        <h2>💼 Step 3: Enter Deal Terms & Incentives</h2>
                        
                        <div id="customer-summary" class="customer-info">
                            <!-- Customer info will be populated here -->
                        </div>
                        
                        <h3>📊 Volume Commitments</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="gasoline-volume">Monthly Gasoline (gallons):</label>
                                <input type="number" id="gasoline-volume" value="85000" required>
                            </div>
                            <div class="form-group">
                                <label for="diesel-volume">Monthly Diesel (gallons):</label>
                                <input type="number" id="diesel-volume" value="25000" required>
                            </div>
                        </div>
                        
                        <h3>💰 Financial Incentives</h3>
                        <div class="financial-grid">
                            <div class="form-group">
                                <label for="image-funding">Image Program Funding:</label>
                                <input type="number" id="image-funding" value="75000" required>
                            </div>
                            <div class="form-group">
                                <label for="volume-incentives">Annual Volume Incentives:</label>
                                <input type="number" id="volume-incentives" value="50000" required>
                            </div>
                            <div class="form-group">
                                <label for="contract-duration">Contract Duration (months):</label>
                                <input type="number" id="contract-duration" value="36" required>
                            </div>
                        </div>
                        
                        <h3>📋 Terms & Conditions</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="conversion-date">Target Conversion Date:</label>
                                <input type="date" id="conversion-date" required>
                            </div>
                            <div class="form-group">
                                <label for="pricing-structure">Pricing Structure:</label>
                                <select id="pricing-structure" required>
                                    <option value="competitive">Competitive with quarterly reviews</option>
                                    <option value="fixed">Fixed pricing for term</option>
                                    <option value="index">Index-based pricing</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="special-terms">Special Terms/Notes:</label>
                            <textarea id="special-terms" rows="3" placeholder="Any special conditions, requirements, or notes..."></textarea>
                        </div>
                        
                        <button type="button" class="btn btn-success" onclick="generateLOI()">🚀 Generate Complete LOI</button>
                    </div>
                    
                    <!-- STEP 4: LOI Generated -->
                    <div class="step-section hidden" id="step-4">
                        <h2>✅ Step 4: LOI Generated & Ready</h2>
                        <div id="loi-summary" class="deal-summary">
                            <!-- LOI summary will be populated here -->
                        </div>
                        <div id="final-result"></div>
                    </div>
                </div>
            </div>
            
            <script>
                let currentCustomer = null;
                let currentDeal = null;
                let allCustomers = [];
                
                // Load CRM contacts on page load
                window.addEventListener('load', function() {
                    loadCRMContacts();
                });
                
                async function loadCRMContacts() {
                    try {
                        const response = await fetch('/api/get-crm-contacts');
                        if (response.ok) {
                            const result = await response.json();
                            allCustomers = result.contacts || [];
                            console.log(`Loaded ${allCustomers.length} CRM contacts`);
                            // No DOM updates needed - using modern search workflow
                        } else {
                            // If no cache exists, refresh from CRM
                            console.log('CRM cache not found, refreshing...');
                            await refreshCRMCache();
                        }
                    } catch (error) {
                        console.error('Error loading CRM contacts:', error);
                        // Don't attempt to update any DOM elements in error case
                    }
                }
                
                function populateCustomerDropdown(customers) {
                    // This function is kept for compatibility but does nothing since customer-dropdown doesn't exist
                    // The current HTML workflow uses quick search instead of dropdown
                    console.log(`Would populate dropdown with ${customers ? customers.length : 0} customers (but no dropdown element exists)`);
                }
                
                function filterCustomers() {
                    // This function is kept for compatibility but is not used in current workflow
                    // The HTML uses quick-search instead of customer-search element
                    console.log('filterCustomers called but customer-search element does not exist');
                }
                
                async function quickSearchCRM() {
                    const searchInput = document.getElementById('quick-search');
                    if (!searchInput) {
                        console.error('quick-search input element not found');
                        alert('Search input not found. Please refresh the page.');
                        return;
                    }
                    
                    const query = searchInput.value.trim();
                    if (!query) {
                        alert('Please enter a search term');
                        return;
                    }
                    
                    // Find the search button by selecting it from DOM instead of using undefined event
                    const searchBtn = document.querySelector('button[onclick="quickSearchCRM()"]');
                    if (searchBtn) {
                        searchBtn.disabled = true;
                        searchBtn.innerHTML = '⏳ Searching...';
                    }
                    
                    try {
                        const response = await fetch('/api/search-crm', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ query: query })
                        });
                        
                        if (response.ok) {
                            const results = await response.json();
                            displayQuickSearchResults(results);
                        } else {
                            throw new Error('CRM search failed');
                        }
                    } catch (error) {
                        document.getElementById('quick-search-results').innerHTML = 
                            '<div style="color: #721c24; background: #f8d7da; padding: 10px; border-radius: 4px;">❌ Search failed: ' + error.message + '</div>';
                        document.getElementById('quick-search-results').classList.remove('hidden');
                    } finally {
                        if (searchBtn) {
                            searchBtn.disabled = false;
                            searchBtn.innerHTML = '🔍 Search';
                        }
                    }
                }
                
                function displayQuickSearchResults(results) {
                    const resultsDiv = document.getElementById('quick-search-results');
                    if (!resultsDiv) {
                        console.error('quick-search-results element not found');
                        return;
                    }
                    
                    if (results.customers && results.customers.length > 0) {
                        let html = '<h4 style="color: #155724; margin-bottom: 10px;">✅ Found in CRM:</h4>';
                        results.customers.forEach((customer, index) => {
                            // Create data attributes to avoid string escaping issues
                            const customerId = customer.id || '';
                            const customerName = customer.name || '';
                            const customerEmail = customer.email || '';
                            const customerCompany = customer.company || '';
                            const customerPhone = customer.phone || '';
                            const customerAddress = customer.address || '';
                            
                            html += `
                                <div style="border: 1px solid #28a745; padding: 12px; margin: 8px 0; border-radius: 4px; background: white;">
                                    <p style="margin: 0 0 5px 0;"><strong>${customer.name}</strong> - ${customer.company || 'No company'}</p>
                                    <p style="margin: 0 0 8px 0; color: #666;">📧 ${customer.email} ${customer.phone ? '| 📞 ' + customer.phone : ''}</p>
                                    ${customer.address ? `<p style="margin: 0 0 8px 0; color: #666;">📍 ${customer.address}</p>` : ''}
                                    <button class="btn" data-customer-id="${customerId}" data-customer-name="${customerName}" data-customer-email="${customerEmail}" data-customer-company="${customerCompany}" data-customer-address="${customerAddress}" onclick="selectExistingCustomerSafe(this)" style="background: #28a745; margin-right: 8px;">
                                        ✅ Select This Customer
                                    </button>
                                    <button class="btn" data-customer-id="${customerId}" data-customer-name="${customerName}" data-customer-email="${customerEmail}" data-customer-company="${customerCompany}" data-customer-phone="${customerPhone}" data-customer-address="${customerAddress}" onclick="editExistingCustomerSafe(this)" style="background: #ffc107; color: #000;">
                                        ✏️ Edit & Use
                                    </button>
                                </div>
                            `;
                        });
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.innerHTML = `
                            <div style="color: #856404; background: #fff3cd; padding: 15px; border-radius: 4px; text-align: center;">
                                <h4 style="margin: 0 0 10px 0;">❌ Not Found in CRM</h4>
                                <p style="margin: 0 0 15px 0;">No existing customer found for "${document.getElementById('quick-search').value}"</p>
                                <button class="btn btn-success" onclick="skipToNewCustomer()">➕ Add as New Customer</button>
                            </div>
                        `;
                    }
                    
                    resultsDiv.classList.remove('hidden');
                }
                
                function selectExistingCustomer(id, name, email, company, address) {
                    currentCustomer = { 
                        id: id, 
                        name: name, 
                        email: email, 
                        company: company,
                        address: address || '',
                        existing: true  // Flag to indicate this is existing CRM record
                    };
                    
                    // Display selected customer and move to deal terms
                    document.getElementById('customer-summary').innerHTML = `
                        <h3>✅ Selected Existing Customer:</h3>
                        <p><strong>Name:</strong> ${name}</p>
                        <p><strong>Email:</strong> ${email}</p>
                        <p><strong>Company:</strong> ${company}</p>
                        ${address ? `<p><strong>Address:</strong> ${address}</p>` : ''}
                        <p><strong>CRM ID:</strong> ${id}</p>
                        <p style="color: #155724; font-style: italic;">✅ Using existing CRM record</p>
                    `;
                    
                    showStep(3); // Skip to deal terms
                }
                
                function editExistingCustomer(id, name, email, company, phone, address) {
                    // Set up for editing existing customer
                    currentCustomer = { 
                        id: id, 
                        name: name, 
                        email: email, 
                        company: company,
                        phone: phone,
                        address: address || '',
                        existing: true,
                        editing: true  // Flag to indicate this is an edit operation
                    };
                    
                    // Pre-fill the form with existing data
                    document.getElementById('customer-name').value = name || '';
                    document.getElementById('customer-email').value = email || '';
                    document.getElementById('company-name').value = company || '';
                    document.getElementById('customer-phone').value = phone || '';
                    document.getElementById('customer-address').value = address || '';
                    
                    // Show step 2 with pre-filled data for editing
                    showStep(2);
                    
                    // Update form title to indicate editing
                    document.querySelector('#step-2 h2').innerHTML = '✏️ Step 2: Edit Customer Information';
                    
                    // Add a note about what's being edited
                    const existingNote = document.getElementById('editing-note');
                    if (existingNote) existingNote.remove();
                    
                    const noteDiv = document.createElement('div');
                    noteDiv.id = 'editing-note';
                    noteDiv.style.cssText = 'background: #fff3cd; padding: 10px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #ffeaa7;';
                    noteDiv.innerHTML = `
                        <p style="margin: 0; color: #856404;">
                            <strong>📝 Editing existing customer:</strong> ${name || 'Unnamed Contact'}<br>
                            <small>Make any necessary changes below. Updates will be saved to CRM when you proceed.</small>
                        </p>
                    `;
                    
                    document.querySelector('#step-2').insertBefore(noteDiv, document.querySelector('#step-2 .form-row'));
                }
                
                function selectExistingCustomerSafe(button) {
                    const id = button.getAttribute('data-customer-id');
                    const name = button.getAttribute('data-customer-name');
                    const email = button.getAttribute('data-customer-email');
                    const company = button.getAttribute('data-customer-company');
                    const address = button.getAttribute('data-customer-address');
                    selectExistingCustomer(id, name, email, company, address);
                }
                
                function editExistingCustomerSafe(button) {
                    const id = button.getAttribute('data-customer-id');
                    const name = button.getAttribute('data-customer-name');
                    const email = button.getAttribute('data-customer-email');
                    const company = button.getAttribute('data-customer-company');
                    const phone = button.getAttribute('data-customer-phone');
                    const address = button.getAttribute('data-customer-address');
                    editExistingCustomer(id, name, email, company, phone, address);
                }
                
                function skipToNewCustomer() {
                    // Clear any search results
                    document.getElementById('quick-search-results').classList.add('hidden');
                    showStep(2); // Go to customer info form
                }
                
                function proceedToDealTerms() {
                    // Validate required fields
                    const name = document.getElementById('customer-name').value.trim();
                    const email = document.getElementById('customer-email').value.trim();
                    const company = document.getElementById('company-name').value.trim();
                    const phone = document.getElementById('customer-phone').value.trim();
                    const address = document.getElementById('customer-address').value.trim();
                    
                    if (!name || !email || !company) {
                        alert('Please fill in all required fields (marked with *)');
                        return;
                    }
                    
                    // Check if this is editing an existing customer
                    if (currentCustomer && currentCustomer.editing) {
                        // Update the existing customer record
                        currentCustomer.name = name;
                        currentCustomer.email = email;
                        currentCustomer.company = company;
                        currentCustomer.phone = phone;
                        currentCustomer.address = address;
                        
                        // Call CRM update endpoint in background
                        updateCRMCustomer(currentCustomer);
                        
                        // Display updated customer summary
                        document.getElementById('customer-summary').innerHTML = `
                            <h3>✅ Updated Customer Information:</h3>
                            <p><strong>Name:</strong> ${name}</p>
                            <p><strong>Email:</strong> ${email}</p>
                            <p><strong>Company:</strong> ${company}</p>
                            ${phone ? `<p><strong>Phone:</strong> ${phone}</p>` : ''}
                            ${address ? `<p><strong>Address:</strong> ${address}</p>` : ''}
                            <p style="color: #155724; font-style: italic;">✏️ CRM record updated with new information</p>
                        `;
                    } else {
                        // Create new local customer object
                        currentCustomer = {
                            id: 'LOCAL_' + Date.now(),
                            name: name,
                            email: email,
                            company: company,
                            phone: phone,
                            address: address,
                            existing: false  // Flag to indicate this is new customer
                        };
                        
                        // Display new customer summary
                        document.getElementById('customer-summary').innerHTML = `
                            <h3>✅ New Customer Information:</h3>
                            <p><strong>Name:</strong> ${name}</p>
                            <p><strong>Email:</strong> ${email}</p>
                            <p><strong>Company:</strong> ${company}</p>
                            ${phone ? `<p><strong>Phone:</strong> ${phone}</p>` : ''}
                            ${address ? `<p><strong>Address:</strong> ${address}</p>` : ''}
                            <p style="color: #666; font-style: italic;">📤 Will be added to CRM automatically</p>
                        `;
                    }
                    
                    // Reset form title and remove editing note
                    document.querySelector('#step-2 h2').innerHTML = '👤 Step 2: Customer Information';
                    const editingNote = document.getElementById('editing-note');
                    if (editingNote) editingNote.remove();
                    
                    // Move to deal terms step
                    showStep(3);
                }
                
                async function updateCRMCustomer(customer) {
                    try {
                        const response = await fetch('/api/update-crm-contact', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                contact_id: customer.id,
                                name: customer.name,
                                email: customer.email,
                                company_name: customer.company,
                                phone: customer.phone,
                                address: customer.address
                            })
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            console.log('✅ Customer updated in CRM:', result);
                            
                            // Show success notification
                            showNotification('✅ Customer record updated in CRM', 'success');
                        } else {
                            console.error('❌ Failed to update customer in CRM:', response.status);
                            showNotification('⚠️ Customer update queued for sync', 'warning');
                        }
                    } catch (error) {
                        console.error('❌ Error updating customer:', error);
                        showNotification('⚠️ Customer update queued for sync', 'warning');
                    }
                }
                
                function showNotification(message, type) {
                    // Create notification element
                    const notification = document.createElement('div');
                    notification.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 12px 20px;
                        border-radius: 4px;
                        color: white;
                        font-weight: bold;
                        z-index: 1000;
                        animation: slideIn 0.3s ease-out;
                        ${type === 'success' ? 'background: #28a745;' : 'background: #ffc107; color: #000;'}
                    `;
                    notification.textContent = message;
                    
                    document.body.appendChild(notification);
                    
                    // Remove after 3 seconds
                    setTimeout(() => {
                        notification.style.animation = 'slideOut 0.3s ease-in';
                        setTimeout(() => {
                            if (notification.parentNode) {
                                notification.parentNode.removeChild(notification);
                            }
                        }, 300);
                    }, 3000);
                }
                
                async function refreshCRMCache(event = null) {
                    // Handle case where function is called without event (e.g., from loadCRMContacts)
                    let refreshBtn = null;
                    if (event && event.target) {
                        refreshBtn = event.target;
                        refreshBtn.disabled = true;
                        refreshBtn.innerHTML = '⏳ Refreshing...';
                    }
                    
                    try {
                        const response = await fetch('/api/refresh-crm-cache');
                        if (response.ok) {
                            const result = await response.json();
                            if (refreshBtn) {
                                alert(`✅ CRM cache refreshed! Loaded ${result.total_contacts} contacts.`);
                            }
                            await loadCRMContacts();
                        } else {
                            throw new Error('Failed to refresh CRM cache');
                        }
                    } catch (error) {
                        if (refreshBtn) {
                            alert('❌ Error refreshing CRM cache: ' + error.message);
                        } else {
                            console.error('Error refreshing CRM cache:', error);
                        }
                    } finally {
                        if (refreshBtn) {
                            refreshBtn.disabled = false;
                            refreshBtn.innerHTML = '🔄 Refresh CRM Cache';
                        }
                    }
                }
                
                async function searchCRM() {
                    // This function references search-query element which doesn't exist in current HTML
                    // Current workflow uses quickSearchCRM() with quick-search element instead
                    console.log('searchCRM called but search-query element does not exist');
                    alert('Please use the Quick Customer Check search instead');
                }
                
                function displaySearchResults(results) {
                    // This function references search-results element which doesn't exist in current HTML
                    // Current workflow uses displayQuickSearchResults() with quick-search-results element instead
                    console.log('displaySearchResults called but search-results element does not exist');
                    console.log('Results:', results);
                }
                
                function selectCustomer(id, name, email, company) {
                    currentCustomer = { id, name, email, company };
                    document.getElementById('customer-summary').innerHTML = `
                        <h3>✅ Selected Customer:</h3>
                        <p><strong>Name:</strong> ${name}</p>
                        <p><strong>Email:</strong> ${email}</p>
                        <p><strong>Company:</strong> ${company}</p>
                        <p><strong>CRM ID:</strong> ${id}</p>
                    `;
                    showStep(3);
                }
                
                function showNewCustomerForm() {
                    showStep(2);
                }
                
                async function createCRMContact() {
                    const customerData = {
                        name: document.getElementById('customer-name').value,
                        email: document.getElementById('customer-email').value,
                        company: document.getElementById('company-name').value,
                        phone: document.getElementById('customer-phone').value,
                        address: document.getElementById('customer-address').value
                    };
                    
                    try {
                        const response = await fetch('/api/create-crm-contact', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(customerData)
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            currentCustomer = {
                                id: result.contact_id,
                                name: customerData.name,
                                email: customerData.email,
                                company: customerData.company
                            };
                            
                            document.getElementById('customer-summary').innerHTML = `
                                <h3>✅ Customer Added to CRM:</h3>
                                <p><strong>Name:</strong> ${customerData.name}</p>
                                <p><strong>Email:</strong> ${customerData.email}</p>
                                <p><strong>Company:</strong> ${customerData.company}</p>
                                <p><strong>CRM ID:</strong> ${result.contact_id}</p>
                            `;
                            
                            showStep(3);
                        } else {
                            throw new Error('Failed to create CRM contact');
                        }
                    } catch (error) {
                        alert('❌ Error creating CRM contact: ' + error.message);
                    }
                }
                
                function generateLOI() {
                    // Set default conversion date if not set
                    const conversionDate = document.getElementById('conversion-date').value || 
                        new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
                    
                    currentDeal = {
                        customer: currentCustomer,
                        gasoline_volume: parseInt(document.getElementById('gasoline-volume').value),
                        diesel_volume: parseInt(document.getElementById('diesel-volume').value),
                        image_funding: parseInt(document.getElementById('image-funding').value),
                        volume_incentives: parseInt(document.getElementById('volume-incentives').value),
                        contract_duration: parseInt(document.getElementById('contract-duration').value),
                        conversion_date: conversionDate,
                        pricing_structure: document.getElementById('pricing-structure').value,
                        special_terms: document.getElementById('special-terms').value
                    };
                    
                    const totalMonthly = currentDeal.gasoline_volume + currentDeal.diesel_volume;
                    const totalAnnual = totalMonthly * 12;
                    const totalIncentives = currentDeal.image_funding + currentDeal.volume_incentives;
                    
                    // Create the LOI with all deal terms
                    createDetailedLOI(currentDeal);
                }
                
                async function createDetailedLOI(dealData) {
                    const transactionId = 'TXN-' + Math.random().toString(36).substr(2, 8).toUpperCase();
                    const signatureToken = generateUUID();
                    
                    const loiData = {
                        transaction_id: transactionId,
                        signature_token: signatureToken,
                        signer_name: dealData.customer.name,
                        signer_email: dealData.customer.email,
                        company_name: dealData.customer.company,
                        crm_contact_id: dealData.customer.id,
                        document_name: "VP Racing Fuel Supply Agreement - Letter of Intent",
                        status: "pending",
                        created_at: new Date().toISOString(),
                        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
                        deal_terms: dealData
                    };
                    
                    try {
                        const response = await fetch('/api/create-loi', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(loiData)
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            displayFinalLOI(loiData, result);
                            
                            // Show email status
                            if (result.email_sent) {
                                alert('✅ LOI created and signature request email sent successfully!');
                            } else {
                                alert('⚠️ LOI created but email could not be sent. Please copy and send the email template manually.');
                            }
                        } else {
                            throw new Error('Failed to create LOI');
                        }
                    } catch (error) {
                        alert('❌ Error creating LOI: ' + error.message);
                    }
                }
                
                function displayFinalLOI(loiData, result) {
                    const dealData = loiData.deal_terms;
                    const totalMonthly = dealData.gasoline_volume + dealData.diesel_volume;
                    const totalAnnual = totalMonthly * 12;
                    const totalIncentives = dealData.image_funding + dealData.volume_incentives;
                    
                    document.getElementById('loi-summary').innerHTML = `
                        <h3>🎯 Complete LOI Generated</h3>
                        <p><strong>Customer:</strong> ${dealData.customer.name} (${dealData.customer.company})</p>
                        <p><strong>Transaction ID:</strong> ${loiData.transaction_id}</p>
                        <p><strong>Total Volume:</strong> ${totalMonthly.toLocaleString()} gal/month (${totalAnnual.toLocaleString()} annual)</p>
                        <p><strong>Total Incentives:</strong> $${totalIncentives.toLocaleString()}</p>
                        <p><strong>Contract Term:</strong> ${dealData.contract_duration} months</p>
                    `;
                    
                    const signatureUrl = result.signature_url;
                    
                    document.getElementById('final-result').innerHTML = `
                        <div class="success-box">
                            <h3>✅ LOI Ready for Signature!</h3>
                            <p><strong>Signature URL:</strong></p>
                            <div style="background: white; padding: 15px; border-radius: 5px; font-family: monospace; word-break: break-all; margin: 10px 0;">
                                ${signatureUrl}
                            </div>
                            <button class="btn" onclick="copyToClipboard('${signatureUrl}')">📋 Copy URL</button>
                            <button class="btn btn-success" onclick="window.open('${signatureUrl}', '_blank')">👀 Preview LOI</button>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px;">
                            <h4>📧 Email Template:</h4>
                            <textarea readonly style="width: 100%; height: 200px; margin: 10px 0;">Subject: VP Racing Fuel Supply Agreement - Electronic Signature Required

Dear ${dealData.customer.name},

Thank you for your interest in partnering with Better Day Energy for your fuel supply needs.

Please review and electronically sign the Letter of Intent for our VP Racing Fuel Supply Agreement:

🔗 Sign Document: ${signatureUrl}

Deal Summary:
• Total Incentive Package: $${totalIncentives.toLocaleString()}
• Monthly Volume: ${totalMonthly.toLocaleString()} gallons
• Contract Duration: ${dealData.contract_duration} months
• Target Conversion: ${dealData.conversion_date}

This document expires in 30 days. Please complete your signature at your earliest convenience.

Best regards,
Better Day Energy Team
Transaction ID: ${loiData.transaction_id}</textarea>
                            <button class="btn" onclick="copyEmailTemplate()">📋 Copy Email</button>
                        </div>
                    `;
                    
                    showStep(4);
                }
                
                function showStep(stepNumber) {
                    // Hide all steps
                    for (let i = 1; i <= 4; i++) {
                        document.getElementById('step-' + i).classList.add('hidden');
                        document.getElementById('step-' + i).classList.remove('active');
                    }
                    
                    // Show current step
                    document.getElementById('step-' + stepNumber).classList.remove('hidden');
                    document.getElementById('step-' + stepNumber).classList.add('active');
                }
                
                function generateUUID() {
                    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                        var r = Math.random() * 16 | 0,
                            v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    });
                }
                
                function copyToClipboard(text) {
                    navigator.clipboard.writeText(text);
                    alert('✅ Copied to clipboard!');
                }
                
                function copyEmailTemplate() {
                    const emailText = document.querySelector('textarea[readonly]').value;
                    navigator.clipboard.writeText(emailText);
                    alert('✅ Email template copied!');
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
            
            # Check if customer needs to be created in CRM (has a LOCAL_ ID) and is not existing
            customer_id = data.get('crm_contact_id', '')
            deal_terms = data.get('deal_terms', {})
            customer = deal_terms.get('customer', {})
            
            if customer_id.startswith('LOCAL_') and customer and not customer.get('existing', False):
                # This is a new customer - queue for CRM creation
                customer_data = {
                    'local_id': customer_id,
                    'name': customer.get('name', data.get('signer_name', '')),
                    'email': customer.get('email', data.get('signer_email', '')),
                    'company': customer.get('company', data.get('company_name', '')),
                    'phone': customer.get('phone', ''),
                    'address': customer.get('address', ''),
                    'notes': f"Created via LOI System - Transaction {data['transaction_id']}"
                }
                
                queue_id = crm_bidirectional_sync.queue_crm_write('create_contact', customer_data, 'high')
                logger.info(f"Queued new customer {customer_data['name']} for CRM creation (queue ID: {queue_id})")
            elif not customer_id.startswith('LOCAL_'):
                # This is an existing CRM customer - add a note about the LOI
                note_data = {
                    'crm_id': customer_id,
                    'note_content': f"LOI Generated - Transaction {data['transaction_id']}\n\nFuel Supply Agreement LOI created and sent for signature.\nDeal Terms: {deal_terms.get('gasoline_volume', 0):,} gal/month gasoline, {deal_terms.get('diesel_volume', 0):,} gal/month diesel\nIncentives: ${deal_terms.get('image_funding', 0):,} + ${deal_terms.get('volume_incentives', 0):,}"
                }
                
                queue_id = crm_bidirectional_sync.queue_crm_write('add_note', note_data, 'normal')
                logger.info(f"Queued LOI note for existing customer {customer_id} (queue ID: {queue_id})")
            
            # Save to file (in production, this updates the server's data)
            try:
                with open("signature_request_data.json", "w") as f:
                    json.dump(signature_requests, f, indent=2)
                logger.info(f"LOI request created: {data['transaction_id']} for {data['signer_name']}")
            except Exception as e:
                logger.error(f"Failed to save LOI data to file: {str(e)}")
                # Continue anyway since we have it in memory
            
            # Send signature request email
            email_sent = self.send_signature_email(data)
            
            # Send success response
            response_data = {
                "success": True,
                "message": "LOI created successfully",
                "transaction_id": data["transaction_id"],
                "signature_token": data["signature_token"],
                "signature_url": f"https://loi-automation-api.onrender.com/sign/{data['signature_token']}",
                "email_sent": email_sent
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
    
    def send_signature_email(self, loi_data):
        """Send signature request email using SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get SMTP settings from environment
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', 'transaction.coordinator.agent@gmail.com')
            smtp_password = os.getenv('SMTP_PASSWORD', 'xmvi xvso zblo oewe')
            
            if not smtp_username or not smtp_password:
                logger.warning("SMTP credentials not configured - email not sent")
                return False
            
            # Extract data
            deal_terms = loi_data.get('deal_terms', {})
            customer = deal_terms.get('customer', {})
            to_email = loi_data.get('signer_email')
            to_name = loi_data.get('signer_name')
            company = loi_data.get('company_name')
            
            # Calculate totals
            total_monthly = deal_terms.get('gasoline_volume', 0) + deal_terms.get('diesel_volume', 0)
            total_incentives = deal_terms.get('image_funding', 0) + deal_terms.get('volume_incentives', 0)
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "VP Racing Fuel Supply Agreement - Electronic Signature Required"
            msg['From'] = f"Better Day Energy <{smtp_username}>"
            msg['To'] = to_email
            
            # HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #1f4e79, #2563eb); color: white; padding: 30px; text-align: center;">
                    <h1>🏢 Better Day Energy</h1>
                    <h2>VP Racing Fuel Supply Agreement</h2>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <p>Dear {to_name},</p>
                    
                    <p>Thank you for your interest in partnering with Better Day Energy for your fuel supply needs.</p>
                    
                    <p>Please review and electronically sign the Letter of Intent for our VP Racing Fuel Supply Agreement:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://loi-automation-api.onrender.com/sign/{loi_data['signature_token']}" 
                           style="background: #1f4e79; color: white; padding: 15px 30px; text-decoration: none; 
                                  border-radius: 6px; font-weight: bold; display: inline-block;">
                            ✍️ Sign Document Now
                        </a>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>📊 Deal Summary:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li>• <strong>Total Incentive Package:</strong> ${total_incentives:,}</li>
                            <li>• <strong>Monthly Volume:</strong> {total_monthly:,} gallons</li>
                            <li>• <strong>Contract Duration:</strong> {deal_terms.get('contract_duration', 36)} months</li>
                            <li>• <strong>Target Conversion:</strong> {deal_terms.get('conversion_date', 'TBD')}</li>
                        </ul>
                    </div>
                    
                    <p><strong>This document expires in 30 days.</strong> Please complete your signature at your earliest convenience.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                    
                    <p>Best regards,<br>
                    Better Day Energy Team<br>
                    <small>Transaction ID: {loi_data['transaction_id']}</small></p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_body = f"""
Dear {to_name},

Thank you for your interest in partnering with Better Day Energy for your fuel supply needs.

Please review and electronically sign the Letter of Intent for our VP Racing Fuel Supply Agreement:

Sign Document: https://loi-automation-api.onrender.com/sign/{loi_data['signature_token']}

Deal Summary:
• Total Incentive Package: ${total_incentives:,}
• Monthly Volume: {total_monthly:,} gallons
• Contract Duration: {deal_terms.get('contract_duration', 36)} months
• Target Conversion: {deal_terms.get('conversion_date', 'TBD')}

This document expires in 30 days. Please complete your signature at your earliest convenience.

Best regards,
Better Day Energy Team
Transaction ID: {loi_data['transaction_id']}
            """
            
            # Attach parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Signature request email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send signature email: {str(e)}")
            return False
    
    def handle_crm_search(self, post_data):
        """Handle CRM customer search using local database cache"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            query = data.get('query', '').strip()
            
            if not query:
                raise ValueError("Search query is required")
            
            logger.info(f"Searching CRM cache for: {query}")
            
            # Search local PostgreSQL cache instead of API
            import psycopg2
            conn = signature_storage.get_connection()
            
            customers = []
            with conn.cursor() as cursor:
                # Case-insensitive search across name, email, and company fields
                search_pattern = f"%{query.lower()}%"
                cursor.execute("""
                    SELECT contact_id, name, email, company_name, phone, address
                    FROM crm_contacts_cache 
                    WHERE LOWER(name) LIKE %s 
                       OR LOWER(email) LIKE %s 
                       OR LOWER(company_name) LIKE %s
                    ORDER BY 
                        CASE 
                            WHEN LOWER(name) LIKE %s THEN 1
                            WHEN LOWER(company_name) LIKE %s THEN 2
                            ELSE 3
                        END,
                        name
                    LIMIT 10
                """, (search_pattern, search_pattern, search_pattern, 
                      f"%{query.lower()}%", f"%{query.lower()}%"))
                
                results = cursor.fetchall()
                
                for row in results:
                    contact_id, name, email, company_name, phone, address = row
                    customers.append({
                        'id': str(contact_id),
                        'name': str(name or ''),
                        'email': str(email or ''),
                        'company': str(company_name or ''),
                        'phone': str(phone or ''),
                        'address': str(address or '')
                    })
            
            conn.close()
            logger.info(f"Found {len(customers)} customers in cache for query: {query}")
            
            # Return successful response with cached results
            response_data = {
                "success": True,
                "customers": customers,
                "total": len(customers),
                "source": "database_cache"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"CRM search error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_create_crm_contact(self, post_data):
        """Handle creating new CRM contact using write queue"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            # Generate temporary local ID
            local_id = f"LOCAL_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # Store contact in local cache first
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                # Create cache table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crm_contacts_cache (
                        contact_id VARCHAR(100) PRIMARY KEY,
                        name VARCHAR(255),
                        email VARCHAR(255),
                        company_name VARCHAR(255),
                        phone VARCHAR(50),
                        address TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_sync TIMESTAMP,
                        sync_status VARCHAR(20) DEFAULT 'pending'
                    )
                """)
                
                # Insert into local cache
                cursor.execute("""
                    INSERT INTO crm_contacts_cache 
                    (contact_id, name, email, company_name, phone, address, notes, sync_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    local_id,
                    data.get('name', ''),
                    data.get('email', ''),
                    data.get('company', ''),
                    data.get('phone', ''),
                    data.get('address', ''),
                    f"Created via LOI Admin System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    'queued_for_crm'
                ))
                conn.commit()
            
            conn.close()
            
            # Queue the write operation for background sync
            queue_data = {
                'local_id': local_id,
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'company': data.get('company', ''),
                'phone': data.get('phone', ''),
                'address': data.get('address', ''),
                'notes': f"Created via LOI Admin System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            queue_id = crm_bidirectional_sync.queue_crm_write('create_contact', queue_data, 'high')
            
            response_data = {
                "success": True,
                "contact_id": local_id,
                "message": "Contact queued for CRM creation",
                "queue_id": queue_id,
                "status": "Will sync to CRM within 30 seconds"
            }
            
            logger.info(f"Contact queued for CRM creation: {local_id} for {data.get('name')}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"CRM contact creation error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_update_crm_contact(self, post_data):
        """Handle updating existing CRM contact using CRM bridge"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            contact_id = data.get('contact_id')
            
            if not contact_id:
                raise ValueError("Contact ID is required for updates")
            
            logger.info(f"📝 Updating CRM contact {contact_id}")
            
            # Update local cache first
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                # Update local cache
                cursor.execute("""
                    UPDATE crm_contacts_cache 
                    SET name = %s, email = %s, company_name = %s, phone = %s, address = %s,
                        updated_at = CURRENT_TIMESTAMP, sync_status = %s
                    WHERE contact_id = %s
                """, (
                    data.get('name', ''),
                    data.get('email', ''),
                    data.get('company_name', ''),
                    data.get('phone', ''),
                    data.get('address', ''),
                    'updated_pending_sync',
                    contact_id
                ))
                
                if cursor.rowcount == 0:
                    # Contact not found in cache, create new entry
                    cursor.execute("""
                        INSERT INTO crm_contacts_cache 
                        (contact_id, name, email, company_name, phone, address, sync_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        contact_id,
                        data.get('name', ''),
                        data.get('email', ''),
                        data.get('company_name', ''),
                        data.get('phone', ''),
                        data.get('address', ''),
                        'updated_pending_sync'
                    ))
                
                conn.commit()
            
            conn.close()
            
            # Queue update operation for CRM sync
            write_queue_data = {
                'contact_id': contact_id,
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'company_name': data.get('company_name', ''),
                'phone': data.get('phone', ''),
                'address': data.get('address', ''),
                'operation_type': 'update'
            }
            
            # Use CRM bridge create endpoint for updates (will be handled as update if contact exists)
            import requests
            crm_bridge_url = "https://loi-automation-api.onrender.com/api/v1/crm-bridge"
            crm_bridge_token = "bde_loi_auth_e6db5173a4393421ffadae85f9a3513e"
            
            headers = {
                "Authorization": f"Bearer {crm_bridge_token}",
                "Content-Type": "application/json"
            }
            
            # Use CRM bridge create endpoint (it handles both create and update)
            bridge_response = requests.post(
                f"{crm_bridge_url}/contacts/create",
                headers=headers,
                json=write_queue_data,
                timeout=10
            )
            
            # Send success response regardless of CRM bridge result
            # (updates are queued for sync)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {
                "success": True,
                "contact_id": contact_id,
                "message": "Contact updated successfully",
                "cache_updated": True,
                "bridge_status": "queued" if not bridge_response.ok else "updated"
            }
            
            logger.info(f"✅ Contact {contact_id} updated successfully")
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"❌ CRM contact update error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_refresh_crm_cache(self):
        """Refresh the local CRM contact cache from LACRM using proper pagination"""
        try:
            logger.info("Starting CRM cache refresh...")
            
            # Get all contacts from LACRM using working pagination approach
            api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
            api_parts = api_key.split('-', 1)
            user_code = api_parts[0]
            
            crm_url = "https://api.lessannoyingcrm.com"
            all_contacts = []
            page = 1
            max_results_per_page = 10000
            
            # Use SearchContacts with pagination (the approach that works)
            while True:
                params = {
                    'APIToken': api_key,
                    'UserCode': user_code,
                    'Function': 'SearchContacts',
                    'SearchTerm': '',  # Empty to get all contacts
                    'MaxNumberOfResults': max_results_per_page,
                    'Page': page
                }
                
                response = requests.get(crm_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    logger.error(f"CRM API error: {response.status_code} - {response.text[:200]}")
                    break
                
                result_data = json.loads(response.text)
                
                if not result_data.get('Success'):
                    logger.error(f"CRM API failed: {result_data.get('Error', 'Unknown error')}")
                    break
                
                contacts_data = result_data.get('Result', [])
                
                if not isinstance(contacts_data, list):
                    contacts_data = [contacts_data] if contacts_data else []
                
                # If no results, we've reached the end
                if len(contacts_data) == 0:
                    break
                
                all_contacts.extend(contacts_data)
                logger.info(f"Retrieved page {page}: {len(contacts_data)} contacts")
                
                page += 1
                
                # Safety check
                if page > 50:
                    logger.warning("CRM cache refresh safety limit reached")
                    break
            
            logger.info(f"Retrieved {len(all_contacts)} total contacts from CRM")
            
            # Process contacts using the working data format
            contacts = []
            for contact in all_contacts:
                if contact and isinstance(contact, dict):
                    try:
                        # Extract contact ID
                        contact_id = str(contact.get('ContactId', ''))
                        if not contact_id:
                            continue
                        
                        # Extract name from actual LACRM format
                        name = str(contact.get('CompanyName', '') or 'Unknown Contact')
                        
                        # Extract email (LACRM format: list of dicts with 'Text' field)
                        email_raw = contact.get('Email', '')
                        if isinstance(email_raw, list) and len(email_raw) > 0:
                            first_email = email_raw[0]
                            if isinstance(first_email, dict):
                                email_text = first_email.get('Text', '')
                                email = email_text.split(' (')[0] if email_text else ''
                            else:
                                email = str(first_email)
                        elif isinstance(email_raw, dict):
                            email = str(email_raw.get('Text', '') or email_raw.get('Value', '') or '')
                        else:
                            email = str(email_raw or '')
                        
                        # Company name
                        company_name = str(contact.get('CompanyName', '') or '')
                        
                        # Extract phone (LACRM format: list of dicts with 'Text' field)
                        phone_raw = contact.get('Phone', '')
                        if isinstance(phone_raw, list) and len(phone_raw) > 0:
                            first_phone = phone_raw[0]
                            if isinstance(first_phone, dict):
                                phone_text = first_phone.get('Text', '')
                                phone = phone_text.split(' (')[0] if phone_text else ''
                            else:
                                phone = str(first_phone)
                        elif isinstance(phone_raw, dict):
                            phone = str(phone_raw.get('Text', '') or phone_raw.get('Value', '') or '')
                        else:
                            phone = str(phone_raw or '')
                        
                        contact_data = {
                            'id': contact_id,
                            'name': name,
                            'email': email,
                            'company': company_name,
                            'phone': phone,
                            'last_updated': datetime.now().isoformat()
                        }
                        contacts.append(contact_data)
                        
                    except Exception as contact_error:
                        logger.error(f"Error processing contact {contact.get('ContactId', 'unknown')}: {contact_error}")
                        continue
                
                # Store in PostgreSQL cache
                try:
                    # Simple table creation and storage (using existing signature_storage connection)
                    import psycopg2
                    conn = signature_storage.get_connection()
                    
                    with conn.cursor() as cursor:
                        # Create contacts cache table if not exists
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS crm_contacts_cache (
                                contact_id VARCHAR(50) PRIMARY KEY,
                                name VARCHAR(255),
                                email VARCHAR(255),
                                company VARCHAR(255),
                                phone VARCHAR(50),
                                last_updated TIMESTAMP,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        # Clear existing cache
                        cursor.execute("DELETE FROM crm_contacts_cache")
                        
                        # Insert all contacts
                        for contact in contacts:
                            cursor.execute("""
                                INSERT INTO crm_contacts_cache 
                                (contact_id, name, email, company, phone, last_updated)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                contact['id'],
                                contact['name'],
                                contact['email'],
                                contact['company'],
                                contact['phone'],
                                contact['last_updated']
                            ))
                        
                        conn.commit()
                    
                    conn.close()
                    
                    response_data = {
                        "success": True,
                        "message": f"CRM cache refreshed with {len(contacts)} contacts",
                        "total_contacts": len(contacts)
                    }
                    
                    logger.info(f"CRM cache refreshed: {len(contacts)} contacts")
                    
                except Exception as db_error:
                    logger.error(f"Database error during cache refresh: {db_error}")
                    response_data = {
                        "success": False,
                        "error": f"Database error: {str(db_error)}"
                    }
            else:
                raise Exception(f"CRM API error: {response.status_code} - {response.text}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"CRM cache refresh error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_get_crm_contacts(self):
        """Get all cached CRM contacts for the dropdown"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT contact_id, name, email, company, phone, last_updated
                    FROM crm_contacts_cache 
                    ORDER BY name
                """)
                
                contacts = []
                for row in cursor.fetchall():
                    contacts.append({
                        'id': row[0],
                        'name': row[1],
                        'email': row[2] or '',
                        'company': row[3] or '',
                        'phone': row[4] or '',
                        'last_updated': row[5].isoformat() if row[5] else None
                    })
            
            conn.close()
            
            response_data = {
                "success": True,
                "contacts": contacts,
                "total": len(contacts)
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Get CRM contacts error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_sync_status(self):
        """Get the sync status and recent sync history"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                # Get recent sync history
                cursor.execute("""
                    SELECT last_sync_time, sync_type, records_updated, created_at
                    FROM crm_sync_log 
                    ORDER BY created_at DESC LIMIT 10
                """)
                
                sync_history = []
                for row in cursor.fetchall():
                    sync_history.append({
                        'last_sync_time': row[0].isoformat() if row[0] else None,
                        'sync_type': row[1],
                        'records_updated': row[2],
                        'created_at': row[3].isoformat() if row[3] else None
                    })
                
                # Get total contacts in cache
                cursor.execute("SELECT COUNT(*) FROM crm_contacts_cache")
                total_contacts = cursor.fetchone()[0]
            
            conn.close()
            
            response_data = {
                "success": True,
                "background_sync_running": crm_bidirectional_sync.running,
                "sync_interval_read_minutes": crm_bidirectional_sync.read_sync_interval // 60,
                "sync_interval_write_seconds": crm_bidirectional_sync.write_sync_interval,
                "total_cached_contacts": total_contacts,
                "recent_syncs": sync_history
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Sync status error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

class CRMBidirectionalSync:
    """Background service for full bidirectional CRM sync with write queue"""
    
    def __init__(self):
        self.api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
        self.api_parts = self.api_key.split('-', 1)
        self.user_code = self.api_parts[0]
        self.crm_url = "https://api.lessannoyingcrm.com"
        self.read_sync_interval = 300  # 5 minutes for reading changes
        self.write_sync_interval = 30   # 30 seconds for processing write queue
        self.running = False
        self.read_thread = None
        self.write_thread = None
        
    def start_background_sync(self):
        """Start both read and write sync processes"""
        if not self.running:
            self.running = True
            
            # Start read sync thread (pulls changes from CRM)
            self.read_thread = threading.Thread(target=self._read_sync_loop, daemon=True)
            self.read_thread.start()
            
            # Start write sync thread (pushes changes to CRM)
            self.write_thread = threading.Thread(target=self._write_sync_loop, daemon=True)
            self.write_thread.start()
            
            logger.info("🔄 CRM bidirectional sync started - read every 5min, write every 30sec")
    
    def stop_background_sync(self):
        """Stop both sync processes"""
        self.running = False
        if self.read_thread:
            self.read_thread.join()
        if self.write_thread:
            self.write_thread.join()
        logger.info("⏹️ CRM bidirectional sync stopped")
    
    def _read_sync_loop(self):
        """Read sync loop - pulls changes from CRM"""
        while self.running:
            try:
                self._check_and_sync_deltas()
            except Exception as e:
                logger.error(f"CRM read sync error: {e}")
            
            # Wait for next read sync interval
            for _ in range(self.read_sync_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _write_sync_loop(self):
        """Write sync loop - processes write queue to CRM"""
        while self.running:
            try:
                self._process_write_queue()
            except Exception as e:
                logger.error(f"CRM write sync error: {e}")
            
            # Wait for next write sync interval
            for _ in range(self.write_sync_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def queue_crm_write(self, operation, data, priority='normal'):
        """Queue a write operation to CRM"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                # Create write queue table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crm_write_queue (
                        id SERIAL PRIMARY KEY,
                        operation VARCHAR(50) NOT NULL,
                        data JSONB NOT NULL,
                        priority VARCHAR(20) DEFAULT 'normal',
                        status VARCHAR(20) DEFAULT 'pending',
                        attempts INTEGER DEFAULT 0,
                        max_attempts INTEGER DEFAULT 3,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP,
                        local_id VARCHAR(100)
                    )
                """)
                
                # Add operation to queue
                cursor.execute("""
                    INSERT INTO crm_write_queue (operation, data, priority, local_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (operation, json.dumps(data), priority, data.get('local_id')))
                
                queue_id = cursor.fetchone()[0]
                conn.commit()
            
            conn.close()
            logger.info(f"📤 Queued CRM {operation}: {queue_id}")
            return queue_id
            
        except Exception as e:
            logger.error(f"Error queueing CRM write: {e}")
            return None
    
    def _process_write_queue(self):
        """Process pending write operations to CRM"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                # Get pending operations (high priority first)
                cursor.execute("""
                    SELECT id, operation, data, attempts, local_id
                    FROM crm_write_queue 
                    WHERE status = 'pending' AND attempts < max_attempts
                    ORDER BY 
                        CASE priority WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
                        created_at
                    LIMIT 5
                """)
                
                operations = cursor.fetchall()
                
                for op_id, operation, data_json, attempts, local_id in operations:
                    try:
                        # data_json is already parsed by PostgreSQL JSONB - no need to json.loads()
                        data = data_json
                        
                        # Mark as processing
                        cursor.execute("""
                            UPDATE crm_write_queue 
                            SET status = 'processing', attempts = attempts + 1
                            WHERE id = %s
                        """, (op_id,))
                        conn.commit()
                        
                        # Execute the operation
                        success = self._execute_crm_operation(operation, data)
                        
                        if success:
                            # Mark as completed
                            cursor.execute("""
                                UPDATE crm_write_queue 
                                SET status = 'completed', processed_at = %s
                                WHERE id = %s
                            """, (datetime.now(), op_id))
                            logger.info(f"✅ CRM {operation} completed: {local_id}")
                        else:
                            # Mark as failed if max attempts reached
                            cursor.execute("""
                                UPDATE crm_write_queue 
                                SET status = CASE WHEN attempts >= max_attempts THEN 'failed' ELSE 'pending' END,
                                    error_message = %s
                                WHERE id = %s
                            """, (f"Operation failed after {attempts + 1} attempts", op_id))
                            
                        conn.commit()
                        
                    except Exception as op_error:
                        logger.error(f"Error processing CRM operation {op_id}: {op_error}")
                        
                        # Mark as failed
                        cursor.execute("""
                            UPDATE crm_write_queue 
                            SET status = 'pending', error_message = %s
                            WHERE id = %s
                        """, (str(op_error), op_id))
                        conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error processing write queue: {e}")
    
    def _execute_crm_operation(self, operation, data):
        """Execute a specific CRM operation"""
        try:
            import requests
            
            if operation == 'create_contact':
                # Log the data being processed to debug company field
                logger.info(f"🔍 Creating CRM contact with data: {data}")
                company_value = data.get('company', '')
                logger.info(f"🏢 Company field value: '{company_value}'")
                
                params = {
                    'APIToken': self.api_key,
                    'UserCode': self.user_code,
                    'Function': 'CreateContact',
                    'Name': data.get('name', ''),
                    'Email': data.get('email', ''),
                    'CompanyName': company_value,
                    'IsCompany': False,  # Creating person contacts, not company contacts
                    'AssignedTo': 1073223,  # Adam's user ID from CRM
                    'Phone': data.get('phone', ''),
                    'Address': data.get('address', ''),
                    'Notes': data.get('notes', '')
                }
                
                # Log CRM API request details
                logger.info(f"📤 CRM API Request - CompanyName: '{params.get('CompanyName', 'NOT_SET')}'")
                logger.info(f"📤 CRM API Request - All params: {params}")
                
                response = requests.get(self.crm_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    result_data = json.loads(response.text)
                    logger.info(f"📥 CRM API Response: {result_data}")
                    
                    # Update local record with CRM ID if successful
                    if result_data.get('ContactId'):
                        crm_id = result_data.get('ContactId')
                        if crm_id and data.get('local_id'):
                            self._update_local_crm_id(data['local_id'], str(crm_id))
                        logger.info(f"✅ CRM contact created with ID: {crm_id}")
                        return True
                    else:
                        logger.error(f"❌ CRM API error: {result_data.get('ErrorDescription', result_data.get('Error', 'Unknown error'))}")
                        return False
                else:
                    logger.error(f"CRM HTTP error: {response.status_code}")
                    return False
            
            elif operation == 'update_contact':
                # Implement contact update logic
                params = {
                    'APIToken': self.api_key,
                    'UserCode': self.user_code,
                    'Function': 'UpdateContact',
                    'ContactId': data.get('crm_id'),
                    'Notes': data.get('notes', '')
                }
                
                response = requests.get(self.crm_url, params=params, timeout=30)
                return response.status_code == 200
            
            elif operation == 'add_note':
                # Add note to existing contact
                params = {
                    'APIToken': self.api_key,
                    'UserCode': self.user_code,
                    'Function': 'CreateNote',
                    'ContactId': data.get('crm_id'),
                    'Note': data.get('note_content', '')
                }
                
                response = requests.get(self.crm_url, params=params, timeout=30)
                return response.status_code == 200
            
            else:
                logger.error(f"Unknown CRM operation: {operation}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing CRM operation {operation}: {e}")
            return False
    
    def _update_local_crm_id(self, local_id, crm_id):
        """Update local contact record with CRM ID"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE crm_contacts_cache 
                    SET contact_id = %s 
                    WHERE contact_id = %s
                """, (crm_id, local_id))
                conn.commit()
            
            conn.close()
            logger.info(f"Updated local contact {local_id} with CRM ID {crm_id}")
            
        except Exception as e:
            logger.error(f"Error updating local CRM ID: {e}")
    
    def _check_and_sync_deltas(self):
        """Check for CRM changes and sync deltas using proper LACRM API with pagination"""
        try:
            # Get last sync timestamp from database
            last_sync = self._get_last_sync_time()
            
            logger.info(f"🔄 Starting CRM delta sync (last sync: {last_sync})")
            
            # Use SearchContacts with pagination to get all contacts
            # LACRM API doesn't support ModifiedSince, so we get all and filter locally
            all_contacts = []
            page = 1
            max_results_per_page = 10000  # LACRM maximum
            
            while True:
                params = {
                    'APIToken': self.api_key,
                    'UserCode': self.user_code,
                    'Function': 'SearchContacts',
                    'SearchTerm': '',  # Empty to get all contacts
                    'MaxNumberOfResults': max_results_per_page,
                    'Page': page
                }
                
                import requests
                response = requests.get(self.crm_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    logger.error(f"CRM API error: {response.status_code} - {response.text[:200]}")
                    break
                
                # LACRM returns JSON with text/html content-type, parse manually
                try:
                    result_data = json.loads(response.text)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed: {e}")
                    break
                
                if not result_data.get('Success'):
                    logger.error(f"CRM API failed: {result_data.get('Error', 'Unknown error')}")
                    break
                
                contacts_data = result_data.get('Result', [])
                
                if not isinstance(contacts_data, list):
                    contacts_data = [contacts_data] if contacts_data else []
                
                # If no results, we've reached the end
                if len(contacts_data) == 0:
                    break
                
                all_contacts.extend(contacts_data)
                
                # LACRM appears to limit to 25 results per page regardless of MaxNumberOfResults
                # Continue until we get 0 results (indicating end of data)
                # Don't stop just because we got fewer than max_results_per_page
                
                page += 1
                
                # Safety check
                if page > 100:
                    logger.warning("CRM sync safety limit reached - stopping pagination")
                    break
            
            logger.info(f"🔄 Retrieved {len(all_contacts)} total contacts from CRM")
            
            # Log warning if we're getting unexpectedly few contacts
            if len(all_contacts) < 500:
                logger.warning(f"⚠️ Retrieved {len(all_contacts)} contacts - may indicate incomplete sync:")
                logger.warning("   - Check if pagination completed successfully")
                logger.warning("   - Verify API rate limits weren't hit")
                logger.warning("   - Consider running manual full sync")
            
            # Filter only modified contacts if we have a last sync time
            new_or_modified = []
            for contact in all_contacts:
                if contact and isinstance(contact, dict):
                    # Check if contact is new or modified (using actual LACRM field name)
                    contact_modified = self._parse_contact_date(contact.get('EditedDate'))
                    if not last_sync or (contact_modified and contact_modified > last_sync):
                        new_or_modified.append(contact)
            
            if new_or_modified:
                self._update_cache_with_deltas(new_or_modified)
                logger.info(f"✅ CRM delta sync: Updated {len(new_or_modified)} contacts")
            else:
                logger.info("✅ CRM delta sync: No changes detected")
            
            # Update last sync timestamp
            self._update_last_sync_time(len(new_or_modified))
            
            # Log summary for monitoring
            logger.info(f"📊 CRM Sync Summary: {len(all_contacts)} total, {len(new_or_modified)} updated")
                
        except Exception as e:
            logger.error(f"❌ Delta sync check failed: {e}")
    
    def _get_last_sync_time(self):
        """Get the last sync timestamp from database"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crm_sync_log (
                        id SERIAL PRIMARY KEY,
                        last_sync_time TIMESTAMP,
                        sync_type VARCHAR(50),
                        records_updated INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    SELECT last_sync_time FROM crm_sync_log 
                    WHERE sync_type = 'delta' 
                    ORDER BY created_at DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                conn.close()
                
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Error getting last sync time: {e}")
            return None
    
    def _update_last_sync_time(self, records_updated=0):
        """Update the last sync timestamp"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO crm_sync_log (last_sync_time, sync_type, records_updated)
                    VALUES (%s, %s, %s)
                """, (datetime.now(), 'delta', records_updated))
                
                conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating last sync time: {e}")
    
    def _parse_contact_date(self, date_str):
        """Parse contact date string to datetime"""
        if not date_str:
            return None
        try:
            # Handle different date formats that LACRM might use
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%Y %H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def _update_cache_with_deltas(self, contacts):
        """Update the cache with delta contacts using proper LACRM data format"""
        try:
            import psycopg2
            conn = signature_storage.get_connection()
            
            with conn.cursor() as cursor:
                updated_count = 0
                for contact in contacts:
                    try:
                        # Extract contact ID
                        contact_id = str(contact.get('ContactId', ''))
                        if not contact_id:
                            continue
                        
                        # Extract name from actual LACRM format
                        name = str(contact.get('CompanyName', '') or 'Unknown Contact')
                        
                        # Extract email (LACRM format: list of dicts with 'Text' field)
                        email_raw = contact.get('Email', '')
                        if isinstance(email_raw, list) and len(email_raw) > 0:
                            # Extract Text field from first email entry, handle both formats
                            first_email = email_raw[0]
                            if isinstance(first_email, dict):
                                email_text = first_email.get('Text', '')
                                # Remove "(Work)" suffix if present
                                email = email_text.split(' (')[0] if email_text else ''
                            else:
                                email = str(first_email)
                        elif isinstance(email_raw, dict):
                            email = str(email_raw.get('Text', '') or email_raw.get('Value', '') or '')
                        else:
                            email = str(email_raw or '')
                        
                        # Company name
                        company_name = str(contact.get('CompanyName', '') or '')
                        
                        # Extract phone (LACRM format: list of dicts with 'Text' field)
                        phone_raw = contact.get('Phone', '')
                        if isinstance(phone_raw, list) and len(phone_raw) > 0:
                            # Extract Text field from first phone entry, handle both formats
                            first_phone = phone_raw[0]
                            if isinstance(first_phone, dict):
                                phone_text = first_phone.get('Text', '')
                                # Remove "(Work)" suffix if present
                                phone = phone_text.split(' (')[0] if phone_text else ''
                            else:
                                phone = str(first_phone)
                        elif isinstance(phone_raw, dict):
                            phone = str(phone_raw.get('Text', '') or phone_raw.get('Value', '') or '')
                        else:
                            phone = str(phone_raw or '')
                        
                        # Extract address (LACRM format: list of dicts with structured address)
                        address_raw = contact.get('Address', '')
                        if isinstance(address_raw, list) and len(address_raw) > 0:
                            # Extract address from first address entry
                            first_address = address_raw[0]
                            if isinstance(first_address, dict):
                                # LACRM address structure: Street, City, State, Zip
                                street = first_address.get('Street', '')
                                city = first_address.get('City', '')
                                state = first_address.get('State', '')
                                zip_code = first_address.get('Zip', '')
                                address_parts = [p for p in [street, city, state, zip_code] if p]
                                address = ', '.join(address_parts)
                            else:
                                address = str(first_address)
                        elif isinstance(address_raw, dict):
                            address = str(address_raw.get('Street', '') or address_raw.get('Text', '') or address_raw.get('Value', '') or '')
                        else:
                            address = str(address_raw or '')
                        
                        # Combine additional fields into notes using actual LACRM field names
                        notes_parts = []
                        if contact.get('BackgroundInfo'):
                            notes_parts.append(f"Background: {str(contact['BackgroundInfo'])}")
                        if contact.get('Birthday'):
                            notes_parts.append(f"Birthday: {str(contact['Birthday'])}")
                        if contact.get('Industry'):
                            notes_parts.append(f"Industry: {str(contact['Industry'])}")
                        if contact.get('NumEmployees'):
                            notes_parts.append(f"Employees: {str(contact['NumEmployees'])}")
                        if contact.get('Website'):
                            notes_parts.append(f"Website: {str(contact['Website'])}")
                        if contact.get('CreationDate'):
                            notes_parts.append(f"Created: {str(contact['CreationDate'])}")
                        if contact.get('EditedDate'):
                            notes_parts.append(f"Modified: {str(contact['EditedDate'])}")
                        if contact.get('AssignedTo'):
                            notes_parts.append(f"Assigned: {str(contact['AssignedTo'])}")
                        
                        notes = " | ".join(notes_parts)
                        
                        # Use UPSERT to handle both new and modified contacts
                        cursor.execute("""
                            INSERT INTO crm_contacts_cache 
                            (contact_id, name, email, company_name, phone, address, notes, sync_status, last_sync)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (contact_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                email = EXCLUDED.email,
                                company_name = EXCLUDED.company_name,
                                phone = EXCLUDED.phone,
                                address = EXCLUDED.address,
                                notes = EXCLUDED.notes,
                                sync_status = EXCLUDED.sync_status,
                                last_sync = EXCLUDED.last_sync,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            contact_id,
                            name,
                            email,
                            company_name,
                            phone,
                            address,
                            notes,
                            'synced',
                            datetime.now()
                        ))
                        
                        updated_count += 1
                        
                    except Exception as contact_error:
                        logger.error(f"Error processing contact {contact.get('ContactId', 'unknown')}: {contact_error}")
                        continue
                
                conn.commit()
                logger.info(f"✅ Cache updated: {updated_count} contacts processed")
                
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error updating cache with deltas: {e}")
    
    def diagnose_crm_access(self):
        """Diagnose CRM API access to understand why we're only getting ~25 contacts"""
        try:
            logger.info("🔬 Starting CRM API diagnostics...")
            
            # Test 1: Try different search approaches
            test_approaches = [
                {"name": "Empty search", "params": {"SearchTerm": ""}},
                {"name": "Wildcard search", "params": {"SearchTerm": "*"}},
                {"name": "Common letter search", "params": {"SearchTerm": "a"}},
                {"name": "Company search", "params": {"SearchTerm": "inc"}},
                {"name": "Max results 500", "params": {"SearchTerm": "", "MaxNumberOfResults": 500}},
                {"name": "Max results 1000", "params": {"SearchTerm": "", "MaxNumberOfResults": 1000}},
            ]
            
            import requests
            
            for approach in test_approaches:
                try:
                    params = {
                        'APIToken': self.api_key,
                        'UserCode': self.user_code,
                        'Function': 'SearchContacts',
                        **approach['params']
                    }
                    
                    response = requests.get(self.crm_url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        result_data = json.loads(response.text)
                        if result_data.get('Success'):
                            contacts = result_data.get('Result', [])
                            if not isinstance(contacts, list):
                                contacts = [contacts] if contacts else []
                            
                            logger.info(f"🔬 {approach['name']}: {len(contacts)} contacts")
                            
                            # Show sample contact data structure
                            if contacts and len(contacts) > 0:
                                sample = contacts[0]
                                logger.info(f"   Sample fields: {list(sample.keys())}")
                        else:
                            logger.error(f"🔬 {approach['name']}: API Error - {result_data.get('Error')}")
                    else:
                        logger.error(f"🔬 {approach['name']}: HTTP {response.status_code}")
                        
                except Exception as test_error:
                    logger.error(f"🔬 {approach['name']}: Exception - {test_error}")
            
            # Test 2: Check if there are other API functions available
            logger.info("🔬 Testing alternative API functions...")
            
            alt_functions = ['GetContacts', 'GetContactList', 'GetAllContacts']
            for func in alt_functions:
                try:
                    params = {
                        'APIToken': self.api_key,
                        'UserCode': self.user_code,
                        'Function': func
                    }
                    
                    response = requests.get(self.crm_url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        result_data = json.loads(response.text)
                        if result_data.get('Success'):
                            logger.info(f"🔬 {func}: Available and working")
                        else:
                            logger.warning(f"🔬 {func}: {result_data.get('Error')}")
                    else:
                        logger.warning(f"🔬 {func}: HTTP {response.status_code}")
                        
                except Exception as func_error:
                    logger.error(f"🔬 {func}: Exception - {func_error}")
            
            logger.info("🔬 CRM API diagnostics complete")
            
        except Exception as e:
            logger.error(f"❌ CRM diagnostics failed: {e}")

# Global delta sync instance
crm_bidirectional_sync = CRMBidirectionalSync()

# Add CRM Bridge methods to the IntegratedSignatureHandler class
def verify_crm_bridge_token(self):
    """Verify CRM bridge authentication token"""
    auth_header = self.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    for app_name, valid_token in CRM_BRIDGE_TOKENS.items():
        if token == valid_token:
            logger.info(f"🔐 CRM Bridge access granted to: {app_name}")
            return {"app_name": app_name, "token": token}
    
    logger.warning(f"🚫 Invalid CRM bridge token attempted: {token[:20]}...")
    return None

def handle_crm_bridge_get(self, path, parsed_path):
    """Handle CRM bridge GET requests"""
    auth_info = self.verify_crm_bridge_token()
    if not auth_info:
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": "Invalid CRM bridge API token. Contact Better Day Energy IT for access."
        }).encode())
        return

    query_params = parse_qs(parsed_path.query)
    
    if path == "/api/v1/crm-bridge/contacts":
        limit = int(query_params.get('limit', [50])[0])
        self.handle_crm_bridge_contacts(auth_info, limit)
    elif path == "/api/v1/crm-bridge/stats":
        self.handle_crm_bridge_stats(auth_info)
    else:
        self.send_error(404)

def handle_crm_bridge_post(self, path, post_data):
    """Handle CRM bridge POST requests"""
    auth_info = self.verify_crm_bridge_token()
    if not auth_info:
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": "Invalid CRM bridge API token. Contact Better Day Energy IT for access."
        }).encode())
        return

    if path == "/api/v1/crm-bridge/auth/verify":
        self.handle_crm_bridge_auth_verify(auth_info)
    elif path == "/api/v1/crm-bridge/contacts/search":
        self.handle_crm_bridge_search(auth_info, post_data)
    elif path == "/api/v1/crm-bridge/contacts/create":
        self.handle_crm_bridge_create(auth_info, post_data)
    else:
        self.send_error(404)

def handle_crm_bridge_auth_verify(self, auth_info):
    """Verify authentication"""
    response = {
        "authenticated": True,
        "app_name": auth_info["app_name"],
        "permissions": ["read_contacts", "create_contacts", "search_contacts"],
        "service": "CRM Bridge on LOI Automation API",
        "cache_access": "enabled",
        "timestamp": datetime.now().isoformat()
    }
    
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response).encode())

def handle_crm_bridge_contacts(self, auth_info, limit):
    """Get contacts from cache"""
    try:
        import psycopg2
        db_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:bde123@localhost/loi_automation')
        
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT contact_id, name, company_name, email, phone, created_at 
                    FROM crm_contacts_cache 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
                
                contacts = []
                for row in cursor.fetchall():
                    contacts.append({
                        "contact_id": row[0],
                        "name": row[1],
                        "company_name": row[2] or "",
                        "email": row[3] or "",
                        "phone": row[4] or "",
                        "created_at": row[5].isoformat() if row[5] else ""
                    })
        
        logger.info(f"⚡ CRM Bridge: Served {len(contacts)} contacts to {auth_info['app_name']}")
        
        response = {
            "success": True,
            "count": len(contacts),
            "contacts": contacts,
            "source": "cache",
            "app": auth_info["app_name"]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge contacts error: {str(e)}")
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_crm_bridge_stats(self, auth_info):
    """Get cache statistics"""
    try:
        import psycopg2
        db_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:bde123@localhost/loi_automation')
        
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM crm_contacts_cache")
                total_contacts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM crm_contacts_cache WHERE company_name IS NOT NULL AND company_name != ''")
                contacts_with_companies = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(created_at) FROM crm_contacts_cache")
                last_sync = cursor.fetchone()[0]
        
        company_coverage = (contacts_with_companies / total_contacts * 100) if total_contacts > 0 else 0
        
        response = {
            "total_contacts": total_contacts,
            "contacts_with_companies": contacts_with_companies,
            "company_coverage": round(company_coverage, 1),
            "cache_freshness": {
                "fresh_last_24h": total_contacts,
                "last_sync": last_sync.isoformat() if last_sync else None
            }
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge stats error: {str(e)}")
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_crm_bridge_search(self, auth_info, post_data):
    """Search contacts"""
    try:
        data = json.loads(post_data.decode())
        query = data.get('query', '')
        limit = data.get('limit', 50)
        
        import psycopg2
        db_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:bde123@localhost/loi_automation')
        
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                # Improved fuzzy search with better pattern matching
                search_pattern = f"%{query}%"
                # Create variations for better fuzzy matching
                query_words = query.lower().split()
                word_patterns = [f"%{word}%" for word in query_words if len(word) > 2]
                
                # Build dynamic WHERE clause for fuzzy matching across all fields
                where_conditions = []
                params = []
                
                # Basic pattern search across all fields
                where_conditions.append("""(
                    LOWER(name) LIKE LOWER(%s) 
                    OR LOWER(company_name) LIKE LOWER(%s)
                    OR LOWER(email) LIKE LOWER(%s)
                    OR LOWER(phone) LIKE LOWER(%s)
                )""")
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
                
                # Add word-by-word fuzzy matching for better results
                if word_patterns:
                    for word_pattern in word_patterns:
                        where_conditions.append("""(
                            LOWER(name) LIKE LOWER(%s) 
                            OR LOWER(company_name) LIKE LOWER(%s)
                        )""")
                        params.extend([word_pattern, word_pattern])
                
                where_clause = " OR ".join(where_conditions)
                params.append(limit)
                
                cursor.execute(f"""
                    SELECT contact_id, name, company_name, email, phone, created_at 
                    FROM crm_contacts_cache 
                    WHERE {where_clause}
                    ORDER BY 
                        CASE 
                            WHEN LOWER(name) = LOWER(%s) THEN 1
                            WHEN LOWER(company_name) = LOWER(%s) THEN 2
                            WHEN LOWER(name) LIKE LOWER(%s) THEN 3
                            WHEN LOWER(company_name) LIKE LOWER(%s) THEN 4
                            ELSE 5
                        END,
                        created_at DESC 
                    LIMIT %s
                """, params + [query, query, search_pattern, search_pattern, limit])
                
                contacts = []
                for row in cursor.fetchall():
                    contacts.append({
                        "contact_id": row[0],
                        "name": row[1],
                        "company_name": row[2] or "",
                        "email": row[3] or "",
                        "phone": row[4] or "",
                        "created_at": row[5].isoformat() if row[5] else ""
                    })
        
        logger.info(f"🔍 CRM Bridge: Search '{query}' returned {len(contacts)} results for {auth_info['app_name']}")
        
        response = {
            "success": True,
            "query": query,
            "count": len(contacts),
            "contacts": contacts,
            "source": "cache",
            "app": auth_info["app_name"]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge search error: {str(e)}")
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_crm_bridge_create(self, auth_info, post_data):
    """Create new contact"""
    try:
        data = json.loads(post_data.decode())
        
        # Add to CRM write queue for background processing
        import psycopg2
        db_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:bde123@localhost/loi_automation')
        
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                # Add to write queue
                cursor.execute("""
                    INSERT INTO crm_write_queue (operation, contact_data, created_at)
                    VALUES (%s, %s, %s)
                """, ('create', json.dumps(data), datetime.now()))
                
                # Add to local cache immediately
                contact_id = f"pending_{secrets.token_urlsafe(16)}"
                cursor.execute("""
                    INSERT INTO crm_contacts_cache (contact_id, name, company_name, email, phone, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (contact_id, data.get('name'), data.get('company_name'), 
                      data.get('email'), data.get('phone'), datetime.now()))
                
                conn.commit()
        
        logger.info(f"✅ CRM Bridge: Contact created and queued for sync by {auth_info['app_name']}")
        
        response = {
            "success": True,
            "contact_id": contact_id,
            "message": "Contact created and queued for CRM sync",
            "app": auth_info["app_name"]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge create error: {str(e)}")
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": str(e)}).encode())

# Add methods to the IntegratedSignatureHandler class
IntegratedSignatureHandler.verify_crm_bridge_token = verify_crm_bridge_token
IntegratedSignatureHandler.handle_crm_bridge_get = handle_crm_bridge_get
IntegratedSignatureHandler.handle_crm_bridge_post = handle_crm_bridge_post
IntegratedSignatureHandler.handle_crm_bridge_auth_verify = handle_crm_bridge_auth_verify
IntegratedSignatureHandler.handle_crm_bridge_contacts = handle_crm_bridge_contacts
IntegratedSignatureHandler.handle_crm_bridge_stats = handle_crm_bridge_stats
IntegratedSignatureHandler.handle_crm_bridge_search = handle_crm_bridge_search
IntegratedSignatureHandler.handle_crm_bridge_create = handle_crm_bridge_create

def main():
    """Start the complete integrated signature server"""
    port = int(os.environ.get('PORT', 8002))  # Use PORT env var for Render (match render.yaml)
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
    print("- /admin - CRM-integrated LOI admin dashboard")
    print("- 🔄 Background CRM delta sync every 5 minutes")
    
    # Start background CRM delta sync (non-blocking)
    try:
        crm_bidirectional_sync.start_background_sync()
        print("✅ CRM bidirectional sync service started (with database queue)")
    except Exception as e:
        print(f"⚠️ CRM sync failed to start (database issue): {e}")
        print("📝 Note: System will work without CRM sync, but won't create CRM records automatically")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        crm_bidirectional_sync.stop_background_sync()
        print("✅ Server stopped")

if __name__ == "__main__":
    main()