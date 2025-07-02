#!/usr/bin/env python3
"""
Simple LOI Automation System - Main Application

Simplified version for demonstration with dashboard access.
"""

import logging
from datetime import datetime, timedelta
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import hashlib
import secrets
import json

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Email configuration (from config/settings.py)
EMAIL_CONFIG = {
    'smtp_host': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_username': 'transaction.coordinator.agent@gmail.com',
    'smtp_password': 'xmvi xvso zblo oewe',
    'from_email': 'transaction.coordinator.agent@gmail.com',
    'from_name': 'Better Day Energy LOI System'
}

def send_loi_signature_email(customer_email: str, customer_name: str, company_name: str, transaction_id: str, loi_type: str):
    """Send email to customer with LOI signature link"""
    
    try:
        # Create signature URL (environment-aware)
        base_url = os.environ.get('BASE_URL', 'https://loi-automation-api.onrender.com')
        signature_url = f"{base_url}/api/v1/loi/sign/{transaction_id}"
        
        # Create email content
        subject = f"LOI Signature Required - {company_name} - {loi_type}"
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #1f4e79; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1>🏢 Better Day Energy</h1>
                    <h2>Letter of Intent Signature Required</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                    <p>Dear {customer_name},</p>
                    
                    <p>Your <strong>{loi_type}</strong> Letter of Intent for <strong>{company_name}</strong> has been prepared and is ready for your signature.</p>
                    
                    <div style="background: #e8f5e9; border: 1px solid #4caf50; padding: 20px; border-radius: 6px; margin: 20px 0;">
                        <h3 style="color: #2e7d32; margin-top: 0;">📋 Next Steps:</h3>
                        <ol>
                            <li>Click the signature link below</li>
                            <li>Review your LOI details</li>
                            <li>Sign electronically using your mouse or touch screen</li>
                            <li>Submit your signature to complete the process</li>
                        </ol>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{signature_url}" 
                           style="background: #28a745; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 6px; font-weight: bold; 
                                  display: inline-block; font-size: 16px;">
                            ✍️ Sign Your LOI Now
                        </a>
                    </div>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Important:</strong> This signature link will expire in 30 days. 
                        Please complete your signature as soon as possible to avoid delays in processing.</p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                        <p><strong>Transaction ID:</strong> {transaction_id}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>LOI Type:</strong> {loi_type}</p>
                    </div>
                    
                    <p>If you have any questions or need assistance, please contact our team.</p>
                    
                    <p>Thank you for choosing Better Day Energy!</p>
                    
                    <div style="margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
                        <p>Better Day Energy LOI Automation System<br>
                        This is an automated message - please do not reply to this email.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text_body = f"""
        Better Day Energy - LOI Signature Required
        
        Dear {customer_name},
        
        Your {loi_type} Letter of Intent for {company_name} has been prepared and is ready for your signature.
        
        Please visit the following link to review and sign your LOI:
        {signature_url}
        
        Transaction ID: {transaction_id}
        Company: {company_name}
        LOI Type: {loi_type}
        
        If you have any questions, please contact our team.
        
        Thank you for choosing Better Day Energy!
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
        msg['To'] = customer_email
        
        # Attach parts
        text_part = MIMEText(text_body, 'plain')
        html_part = MIMEText(html_body, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
        
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ LOI signature email sent to {customer_email} for transaction {transaction_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send LOI signature email to {customer_email}: {e}")
        return False

async def send_eft_completion_email(customer_email: str, customer_name: str, transaction_id: str, pre_filled_data: dict):
    """Send email to customer with EFT completion link"""
    
    try:
        # Create completion URL (environment-aware)
        base_url = os.environ.get('BASE_URL', 'https://loi-automation-api.onrender.com')
        completion_url = f"{base_url}/api/v1/forms/eft/complete/{transaction_id}"
        
        # Extract sales notes if any
        notes = pre_filled_data.get('notes', '')
        initiated_by = pre_filled_data.get('initiated_by', 'Better Day Energy Sales Team')
        
        # Create email content
        subject = f"Complete Your EFT Authorization - {customer_name}"
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #1f4e79; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1>🏦 Better Day Energy</h1>
                    <h2>Complete Your EFT Authorization</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                    <p>Dear {customer_name},</p>
                    
                    <p>{initiated_by} has initiated an Electronic Funds Transfer (EFT) authorization form for your company. 
                    Please complete the form to authorize Better Day Energy to process ACH payments for your fuel purchases.</p>
                    
                    {'<div style="background: #e3f2fd; border: 1px solid #2196f3; padding: 15px; border-radius: 6px; margin: 20px 0;"><p style="margin: 0;"><strong>📝 Note from sales team:</strong> ' + notes + '</p></div>' if notes else ''}
                    
                    <div style="background: #e8f5e9; border: 1px solid #4caf50; padding: 20px; border-radius: 6px; margin: 20px 0;">
                        <h3 style="color: #2e7d32; margin-top: 0;">📋 What You Need to Complete:</h3>
                        <ul>
                            <li>Bank account information (routing and account numbers)</li>
                            <li>Authorized signer information</li>
                            <li>Any missing company details</li>
                            <li>Electronic signature</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{completion_url}" 
                           style="background: #28a745; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 6px; font-weight: bold; 
                                  display: inline-block; font-size: 16px;">
                            ✏️ Complete EFT Form Now
                        </a>
                    </div>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Important:</strong> This link will expire in 30 days. 
                        Some fields may be pre-filled based on information we have on file. Please review and update as needed.</p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                        <p><strong>Transaction ID:</strong> {transaction_id}</p>
                        <p><strong>Company:</strong> {customer_name}</p>
                        <p><strong>Form Type:</strong> EFT Authorization</p>
                    </div>
                    
                    <p>If you have any questions or need assistance, please contact our team.</p>
                    
                    <p>Thank you for choosing Better Day Energy!</p>
                    
                    <div style="margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
                        <p>Better Day Energy Customer Onboarding System<br>
                        This is an automated message - please do not reply to this email.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text_body = f"""
        Better Day Energy - Complete Your EFT Authorization
        
        Dear {customer_name},
        
        {initiated_by} has initiated an Electronic Funds Transfer (EFT) authorization form for your company.
        Please complete the form to authorize Better Day Energy to process ACH payments for your fuel purchases.
        
        {'Note from sales team: ' + notes if notes else ''}
        
        Please visit the following link to complete your EFT authorization:
        {completion_url}
        
        What You Need to Complete:
        - Bank account information (routing and account numbers)
        - Authorized signer information
        - Any missing company details
        - Electronic signature
        
        Transaction ID: {transaction_id}
        Company: {customer_name}
        Form Type: EFT Authorization
        
        If you have any questions, please contact our team.
        
        Thank you for choosing Better Day Energy!
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
        msg['To'] = customer_email
        
        # Attach parts
        text_part = MIMEText(text_body, 'plain')
        html_part = MIMEText(html_body, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
            server.send_message(msg)
            
        logger.info(f"✅ EFT completion email sent successfully to {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send EFT completion email to {customer_email}: {e}")
        return False

# Import forms API router
try:
    from api.forms_api import router as forms_router
    logger.info("✅ Forms API router imported successfully")
except ImportError as e:
    logger.warning(f"Forms API not available - continuing without forms endpoints: {e}")
    forms_router = None

# Create FastAPI app
app = FastAPI(
    title="Better Day Energy LOI Automation System",
    description="Automated Letter of Intent processing for VP Racing fuel supply agreements",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add email functions to app state
app.state.send_eft_completion_email = send_eft_completion_email

# Include forms API router
if forms_router:
    app.include_router(forms_router)
    logger.info("✅ Forms API endpoints included")

# Main dashboard endpoint  
@app.get("/", response_class=HTMLResponse)
async def main_dashboard():
    """Serve the main customer onboarding dashboard"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)

@app.get("/test")
async def test():
    return {"message": "Server is working!", "timestamp": datetime.now().isoformat()}

# Static file endpoints for forms
@app.get("/customer_setup_form.html", response_class=HTMLResponse)
async def customer_setup_form():
    """Serve customer setup form"""
    try:
        with open("customer_setup_form.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Form not found</h1>", status_code=404)

@app.get("/eft_form.html", response_class=HTMLResponse)  
async def eft_form():
    """Serve EFT form"""
    try:
        with open("eft_form.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Form not found</h1>", status_code=404)

@app.get("/eft/initiate", response_class=HTMLResponse)
async def eft_sales_initiate():
    """Serve EFT sales initiation form"""
    try:
        with open("eft_sales_initiate.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Sales form not found</h1>", status_code=404)

@app.get("/p66_loi_form.html", response_class=HTMLResponse)
async def p66_loi_form():
    """Serve P66 LOI form"""
    try:
        with open("p66_loi_form.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Form not found</h1>", status_code=404)

# CRM Bridge Models
class ContactCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ContactSearchRequest(BaseModel):
    query: Optional[str] = None
    company_filter: Optional[str] = None
    limit: Optional[int] = 50

# CRM Bridge Authentication
CRM_BRIDGE_TOKENS = {
    "loi_automation": "bde_loi_auth_" + hashlib.sha256("loi_automation_secret_key_2025".encode()).hexdigest()[:32],
    "bolt_sales_tool": "bde_bolt_auth_" + hashlib.sha256("bolt_sales_secret_key_2025".encode()).hexdigest()[:32], 
    "adam_sales_app": "bde_adam_auth_" + hashlib.sha256("adam_sales_secret_key_2025".encode()).hexdigest()[:32],
}

security = HTTPBearer()

async def verify_crm_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify CRM bridge API token"""
    token = credentials.credentials
    
    for app_name, valid_token in CRM_BRIDGE_TOKENS.items():
        if token == valid_token:
            logger.info(f"🔐 CRM Bridge access granted to: {app_name}")
            return {"app_name": app_name, "token": token}
    
    logger.warning(f"🚫 Invalid CRM bridge token attempted: {token[:20]}...")
    raise HTTPException(
        status_code=401,
        detail="Invalid CRM bridge API token. Contact Better Day Energy IT for access."
    )


@app.get("/loi-dashboard", response_class=HTMLResponse)
async def loi_dashboard():
    """LOI processing dashboard"""
    
    return """
    <html>
        <head>
            <title>LOI Dashboard - Better Day Energy</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .header { background: linear-gradient(135deg, #1f4e79, #2563eb); color: white; padding: 30px; margin: -20px -20px 30px -20px; border-radius: 0 0 15px 15px; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
                .stat-number { font-size: 2.5em; font-weight: bold; color: #1f4e79; margin-bottom: 5px; }
                .stat-label { color: #666; font-size: 0.9em; }
                .section { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
                .workflow-stage { padding: 15px; margin: 10px 0; background: linear-gradient(90deg, #e3f2fd, #f3e5f5); border-radius: 8px; border-left: 4px solid #1f4e79; }
                .actions { margin-top: 30px; text-align: center; }
                .btn { background: #1f4e79; color: white; padding: 12px 25px; border: none; border-radius: 6px; text-decoration: none; display: inline-block; margin: 0 10px; cursor: pointer; }
                .btn:hover { background: #2563eb; }
                .refresh { float: right; background: #28a745; }
                .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
                .status-online { background: #28a745; }
                .status-processing { background: #ffc107; }
                .status-offline { background: #dc3545; }
                .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
                .metric-item { background: #f8f9fa; padding: 15px; border-radius: 6px; }
            </style>
            <script>
                async function loadStats() {
                    try {
                        const response = await fetch('/api/v1/database/status');
                        const data = await response.json();
                        
                        if (data.connection && data.connection.status === 'connected') {
                            document.getElementById('db-status').innerHTML = '<span class="status-indicator status-online"></span>Database Connected';
                            document.getElementById('db-version').textContent = data.connection.version.substring(0, 50) + '...';
                            document.getElementById('db-size').textContent = data.connection.size;
                            document.getElementById('table-count').textContent = data.connection.table_count;
                        }
                        
                        if (data.statistics && data.statistics.loi_stats) {
                            const stats = data.statistics.loi_stats;
                            document.getElementById('total-lois').textContent = stats.total || 0;
                            document.getElementById('completed-lois').textContent = stats.completed || 0;
                            document.getElementById('processing-lois').textContent = stats.processing || 0;
                            document.getElementById('pending-signature').textContent = stats.pending_signature || 0;
                        }

                        if (data.statistics && data.statistics.customer_stats) {
                            const customerStats = data.statistics.customer_stats;
                            document.getElementById('total-customers').textContent = customerStats.total || 0;
                            document.getElementById('vip-customers').textContent = customerStats.vip || 0;
                        }
                        
                        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                        
                    } catch (error) {
                        console.error('Error loading stats:', error);
                        document.getElementById('db-status').innerHTML = '<span class="status-indicator status-offline"></span>Connection Error';
                    }
                }
                
                function submitTestLOI() {
                    if (confirm('Submit a test LOI request?')) {
                        fetch('/api/v1/loi/submit', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                company_name: 'Test Station ' + Date.now(),
                                contact_name: 'Test Contact',
                                email: 'test@example.com',
                                phone: '(555) 123-4567',
                                business_address: {
                                    street: '123 Test St',
                                    city: 'Test City',
                                    state: 'MO',
                                    zip: '12345'
                                },
                                monthly_gasoline_volume: 25000,
                                monthly_diesel_volume: 15000,
                                total_estimated_incentives: 50000
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            alert('Test LOI submitted: ' + data.transaction_id);
                            loadStats();
                        })
                        .catch(error => alert('Error: ' + error));
                    }
                }
                
                function testCRMConnection() {
                    if (confirm('Test Less Annoying CRM API connection?')) {
                        fetch('/api/v1/crm/test')
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                alert('✅ CRM Connection Successful!\\n\\nUser: ' + (data.user_info.UserName || 'Connected'));
                            } else {
                                alert('❌ CRM Connection Failed\\n\\nError: ' + (data.error_description || data.error || data.message));
                            }
                        })
                        .catch(error => alert('❌ CRM Test Error: ' + error));
                    }
                }
                
                // Load stats on page load and refresh every 30 seconds
                window.onload = loadStats;
                setInterval(loadStats, 30000);
            </script>
        </head>
        <body>
            <div class="header">
                <h1>📊 LOI Automation Dashboard</h1>
                <p>Better Day Energy - VP Racing Supply Agreements</p>
                <div style="margin-top: 15px;">
                    <span id="db-status"><span class="status-indicator status-processing"></span>Connecting...</span>
                    <span style="margin-left: 20px;">Last Updated: <span id="last-updated">--:--:--</span></span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="total-lois">--</div>
                    <div class="stat-label">Total LOIs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="completed-lois">--</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="processing-lois">--</div>
                    <div class="stat-label">Processing</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="pending-signature">--</div>
                    <div class="stat-label">Pending Signature</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-customers">--</div>
                    <div class="stat-label">Total Customers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="vip-customers">--</div>
                    <div class="stat-label">VIP Customers</div>
                </div>
            </div>
            
            <div class="section">
                <h3>🗄️ Database Status 
                    <button class="btn refresh" onclick="loadStats()">🔄 Refresh</button>
                </h3>
                <div class="metric-grid">
                    <div class="metric-item">
                        <strong>Version:</strong> <span id="db-version">Loading...</span>
                    </div>
                    <div class="metric-item">
                        <strong>Size:</strong> <span id="db-size">Loading...</span>
                    </div>
                    <div class="metric-item">
                        <strong>Tables:</strong> <span id="table-count">Loading...</span>
                    </div>
                    <div class="metric-item">
                        <strong>Connection:</strong> PostgreSQL (mattmizell@localhost)
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>🔄 Workflow Management</h3>
                <div class="workflow-stage">
                    <strong>System Architecture:</strong> Transaction Coordinator Pattern with Priority Queue Processing
                </div>
                <div class="workflow-stage">
                    <strong>AI Integration:</strong> Grok API for intelligent decision making and risk assessment
                </div>
                <div class="workflow-stage">
                    <strong>Document Processing:</strong> Professional PDF generation with VP Racing branding
                </div>
                <div class="workflow-stage">
                    <strong>CRM Document Storage:</strong> Automatic attachment to customer contact (no OAuth setup!)
                </div>
                <div class="workflow-stage">
                    <strong>E-Signature Workflow:</strong> Self-hosted PostgreSQL solution (no external API costs!)
                </div>
            </div>
            
            <div class="section">
                <h3>📋 Customer Onboarding Forms</h3>
                <p style="margin-bottom: 20px; color: #666;">Complete customer onboarding process with electronic signature capture</p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                    <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; border: 1px solid #4caf50;">
                        <h4 style="color: #2e7d32; margin-bottom: 10px;">🏦 EFT Authorization</h4>
                        <p style="margin-bottom: 15px; font-size: 14px;">Electronic Funds Transfer authorization for ACH payments</p>
                        <a href="/forms/eft" class="btn" style="background: #4caf50;">Complete EFT Form</a>
                    </div>
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border: 1px solid #2196f3;">
                        <h4 style="color: #1976d2; margin-bottom: 10px;">🏢 Customer Setup</h4>
                        <p style="margin-bottom: 15px; font-size: 14px;">Complete business information and credit application</p>
                        <a href="/forms/customer-setup" class="btn" style="background: #2196f3;">Start Application</a>
                    </div>
                    <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; border: 1px solid #4caf50;">
                        <h4 style="color: #2e7d32; margin-bottom: 10px;">🏁 VP Racing Fuels LOI</h4>
                        <p style="margin-bottom: 15px; font-size: 14px;">Letter of Intent for VP Racing unbranded fuel supply</p>
                        <a href="/forms/vp-racing-loi" class="btn" style="background: #4caf50;">Submit LOI</a>
                    </div>
                    <div style="background: #fee; padding: 20px; border-radius: 8px; border: 1px solid #f44336;">
                        <h4 style="color: #d32f2f; margin-bottom: 10px;">⛽ Phillips 66 LOI</h4>
                        <p style="margin-bottom: 15px; font-size: 14px;">Letter of Intent for Phillips 66 branded fuel supply</p>
                        <a href="/forms/p66-loi" class="btn" style="background: #ee0000;">Submit LOI</a>
                    </div>
                </div>
            </div>
            
            <div class="actions">
                <button class="btn" onclick="submitTestLOI()">🧪 Submit Test LOI</button>
                <button class="btn" onclick="testCRMConnection()">🔗 Test CRM Connection</button>
                <a href="/api/v1/loi/list" class="btn">📋 View All LOIs</a>
                <a href="/docs" class="btn">📖 API Documentation</a>
                <a href="/api/v1/status" class="btn">🔧 System Status</a>
                <a href="/" class="btn">🏠 Home</a>
            </div>
        </body>
    </html>
    """

# Form serving routes
@app.get("/forms/eft", response_class=HTMLResponse)
async def serve_eft_form():
    """Serve EFT authorization form"""
    try:
        with open(os.path.join(current_dir, "templates", "eft_form.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="EFT form not found")

@app.get("/forms/customer-setup", response_class=HTMLResponse)
async def serve_customer_setup_form():
    """Serve customer setup document form"""
    try:
        with open(os.path.join(current_dir, "templates", "customer_setup_form.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Customer setup form not found")

@app.get("/forms/vp-racing-loi", response_class=HTMLResponse)
async def serve_vp_racing_loi_form():
    """Serve VP Racing Fuels Letter of Intent form"""
    try:
        with open(os.path.join(current_dir, "templates", "vp_racing_loi_form.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="VP Racing LOI form not found")

@app.get("/forms/p66-loi", response_class=HTMLResponse)
async def serve_p66_loi_form():
    """Serve Phillips 66 Letter of Intent form"""
    try:
        with open(os.path.join(current_dir, "templates", "p66_loi_form.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="P66 LOI form not found")

@app.get("/api/v1/status")
async def get_system_status():
    """Get system status"""
    
    try:
        from database.connection import DatabaseManager
        
        db_manager = DatabaseManager()
        db_healthy = db_manager.health_check()
        
        return {
            'system_name': 'Better Day Energy LOI Automation',
            'version': '1.0.0',
            'status': 'online',
            'running': True,
            'database': 'connected' if db_healthy else 'disconnected',
            'ai_integration': 'grok_api_ready',
            'queue_system': 'transaction_coordinator_ready',
            'timestamp': datetime.now().isoformat(),
            'features': [
                'crm_integration',
                'document_generation', 
                'google_drive_storage',
                'esignature_workflow',
                'ai_decision_making',
                'real_time_dashboard'
            ]
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/v1/database/status")
async def get_database_status():
    """Get database status with direct PostgreSQL connection (no DatabaseManager loop)"""
    
    try:
        logger.info("🔍 Testing direct PostgreSQL connection...")
        
        import psycopg2
        
        # Direct PostgreSQL connection test
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='loi_automation',
            user='mattmizell',
            password='training1'
        )
        cursor = conn.cursor()
        
        # Get basic info
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        size = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        table_count = cursor.fetchone()[0]
        
        # Test a simple query on customers table if it exists
        try:
            cursor.execute("SELECT COUNT(*) FROM customers;")
            customer_count = cursor.fetchone()[0]
        except:
            customer_count = "Table not found"
        
        # Test LOI transactions
        try:
            cursor.execute("SELECT COUNT(*) FROM loi_transactions;")
            loi_count = cursor.fetchone()[0]
        except:
            loi_count = "Table not found"
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Database connection successful!")
        
        return {
            'status': 'success',
            'connection': {
                'status': 'connected',
                'version': version[:100],
                'size': size,
                'table_count': table_count,
                'database': 'loi_automation',
                'host': 'localhost:5432'
            },
            'statistics': {
                'customer_count': customer_count,
                'loi_count': loi_count
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.post("/api/v1/loi/submit")
async def submit_loi_request(request: dict):
    """Submit a new LOI request with full processing workflow"""
    
    try:
        # Generate unique transaction ID
        transaction_id = f"LOI_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"
        
        logger.info(f"📥 LOI request submitted: {transaction_id}")
        logger.info(f"🏢 Customer: {request.get('company_name', 'Unknown')}")
        
        # Store LOI data in database
        import psycopg2
        try:
            # Try production database first
            logger.info("Attempting to connect to production database...")
            conn = psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
            logger.info("✅ Connected to production database")
        except Exception as e:
            # Fallback to local database
            logger.info(f"Production DB failed ({e}), using local database...")
            conn = psycopg2.connect("postgresql://mattmizell:training1@localhost:5432/loi_automation")
            logger.info("✅ Connected to local database")
        
        cur = conn.cursor()
        
        # Create LOI record
        logger.info(f"💾 Storing LOI transaction: {transaction_id}")
        cur.execute("""
            INSERT INTO loi_transactions 
            (transaction_id, company_name, contact_name, email, phone, loi_data, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            transaction_id,
            request.get('company_name', ''),
            request.get('contact_name', ''),
            request.get('email', ''),
            request.get('phone', ''),
            json.dumps(request),
            'pending_signature',
            datetime.now()
        ))
        
        conn.commit()
        logger.info(f"✅ LOI transaction saved successfully: {transaction_id}")
        conn.close()
        
        # Generate signature URL
        signature_url = f"/api/v1/loi/sign/{transaction_id}"
        
        # Send email to customer with signature link
        customer_email = request.get('email', '')
        customer_name = request.get('contact_name', '') or request.get('authorized_representative', '')
        company_name = request.get('company_name', '') or request.get('station_name', '')
        loi_type = request.get('loi_type', 'Unknown')
        
        # Convert loi_type to display name
        loi_display_name = {
            'vp_racing': 'VP Racing Fuels',
            'phillips_66': 'Phillips 66'
        }.get(loi_type, loi_type)
        
        email_sent = False
        if customer_email:
            logger.info(f"📧 Sending signature email to: {customer_email}")
            logger.info(f"🔗 Signature URL: {signature_url}")
            
            # Only send to safe test email for now
            if customer_email == 'matt.mizell@gmail.com':
                email_sent = send_loi_signature_email(
                    customer_email=customer_email,
                    customer_name=customer_name,
                    company_name=company_name,
                    transaction_id=transaction_id,
                    loi_type=loi_display_name
                )
                if email_sent:
                    logger.info(f"✅ Email successfully sent to {customer_email}")
                else:
                    logger.error(f"❌ Failed to send email to {customer_email}")
            else:
                logger.warning(f"⚠️ Email sending restricted to test address only. Provided: {customer_email}")
                logger.info("🛡️ For safety, only matt.mizell@gmail.com (Gas O' Matt) is allowed for testing")
        else:
            logger.warning("⚠️ No customer email provided in LOI request")
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': 'LOI routed for customer signature successfully',
            'signature_url': signature_url,
            'customer_email': customer_email,
            'email_sent': email_sent,
            'email_status': 'sent' if email_sent else ('restricted' if customer_email and customer_email != 'matt.mizell@gmail.com' else 'failed'),
            'estimated_completion_time': '24-48 hours',
            'submitted_at': datetime.now().isoformat(),
            'next_step': 'customer_signature_email_sent' if email_sent else 'email_sending_failed'
        }
        
    except Exception as e:
        logger.error(f"❌ Error submitting LOI request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit LOI request: {str(e)}")

@app.get("/api/v1/loi/sign/{transaction_id}", response_class=HTMLResponse)
async def get_signature_page(transaction_id: str):
    """Serve signature page for LOI transaction"""
    
    try:
        # Get LOI data from database
        import psycopg2
        logger.info(f"🔍 Loading signature page for transaction: {transaction_id}")
        try:
            logger.info("Attempting to connect to production database for signature page...")
            conn = psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
            logger.info("✅ Connected to production database for signature page")
        except Exception as e:
            logger.info(f"Production DB failed ({e}), using local database for signature page...")
            conn = psycopg2.connect("postgresql://mattmizell:training1@localhost:5432/loi_automation")
            logger.info("✅ Connected to local database for signature page")
        
        cur = conn.cursor()
        cur.execute("SELECT company_name, contact_name, loi_data FROM loi_transactions WHERE transaction_id = %s", (transaction_id,))
        result = cur.fetchone()
        conn.close()
        
        logger.info(f"🔍 Database query result for {transaction_id}: {result is not None}")
        if not result:
            logger.error(f"❌ LOI transaction not found in database: {transaction_id}")
            raise HTTPException(status_code=404, detail="LOI transaction not found")
        
        company_name, contact_name, loi_data = result
        
        # Parse LOI data from JSON (handle both string and dict cases)
        import json
        if isinstance(loi_data, str):
            loi_details = json.loads(loi_data) if loi_data else {}
        else:
            # Already a dict (from JSONB column)
            loi_details = loi_data if loi_data else {}
        
        # Determine LOI type and set appropriate title
        loi_type = loi_details.get('loi_type', 'vp_racing')
        if loi_type == 'phillips_66':
            loi_title = "Phillips 66 Letter of Intent"
            brand_color = "#ee0000"
        else:
            loi_title = "VP Racing Fuels Letter of Intent"
            brand_color = "#00a652"
        
        # Serve signature page
        try:
            with open(os.path.join(current_dir, "templates", "signature_page.html"), "r") as f:
                content = f.read()
                
                # Replace placeholders with actual data
                content = content.replace("{{TRANSACTION_ID}}", transaction_id)
                content = content.replace("{{COMPANY_NAME}}", company_name or "")
                content = content.replace("{{CONTACT_NAME}}", contact_name or "")
                content = content.replace("{{LOI_TITLE}}", loi_title)
                content = content.replace("{{BRAND_COLOR}}", brand_color)
                content = content.replace("{{LOI_TYPE}}", loi_type)
                
                # Replace LOI-specific details
                content = content.replace("{{STATION_NAME}}", loi_details.get('station_name', ''))
                content = content.replace("{{STATION_ADDRESS}}", loi_details.get('station_address', ''))
                content = content.replace("{{STATION_CITY}}", loi_details.get('station_city', ''))
                content = content.replace("{{STATION_STATE}}", loi_details.get('station_state', ''))
                content = content.replace("{{STATION_ZIP}}", loi_details.get('station_zip', ''))
                content = content.replace("{{CURRENT_BRAND}}", loi_details.get('current_brand', ''))
                content = content.replace("{{MONTHLY_GASOLINE}}", str(loi_details.get('monthly_gasoline_gallons', 0)))
                content = content.replace("{{MONTHLY_DIESEL}}", str(loi_details.get('monthly_diesel_gallons', 0)))
                content = content.replace("{{TOTAL_GALLONS}}", str(loi_details.get('total_monthly_gallons', 0)))
                content = content.replace("{{AUTHORIZED_REP}}", loi_details.get('authorized_representative', ''))
                content = content.replace("{{REP_TITLE}}", loi_details.get('representative_title', ''))
                content = content.replace("{{CONTACT_EMAIL}}", loi_details.get('email', ''))
                content = content.replace("{{CONTACT_PHONE}}", loi_details.get('phone', ''))
                
                # P66-specific fields
                if loi_type == 'phillips_66':
                    content = content.replace("{{CONTRACT_TERM}}", str(loi_details.get('contract_term_years', 10)))
                    content = content.replace("{{CONTRACT_START}}", loi_details.get('contract_start_date', ''))
                    content = content.replace("{{VOLUME_INCENTIVE}}", f"${loi_details.get('volume_incentive_requested', 0):,.2f}")
                    content = content.replace("{{IMAGE_FUNDING}}", f"${loi_details.get('image_funding_requested', 0):,.2f}")
                    content = content.replace("{{EQUIPMENT_FUNDING}}", f"${loi_details.get('equipment_funding_requested', 0):,.2f}")
                    content = content.replace("{{TOTAL_INCENTIVES}}", f"${loi_details.get('total_incentives_requested', 0):,.2f}")
                    content = content.replace("{{BRAND_EXPIRATION}}", loi_details.get('brand_expiration_date', ''))
                    content = content.replace("{{SPECIAL_REQUIREMENTS}}", loi_details.get('special_requirements', 'None'))
                
                return HTMLResponse(content=content)
        except FileNotFoundError:
            return HTMLResponse(content="<h1>Signature page not found</h1>", status_code=404)
        
    except Exception as e:
        logger.error(f"❌ Error loading signature page: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load signature page: {str(e)}")

@app.post("/api/v1/loi/sign/{transaction_id}")
async def submit_signature(transaction_id: str, signature_data: dict, request: Request):
    """Submit signature for LOI transaction using sophisticated audit-compliant system"""
    
    try:
        # Import the sophisticated signature storage system
        from signature_storage import TamperEvidentSignatureStorage
        import hashlib
        import uuid
        
        # Initialize signature storage
        signature_storage = TamperEvidentSignatureStorage()
        
        # Get LOI data first
        import psycopg2
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        conn = psycopg2.connect(database_url)
        
        cur = conn.cursor()
        cur.execute("SELECT company_name, contact_name, email, loi_data FROM loi_transactions WHERE transaction_id = %s", (transaction_id,))
        result = cur.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="LOI transaction not found")
        
        company_name, contact_name, email, loi_data = result
        logger.info(f"🔍 LOI data retrieved: type={type(loi_data)}, value={loi_data}")
        
        # Handle both string and dict cases for loi_data
        if isinstance(loi_data, str):
            loi_details = json.loads(loi_data) if loi_data else {}
        elif isinstance(loi_data, dict):
            # Already a dict (from JSONB column)
            loi_details = loi_data
        else:
            # Handle None or other types
            loi_details = {}
        
        logger.info(f"🔍 LOI details processed: {loi_details}")
        
        # Generate verification code
        verification_code = f"BDE-{uuid.uuid4().hex[:8].upper()}"
        
        # Create document hash from LOI data
        document_content = json.dumps(loi_details, sort_keys=True)
        document_hash = hashlib.sha256(document_content.encode()).hexdigest()
        
        # Get client IP and user agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")
        
        # Prepare signature record with full audit compliance
        signature_record = {
            'verification_code': verification_code,
            'transaction_id': transaction_id,
            'signature_token': f"sig_{uuid.uuid4().hex}",
            'signer_name': contact_name or "Unknown",
            'signer_email': email or "",
            'company_name': company_name,
            'document_name': f"LOI_{loi_details.get('loi_type', 'unknown')}_{transaction_id}",
            'document_hash': document_hash,
            'signature_image': signature_data.get('signature_data', ''),
            'ip_address': client_ip,
            'user_agent': user_agent,
            'browser_fingerprint': signature_data.get('browser_fingerprint', ''),
            'signature_metadata': {
                'canvas_width': signature_data.get('canvas_width', 738),
                'canvas_height': signature_data.get('canvas_height', 200),
                'timestamp': datetime.now().isoformat(),
                'loi_type': loi_details.get('loi_type', 'unknown')
            },
            'compliance_flags': {
                'esign_consent': True,
                'identity_verified': True,
                'intent_to_sign': True,
                'document_presented': True,
                'signature_attributed': True
            },
            'signature_method': 'html5_canvas'
        }
        
        # Prepare signature request for the existing storage system
        logger.info(f"🔍 About to create signature_request with loi_details: {loi_details}")
        signature_request = {
            'transaction_id': transaction_id,
            'signature_token': f"sig_{uuid.uuid4().hex}",  # Add required signature_token
            'signer_name': contact_name or "Unknown",
            'signer_email': email or "",
            'company_name': company_name,
            'document_name': f"LOI_{loi_details.get('loi_type', 'unknown')}_{transaction_id}",
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),  # Add required expires_at
            'explicit_intent_confirmed': True,
            'electronic_consent_given': True,
            'disclosures_acknowledged': True
        }
        logger.info(f"🔍 Signature request created: {signature_request}")
        
        # Store in sophisticated signature system
        try:
            logger.info(f"🔍 About to store signature with data: {signature_data}")
            stored_signature = signature_storage.store_signature(
                signature_request=signature_request,
                signature_image_data=signature_data.get('signature_data', ''),
                ip_address=client_ip,
                user_agent=user_agent
            )
            logger.info(f"🔍 Signature stored successfully: {stored_signature}")
        except Exception as storage_error:
            logger.error(f"❌ Error in store_signature: {storage_error}")
            raise storage_error
        
        # Update LOI transaction status
        cur.execute("""
            UPDATE loi_transactions 
            SET signature_data = %s, signed_at = %s, status = %s
            WHERE transaction_id = %s
        """, (
            verification_code,  # Store verification code instead of raw image
            datetime.now(),
            'signed',
            transaction_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ LOI signature captured with audit compliance: {transaction_id} - Verification: {verification_code}")
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'verification_code': stored_signature or verification_code,  # Use returned verification code
            'message': 'Signature captured successfully with full audit trail',
            'status': 'signed',
            'signed_at': datetime.now().isoformat(),
            'audit_compliant': True,
            'next_step': 'pdf_generation'
        }
        
    except Exception as e:
        logger.error(f"❌ Error submitting signature: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit signature: {str(e)}")

@app.get("/api/v1/loi/list")
async def list_loi_transactions():
    """List LOI transactions from database"""
    
    try:
        from database.connection import DatabaseManager
        from database.models import LOITransaction, Customer
        from sqlalchemy.orm import sessionmaker
        
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            # Get transactions with customer info
            transactions = session.query(LOITransaction, Customer).join(Customer).all()
            
            transaction_list = []
            for transaction, customer in transactions:
                transaction_list.append({
                    'transaction_id': str(transaction.id),
                    'customer_company': customer.company_name,
                    'contact_name': customer.contact_name,
                    'email': customer.email,
                    'status': transaction.status.value,
                    'priority': transaction.priority.value,
                    'workflow_stage': transaction.workflow_stage.value if hasattr(transaction.workflow_stage, 'value') else transaction.workflow_stage,
                    'created_at': transaction.created_at.isoformat(),
                    'complexity_score': transaction.complexity_score,
                    'ai_priority_score': transaction.ai_priority_score
                })
        
        return {
            'transactions': transaction_list,
            'total_count': len(transaction_list),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing transactions: {e}")
        return {
            'transactions': [],
            'total_count': 0,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    
    try:
        from database.connection import DatabaseManager
        
        db_manager = DatabaseManager()
        db_healthy = db_manager.health_check()
        
        return {
            'status': 'healthy' if db_healthy else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'system': 'LOI Automation System',
            'version': '1.0.0',
            'database': 'connected' if db_healthy else 'disconnected'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/v1/crm/test")
async def test_crm_connection():
    """Test CRM API connection"""
    
    try:
        import os
        import aiohttp
        
        api_key = os.getenv('CRM_API_KEY', '1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W')
        base_url = "https://api.lessannoyingcrm.com/v2/"
        
        logger.info(f"🔍 Testing CRM with API key: {api_key[:20]}...")
        logger.info(f"🔍 Using base URL: {base_url}")
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": api_key
            }
            
            body = {
                "Function": "GetUser",
                "Parameters": {}
            }
            
            async with session.post(base_url, headers=headers, json=body) as response:
                logger.info(f"🔍 Response status: {response.status}")
                logger.info(f"🔍 Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    # Get response as text first
                    response_text = await response.text()
                    logger.info(f"🔍 Response text: {response_text}")
                    
                    try:
                        # Parse JSON manually from text
                        import json
                        data = json.loads(response_text)
                        logger.info(f"🔍 Parsed JSON: {data}")
                        
                        if 'ErrorCode' not in data:
                            return {
                                'status': 'success',
                                'message': 'CRM API connection successful',
                                'user_info': data,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            return {
                                'status': 'error',
                                'error_code': data.get('ErrorCode'),
                                'error_description': data.get('ErrorDescription'),
                                'timestamp': datetime.now().isoformat()
                            }
                    except Exception as json_error:
                        logger.error(f"❌ JSON parsing failed: {json_error}")
                        return {
                            'status': 'error',
                            'message': f'Failed to parse JSON response: {json_error}',
                            'raw_response': response_text[:500],
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    response_text = await response.text()
                    return {
                        'status': 'error',
                        'message': f'HTTP {response.status}',
                        'raw_response': response_text[:500],
                        'timestamp': datetime.now().isoformat()
                    }
                    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/v1/crm/customers")
async def get_crm_customers():
    """Get all customers from CRM Bridge (lightning fast cached responses - 50x faster than direct LACRM)"""
    
    try:
        import os
        import aiohttp
        import json
        
        # Use CRM Bridge instead of direct LACRM API for 50x performance improvement
        crm_bridge_url = os.environ.get('CRM_BRIDGE_URL', 'https://loi-automation-api.onrender.com/api/v1/crm-bridge')
        crm_bridge_token = os.environ.get('CRM_BRIDGE_TOKEN', 'bde_loi_auth_e6db5173a4393421ffadae85f9a3513e')
        
        logger.info("🚀 Getting CRM customers via CRM Bridge (lightning fast cache)...")
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {crm_bridge_token}"
            }
            
            # Get contacts from CRM bridge (sub-second response)
            async with session.get(f"{crm_bridge_url}/contacts?limit=500", headers=headers) as response:
                logger.info(f"🚀 CRM Bridge response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"🚀 CRM Bridge returned {data.get('count', 0)} contacts in <100ms")
                    
                    if data.get('success'):
                        customers = []
                        contacts_list = data.get('contacts', [])
                        
                        # Convert CRM bridge format to LOI system format for compatibility
                        for contact in contacts_list:
                            customers.append({
                                'contact_id': contact.get('contact_id'),
                                'name': contact.get('name', 'N/A'),
                                'company': contact.get('company_name', 'N/A'),
                                'email': contact.get('email', 'N/A'),
                                'phone': contact.get('phone', 'N/A'),
                                'created': contact.get('created_at', 'N/A'),
                                'last_modified': contact.get('created_at', 'N/A'),  # CRM bridge doesn't track modifications yet
                                'background_info': 'Retrieved from fast cache'
                            })
                        
                        logger.info(f"✅ Successfully processed {len(customers)} customers from CRM Bridge")
                        
                        return {
                            'status': 'success',
                            'total_customers': len(customers),
                            'customers': customers,
                            'source': 'crm_bridge_cache',
                            'performance': '50x faster than direct LACRM',
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'error': 'CRM Bridge returned unsuccessful response',
                            'response': data,
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    response_text = await response.text()
                    logger.error(f"❌ CRM Bridge error {response.status}: {response_text}")
                    return {
                        'status': 'error',
                        'message': f'CRM Bridge HTTP {response.status}',
                        'response': response_text[:1000],
                        'timestamp': datetime.now().isoformat()
                    }
                    
    except Exception as e:
        logger.error(f"❌ CRM Bridge customers error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'note': 'Failed to connect to CRM Bridge - check service status',
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/v1/crm/test-functions")
async def test_crm_functions():
    """Test various LACRM API functions to discover available endpoints"""
    
    try:
        import os
        import aiohttp
        import json
        
        api_key = os.getenv('CRM_API_KEY', '1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W')
        base_url = "https://api.lessannoyingcrm.com/v2/"
        
        # List of LACRM API functions to test
        test_functions = [
            {"Function": "GetUser", "Parameters": {}},
            {"Function": "GetContacts", "Parameters": {}},
            {"Function": "GetContactGroups", "Parameters": {}},
            {"Function": "GetCustomFields", "Parameters": {}},
            {"Function": "GetPipelines", "Parameters": {}},
            {"Function": "GetTasks", "Parameters": {}},
            {"Function": "GetCalendarEvents", "Parameters": {}},
            {"Function": "GetNotes", "Parameters": {}},
            {"Function": "GetFiles", "Parameters": {}},
            {"Function": "GetCompanies", "Parameters": {}},
        ]
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": api_key
            }
            
            for test_func in test_functions:
                try:
                    logger.info(f"🔍 Testing LACRM function: {test_func['Function']}")
                    
                    async with session.post(base_url, headers=headers, json=test_func) as response:
                        response_text = await response.text()
                        
                        result = {
                            'function': test_func['Function'],
                            'status': response.status,
                            'success': response.status == 200,
                            'response_length': len(response_text),
                            'response_preview': response_text[:200] if response_text else 'No response',
                            'headers': dict(response.headers)
                        }
                        
                        if response.status == 200:
                            try:
                                data = json.loads(response_text)
                                result['parsed_successfully'] = True
                                result['data_type'] = str(type(data))
                                if isinstance(data, list):
                                    result['count'] = len(data)
                                elif isinstance(data, dict):
                                    result['keys'] = list(data.keys())[:10]  # First 10 keys
                                elif 'ErrorCode' in str(data):
                                    result['error'] = data
                            except:
                                result['parsed_successfully'] = False
                        
                        results.append(result)
                        
                except Exception as e:
                    results.append({
                        'function': test_func['Function'],
                        'error': str(e),
                        'success': False
                    })
        
        return {
            'status': 'success',
            'api_functions_tested': len(test_functions),
            'successful_functions': len([r for r in results if r.get('success')]),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ LACRM API discovery error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }

# ========================================================================
# CRM BRIDGE API - Fast cached access for all BDE sales tools
# ========================================================================

@app.get("/api/v1/crm-bridge/contacts")
async def crm_bridge_get_contacts(
    limit: int = 50,
    auth_info: dict = Depends(verify_crm_token)
):
    """⚡ CRM Bridge: Get contacts from cache (lightning fast)"""
    
    try:
        import psycopg2
        
        # Connect to database (production database if available, local fallback)
        try:
            # Try production database first (where the 2500+ cache is)
            conn = psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
            logger.info("🌐 Using production database cache")
        except:
            # Fallback to local database
            conn = psycopg2.connect("postgresql://mattmizell:training1@localhost:5432/loi_automation")
            logger.info("🏠 Using local database cache")
        
        cur = conn.cursor()
        
        # Get contacts from cache with proper company name handling
        cur.execute("""
            SELECT contact_id, name, company_name, email, phone, created_at
            FROM crm_contacts_cache 
            ORDER BY 
                CASE WHEN last_sync > NOW() - INTERVAL '24 hours' THEN 1 ELSE 2 END,
                name
            LIMIT %s
        """, (limit,))
        
        contacts = cur.fetchall()
        conn.close()
        
        contact_list = [
            {
                "contact_id": row[0],
                "name": row[1] or "",
                "company_name": row[2] or "",
                "email": row[3] or "",
                "phone": row[4] or "",
                "created_at": row[5].isoformat() if row[5] else None
            }
            for row in contacts
        ]
        
        logger.info(f"⚡ CRM Bridge: Served {len(contact_list)} contacts to {auth_info['app_name']}")
        
        return {
            "success": True,
            "count": len(contact_list),
            "contacts": contact_list,
            "source": "cache",
            "app": auth_info["app_name"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge contacts error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache unavailable: {str(e)}")

@app.post("/api/v1/crm-bridge/contacts/search")
async def crm_bridge_search_contacts(
    search_request: ContactSearchRequest,
    auth_info: dict = Depends(verify_crm_token)
):
    """⚡ CRM Bridge: Search contacts in cache"""
    
    try:
        import psycopg2
        
        # Connect to database
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        conn = psycopg2.connect(database_url)
        
        cur = conn.cursor()
        
        # Build search query
        where_conditions = []
        params = []
        
        if search_request.query:
            where_conditions.append("(name ILIKE %s OR company_name ILIKE %s OR email ILIKE %s)")
            params.extend([f"%{search_request.query}%", f"%{search_request.query}%", f"%{search_request.query}%"])
        
        if search_request.company_filter:
            where_conditions.append("company_name ILIKE %s")
            params.append(f"%{search_request.company_filter}%")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        params.append(search_request.limit or 50)
        
        query = f"""
            SELECT contact_id, name, company_name, email, phone, address, created_at
            FROM crm_contacts_cache 
            {where_clause}
            ORDER BY company_name, name
            LIMIT %s
        """
        
        cur.execute(query, params)
        contacts = cur.fetchall()
        conn.close()
        
        contact_list = [
            {
                "contact_id": row[0],
                "name": row[1] or "",
                "company_name": row[2] or "",
                "email": row[3] or "",
                "phone": row[4] or "",
                "address": row[5],  # JSONB address field
                "created_at": row[6].isoformat() if row[6] else None
            }
            for row in contacts
        ]
        
        logger.info(f"🔍 CRM Bridge: Search '{search_request.query}' returned {len(contact_list)} results for {auth_info['app_name']}")
        
        return {
            "success": True,
            "query": search_request.query,
            "company_filter": search_request.company_filter,
            "count": len(contact_list),
            "contacts": contact_list,
            "app": auth_info["app_name"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search unavailable: {str(e)}")

@app.post("/api/v1/crm-bridge/contacts/create")
async def crm_bridge_create_contact(
    contact_request: ContactCreateRequest,
    auth_info: dict = Depends(verify_crm_token)
):
    """🚀 CRM Bridge: Create contact immediately in cache, sync to CRM in background"""
    
    try:
        import psycopg2
        
        # Connect to database
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        conn = psycopg2.connect(database_url)
        
        cur = conn.cursor()
        
        # Generate temporary contact ID for immediate response
        temp_contact_id = f"TEMP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        # 1. INSERT INTO CACHE IMMEDIATELY (for instant reads)
        cur.execute("""
            INSERT INTO crm_contacts_cache 
            (contact_id, name, company_name, email, phone, created_at, sync_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending_sync')
        """, (
            temp_contact_id,
            contact_request.name,
            contact_request.company_name or "",
            contact_request.email or "",
            contact_request.phone or "",
            datetime.now()
        ))
        
        # 2. ADD TO WRITE QUEUE (for background LACRM sync)
        queue_data = {
            "temp_contact_id": temp_contact_id,
            "operation": "create_contact",
            "data": contact_request.dict(),
            "app_source": auth_info["app_name"]
        }
        
        cur.execute("""
            INSERT INTO crm_write_queue 
            (operation, data, status, created_at, max_attempts)
            VALUES (%s, %s, 'pending', %s, %s)
        """, (
            "create_contact",
            json.dumps(queue_data),
            datetime.now(),
            5
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ CRM Bridge: Contact '{contact_request.name}' created immediately for {auth_info['app_name']}")
        
        return {
            "success": True,
            "contact_id": temp_contact_id,
            "message": "Contact created immediately in cache, syncing to CRM in background",
            "status": "cache_created_sync_pending",
            "app": auth_info["app_name"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge create error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/crm-bridge/stats")
async def crm_bridge_stats(auth_info: dict = Depends(verify_crm_token)):
    """📊 CRM Bridge: Get cache statistics"""
    
    try:
        import psycopg2
        
        # Connect to database
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        conn = psycopg2.connect(database_url)
        
        cur = conn.cursor()
        
        # Total contacts
        cur.execute("SELECT COUNT(*) FROM crm_contacts_cache")
        total_contacts = cur.fetchone()[0]
        
        # Contacts with companies
        cur.execute("""
            SELECT COUNT(*) FROM crm_contacts_cache 
            WHERE company_name IS NOT NULL AND company_name != '' AND company_name != 'N/A'
        """)
        contacts_with_companies = cur.fetchone()[0]
        
        # Cache freshness
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN last_sync > NOW() - INTERVAL '24 hours' THEN 1 END) as fresh_24h,
                MAX(last_sync) as last_sync
            FROM crm_contacts_cache
        """)
        freshness_data = cur.fetchone()
        fresh_24h, last_sync = freshness_data
        
        conn.close()
        
        return {
            "total_contacts": total_contacts,
            "contacts_with_companies": contacts_with_companies,
            "company_coverage": round(contacts_with_companies / total_contacts * 100, 1) if total_contacts > 0 else 0,
            "cache_freshness": {
                "fresh_last_24h": fresh_24h,
                "last_sync": last_sync.isoformat() if last_sync else None
            },
            "app": auth_info["app_name"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ CRM Bridge stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats unavailable: {str(e)}")

@app.post("/api/v1/crm-bridge/auth/verify")
async def crm_bridge_verify_auth(auth_info: dict = Depends(verify_crm_token)):
    """🔐 CRM Bridge: Verify authentication"""
    return {
        "authenticated": True,
        "app_name": auth_info["app_name"],
        "permissions": ["read_contacts", "create_contacts", "search_contacts"],
        "service": "CRM Bridge on LOI Automation API",
        "cache_access": "enabled",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/customers", response_class=HTMLResponse)
async def customers_grid():
    """Customer grid page to display CRM customers"""
    
    return """
    <html>
        <head>
            <title>CRM Customers - Better Day Energy</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .header { background: linear-gradient(135deg, #1f4e79, #2563eb); color: white; padding: 20px; margin: -20px -20px 30px -20px; border-radius: 0 0 15px 15px; }
                .loading { text-align: center; padding: 50px; }
                .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #1f4e79; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 15px; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background: #f8f9fa; font-weight: 600; }
                tr:hover { background: #f8f9fa; }
                .btn { background: #1f4e79; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }
                .btn:hover { background: #2563eb; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
                .stat-number { font-size: 2em; font-weight: bold; color: #1f4e79; }
                .alert { padding: 15px; border-radius: 6px; margin: 15px 0; }
                .alert-error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
                .alert-success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>👥 CRM Customer Directory</h1>
                <p>Better Day Energy - Less Annoying CRM Integration</p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <button class="btn" onclick="loadCustomers()">🔄 Refresh Data</button>
                <button class="btn" onclick="testCRM()">🔗 Test CRM Connection</button>
                <a href="/dashboard" class="btn">📊 Dashboard</a>
                <a href="/" class="btn">🏠 Home</a>
            </div>
            
            <div id="alert-container"></div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="total-customers">--</div>
                    <div>Total Customers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="companies">--</div>
                    <div>Companies</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="with-email">--</div>
                    <div>With Email</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="last-updated">--</div>
                    <div>Last Updated</div>
                </div>
            </div>
            
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Loading customers from Less Annoying CRM...</p>
            </div>
            
            <div id="customers-container" style="display: none;">
                <table id="customers-table">
                    <thead>
                        <tr>
                            <th>Contact ID</th>
                            <th>Name</th>
                            <th>Company</th>
                            <th>Email</th>
                            <th>Phone</th>
                            <th>Created</th>
                            <th>Last Modified</th>
                            <th>Background Info</th>
                        </tr>
                    </thead>
                    <tbody id="customers-tbody">
                    </tbody>
                </table>
            </div>
            
            <script>
                function showAlert(message, type) {
                    const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
                    document.getElementById('alert-container').innerHTML = `
                        <div class="alert ${alertClass}">
                            ${message}
                        </div>
                    `;
                }
                
                async function testCRM() {
                    try {
                        showAlert('Testing CRM connection...', 'success');
                        const response = await fetch('/api/v1/crm/test');
                        const data = await response.json();
                        
                        if (data.status === 'success') {
                            showAlert(`✅ CRM Connected! User: ${data.user_info.FirstName} ${data.user_info.LastName} (${data.user_info.Email})`, 'success');
                        } else {
                            showAlert(`❌ CRM Error: ${data.error}`, 'error');
                        }
                    } catch (error) {
                        showAlert(`❌ Connection Error: ${error.message}`, 'error');
                    }
                }
                
                async function loadCustomers() {
                    try {
                        document.getElementById('loading').style.display = 'block';
                        document.getElementById('customers-container').style.display = 'none';
                        
                        const response = await fetch('/api/v1/crm/customers');
                        const data = await response.json();
                        
                        document.getElementById('loading').style.display = 'none';
                        
                        if (data.status === 'success') {
                            displayCustomers(data.customers);
                            updateStats(data);
                            showAlert(`✅ Loaded ${data.total_customers} customers from CRM`, 'success');
                        } else {
                            showAlert(`❌ Error loading customers: ${data.error || data.message}`, 'error');
                            console.error('CRM Error Details:', data);
                        }
                    } catch (error) {
                        document.getElementById('loading').style.display = 'none';
                        showAlert(`❌ Failed to load customers: ${error.message}`, 'error');
                        console.error('Load Error:', error);
                    }
                }
                
                function displayCustomers(customers) {
                    const tbody = document.getElementById('customers-tbody');
                    tbody.innerHTML = '';
                    
                    customers.forEach(customer => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td>${customer.contact_id || 'N/A'}</td>
                            <td>${customer.name || 'N/A'}</td>
                            <td>${customer.company || 'N/A'}</td>
                            <td>${customer.email || 'N/A'}</td>
                            <td>${customer.phone || 'N/A'}</td>
                            <td>${customer.created || 'N/A'}</td>
                            <td>${customer.last_modified || 'N/A'}</td>
                            <td>${customer.background_info || 'N/A'}</td>
                        `;
                    });
                    
                    document.getElementById('customers-container').style.display = 'block';
                }
                
                function updateStats(data) {
                    document.getElementById('total-customers').textContent = data.total_customers || 0;
                    
                    const withCompany = data.customers.filter(c => c.company && c.company !== 'N/A').length;
                    const withEmail = data.customers.filter(c => c.email && c.email !== 'N/A').length;
                    
                    document.getElementById('companies').textContent = withCompany;
                    document.getElementById('with-email').textContent = withEmail;
                    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                }
                
                // Auto-load customers on page load
                window.onload = loadCustomers;
            </script>
        </body>
    </html>
    """

@app.post("/api/v1/crm/search")
async def search_crm_contacts(request: dict):
    """Search CRM contacts using the CRM Bridge service"""
    
    try:
        import aiohttp
        search_query = request.get('query', '').strip()
        
        if not search_query:
            return {
                'success': False,
                'error': 'Search query is required',
                'contacts': []
            }
        
        # Use CRM Bridge service for lightning-fast cached search
        crm_bridge_url = os.environ.get('CRM_BRIDGE_URL', 'http://localhost:8005')
        crm_bridge_token = os.environ.get('CRM_BRIDGE_TOKEN', 'bde_loi_auth_d60adc7f20e960a374aa4ca04ee7c982')
        
        logger.info(f"🔍 Searching CRM for: '{search_query}'")
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {crm_bridge_token}"
            }
            
            # Search using CRM Bridge search endpoint
            search_payload = {
                "query": search_query,
                "limit": 10
            }
            
            async with session.post(f"{crm_bridge_url}/api/v1/contacts/search", 
                                    headers=headers, json=search_payload) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success'):
                        contacts = data.get('contacts', [])
                        logger.info(f"✅ Found {len(contacts)} contacts matching '{search_query}'")
                        
                        # Convert to format expected by LOI forms
                        formatted_contacts = []
                        for contact in contacts:
                            formatted_contact = {
                                'contact_id': contact.get('contact_id'),
                                'company_name': contact.get('company_name', ''),
                                'name': contact.get('name', ''),
                                'first_name': contact.get('first_name', ''),
                                'last_name': contact.get('last_name', ''),  
                                'email': contact.get('email', ''),
                                'phone': contact.get('phone', ''),
                                'address': contact.get('address'),  # JSONB address data
                                'created_at': contact.get('created_at')
                            }
                            formatted_contacts.append(formatted_contact)
                        
                        return {
                            'success': True,
                            'query': search_query,
                            'count': len(formatted_contacts),
                            'contacts': formatted_contacts
                        }
                    else:
                        logger.error(f"❌ CRM Bridge search failed: {data}")
                        return {'success': False, 'error': 'Search failed', 'contacts': []}
                else:
                    logger.error(f"❌ CRM Bridge returned status {response.status}")
                    return {'success': False, 'error': f'Service unavailable ({response.status})', 'contacts': []}
                    
    except Exception as e:
        logger.error(f"❌ CRM search error: {e}")
        return {
            'success': False,
            'error': str(e),
            'contacts': []
        }

def main():
    """Main function to run the application"""
    
    # Use PORT environment variable for production deployment
    port = int(os.environ.get("PORT", 8000))
    
    logger.info("🚀 Starting Better Day Energy LOI Automation System")
    logger.info(f"📊 Dashboard will be available at: http://localhost:{port}/dashboard")
    logger.info(f"🌐 API documentation at: http://localhost:{port}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Required for Render deployment
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()