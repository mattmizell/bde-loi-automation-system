#!/usr/bin/env python3
"""
Signature Server - DocuSign-like Experience

Create a web-based signature routing experience using FastAPI and HTML5 Canvas
for document review and electronic signature capture.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid
import base64
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Better Day Energy Signature System",
    description="DocuSign-like signature routing for LOI documents",
    version="1.0.0"
)

# Create directories
templates_dir = Path("./signature_templates")
templates_dir.mkdir(exist_ok=True)

static_dir = Path("./signature_static")
static_dir.mkdir(exist_ok=True)

documents_dir = Path("./signature_documents")
documents_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Load signature request data from file
def load_signature_requests():
    """Load signature requests from JSON file"""
    import json
    data_file = Path("./signature_request_data.json")
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}

# In-memory storage for demo (in production, use PostgreSQL)
signature_requests = {}
signed_documents = {}

@app.get("/", response_class=HTMLResponse)
async def signature_home():
    """Signature system home page"""
    return """
    <html>
    <head>
        <title>Better Day Energy Signature System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }
            .header { text-align: center; color: #1f4e79; margin-bottom: 30px; }
            .btn { background: #1f4e79; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🖊️ Better Day Energy</h1>
                <h2>Electronic Signature System</h2>
                <p>DocuSign-like signature routing for LOI documents</p>
            </div>
            <div style="text-align: center;">
                <a href="/create-signature-request" class="btn">📄 Create New Signature Request</a>
                <a href="/admin" class="btn">⚙️ Admin Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/sign/{token}", response_class=HTMLResponse)
async def sign_document(request: Request, token: str):
    """Document signing interface - DocuSign-like experience"""
    
    # Find signature request by token
    signature_request = None
    for req_id, req_data in signature_requests.items():
        if req_data.get('signature_token') == token:
            signature_request = req_data
            break
    
    if not signature_request:
        raise HTTPException(status_code=404, detail="Signature request not found")
    
    # Check if already signed
    if signature_request.get('status') == 'completed':
        return await show_already_signed(signature_request)
    
    # Check if expired
    if datetime.now() > datetime.fromisoformat(signature_request['expires_at']):
        return await show_expired_request(signature_request)
    
    # Create signature interface HTML
    html_content = create_signature_interface_html(signature_request)
    
    return HTMLResponse(content=html_content)

def create_signature_interface_html(signature_request: Dict[str, Any]) -> str:
    """Create DocuSign-like signature interface"""
    
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
                min-height: 100vh;
            }}
            
            .header {{
                background: white;
                border-bottom: 1px solid #e9ecef;
                padding: 15px 0;
                position: sticky;
                top: 0;
                z-index: 100;
            }}
            
            .header-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
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
            
            .main-container {{
                max-width: 1200px;
                margin: 20px auto;
                padding: 0 20px;
                display: grid;
                grid-template-columns: 1fr 350px;
                gap: 20px;
            }}
            
            .document-panel {{
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .document-header {{
                background: #f8f9fa;
                padding: 20px;
                border-bottom: 1px solid #e9ecef;
            }}
            
            .document-content {{
                padding: 30px;
                max-height: 600px;
                overflow-y: auto;
                border: 2px solid #007bff;
                margin: 20px;
                border-radius: 8px;
            }}
            
            .signature-panel {{
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                height: fit-content;
                position: sticky;
                top: 100px;
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
                transition: all 0.2s;
            }}
            
            .btn-primary {{
                background: #007bff;
                color: white;
            }}
            
            .btn-primary:hover {{
                background: #0056b3;
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
            
            .btn-success:hover {{
                background: #218838;
            }}
            
            .signer-info {{
                background: #e7f3ff;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
            }}
            
            .document-info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
            }}
            
            .signature-required {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
            }}
            
            .progress-indicator {{
                display: flex;
                align-items: center;
                margin-bottom: 20px;
            }}
            
            .progress-step {{
                flex: 1;
                text-align: center;
                padding: 10px;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                font-size: 14px;
            }}
            
            .progress-step.active {{
                background: #007bff;
                color: white;
            }}
            
            .agreement-content {{
                line-height: 1.6;
                color: #333;
            }}
            
            .agreement-content h1, .agreement-content h2, .agreement-content h3 {{
                color: #1f4e79;
                margin: 20px 0 10px 0;
            }}
            
            .agreement-content table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            
            .agreement-content th, .agreement-content td {{
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            
            .agreement-content th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            .signature-info {{
                font-size: 12px;
                color: #666;
                margin-top: 10px;
            }}
            
            .security-info {{
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                font-size: 12px;
                color: #666;
                margin-top: 20px;
            }}
            
            @media (max-width: 768px) {{
                .main-container {{
                    grid-template-columns: 1fr;
                }}
                
                .signature-panel {{
                    position: static;
                }}
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    🖊️ Better Day Energy - Electronic Signature
                </div>
                <div class="status">
                    ⏰ Expires {datetime.fromisoformat(signature_request['expires_at']).strftime('%B %d, %Y')}
                </div>
            </div>
        </div>
        
        <div class="main-container">
            <div class="document-panel">
                <div class="document-header">
                    <h2>📄 {signature_request['document_name']}</h2>
                    <p>Please review the document below and provide your electronic signature</p>
                </div>
                
                <div class="progress-indicator">
                    <div class="progress-step active">1. Review Document</div>
                    <div class="progress-step active">2. Sign Document</div>
                    <div class="progress-step">3. Complete</div>
                </div>
                
                <div class="document-content">
                    <div class="agreement-content">
                        {get_loi_agreement_content(signature_request)}
                    </div>
                </div>
            </div>
            
            <div class="signature-panel">
                <div class="signer-info">
                    <h3>📝 Signer Information</h3>
                    <p><strong>Name:</strong> {signature_request['signer_name']}</p>
                    <p><strong>Email:</strong> {signature_request['signer_email']}</p>
                    <p><strong>Company:</strong> {signature_request['company_name']}</p>
                </div>
                
                <div class="document-info">
                    <h3>📋 Document Details</h3>
                    <p><strong>Type:</strong> Letter of Intent</p>
                    <p><strong>Created:</strong> {datetime.fromisoformat(signature_request['created_at']).strftime('%B %d, %Y')}</p>
                    <p><strong>Transaction:</strong> {signature_request['transaction_id']}</p>
                </div>
                
                <div class="signature-required">
                    <h3>🖊️ Your Signature Required</h3>
                    <p>Please sign in the box below to electronically execute this agreement.</p>
                </div>
                
                <div class="signature-area">
                    <p><strong>Sign Here:</strong></p>
                    <canvas id="signature-canvas" width="300" height="150"></canvas>
                    <div class="signature-info">
                        Use your mouse or finger to sign above
                    </div>
                    <div style="margin-top: 10px;">
                        <button type="button" class="btn btn-secondary" onclick="clearSignature()">
                            🗑️ Clear
                        </button>
                    </div>
                </div>
                
                <button type="button" class="btn btn-success" onclick="submitSignature()" id="sign-button">
                    ✅ Sign Document
                </button>
                
                <div class="security-info">
                    🔒 <strong>Security Information:</strong><br>
                    • This signature is legally binding<br>
                    • IP address will be recorded<br>
                    • Timestamp will be applied<br>
                    • Audit trail will be maintained
                </div>
            </div>
        </div>
        
        <script>
            // Initialize signature pad
            const canvas = document.getElementById('signature-canvas');
            const signaturePad = new SignaturePad(canvas, {{
                backgroundColor: 'rgba(255, 255, 255, 0)',
                penColor: 'rgb(0, 0, 0)',
                velocityFilterWeight: 0.7,
                minWidth: 1,
                maxWidth: 3
            }});
            
            // Clear signature function
            function clearSignature() {{
                signaturePad.clear();
            }}
            
            // Submit signature function
            async function submitSignature() {{
                if (signaturePad.isEmpty()) {{
                    alert('Please provide your signature before submitting.');
                    return;
                }}
                
                const signButton = document.getElementById('sign-button');
                signButton.disabled = true;
                signButton.innerHTML = '⏳ Processing Signature...';
                
                try {{
                    // Get signature data
                    const signatureData = signaturePad.toDataURL('image/png');
                    
                    // Submit to server
                    const response = await fetch('/api/submit-signature', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            signature_token: '{signature_request['signature_token']}',
                            signature_data: signatureData,
                            signer_ip: await getUserIP(),
                            signed_at: new Date().toISOString()
                        }})
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        window.location.href = '/signature-complete/' + result.verification_code;
                    }} else {{
                        throw new Error('Signature submission failed');
                    }}
                }} catch (error) {{
                    alert('Error submitting signature. Please try again.');
                    signButton.disabled = false;
                    signButton.innerHTML = '✅ Sign Document';
                }}
            }}
            
            // Get user IP (simplified for demo)
            async function getUserIP() {{
                try {{
                    const response = await fetch('https://api.ipify.org?format=json');
                    const data = await response.json();
                    return data.ip;
                }} catch (error) {{
                    return '127.0.0.1';
                }}
            }}
            
            // Resize canvas for high DPI displays
            function resizeCanvas() {{
                const ratio = Math.max(window.devicePixelRatio || 1, 1);
                canvas.width = canvas.offsetWidth * ratio;
                canvas.height = canvas.offsetHeight * ratio;
                canvas.getContext('2d').scale(ratio, ratio);
                signaturePad.clear();
            }}
            
            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();
        </script>
    </body>
    </html>
    """

def get_loi_agreement_content(signature_request: Dict[str, Any]) -> str:
    """Get the LOI agreement content for display"""
    
    return f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #1f4e79;">Better Day Energy</h1>
        <h2>Letter of Intent</h2>
        <h3>VP Racing Fuel Supply Agreement</h3>
    </div>
    
    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
    <p><strong>Transaction ID:</strong> {signature_request['transaction_id']}</p>
    
    <h3>🏢 Customer Information</h3>
    <table>
        <tr><th>Business Name</th><td>{signature_request['company_name']}</td></tr>
        <tr><th>Owner/Contact</th><td>{signature_request['signer_name']}</td></tr>
        <tr><th>Email</th><td>{signature_request['signer_email']}</td></tr>
        <tr><th>Business Type</th><td>Independent Gas Station</td></tr>
    </table>
    
    <h3>⛽ Fuel Volume Commitments</h3>
    <table>
        <tr><th>Product</th><th>Monthly Volume</th><th>Annual Volume</th></tr>
        <tr><td>Gasoline</td><td>85,000 gallons</td><td>1,020,000 gallons</td></tr>
        <tr><td>Diesel</td><td>25,000 gallons</td><td>300,000 gallons</td></tr>
        <tr><td><strong>Total</strong></td><td><strong>110,000 gallons</strong></td><td><strong>1,320,000 gallons</strong></td></tr>
    </table>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3>💰 Financial Incentive Package</h3>
        <table>
            <tr><th>Incentive Type</th><th>Amount</th><th>Description</th></tr>
            <tr><td>Image Program Funding</td><td>$75,000</td><td>Branding, signage, and facility improvements</td></tr>
            <tr><td>Volume Incentives</td><td>$50,000 annually</td><td>Performance-based quarterly payments</td></tr>
            <tr><td><strong>Total First Year Value</strong></td><td><strong>$125,000</strong></td><td><strong>Combined incentive package</strong></td></tr>
        </table>
    </div>
    
    <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #1f4e79; margin: 20px 0;">
        <h3>📋 Agreement Terms & Conditions</h3>
        
        <h4>Volume Commitments:</h4>
        <ul>
            <li>Minimum monthly volume: 110,000 gallons</li>
            <li>Contract duration: 36 months</li>
            <li>Exclusive purchasing agreement with Better Day Energy</li>
            <li>Volume discount tiers based on monthly performance</li>
        </ul>
        
        <h4>Service Commitments from Better Day Energy:</h4>
        <ul>
            <li>Dedicated account management and support</li>
            <li>Guaranteed delivery scheduling (twice weekly)</li>
            <li>24/7 emergency fuel supply availability</li>
            <li>Competitive pricing with quarterly market reviews</li>
            <li>Business growth consulting and market intelligence</li>
        </ul>
        
        <h4>Implementation Timeline:</h4>
        <ul>
            <li>Target conversion date: August 1, 2025</li>
            <li>LOI execution and due diligence: 2 weeks</li>
            <li>Contract finalization: 2 weeks</li>
            <li>Logistics setup and testing: 2 weeks</li>
            <li>Full service commencement: Week 7</li>
        </ul>
    </div>
    
    <h3>🤝 Mutual Commitments</h3>
    <p><strong>Customer Commitments ({signature_request['company_name']}):</strong></p>
    <ul>
        <li>Maintain minimum volume commitments as specified</li>
        <li>Exclusive fuel purchasing through Better Day Energy</li>
        <li>Compliance with VP Racing branding standards</li>
        <li>Payment terms: Net 15 days from delivery</li>
        <li>Cooperation with transition and implementation processes</li>
    </ul>
    
    <p><strong>Better Day Energy Commitments:</strong></p>
    <ul>
        <li>Deliver agreed-upon volume incentives and image funding</li>
        <li>Maintain service levels and delivery commitments</li>
        <li>Provide dedicated account management support</li>
        <li>Honor pricing structure and market adjustment terms</li>
        <li>Complete implementation within agreed timeline</li>
    </ul>
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3>🖊️ Electronic Signature Authorization</h3>
        <p>By signing this Letter of Intent electronically, both parties acknowledge:</p>
        <ul>
            <li>Understanding and agreement to all terms stated above</li>
            <li>Commitment to proceed with formal contract negotiation</li>
            <li>Authorization to begin implementation planning</li>
            <li>Legal binding nature of this agreement</li>
        </ul>
    </div>
    """

@app.post("/api/submit-signature")
async def submit_signature(request: Request):
    """Submit electronic signature"""
    
    try:
        data = await request.json()
        signature_token = data.get('signature_token')
        signature_data = data.get('signature_data')
        signer_ip = data.get('signer_ip')
        signed_at = data.get('signed_at')
        
        # Find signature request
        signature_request = None
        for req_id, req_data in signature_requests.items():
            if req_data.get('signature_token') == signature_token:
                signature_request = req_data
                break
        
        if not signature_request:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        # Generate verification code
        verification_code = f"LOI-{str(uuid.uuid4())[:8].upper()}"
        
        # Update signature request
        signature_request.update({
            'status': 'completed',
            'signed_at': signed_at,
            'signature_data': signature_data,
            'signer_ip': signer_ip,
            'verification_code': verification_code
        })
        
        # Store in signed documents
        signed_documents[verification_code] = signature_request.copy()
        
        # Send completion notification
        await send_signature_completion_email(signature_request)
        
        logger.info(f"✅ Signature completed for {signature_request['signer_name']}")
        
        return JSONResponse({
            'success': True,
            'verification_code': verification_code,
            'message': 'Signature submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Signature submission failed: {e}")
        raise HTTPException(status_code=500, detail="Signature submission failed")

@app.get("/signature-complete/{verification_code}", response_class=HTMLResponse)
async def signature_complete(verification_code: str):
    """Signature completion page"""
    
    signed_doc = signed_documents.get(verification_code)
    if not signed_doc:
        raise HTTPException(status_code=404, detail="Signed document not found")
    
    return f"""
    <html>
    <head>
        <title>Signature Complete - Better Day Energy</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; text-align: center; }}
            .success {{ color: #28a745; font-size: 48px; margin-bottom: 20px; }}
            .verification {{ background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅</div>
            <h1>Document Signed Successfully!</h1>
            <p>Your Letter of Intent has been electronically executed.</p>
            
            <div class="verification">
                <h3>🔐 Verification Code</h3>
                <code style="font-size: 18px; font-weight: bold;">{verification_code}</code>
                <p>Keep this code for your records</p>
            </div>
            
            <div class="details">
                <h3>📋 Signature Details</h3>
                <p><strong>Signer:</strong> {signed_doc['signer_name']}</p>
                <p><strong>Company:</strong> {signed_doc['company_name']}</p>
                <p><strong>Document:</strong> {signed_doc['document_name']}</p>
                <p><strong>Signed:</strong> {datetime.fromisoformat(signed_doc['signed_at']).strftime('%B %d, %Y at %I:%M %p')}</p>
                <p><strong>IP Address:</strong> {signed_doc['signer_ip']}</p>
            </div>
            
            <div style="margin-top: 30px;">
                <h3>🤝 What Happens Next</h3>
                <ul style="text-align: left;">
                    <li>You'll receive a confirmation email shortly</li>
                    <li>Better Day Energy will begin contract preparation</li>
                    <li>Our team will contact you within 2 business days</li>
                    <li>Implementation planning will commence</li>
                </ul>
            </div>
            
            <p style="margin-top: 30px; color: #666;">
                Thank you for choosing Better Day Energy!
            </p>
        </div>
    </body>
    </html>
    """

async def send_signature_completion_email(signature_request: Dict[str, Any]):
    """Send signature completion notification email"""
    
    try:
        # Gmail SMTP configuration
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "transaction.coordinator.agent@gmail.com"
        smtp_password = "xmvi xvso zblo oewe"
        
        # Create completion email
        msg = MIMEMultipart()
        msg['From'] = f"Better Day Energy LOI Team <{smtp_username}>"
        msg['To'] = signature_request['signer_email']
        msg['Subject'] = f"✅ LOI Signed Successfully - {signature_request['company_name']}"
        
        body = f"""Dear {signature_request['signer_name']},

🎉 EXCELLENT NEWS! Your Letter of Intent has been successfully signed!

✅ SIGNATURE CONFIRMATION:
Document: {signature_request['document_name']}
Company: {signature_request['company_name']}
Signed Date: {datetime.fromisoformat(signature_request['signed_at']).strftime('%B %d, %Y at %I:%M %p')}
Verification Code: {signature_request['verification_code']}

Your electronic signature is legally binding and the partnership process is now initiated.

📞 NEXT STEPS:
Our implementation team will contact you within 2 business days to begin the transition process.

Thank you for choosing Better Day Energy!

Best regards,
Better Day Energy Team
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(f"📧 Completion notification sent to {signature_request['signer_email']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send completion email: {e}")

@app.post("/api/create-signature-request")
async def create_signature_request(
    signer_name: str = Form(...),
    signer_email: str = Form(...),
    company_name: str = Form(...),
    document_name: str = Form(...),
    transaction_id: str = Form(...)
):
    """Create a new signature request"""
    
    try:
        # Generate IDs
        request_id = str(uuid.uuid4())
        signature_token = str(uuid.uuid4())
        
        # Create signature request
        signature_request = {
            'request_id': request_id,
            'transaction_id': transaction_id,
            'signer_name': signer_name,
            'signer_email': signer_email,
            'company_name': company_name,
            'document_name': document_name,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
            'status': 'pending',
            'signature_token': signature_token,
            'signature_url': f"http://localhost:8001/sign/{signature_token}"
        }
        
        # Store signature request
        signature_requests[request_id] = signature_request
        
        logger.info(f"📝 Created signature request for {signer_name}")
        
        return JSONResponse({
            'success': True,
            'request_id': request_id,
            'signature_url': signature_request['signature_url']
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to create signature request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create signature request")

async def show_already_signed(signature_request: Dict[str, Any]):
    """Show page for already signed document"""
    
    return HTMLResponse(f"""
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
            <p>This document has already been signed by {signature_request['signer_name']}.</p>
            <p><strong>Signed:</strong> {datetime.fromisoformat(signature_request['signed_at']).strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Verification Code:</strong> {signature_request['verification_code']}</p>
        </div>
    </body>
    </html>
    """)

async def show_expired_request(signature_request: Dict[str, Any]):
    """Show page for expired signature request"""
    
    return HTMLResponse(f"""
    <html>
    <head>
        <title>Signature Request Expired</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; text-align: center; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⏰ Signature Request Expired</h1>
            <p>This signature request has expired.</p>
            <p><strong>Expired:</strong> {datetime.fromisoformat(signature_request['expires_at']).strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>Please contact Better Day Energy to request a new signature link.</p>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    print("🖊️ Starting Better Day Energy Signature Server...")
    print("🌐 Access at: http://localhost:8001")
    print("📝 Signature interface ready for Farely Barnhart's LOI")
    uvicorn.run(app, host="0.0.0.0", port=8001)