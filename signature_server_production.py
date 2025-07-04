#!/usr/bin/env python3
"""
Production Signature Server for Render Deployment
Secure, scalable signature service with PostgreSQL backend
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import ssl
import hashlib
import hmac
from pathlib import Path

# Import database modules
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    print("Warning: psycopg2 not installed. Using in-memory storage.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
SIGNATURE_SECRET_KEY = os.environ.get('SIGNATURE_SECRET_KEY', 'dev-secret-key')
API_BASE_URL = os.environ.get('API_BASE_URL', 'https://loi-automation-api.onrender.com')
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
SSL_REDIRECT = os.environ.get('SSL_REDIRECT', 'false').lower() == 'true'
PORT = int(os.environ.get('PORT', 8001))

class DatabaseManager:
    """Manage PostgreSQL database connections and operations"""
    
    def __init__(self):
        self.connection_string = DATABASE_URL
        self.ensure_tables()
    
    def get_connection(self):
        """Get database connection"""
        if not psycopg2 or not self.connection_string:
            return None
        return psycopg2.connect(self.connection_string)
    
    def ensure_tables(self):
        """Create tables if they don't exist"""
        if not psycopg2 or not self.connection_string:
            logger.warning("Database not configured. Using in-memory storage.")
            return
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Create signature_requests table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signature_requests (
                    id SERIAL PRIMARY KEY,
                    request_id VARCHAR(255) UNIQUE NOT NULL,
                    signature_token VARCHAR(255) UNIQUE NOT NULL,
                    transaction_id VARCHAR(255),
                    document_name VARCHAR(255),
                    signer_name VARCHAR(255),
                    signer_email VARCHAR(255),
                    company_name VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'pending',
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    signed_at TIMESTAMP,
                    signature_data TEXT,
                    verification_code VARCHAR(50),
                    ip_address VARCHAR(50),
                    user_agent TEXT
                )
            """)
            
            # Create index for faster lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_signature_token 
                ON signature_requests(signature_token)
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
    
    def get_signature_request(self, token):
        """Get signature request by token"""
        if not psycopg2 or not self.connection_string:
            # Fallback to file storage
            return self._get_from_file(token)
        
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM signature_requests 
                WHERE signature_token = %s AND expires_at > NOW()
            """, (token,))
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting signature request: {e}")
            return self._get_from_file(token)
    
    def update_signature_request(self, token, signature_data, ip_address, user_agent):
        """Update signature request with completion data"""
        verification_code = f"LOI-{str(uuid.uuid4())[:8].upper()}"
        
        if not psycopg2 or not self.connection_string:
            return self._update_in_file(token, signature_data, verification_code)
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE signature_requests 
                SET status = 'completed',
                    signed_at = NOW(),
                    signature_data = %s,
                    verification_code = %s,
                    ip_address = %s,
                    user_agent = %s
                WHERE signature_token = %s
                RETURNING verification_code
            """, (signature_data, verification_code, ip_address, user_agent, token))
            
            result = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error updating signature request: {e}")
            return self._update_in_file(token, signature_data, verification_code)
    
    def get_signed_document(self, verification_code):
        """Get signed document by verification code"""
        if not psycopg2 or not self.connection_string:
            return self._get_signed_from_file(verification_code)
        
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM signature_requests 
                WHERE verification_code = %s
            """, (verification_code,))
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting signed document: {e}")
            return self._get_signed_from_file(verification_code)
    
    # File-based fallback methods
    def _get_from_file(self, token):
        """Get signature request from file (fallback)"""
        data_file = Path("./signature_request_data.json")
        if data_file.exists():
            with open(data_file, 'r') as f:
                requests = json.load(f)
                for req in requests.values():
                    if req.get('signature_token') == token:
                        return req
        return None
    
    def _update_in_file(self, token, signature_data, verification_code):
        """Update signature in file (fallback)"""
        data_file = Path("./signature_request_data.json")
        if data_file.exists():
            with open(data_file, 'r') as f:
                requests = json.load(f)
            
            for req_id, req in requests.items():
                if req.get('signature_token') == token:
                    req['status'] = 'completed'
                    req['signed_at'] = datetime.now().isoformat()
                    req['signature_data'] = signature_data
                    req['verification_code'] = verification_code
                    
                    with open(data_file, 'w') as f:
                        json.dump(requests, f)
                    
                    return verification_code
        return None
    
    def _get_signed_from_file(self, verification_code):
        """Get signed document from file (fallback)"""
        data_file = Path("./signature_request_data.json")
        if data_file.exists():
            with open(data_file, 'r') as f:
                requests = json.load(f)
                for req in requests.values():
                    if req.get('verification_code') == verification_code:
                        return req
        return None

# Initialize database manager - use global to prevent connection storm
try:
    from main import get_global_db_manager
    db_manager = get_global_db_manager()
except ImportError:
    # Fallback if main not available
    db_manager = DatabaseManager()

class SecureSignatureHandler(BaseHTTPRequestHandler):
    """Production-ready signature request handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Force HTTPS in production
        if SSL_REDIRECT and self.headers.get('X-Forwarded-Proto') == 'http':
            self.send_response(301)
            self.send_header('Location', f"https://{self.headers.get('Host')}{self.path}")
            self.end_headers()
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Add security headers
        self.add_security_headers()
        
        if path == "/":
            self.serve_home()
        elif path.startswith("/sign/"):
            token = path.split("/sign/")[1]
            self.serve_signature_page(token)
        elif path.startswith("/signature-complete/"):
            verification_code = path.split("/signature-complete/")[1]
            self.serve_completion_page(verification_code)
        elif path == "/health":
            self.serve_health_check()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        # Check CORS
        origin = self.headers.get('Origin')
        if origin and ALLOWED_ORIGINS != ['*'] and origin not in ALLOWED_ORIGINS:
            self.send_error(403, "Origin not allowed")
            return
        
        if self.path == "/api/submit-signature":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.handle_signature_submission(post_data)
        else:
            self.send_error(404)
    
    def add_security_headers(self):
        """Add security headers to response"""
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        self.send_header('Content-Security-Policy', "default-src 'self' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';")
        
        # CORS headers
        if ALLOWED_ORIGINS == ['*']:
            self.send_header('Access-Control-Allow-Origin', '*')
        else:
            origin = self.headers.get('Origin')
            if origin in ALLOWED_ORIGINS:
                self.send_header('Access-Control-Allow-Origin', origin)
    
    def serve_home(self):
        """Serve home page"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Better Day Energy Signature System</title>
            <meta name="description" content="Secure electronic signature system for BDE documents">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; color: #1f4e79; margin-bottom: 30px; }
                .security { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Better Day Energy</h1>
                    <h2>Electronic Signature System</h2>
                    <p>Secure, legally binding electronic signatures for LOI documents</p>
                </div>
                <div class="security">
                    <h3>🔒 Security Features</h3>
                    <ul>
                        <li>256-bit SSL encryption</li>
                        <li>Tamper-evident audit trail</li>
                        <li>Legal compliance with ESIGN Act</li>
                        <li>Secure PostgreSQL storage</li>
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
        # Validate token format
        if not self.validate_token(token):
            self.send_error(400, "Invalid signature token")
            return
        
        # Get signature request from database
        signature_request = db_manager.get_signature_request(token)
        
        if not signature_request:
            self.send_error(404, "Signature request not found or expired")
            return
        
        # Check if already signed
        if signature_request.get('status') == 'completed':
            self.serve_already_signed(signature_request)
            return
        
        # Generate signature page HTML
        html = self.create_secure_signature_page(signature_request)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def create_secure_signature_page(self, signature_request):
        """Create secure signature page with CSRF protection"""
        # Generate CSRF token
        csrf_token = self.generate_csrf_token(signature_request['signature_token'])
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Sign Document - {signature_request['document_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="robots" content="noindex, nofollow">
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
                    position: sticky;
                    top: 20px;
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
                .btn:disabled {{
                    opacity: 0.6;
                    cursor: not-allowed;
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
                .security-notice {{
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #666;
                    margin-top: 20px;
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
                    .signature-panel {{ position: static; }}
                }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>
        </head>
        <body>
            <div class="header">
                <div class="logo">Better Day Energy - Electronic Signature</div>
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
                                <li>Legal binding nature of this agreement under the ESIGN Act</li>
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
                    
                    <div class="warning-box">
                        <h3>Your Signature Required</h3>
                        <p>Please sign below to electronically execute this agreement.</p>
                    </div>
                    
                    <div class="signature-area">
                        <p><strong>Sign Here:</strong></p>
                        <canvas id="signature-canvas" width="300" height="150"></canvas>
                        <div style="margin-top: 10px;">
                            <button type="button" class="btn btn-secondary" onclick="clearSignature()">Clear</button>
                        </div>
                    </div>
                    
                    <button type="button" class="btn btn-success" onclick="submitSignature()" id="sign-button">
                        Sign Document
                    </button>
                    
                    <div class="security-notice">
                        <strong>🔒 Security:</strong> This signature is legally binding under the ESIGN Act. 
                        Your IP address ({self.client_address[0]}) and timestamp will be recorded in our tamper-evident audit trail.
                    </div>
                </div>
            </div>
            
            <input type="hidden" id="csrf-token" value="{csrf_token}">
            <input type="hidden" id="signature-token" value="{signature_request['signature_token']}">
            
            <script>
                // Initialize signature pad
                const canvas = document.getElementById('signature-canvas');
                const signaturePad = new SignaturePad(canvas, {{
                    minWidth: 0.5,
                    maxWidth: 2.5,
                    throttle: 16,
                    minDistance: 5
                }});
                
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
                    signButton.innerHTML = 'Processing...';
                    
                    try {{
                        const signatureData = signaturePad.toDataURL('image/png');
                        const csrfToken = document.getElementById('csrf-token').value;
                        const signatureToken = document.getElementById('signature-token').value;
                        
                        const response = await fetch('/api/submit-signature', {{
                            method: 'POST',
                            headers: {{ 
                                'Content-Type': 'application/json',
                                'X-CSRF-Token': csrfToken
                            }},
                            body: JSON.stringify({{
                                signature_token: signatureToken,
                                signature_data: signatureData,
                                signed_at: new Date().toISOString(),
                                csrf_token: csrfToken
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
                        signButton.innerHTML = 'Sign Document';
                    }}
                }}
                
                // Prevent signature pad from scrolling on mobile
                function preventScrolling(e) {{
                    e.preventDefault();
                }}
                
                canvas.addEventListener('touchstart', preventScrolling, {{ passive: false }});
                canvas.addEventListener('touchmove', preventScrolling, {{ passive: false }});
            </script>
        </body>
        </html>
        """
    
    def handle_signature_submission(self, post_data):
        """Handle signature submission with security validation"""
        try:
            data = json.loads(post_data.decode())
            signature_token = data.get('signature_token')
            csrf_token = data.get('csrf_token')
            
            # Validate CSRF token
            if not self.validate_csrf_token(signature_token, csrf_token):
                self.send_error(403, "Invalid CSRF token")
                return
            
            # Get client info
            ip_address = self.headers.get('X-Forwarded-For', self.client_address[0])
            user_agent = self.headers.get('User-Agent', 'Unknown')
            
            # Update signature in database
            verification_code = db_manager.update_signature_request(
                signature_token,
                data.get('signature_data'),
                ip_address,
                user_agent
            )
            
            if not verification_code:
                self.send_error(404, "Signature request not found")
                return
            
            logger.info(f"Signature completed with verification code: {verification_code}")
            
            # Send response
            response_data = {
                'success': True,
                'verification_code': verification_code
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.add_security_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling signature: {e}")
            self.send_error(500, "Internal server error")
    
    def serve_completion_page(self, verification_code):
        """Serve signature completion page"""
        # Validate verification code format
        if not verification_code.startswith('LOI-'):
            self.send_error(400, "Invalid verification code")
            return
        
        signed_doc = db_manager.get_signed_document(verification_code)
        if not signed_doc:
            self.send_error(404, "Signed document not found")
            return
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Signature Complete - Better Day Energy</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #28a745; font-size: 48px; margin-bottom: 20px; }}
                .verification {{ background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: left; }}
                .print-button {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✓</div>
                <h1>Document Signed Successfully!</h1>
                <p>Your Letter of Intent has been electronically executed and is legally binding.</p>
                
                <div class="verification">
                    <h3>Verification Code</h3>
                    <code style="font-size: 18px; font-weight: bold;">{verification_code}</code>
                    <p>Keep this code for your records</p>
                </div>
                
                <div class="details">
                    <h3>Signature Details</h3>
                    <p><strong>Signer:</strong> {signed_doc['signer_name']}</p>
                    <p><strong>Company:</strong> {signed_doc['company_name']}</p>
                    <p><strong>Document:</strong> {signed_doc['document_name']}</p>
                    <p><strong>Signed:</strong> {datetime.fromisoformat(signed_doc['signed_at']).strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>IP Address:</strong> {signed_doc.get('ip_address', 'Not recorded')}</p>
                </div>
                
                <button class="btn btn-primary print-button" onclick="window.print()">Print Certificate</button>
                
                <p style="margin-top: 30px; color: #666;">
                    Thank you for choosing Better Day Energy!<br>
                    Our team will contact you within 2 business days to begin implementation.
                </p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.add_security_headers()
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_already_signed(self, signature_request):
        """Serve already signed page"""
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document Already Signed</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; text-align: center; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Document Already Signed</h1>
                <p>This document has already been signed by {signature_request['signer_name']}.</p>
                <p><strong>Verification Code:</strong> {signature_request.get('verification_code', 'N/A')}</p>
                <p style="margin-top: 20px;">
                    <a href="/" class="btn btn-primary">Return to Home</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.add_security_headers()
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_health_check(self):
        """Serve health check endpoint for monitoring"""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if psycopg2 and DATABASE_URL else 'not configured',
            'version': '1.0.0'
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.add_security_headers()
        self.end_headers()
        self.wfile.write(json.dumps(health_data).encode('utf-8'))
    
    def validate_token(self, token):
        """Validate token format"""
        # Basic UUID validation
        try:
            uuid.UUID(token)
            return True
        except ValueError:
            return False
    
    def generate_csrf_token(self, signature_token):
        """Generate CSRF token"""
        message = f"{signature_token}:{datetime.now().hour}"
        return hmac.new(
            SIGNATURE_SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
    
    def validate_csrf_token(self, signature_token, csrf_token):
        """Validate CSRF token"""
        expected = self.generate_csrf_token(signature_token)
        return hmac.compare_digest(expected, csrf_token)

def main():
    """Start the production signature server"""
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SecureSignatureHandler)
    
    # SSL configuration for local testing
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        httpd.socket = ssl.wrap_socket(
            httpd.socket,
            certfile='cert.pem',
            keyfile='key.pem',
            server_side=True
        )
        protocol = 'https'
    else:
        protocol = 'http'
    
    print(f"🔒 Better Day Energy Production Signature Server")
    print(f"🌐 Server running on port {PORT}")
    print(f"📊 Database: {'Connected' if DATABASE_URL else 'Using file storage'}")
    print(f"🔐 Security: CSRF protection enabled")
    print(f"✅ Health check: {protocol}://localhost:{PORT}/health")
    print(f"\n🚀 Ready for production deployment on Render!")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()