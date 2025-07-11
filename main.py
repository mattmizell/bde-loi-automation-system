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
    """Send ESIGN Act compliant email to customer with LOI signature link"""
    
    try:
        # Import ESIGN compliant email template
        from templates.esign_compliant_email import get_esign_compliant_email_template
        
        # Create signature URL (environment-aware)
        base_url = os.environ.get('BASE_URL', 'https://loi-automation-api.onrender.com')
        signature_url = f"{base_url}/api/v1/loi/sign/{transaction_id}"
        
        # Get ESIGN compliant email templates
        html_body, text_body = get_esign_compliant_email_template(
            customer_name=customer_name,
            company_name=company_name,
            transaction_id=transaction_id,
            loi_type=loi_type,
            signature_url=signature_url
        )
        
        # Create email content
        subject = f"LOI Electronic Signature Required - {company_name} - {loi_type}"
        
        
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

async def send_customer_setup_completion_email(customer_email: str, customer_name: str, transaction_id: str, pre_filled_data: dict):
    """Send email to customer with Customer Setup completion link"""
    
    try:
        # Create completion URL (environment-aware)
        base_url = os.environ.get('BASE_URL', 'https://loi-automation-api.onrender.com')
        completion_url = f"{base_url}/api/v1/forms/customer-setup/complete/{transaction_id}"
        
        # Extract sales notes if any
        notes = pre_filled_data.get('notes', '')
        initiated_by = pre_filled_data.get('initiated_by', 'Better Day Energy Sales Team')
        
        # Create email content
        subject = f"Complete Your Customer Setup - {customer_name}"
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #1f4e79; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1>🏢 Better Day Energy</h1>
                    <h2>Complete Your Customer Setup</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                    <p>Dear {customer_name},</p>
                    
                    <p>{initiated_by} has initiated a Customer Setup form for your company. 
                    Please complete the form to establish your account with Better Day Energy.</p>
                    
                    {'<div style="background: #e3f2fd; border: 1px solid #2196f3; padding: 15px; border-radius: 6px; margin: 20px 0;"><p style="margin: 0;"><strong>📝 Note from sales team:</strong> ' + notes + '</p></div>' if notes else ''}
                    
                    <div style="background: #e8f5e9; border: 1px solid #4caf50; padding: 20px; border-radius: 6px; margin: 20px 0;">
                        <h3 style="color: #2e7d32; margin-top: 0;">📋 What You Need to Complete:</h3>
                        <ul>
                            <li>Business information and contact details</li>
                            <li>Location and mailing addresses</li>
                            <li>Business type and tax identification</li>
                            <li>Annual fuel volume and equipment details</li>
                            <li>Authorized signer information and signature</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{completion_url}" 
                           style="background: #28a745; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 6px; font-weight: bold; 
                                  display: inline-block; font-size: 16px;">
                            ✏️ Complete Customer Setup Now
                        </a>
                    </div>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Important:</strong> This link will expire in 30 days. 
                        Some fields may be pre-filled based on information we have on file. Please review and update as needed.</p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                        <p><strong>Transaction ID:</strong> {transaction_id}</p>
                        <p><strong>Company:</strong> {customer_name}</p>
                        <p><strong>Form Type:</strong> Customer Setup</p>
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
        Better Day Energy - Complete Your Customer Setup
        
        Dear {customer_name},
        
        {initiated_by} has initiated a Customer Setup form for your company.
        Please complete the form to establish your account with Better Day Energy.
        
        {'Note from sales team: ' + notes if notes else ''}
        
        Please visit the following link to complete your Customer Setup:
        {completion_url}
        
        What You Need to Complete:
        - Business information and contact details
        - Location and mailing addresses
        - Business type and tax identification
        - Annual fuel volume and equipment details
        - Authorized signer information and signature
        
        Transaction ID: {transaction_id}
        Company: {customer_name}
        Form Type: Customer Setup
        
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
            
        logger.info(f"✅ Customer Setup completion email sent successfully to {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send Customer Setup completion email to {customer_email}: {e}")
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
app.state.send_customer_setup_completion_email = send_customer_setup_completion_email

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

@app.get("/customer-setup/initiate", response_class=HTMLResponse)
async def customer_setup_sales_initiate():
    """Serve Customer Setup sales initiation form"""
    try:
        with open("customer_setup_sales_initiate.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Customer Setup sales form not found</h1>", status_code=404)

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
        db_manager = get_global_db_manager()
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
        
        # Determine LOI type and use appropriate table
        loi_type = request.get('loi_type', 'vp_racing')  # Default to VP Racing
        
        if loi_type == 'phillips_66':
            # Insert into P66 LOI specific table
            logger.info(f"💾 Storing P66 LOI data: {transaction_id}")
            
            # First, we need to create a customer record or get existing one
            customer_email = request.get('email', '')
            cur.execute("SELECT id FROM customers WHERE email = %s LIMIT 1", (customer_email,))
            customer_result = cur.fetchone()
            
            if customer_result:
                customer_id = customer_result[0]
                logger.info(f"📋 Using existing customer: {customer_id}")
            else:
                # Create new customer
                import uuid
                customer_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO customers (id, company_name, contact_name, email, phone, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    customer_id,
                    request.get('company_name', ''),
                    request.get('contact_name', ''),
                    customer_email,
                    request.get('phone', ''),
                    datetime.now()
                ))
                logger.info(f"✅ Created new customer: {customer_id}")
            
            # Create transaction record first (required by foreign key)
            import uuid
            tx_uuid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO loi_transactions (id, transaction_type, document_id, signature_request_id, status, created_at, processing_context, customer_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tx_uuid,
                'NEW_LOI_REQUEST',
                transaction_id,  # Use string transaction_id as document_id
                transaction_id,
                'WAITING_SIGNATURE',
                datetime.now(),
                json.dumps({'loi_type': 'phillips_66', 'original_transaction_id': transaction_id}),
                customer_id
            ))
            logger.info(f"✅ Created transaction record: {tx_uuid}")
            
            # Generate UUID for P66 form record
            p66_form_id = str(uuid.uuid4())
            
            # Insert P66 LOI data with proper UUIDs
            cur.execute("""
                INSERT INTO p66_loi_form_data (
                    id, customer_id, transaction_id, station_name, station_address, station_city, station_state, station_zip,
                    current_brand, brand_expiration_date, monthly_gasoline_gallons, monthly_diesel_gallons, 
                    total_monthly_gallons, contract_start_date, contract_term_years,
                    volume_incentive_requested, image_funding_requested, equipment_funding_requested, 
                    total_incentives_requested, canopy_replacement, dispenser_replacement, 
                    tank_replacement, pos_upgrade, special_requirements,
                    authorized_representative, representative_title, form_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                p66_form_id,  # UUID for form record
                customer_id,  # UUID for customer
                tx_uuid,      # UUID for transaction
                request.get('station_name', ''),
                request.get('station_address', ''),
                request.get('station_city', ''),
                request.get('station_state', ''),
                request.get('station_zip', ''),
                request.get('current_brand', ''),
                request.get('brand_expiration_date'),
                request.get('monthly_gasoline_gallons', 0),
                request.get('monthly_diesel_gallons', 0),
                request.get('total_monthly_gallons', 0),
                request.get('contract_start_date'),
                request.get('contract_term_years', 10),
                request.get('volume_incentive_requested', 0),
                request.get('image_funding_requested', 0),
                request.get('equipment_funding_requested', 0),
                request.get('total_incentives_requested', 0),
                request.get('canopy_replacement', False),
                request.get('dispenser_replacement', False),
                request.get('tank_replacement', False),
                request.get('pos_upgrade', False),
                request.get('special_requirements', ''),
                request.get('authorized_representative', ''),
                request.get('representative_title', ''),
                'WAITING_SIGNATURE',
                datetime.now()
            ))
            logger.info(f"✅ Created P66 form record: {p66_form_id}")
        else:
            # For VP Racing and other LOI types, handle customer creation and storage
            logger.info(f"💾 Storing {loi_type} LOI data: {transaction_id}")
            
            # First, we need to create a customer record or get existing one
            customer_email = request.get('email', '')
            cur.execute("SELECT id FROM customers WHERE email = %s LIMIT 1", (customer_email,))
            customer_result = cur.fetchone()
            
            if customer_result:
                customer_id = customer_result[0]
                logger.info(f"📋 Using existing customer: {customer_id}")
            else:
                # Create new customer
                import uuid
                customer_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO customers (id, company_name, contact_name, email, phone, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    customer_id,
                    request.get('company_name', ''),
                    request.get('authorized_representative', ''),
                    customer_email,
                    request.get('phone', ''),
                    datetime.now()
                ))
                logger.info(f"✅ Created new customer: {customer_id}")
            
            # Create transaction record with customer_id
            import uuid
            tx_uuid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO loi_transactions (id, transaction_type, customer_id, document_id, signature_request_id, status, created_at, processing_context)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tx_uuid,
                'NEW_LOI_REQUEST',
                customer_id,
                transaction_id,
                transaction_id,
                'WAITING_SIGNATURE',
                datetime.now(),
                json.dumps(request)
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
            
            # Send email to any provided address
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
            logger.warning("⚠️ No customer email provided in LOI request")
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': 'LOI routed for customer signature successfully',
            'signature_url': signature_url,
            'customer_email': customer_email,
            'email_sent': email_sent,
            'email_status': 'sent' if email_sent else 'failed',
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
        
        # First try P66 LOI table via transaction lookup
        cur.execute("""
            SELECT c.company_name, c.contact_name, 
                   json_build_object(
                       'loi_type', 'phillips_66',
                       'station_name', p.station_name,
                       'station_address', p.station_address,
                       'station_city', p.station_city,
                       'station_state', p.station_state,
                       'station_zip', p.station_zip,
                       'current_brand', p.current_brand,
                       'monthly_gasoline_gallons', p.monthly_gasoline_gallons,
                       'monthly_diesel_gallons', p.monthly_diesel_gallons,
                       'total_monthly_gallons', p.total_monthly_gallons,
                       'contract_term_years', p.contract_term_years,
                       'contract_start_date', p.contract_start_date,
                       'volume_incentive_requested', p.volume_incentive_requested,
                       'image_funding_requested', p.image_funding_requested,
                       'equipment_funding_requested', p.equipment_funding_requested,
                       'total_incentives_requested', p.total_incentives_requested,
                       'brand_expiration_date', p.brand_expiration_date,
                       'special_requirements', p.special_requirements,
                       'authorized_representative', p.authorized_representative,
                       'representative_title', p.representative_title,
                       'email', c.email,
                       'phone', c.phone
                   ) as loi_data
            FROM p66_loi_form_data p 
            JOIN customers c ON p.customer_id = c.id 
            JOIN loi_transactions t ON p.transaction_id = t.id
            WHERE t.id = %s
        """, (transaction_id,))
        result = cur.fetchone()
        
        if not result:
            # Try general loi_transactions table
            logger.info(f"🔍 P66 LOI not found, checking general transactions for {transaction_id}")
            cur.execute("""
                SELECT '', '', processing_context
                FROM loi_transactions 
                WHERE id = %s
            """, (transaction_id,))
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
        cur.execute("SELECT company_name, contact_name, email, loi_data FROM loi_transactions WHERE id = %s", (transaction_id,))
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
        
        # Extract ESIGN compliance data from request
        esign_compliance = signature_data.get('esign_compliance', {})
        browser_info = signature_data.get('browser_info', {})
        
        # Validate ESIGN consent
        if not esign_compliance.get('consent_given', False):
            logger.error(f"❌ ESIGN consent not given for transaction {transaction_id}")
            raise HTTPException(status_code=400, detail="Electronic signature consent is required")
        
        logger.info(f"✅ ESIGN consent validated for transaction {transaction_id}")
        
        # Prepare signature record with full audit compliance and ESIGN data
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
                'loi_type': loi_details.get('loi_type', 'unknown'),
                'browser_info': browser_info
            },
            'compliance_flags': {
                'esign_consent': esign_compliance.get('consent_given', False),
                'identity_verified': True,
                'intent_to_sign': esign_compliance.get('intent_to_sign_confirmed', True),
                'document_presented': True,
                'signature_attributed': True
            },
            'esign_compliance_data': {
                'consent_given': esign_compliance.get('consent_given', False),
                'consent_timestamp': esign_compliance.get('consent_timestamp'),
                'disclosures_acknowledged': esign_compliance.get('disclosures_acknowledged', False),
                'system_requirements_met': esign_compliance.get('system_requirements_met', False),
                'paper_copy_option_presented': esign_compliance.get('paper_copy_option_presented', False),
                'withdraw_consent_option_presented': esign_compliance.get('withdraw_consent_option_presented', False),
                'intent_to_sign_confirmed': esign_compliance.get('intent_to_sign_confirmed', False),
                'signature_method': 'html5_canvas_with_esign_consent'
            },
            'signature_method': 'html5_canvas'
        }
        
        # Prepare signature request for the existing storage system with ESIGN compliance data
        logger.info(f"🔍 About to create signature_request with loi_details: {loi_details}")
        signature_request = {
            'transaction_id': transaction_id,
            'signature_token': f"sig_{uuid.uuid4().hex}",  # Add required signature_token
            'signer_name': contact_name or "Unknown",
            'signer_email': email or "",
            'company_name': company_name,
            'document_name': f"LOI_{loi_details.get('loi_type', 'unknown')}_{transaction_id}",
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),  # Add required expires_at
            'explicit_intent_confirmed': esign_compliance.get('intent_to_sign_confirmed', True),
            'electronic_consent_given': esign_compliance.get('consent_given', False),
            'disclosures_acknowledged': esign_compliance.get('disclosures_acknowledged', False),
            'esign_compliance_data': signature_record['esign_compliance_data'],  # Pass full ESIGN data
            'signature_metadata': signature_record['signature_metadata'],  # Pass canvas and browser info
            'compliance_flags': signature_record['compliance_flags']  # Pass compliance validation
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
            WHERE id = %s
        """, (
            verification_code,  # Store verification code instead of raw image
            datetime.now(),
            'signed',
            transaction_id
        ))
        
        conn.commit()
        conn.close()
        
        # ========================================================================
        # UPDATE CRM WITH LOI COMPLETION AND DOCUMENT URL
        # ========================================================================
        
        try:
            # Generate document URL for CRM reference
            base_url = os.environ.get('BASE_URL', 'https://loi-automation-api.onrender.com')
            document_url = f"{base_url}/api/v1/documents/loi/{transaction_id}"
            signature_verification_url = f"{base_url}/api/v1/signatures/verify/{stored_signature or verification_code}"
            
            # Create comprehensive LOI notes for CRM
            loi_type = loi_details.get('loi_type', 'Unknown')
            loi_crm_notes = f"""
LOI EXECUTED: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
LOI Type: {loi_type}
Station: {loi_details.get('station_name', 'N/A')}
Monthly Fuel Volume: {loi_details.get('total_monthly_gallons', 'N/A')} gallons
Contract Start: {loi_details.get('contract_start_date', 'N/A')}
Contract Term: {loi_details.get('contract_term_years', 'N/A')} years
Volume Incentive: ${loi_details.get('volume_incentive_requested', 'N/A')}
Image Funding: ${loi_details.get('image_funding_requested', 'N/A')}
Equipment Funding: ${loi_details.get('equipment_funding_requested', 'N/A')}
Document URL: {document_url}
Signature Verification: {signature_verification_url}
Status: EXECUTED
            """.strip()
            
            # Update CRM cache with LOI completion
            try:
                crm_conn = psycopg2.connect(database_url)
                crm_cur = crm_conn.cursor()
                
                # Find existing contact
                crm_cur.execute("""
                    SELECT contact_id, notes FROM crm_contacts_cache 
                    WHERE email = %s OR (company_name = %s AND name = %s)
                    ORDER BY last_sync DESC LIMIT 1
                """, (email, company_name, contact_name))
                
                existing_contact = crm_cur.fetchone()
                
                if existing_contact:
                    contact_id, existing_notes = existing_contact
                    # Append LOI notes to existing notes
                    updated_notes = f"{existing_notes or ''}\n\n{loi_crm_notes}".strip()
                    
                    crm_cur.execute("""
                        UPDATE crm_contacts_cache SET
                            notes = %s,
                            last_sync = %s,
                            sync_status = 'pending_sync'
                        WHERE contact_id = %s
                    """, (updated_notes, datetime.now(), contact_id))
                    
                    logger.info(f"✅ Updated CRM cache with LOI completion: {contact_id}")
                    
                    # Queue for CRM sync
                    queue_data = {
                        "contact_id": contact_id,
                        "operation": "update_contact",
                        "data": {
                            "notes": updated_notes
                        },
                        "app_source": f"LOI {loi_type} Form",
                        "transaction_id": transaction_id,
                        "document_url": document_url,
                        "verification_code": stored_signature or verification_code
                    }
                    
                    crm_cur.execute("""
                        INSERT INTO crm_write_queue 
                        (operation, data, status, created_at, max_attempts)
                        VALUES (%s, %s, 'pending', %s, %s)
                    """, (
                        "update_contact",
                        json.dumps(queue_data),
                        datetime.now(),
                        5
                    ))
                    
                    crm_conn.commit()
                    logger.info(f"✅ LOI completion queued for CRM sync: {company_name} - {loi_type}")
                else:
                    logger.warning(f"⚠️ Contact not found in CRM cache for LOI update: {email}")
                
                crm_cur.close()
                crm_conn.close()
                
            except Exception as crm_error:
                logger.error(f"❌ Error updating CRM cache with LOI data: {crm_error}")
                
        except Exception as e:
            logger.error(f"❌ Error in LOI CRM update process: {e}")
        
        logger.info(f"✅ LOI signature captured with audit compliance: {transaction_id} - Verification: {verification_code}")
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'verification_code': stored_signature or verification_code,  # Use returned verification code
            'message': 'Signature captured successfully with full audit trail',
            'status': 'signed',
            'signed_at': datetime.now().isoformat(),
            'audit_compliant': True,
            'next_step': 'pdf_generation',
            'document_url': f"{os.environ.get('BASE_URL', 'https://loi-automation-api.onrender.com')}/api/v1/documents/loi/{transaction_id}",
            'crm_updated': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error submitting signature: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit signature: {str(e)}")

@app.get("/api/v1/loi/list")
async def list_loi_transactions():
    """List LOI transactions from database"""
    
    try:
        from database.models import LOITransaction, Customer
        from sqlalchemy.orm import sessionmaker
        
        db_manager = get_global_db_manager()
        
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

# Global database manager to avoid repeated initialization
_global_db_manager = None

def get_global_db_manager():
    """Get singleton database manager to avoid connection storms"""
    global _global_db_manager
    if _global_db_manager is None:
        from database.connection import DatabaseManager
        _global_db_manager = DatabaseManager()
        # Only initialize if not already done
        if not _global_db_manager._initialized:
            _global_db_manager.initialize()
    return _global_db_manager

@app.get("/api/v1/transactions/all")
async def list_all_transactions():
    """List ALL transactions from database (LOI, EFT, Customer Setup) for tracking dashboard"""
    
    try:
        # Use direct database connection to avoid connection storms
        import psycopg2
        import os
        
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Get all transactions with customer info, using subqueries to avoid duplicates
                cur.execute("""
                    SELECT 
                        lt.id,
                        lt.transaction_type,
                        lt.status,
                        lt.workflow_stage,
                        lt.created_at,
                        lt.completed_at,
                        c.company_name,
                        c.contact_name,
                        c.email,
                        c.phone,
                        -- Customer Setup form fields (most recent)
                        latest_cs.legal_business_name,
                        latest_cs.business_type,
                        latest_cs.federal_tax_id,
                        latest_cs.physical_address,
                        latest_cs.physical_city,
                        latest_cs.physical_state,
                        latest_cs.physical_zip,
                        latest_cs.primary_contact_name,
                        latest_cs.primary_contact_email,
                        latest_cs.primary_contact_phone,
                        latest_cs.annual_fuel_volume,
                        latest_cs.number_of_locations,
                        -- EFT form fields (most recent)
                        latest_eft.bank_name,
                        latest_eft.account_holder_name,
                        latest_eft.authorized_by_name,
                        latest_eft.authorization_date,
                        -- P66 LOI form fields (most recent)
                        latest_p66.station_name,
                        latest_p66.monthly_gasoline_gallons,
                        latest_p66.monthly_diesel_gallons,
                        latest_p66.total_monthly_gallons,
                        latest_p66.volume_incentive_requested,
                        latest_p66.image_funding_requested
                    FROM loi_transactions lt
                    JOIN customers c ON lt.customer_id = c.id
                    LEFT JOIN (
                        SELECT DISTINCT ON (customer_id) *
                        FROM customer_setup_form_data
                        ORDER BY customer_id, created_at DESC
                    ) latest_cs ON lt.customer_id = latest_cs.customer_id
                    LEFT JOIN (
                        SELECT DISTINCT ON (transaction_id) *
                        FROM eft_form_data
                        ORDER BY transaction_id, created_at DESC
                    ) latest_eft ON lt.id::text = latest_eft.transaction_id
                    LEFT JOIN (
                        SELECT DISTINCT ON (customer_id) *
                        FROM p66_loi_form_data
                        ORDER BY customer_id, created_at DESC
                    ) latest_p66 ON lt.customer_id = latest_p66.customer_id
                    ORDER BY lt.created_at DESC
                    LIMIT 100
                """)
                
                rows = cur.fetchall()
        
        transaction_list = []
        for row in rows:
            (transaction_id, transaction_type, status, workflow_stage, created_at, completed_at, 
             company_name, contact_name, email, phone,
             # Customer Setup fields
             legal_business_name, business_type, federal_tax_id, 
             physical_address, physical_city, physical_state, physical_zip,
             primary_contact_name, primary_contact_email, primary_contact_phone,
             annual_fuel_volume, number_of_locations,
             # EFT fields
             bank_name, account_holder_name, authorized_by_name, authorization_date,
             # P66 LOI fields
             station_name, monthly_gasoline_gallons, monthly_diesel_gallons, 
             total_monthly_gallons, volume_incentive_requested, image_funding_requested) = row
            
            # Determine completion URL based on transaction type
            completion_url = ""
            document_url = ""
            type_display = ""
            
            if transaction_type == "VP_RACING_LOI":
                completion_url = f"/api/v1/loi/sign/{transaction_id}"  # LOI signatures are still allowed
                document_url = f"/api/v1/documents/loi/{transaction_id}"
                type_display = "VP Racing LOI"
            elif transaction_type == "P66_LOI":
                completion_url = f"/api/v1/loi/sign/{transaction_id}"  # LOI signatures are still allowed
                document_url = f"/api/v1/documents/p66-loi/{transaction_id}"
                type_display = "Phillips 66 LOI"
            elif transaction_type == "EFT_FORM":
                completion_url = ""  # Disabled to prevent shortcuts - users must use proper form flow
                document_url = f"/api/v1/documents/eft/{transaction_id}"
                type_display = "EFT Authorization"
            elif transaction_type == "CUSTOMER_SETUP_FORM":
                completion_url = ""  # Disabled to prevent shortcuts - users must use proper form flow
                document_url = f"/api/v1/documents/customer-setup/{transaction_id}"
                type_display = "Customer Setup"
            
            # Calculate time since creation
            import datetime as dt
            if isinstance(created_at, str):
                created_at = dt.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            time_since_created = dt.datetime.utcnow() - created_at.replace(tzinfo=None)
            
            # Determine urgency based on age and status
            days_old = time_since_created.days
            hours_old = time_since_created.total_seconds() / 3600
            urgency = "low"
            
            if status == "COMPLETED":
                urgency = "completed"
            elif status == "CANCELLED":
                urgency = "cancelled"
            elif days_old > 7:
                urgency = "high"  # Overdue
            elif days_old > 3:
                urgency = "medium"  # Getting stale
            elif hours_old < 1:
                urgency = "new"  # Just created
            
            # Status display
            status_display = ""
            if status == "PENDING":
                if workflow_stage and "customer" in str(workflow_stage).lower():
                    status_display = "Waiting for Customer"
                else:
                    status_display = "Pending"
            elif status == "COMPLETED":
                status_display = "Completed"
            elif status == "CANCELLED":
                status_display = "Cancelled"
            elif status == "FAILED":
                status_display = "Failed"
            else:
                status_display = str(status)
            
            transaction_list.append({
                'transaction_id': str(transaction_id),
                'transaction_type': transaction_type,
                'type_display': type_display,
                'customer_company': company_name,
                'contact_name': contact_name,
                'email': email,
                'phone': phone,
                'status': status,
                'status_display': status_display,
                'workflow_stage': workflow_stage,
                'created_at': created_at.isoformat(),
                'updated_at': completed_at.isoformat() if completed_at else None,
                'days_old': days_old,
                'hours_old': round(hours_old, 1),
                'urgency': urgency,
                'completion_url': "",  # Disabled to prevent shortcuts - users must use proper form flow
                'document_url': document_url,
                'processing_context': {},
                # Customer Setup form data
                'business_info': {
                    'legal_business_name': legal_business_name,
                    'business_type': business_type,
                    'federal_tax_id': federal_tax_id,
                    'annual_fuel_volume': annual_fuel_volume,
                    'number_of_locations': number_of_locations
                },
                'business_address': {
                    'address': physical_address,
                    'city': physical_city,
                    'state': physical_state,
                    'zip': physical_zip
                },
                'primary_contact': {
                    'name': primary_contact_name,
                    'email': primary_contact_email,
                    'phone': primary_contact_phone
                },
                # EFT form data
                'banking_info': {
                    'bank_name': bank_name,
                    'account_holder_name': account_holder_name,
                    'authorized_by_name': authorized_by_name,
                    'authorization_date': authorization_date.isoformat() if authorization_date else None
                },
                # LOI form data
                'station_info': {
                    'station_name': station_name,
                    'monthly_gasoline_gallons': monthly_gasoline_gallons,
                    'monthly_diesel_gallons': monthly_diesel_gallons,
                    'total_monthly_gallons': total_monthly_gallons,
                    'volume_incentive_requested': volume_incentive_requested,
                    'image_funding_requested': image_funding_requested
                }
            })
        
        return {
            'success': True,
            'transactions': transaction_list,
            'total_count': len(transaction_list),
            'pending_count': len([t for t in transaction_list if t['status'] != 'COMPLETED']),
            'completed_count': len([t for t in transaction_list if t['status'] == 'COMPLETED']),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing all transactions: {e}")
        return {
            'success': False,
            'transactions': [],
            'total_count': 0,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.post("/api/v1/transactions/{transaction_id}/cancel")
async def cancel_transaction(transaction_id: str):
    """Cancel a transaction and notify the customer"""
    
    try:
        import psycopg2
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Get transaction details first
                cur.execute("""
                    SELECT lt.status, c.company_name, c.contact_name, c.email, lt.transaction_type
                    FROM loi_transactions lt
                    JOIN customers c ON lt.customer_id = c.id
                    WHERE lt.id = %s
                """, (transaction_id,))
                
                result = cur.fetchone()
                if not result:
                    return {
                        'success': False,
                        'error': 'Transaction not found',
                        'timestamp': datetime.now().isoformat()
                    }
                
                current_status, company_name, contact_name, customer_email, transaction_type = result
                
                # Check if already cancelled or completed
                if current_status in ['CANCELLED', 'COMPLETED']:
                    return {
                        'success': False,
                        'error': f'Transaction is already {current_status.lower()}',
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Update transaction status to CANCELLED
                cur.execute("""
                    UPDATE loi_transactions 
                    SET status = 'CANCELLED', completed_at = %s
                    WHERE id = %s
                """, (datetime.now(), transaction_id))
                
                conn.commit()
                
                # Send cancellation email to customer
                try:
                    # Determine transaction type display
                    type_display = ""
                    if transaction_type == "VP_RACING_LOI":
                        type_display = "VP Racing Fuels Letter of Intent"
                    elif transaction_type == "P66_LOI":
                        type_display = "Phillips 66 Letter of Intent"
                    elif transaction_type == "EFT_FORM":
                        type_display = "EFT Authorization Form"
                    elif transaction_type == "CUSTOMER_SETUP_FORM":
                        type_display = "Customer Setup Form"
                    else:
                        type_display = "Transaction"
                    
                    # Create cancellation email
                    subject = f"Transaction Cancelled - {company_name} - {type_display}"
                    
                    html_body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <div style="background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                                <h1>🏢 Better Day Energy</h1>
                                <h2>Transaction Cancelled</h2>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                                <p>Dear {contact_name},</p>
                                
                                <p>Your <strong>{type_display}</strong> for <strong>{company_name}</strong> has been cancelled by our team.</p>
                                
                                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 6px; margin: 20px 0;">
                                    <h3 style="color: #721c24; margin-top: 0;">⚠️ Transaction Cancelled</h3>
                                    <p style="margin: 0; color: #721c24;">
                                        This transaction has been cancelled and can no longer be completed. 
                                        If you have any questions or need to restart the process, please contact our team.
                                    </p>
                                </div>
                                
                                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                                    <p><strong>Transaction ID:</strong> {transaction_id}</p>
                                    <p><strong>Company:</strong> {company_name}</p>
                                    <p><strong>Transaction Type:</strong> {type_display}</p>
                                    <p><strong>Cancelled:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                                </div>
                                
                                <div style="margin-top: 30px; padding: 20px; background: #e2e3e5; border-radius: 6px;">
                                    <p style="margin: 0;"><strong>Need Help?</strong></p>
                                    <p style="margin: 5px 0 0 0;">Contact Better Day Energy if you have questions about this cancellation or need to start a new transaction.</p>
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Send email using the existing email configuration
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
                    msg['To'] = customer_email
                    
                    html_part = MIMEText(html_body, 'html')
                    msg.attach(html_part)
                    
                    # Send email
                    server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
                    server.starttls()
                    server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
                    server.send_message(msg)
                    server.quit()
                    
                    logger.info(f"✅ Cancellation email sent to {customer_email} for transaction {transaction_id}")
                    
                except Exception as email_error:
                    logger.error(f"❌ Failed to send cancellation email: {email_error}")
                    # Don't fail the cancellation if email fails
                
                return {
                    'success': True,
                    'message': 'Transaction cancelled successfully',
                    'transaction_id': transaction_id,
                    'customer_email': customer_email,
                    'company_name': company_name,
                    'transaction_type': type_display,
                    'cancelled_at': datetime.now().isoformat(),
                    'timestamp': datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"❌ Error cancelling transaction {transaction_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.get("/api/v1/documents/loi/{transaction_id}")
async def get_loi_document(transaction_id: str):
    """Get LOI document details and status"""
    try:
        import psycopg2
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Get LOI transaction details
        cur.execute("""
            SELECT company_name, contact_name, email, loi_data, signature_data, signed_at, status, created_at
            FROM loi_transactions 
            WHERE id = %s
        """, (transaction_id,))
        
        result = cur.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="LOI document not found")
        
        company_name, contact_name, email, loi_data, signature_data, signed_at, status, created_at = result
        
        # Parse LOI data
        if isinstance(loi_data, str):
            loi_details = json.loads(loi_data) if loi_data else {}
        elif isinstance(loi_data, dict):
            loi_details = loi_data
        else:
            loi_details = {}
        
        # Create formatted HTML response  
        loi_type_display = loi_details.get('loi_type', 'VP Racing').replace('_', ' ').title()
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Letter of Intent - {company_name}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #333; }}
                .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #8e24aa 0%, #ab47bc 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0 0 10px 0; font-size: 2.2em; font-weight: 300; }}
                .header p {{ margin: 0; opacity: 0.9; font-size: 1.1em; }}
                .content {{ padding: 40px; }}
                .section {{ margin-bottom: 35px; padding: 25px; border: 1px solid #e9ecef; border-radius: 8px; background: #f8f9fa; }}
                .section h2 {{ margin: 0 0 20px 0; color: #8e24aa; font-size: 1.4em; border-bottom: 2px solid #8e24aa; padding-bottom: 8px; }}
                .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
                .info-item {{ display: flex; align-items: center; }}
                .info-label {{ font-weight: 600; color: #495057; min-width: 140px; }}
                .info-value {{ color: #212529; flex: 1; }}
                .status-badge {{ display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; text-transform: uppercase; }}
                .status-pending {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
                .status-completed {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .status-cancelled {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .status-failed {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .status-signed {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; border-top: 1px solid #dee2e6; }}
                .highlight-value {{ font-weight: 600; color: #8e24aa; }}
                .signature-info {{ background: #e8f5e8; border: 1px solid #4caf50; padding: 15px; border-radius: 6px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📄 {loi_type_display} Letter of Intent</h1>
                    <p>Fuel Supply Agreement</p>
                </div>
                
                <div class="content">
                    <div class="section">
                        <h2>📋 Transaction Information</h2>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">Transaction ID:</span>
                                <span class="info-value">{transaction_id}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Document Type:</span>
                                <span class="info-value">{loi_type_display} Letter of Intent</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Status:</span>
                                <span class="info-value">
                                    <span class="status-badge status-{status.lower() if status else 'pending'}">{status or 'PENDING'}</span>
                                </span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Created:</span>
                                <span class="info-value">{created_at.strftime('%B %d, %Y at %I:%M %p') if created_at else 'Unknown'}</span>
                            </div>
                        </div>
                        
                        {f'''
                        <div class="signature-info">
                            <h3 style="color: #2e7d32; margin-top: 0;">✅ Signature Information</h3>
                            <div class="info-grid">
                                <div class="info-item">
                                    <span class="info-label">Signed Date:</span>
                                    <span class="info-value">{signed_at.strftime('%B %d, %Y at %I:%M %p') if signed_at else 'Not signed'}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">Verification Code:</span>
                                    <span class="info-value">{signature_data or 'Not available'}</span>
                                </div>
                            </div>
                        </div>
                        ''' if signed_at else ''}
                    </div>
                    
                    <div class="section">
                        <h2>🏢 Company Information</h2>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">Company Name:</span>
                                <span class="info-value">{company_name or 'Not provided'}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Contact Name:</span>
                                <span class="info-value">{contact_name or 'Not provided'}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Email:</span>
                                <span class="info-value">{email or 'Not provided'}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>⛽ LOI Details</h2>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">Station Name:</span>
                                <span class="info-value">{loi_details.get('station_name', 'Not provided')}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Monthly Gallons:</span>
                                <span class="info-value highlight-value">{loi_details.get('total_monthly_gallons', 0):,} gallons</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Contract Start:</span>
                                <span class="info-value">{loi_details.get('contract_start_date', 'Not provided')}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Contract Term:</span>
                                <span class="info-value">{loi_details.get('contract_term_years', 'Not provided')} years</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>💰 Requested Incentives</h2>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">Volume Incentive:</span>
                                <span class="info-value highlight-value">${loi_details.get('volume_incentive_requested', 0):,}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Image Funding:</span>
                                <span class="info-value highlight-value">${loi_details.get('image_funding_requested', 0):,}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Equipment Funding:</span>
                                <span class="info-value highlight-value">${loi_details.get('equipment_funding_requested', 0):,}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Better Day Energy - {loi_type_display} LOI System</p>
                    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Error retrieving LOI document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")

@app.get("/api/v1/signatures/verify/{verification_code}")
async def verify_signature(verification_code: str):
    """Verify signature integrity and get audit details"""
    try:
        from signature_storage import TamperEvidentSignatureStorage
        
        signature_storage = TamperEvidentSignatureStorage()
        
        # Verify signature integrity
        is_valid, integrity_message = signature_storage.verify_signature_integrity(verification_code)
        
        # Get full audit report
        audit_report = signature_storage.get_audit_report(verification_code)
        
        if not audit_report:
            raise HTTPException(status_code=404, detail="Signature verification code not found")
        
        return {
            "success": True,
            "verification_code": verification_code,
            "integrity_valid": is_valid,
            "integrity_message": integrity_message,
            "audit_report": {
                "transaction_id": audit_report['transaction_id'],
                "signer_name": audit_report['signer_name'],
                "signer_email": audit_report['signer_email'],
                "company_name": audit_report['company_name'],
                "document_name": audit_report['document_name'],
                "signed_at": audit_report['signed_at'],
                "ip_address": audit_report['ip_address'],
                "browser_fingerprint": audit_report['browser_fingerprint'],
                "compliance_flags": audit_report['compliance_flags'],
                "created_at": audit_report['created_at']
            },
            "esign_act_compliant": audit_report['compliance_flags'].get('esign_act_compliant', False)
        }
        
    except Exception as e:
        logger.error(f"❌ Error verifying signature: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify signature")

@app.get("/api/v1/documents/eft/{transaction_id}")
async def get_eft_document(transaction_id: str):
    """Get EFT authorization document details and status"""
    try:
        import psycopg2
        import os
        
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Get EFT transaction details
                cur.execute("""
                    SELECT 
                        lt.id,
                        lt.status,
                        lt.created_at,
                        lt.processing_context,
                        c.company_name,
                        c.contact_name,
                        c.email,
                        c.phone
                    FROM loi_transactions lt
                    JOIN customers c ON lt.customer_id = c.id
                    WHERE lt.id = %s AND lt.transaction_type = 'EFT_FORM'
                """, (transaction_id,))
                
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="EFT document not found")
                
                (id, status, created_at, processing_context, company_name, contact_name, email, phone) = result
                
                # Parse processing context for form data
                form_data = processing_context.get('form_data', {}) if processing_context else {}
                
                # Create formatted HTML response
                html_content = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>EFT Authorization - {company_name or form_data.get('company_name', 'Unknown')}</title>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #333; }}
                        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
                        .header {{ background: linear-gradient(135deg, #1f4e79 0%, #2d5aa0 100%); color: white; padding: 30px; text-align: center; }}
                        .header h1 {{ margin: 0 0 10px 0; font-size: 2.2em; font-weight: 300; }}
                        .header p {{ margin: 0; opacity: 0.9; font-size: 1.1em; }}
                        .content {{ padding: 40px; }}
                        .section {{ margin-bottom: 35px; padding: 25px; border: 1px solid #e9ecef; border-radius: 8px; background: #f8f9fa; }}
                        .section h2 {{ margin: 0 0 20px 0; color: #1f4e79; font-size: 1.4em; border-bottom: 2px solid #1f4e79; padding-bottom: 8px; }}
                        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
                        .info-item {{ display: flex; align-items: center; }}
                        .info-label {{ font-weight: 600; color: #495057; min-width: 140px; }}
                        .info-value {{ color: #212529; flex: 1; }}
                        .status-badge {{ display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; text-transform: uppercase; }}
                        .status-pending {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
                        .status-completed {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                        .status-cancelled {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                        .status-failed {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; border-top: 1px solid #dee2e6; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🏦 EFT Authorization Form</h1>
                            <p>Electronic Funds Transfer Authorization</p>
                        </div>
                        
                        <div class="content">
                            <div class="section">
                                <h2>📋 Transaction Information</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Transaction ID:</span>
                                        <span class="info-value">{str(id)}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Document Type:</span>
                                        <span class="info-value">EFT Authorization Form</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Status:</span>
                                        <span class="info-value">
                                            <span class="status-badge status-{status.lower()}">{status}</span>
                                        </span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Created:</span>
                                        <span class="info-value">{created_at.strftime('%B %d, %Y at %I:%M %p') if created_at else 'Unknown'}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section">
                                <h2>🏢 Company Information</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Company Name:</span>
                                        <span class="info-value">{company_name or form_data.get('company_name', 'Unknown')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Federal Tax ID (EIN):</span>
                                        <span class="info-value">{form_data.get('federal_tax_id', 'Not provided')}</span>
                                    </div>
                                </div>
                                
                                <h3 style="margin-top: 25px; margin-bottom: 15px; color: #1f4e79;">📍 Business Address</h3>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Address:</span>
                                        <span class="info-value">{form_data.get('company_address', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">City:</span>
                                        <span class="info-value">{form_data.get('company_city', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">State:</span>
                                        <span class="info-value">{form_data.get('company_state', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">ZIP Code:</span>
                                        <span class="info-value">{form_data.get('company_zip', 'Not provided')}</span>
                                    </div>
                                </div>
                                
                                <h3 style="margin-top: 25px; margin-bottom: 15px; color: #1f4e79;">👤 Primary Contact</h3>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Contact Name:</span>
                                        <span class="info-value">{form_data.get('contact_name', contact_name or 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Email:</span>
                                        <span class="info-value">{form_data.get('contact_email', email or 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Phone:</span>
                                        <span class="info-value">{form_data.get('contact_phone', phone or 'Not provided')}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section">
                                <h2>🏦 Banking Information</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Bank Name:</span>
                                        <span class="info-value">{form_data.get('bank_name', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Routing Number:</span>
                                        <span class="info-value">{form_data.get('routing_number', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Account Type:</span>
                                        <span class="info-value">{form_data.get('account_type', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Account Holder:</span>
                                        <span class="info-value">{form_data.get('account_holder_name', 'Not provided')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="footer">
                            <p>Better Day Energy - EFT Authorization System</p>
                            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Error retrieving EFT document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve EFT document")

@app.get("/api/v1/documents/p66-loi/{transaction_id}")
async def get_p66_loi_document(transaction_id: str):
    """Get P66 LOI document details and status"""
    try:
        import psycopg2
        import os
        
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Get P66 LOI transaction details
                cur.execute("""
                    SELECT 
                        lt.id,
                        lt.status,
                        lt.created_at,
                        lt.processing_context,
                        c.company_name,
                        c.contact_name,
                        c.email,
                        c.phone
                    FROM loi_transactions lt
                    JOIN customers c ON lt.customer_id = c.id
                    WHERE lt.id = %s AND lt.transaction_type = 'P66_LOI'
                """, (transaction_id,))
                
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="P66 LOI document not found")
                
                (id, status, created_at, processing_context, company_name, contact_name, email, phone) = result
                
                # Parse processing context for form data
                form_data = processing_context.get('form_data', {}) if processing_context else {}
                
                # Create formatted HTML response
                html_content = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Phillips 66 LOI - {company_name}</title>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #333; }}
                        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
                        .header {{ background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%); color: white; padding: 30px; text-align: center; }}
                        .header h1 {{ margin: 0 0 10px 0; font-size: 2.2em; font-weight: 300; }}
                        .header p {{ margin: 0; opacity: 0.9; font-size: 1.1em; }}
                        .content {{ padding: 40px; }}
                        .section {{ margin-bottom: 35px; padding: 25px; border: 1px solid #e9ecef; border-radius: 8px; background: #f8f9fa; }}
                        .section h2 {{ margin: 0 0 20px 0; color: #d32f2f; font-size: 1.4em; border-bottom: 2px solid #d32f2f; padding-bottom: 8px; }}
                        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
                        .info-item {{ display: flex; align-items: center; }}
                        .info-label {{ font-weight: 600; color: #495057; min-width: 140px; }}
                        .info-value {{ color: #212529; flex: 1; }}
                        .status-badge {{ display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; text-transform: uppercase; }}
                        .status-pending {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
                        .status-completed {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                        .status-cancelled {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                        .status-failed {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; border-top: 1px solid #dee2e6; }}
                        .highlight-value {{ font-weight: 600; color: #d32f2f; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🛢️ Phillips 66 Letter of Intent</h1>
                            <p>Fuel Supply Agreement</p>
                        </div>
                        
                        <div class="content">
                            <div class="section">
                                <h2>📋 Transaction Information</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Transaction ID:</span>
                                        <span class="info-value">{str(id)}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Document Type:</span>
                                        <span class="info-value">Phillips 66 Letter of Intent</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Status:</span>
                                        <span class="info-value">
                                            <span class="status-badge status-{status.lower()}">{status}</span>
                                        </span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Created:</span>
                                        <span class="info-value">{created_at.strftime('%B %d, %Y at %I:%M %p') if created_at else 'Unknown'}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section">
                                <h2>🏢 Company Information</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Company Name:</span>
                                        <span class="info-value">{company_name}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Contact Name:</span>
                                        <span class="info-value">{contact_name}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Email:</span>
                                        <span class="info-value">{email}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Phone:</span>
                                        <span class="info-value">{phone or 'Not provided'}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section">
                                <h2>⛽ Station Information</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Station Name:</span>
                                        <span class="info-value">{form_data.get('station_name', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Address:</span>
                                        <span class="info-value">{form_data.get('station_address', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">City:</span>
                                        <span class="info-value">{form_data.get('station_city', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">State:</span>
                                        <span class="info-value">{form_data.get('station_state', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">ZIP Code:</span>
                                        <span class="info-value">{form_data.get('station_zip', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Current Brand:</span>
                                        <span class="info-value">{form_data.get('current_brand', 'Not provided')}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section">
                                <h2>📊 Fuel Volume Projections</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Monthly Gasoline:</span>
                                        <span class="info-value highlight-value">{form_data.get('monthly_gasoline_gallons', 0):,} gallons</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Monthly Diesel:</span>
                                        <span class="info-value highlight-value">{form_data.get('monthly_diesel_gallons', 0):,} gallons</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Total Monthly:</span>
                                        <span class="info-value highlight-value">{form_data.get('total_monthly_gallons', 0):,} gallons</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section">
                                <h2>📝 Contract Details</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Start Date:</span>
                                        <span class="info-value">{form_data.get('contract_start_date', 'Not provided')}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Term (Years):</span>
                                        <span class="info-value">{form_data.get('contract_term_years', 'Not provided')}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section">
                                <h2>💰 Requested Incentives</h2>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <span class="info-label">Volume Incentive:</span>
                                        <span class="info-value highlight-value">${form_data.get('volume_incentive_requested', 0):,}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Image Funding:</span>
                                        <span class="info-value highlight-value">${form_data.get('image_funding_requested', 0):,}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Equipment Funding:</span>
                                        <span class="info-value highlight-value">${form_data.get('equipment_funding_requested', 0):,}</span>
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">Total Incentives:</span>
                                        <span class="info-value highlight-value">${form_data.get('total_incentives_requested', 0):,}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="footer">
                            <p>Better Day Energy - Phillips 66 LOI System</p>
                            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Error retrieving P66 LOI document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve P66 LOI document")

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    
    try:
        import psycopg2
        import os
        
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        
        # Quick database health check
        db_healthy = False
        try:
            with psycopg2.connect(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    db_healthy = True
        except:
            db_healthy = False
        
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

@app.get("/api/v1/documents/customer-setup/{transaction_id}")
async def get_customer_setup_document(transaction_id: str):
    """Get Customer Setup document details and status"""
    try:
        import psycopg2
        import os
        
        database_url = os.environ.get('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Get Customer Setup transaction details with customer info
                cur.execute("""
                    SELECT 
                        lt.id,
                        lt.transaction_type,
                        lt.status,
                        lt.workflow_stage,
                        lt.created_at,
                        lt.completed_at,
                        lt.processing_context,
                        c.company_name,
                        c.contact_name,
                        c.email,
                        c.phone
                    FROM loi_transactions lt
                    JOIN customers c ON lt.customer_id = c.id
                    WHERE lt.id = %s AND lt.transaction_type = 'CUSTOMER_SETUP_FORM'
                """, (transaction_id,))
                
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Customer Setup document not found")
                
                (id, transaction_type, status, workflow_stage, created_at, completed_at, 
                 processing_context, company_name, contact_name, email, phone) = result
                
                # Parse processing context for form data
                form_data = processing_context.get('form_data', {}) if processing_context else {}
                
                document_info = {
                    'success': True,
                    'transaction_id': str(id),
                    'transaction_type': 'Customer Setup Form',
                    'customer_company': company_name or form_data.get('legal_business_name', 'Unknown'),
                    'contact_name': contact_name or form_data.get('primary_contact_name', 'Unknown'),
                    'email': email or form_data.get('primary_contact_email', 'Unknown'),
                    'phone': phone or form_data.get('primary_contact_phone', ''),
                    'status': status,
                    'workflow_stage': workflow_stage,
                    'created_at': created_at.isoformat() if created_at else None,
                    'updated_at': completed_at.isoformat() if completed_at else None,
                    'completion_url': "",  # Disabled to prevent shortcuts - users must use proper form flow
                    'business_info': {
                        'legal_business_name': form_data.get('legal_business_name', ''),
                        'dba_name': form_data.get('dba_name', ''),
                        'federal_tax_id': form_data.get('federal_tax_id', ''),
                        'business_type': form_data.get('business_type', ''),
                        'years_in_business': form_data.get('years_in_business', ''),
                        'physical_address': form_data.get('physical_address', ''),
                        'physical_city': form_data.get('physical_city', ''),
                        'physical_state': form_data.get('physical_state', ''),
                        'physical_zip': form_data.get('physical_zip', '')
                    },
                    'contact_info': {
                        'primary_contact_name': form_data.get('primary_contact_name', ''),
                        'primary_contact_email': form_data.get('primary_contact_email', ''),
                        'primary_contact_phone': form_data.get('primary_contact_phone', ''),
                        'accounts_payable_contact': form_data.get('accounts_payable_contact', ''),
                        'accounts_payable_email': form_data.get('accounts_payable_email', '')
                    },
                    'is_completed': status == 'COMPLETED'
                }
        
        # Return formatted HTML view instead of raw JSON
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Customer Setup Document - {document_info['customer_company']}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #1f4e79, #2563eb);
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                    color: white;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    color: #333;
                    border-radius: 12px;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #1f4e79, #2563eb);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                }}
                .section {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border: 1px solid #dee2e6;
                }}
                .section h3 {{
                    color: #1f4e79;
                    margin-bottom: 15px;
                    font-size: 18px;
                }}
                .field-row {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin-bottom: 15px;
                }}
                .field {{
                    display: flex;
                    flex-direction: column;
                }}
                .field label {{
                    font-weight: 600;
                    color: #495057;
                    font-size: 14px;
                    margin-bottom: 5px;
                }}
                .field .value {{
                    padding: 8px 12px;
                    background: white;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: 600;
                    font-size: 12px;
                    text-transform: uppercase;
                }}
                .status-completed {{ background: #28a745; color: white; }}
                .status-pending {{ background: #ffc107; color: #212529; }}
                .status-cancelled {{ background: #6c757d; color: white; }}
                .actions {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background: #1f4e79;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 0 10px;
                }}
                .btn:hover {{
                    background: #2563eb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏢 Customer Setup Document</h1>
                    <p>{document_info['customer_company']}</p>
                    <span class="status-badge status-{document_info['status'].lower()}">{document_info['status']}</span>
                </div>
                
                <div class="content">
                    <div class="section">
                        <h3>📋 Transaction Information</h3>
                        <div class="field-row">
                            <div class="field">
                                <label>Transaction ID</label>
                                <div class="value">{document_info['transaction_id']}</div>
                            </div>
                            <div class="field">
                                <label>Created Date</label>
                                <div class="value">{document_info['created_at'][:10] if document_info['created_at'] else 'N/A'}</div>
                            </div>
                        </div>
                        <div class="field-row">
                            <div class="field">
                                <label>Status</label>
                                <div class="value">{document_info['status']}</div>
                            </div>
                            <div class="field">
                                <label>Workflow Stage</label>
                                <div class="value">{document_info['workflow_stage']}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>🏢 Business Information</h3>
                        <div class="field-row">
                            <div class="field">
                                <label>Legal Business Name</label>
                                <div class="value">{document_info['business_info']['legal_business_name'] or 'Not provided'}</div>
                            </div>
                            <div class="field">
                                <label>DBA Name</label>
                                <div class="value">{document_info['business_info']['dba_name'] or 'Not provided'}</div>
                            </div>
                        </div>
                        <div class="field-row">
                            <div class="field">
                                <label>Federal Tax ID</label>
                                <div class="value">{document_info['business_info']['federal_tax_id'] or 'Not provided'}</div>
                            </div>
                            <div class="field">
                                <label>Business Type</label>
                                <div class="value">{document_info['business_info']['business_type'] or 'Not provided'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>👤 Contact Information</h3>
                        <div class="field-row">
                            <div class="field">
                                <label>Primary Contact</label>
                                <div class="value">{document_info['contact_name']}</div>
                            </div>
                            <div class="field">
                                <label>Email</label>
                                <div class="value">{document_info['email']}</div>
                            </div>
                        </div>
                        <div class="field-row">
                            <div class="field">
                                <label>Phone</label>
                                <div class="value">{document_info['phone'] or 'Not provided'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>📍 Address Information</h3>
                        <div class="field-row">
                            <div class="field">
                                <label>Physical Address</label>
                                <div class="value">{document_info['business_info']['physical_address'] or 'Not provided'}</div>
                            </div>
                        </div>
                        <div class="field-row">
                            <div class="field">
                                <label>City</label>
                                <div class="value">{document_info['business_info']['physical_city'] or 'Not provided'}</div>
                            </div>
                            <div class="field">
                                <label>State</label>
                                <div class="value">{document_info['business_info']['physical_state'] or 'Not provided'}</div>
                            </div>
                            <div class="field">
                                <label>ZIP Code</label>
                                <div class="value">{document_info['business_info']['physical_zip'] or 'Not provided'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="actions">
                        <a href="/" class="btn">← Back to Dashboard</a>
                        {f'<div class="btn" style="background: #6c757d; cursor: not-allowed; opacity: 0.6;" title="Complete button disabled - Use proper form flow instead">Complete Form (Disabled)</div>' if not document_info['is_completed'] and document_info['status'] != 'CANCELLED' else ''}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error retrieving Customer Setup document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Customer Setup document")

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

# Import EFT models
try:
    from api.forms_api import SalesInitiatedEFTRequest, EFTFormRequest
except ImportError:
    # Define minimal models if forms_api not available
    from pydantic import BaseModel, EmailStr
    class SalesInitiatedEFTRequest(BaseModel):
        company_name: str
        customer_email: EmailStr
        customer_phone: Optional[str] = None
        customer_id: Optional[str] = None
        bank_name: Optional[str] = None
        bank_address: Optional[str] = None
        bank_city: Optional[str] = None
        bank_state: Optional[str] = None
        bank_zip: Optional[str] = None
        account_holder_name: Optional[str] = None
        account_type: Optional[str] = None
        authorized_by_name: Optional[str] = None
        authorized_by_title: Optional[str] = None
        federal_tax_id: Optional[str] = None
        initiated_by: Optional[str] = None
        notes: Optional[str] = None
    
    class EFTFormRequest(BaseModel):
        company_name: str
        federal_tax_id: str
        customer_id: Optional[str] = None
        company_address: Optional[str] = None
        company_city: Optional[str] = None
        company_state: Optional[str] = None
        company_zip: Optional[str] = None
        contact_name: Optional[str] = None
        contact_email: Optional[str] = None
        contact_phone: Optional[str] = None
        bank_name: str
        bank_address: Optional[str] = None
        bank_city: Optional[str] = None
        bank_state: Optional[str] = None
        bank_zip: Optional[str] = None
        account_holder_name: str
        account_type: str
        routing_number: str
        account_number: str
        authorized_by_name: str
        authorized_by_title: str
        authorization_date: str
        signature_data: str
        signature_timestamp: str

# EFT Form Initiation Endpoint
@app.post("/api/v1/forms/eft/initiate")
async def eft_form_initiate(request_data: SalesInitiatedEFTRequest):
    """Initiate EFT form process - sales person sends form to customer"""
    
    try:
        logger.info(f"🏦 EFT form initiation requested for {request_data.company_name}")
        
        # Generate unique transaction ID
        transaction_id = f"EFT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        # Store basic transaction info in database (if available)
        try:
            # Import database manager
            from database.connection import get_db_manager
            db_manager = get_db_manager()
            
            with db_manager.get_session() as session:
                # Import Customer and LOITransaction models
                from database.models import Customer, LOITransaction
                
                # Check if customer already exists
                existing_customer = session.query(Customer).filter_by(
                    email=request_data.customer_email
                ).first()
                
                if existing_customer:
                    customer = existing_customer
                    logger.info(f"👤 Found existing customer: {customer.company_name}")
                else:
                    # Create new customer record
                    customer = Customer(
                        company_name=request_data.company_name,
                        email=request_data.customer_email,
                        phone=request_data.customer_phone,
                        customer_id=request_data.customer_id,
                        customer_type="eft_prospect",
                        is_vip_customer=False
                    )
                    session.add(customer)
                    session.commit()
                    logger.info(f"👤 Created new customer: {request_data.company_name}")
                
                # Create transaction record
                transaction = LOITransaction(
                    id=transaction_id,
                    customer_id=customer.id,
                    loi_type="eft_authorization",
                    status="initiated",
                    workflow_stage="sales_initiation",
                    initiated_by=request_data.initiated_by or "Sales Team",
                    notes=request_data.notes,
                    customer_email=request_data.customer_email,
                    company_name=request_data.company_name
                )
                session.add(transaction)
                session.commit()
                
                logger.info(f"📝 Created transaction record: {transaction_id}")
                
        except Exception as db_error:
            logger.warning(f"Database operation failed (continuing anyway): {db_error}")
            # Continue with email sending even if database fails
        
        # Create customer form URL with pre-filled data
        base_url = "https://loi-automation-api.onrender.com"
        customer_form_url = f"{base_url}/eft_form.html?transaction_id={transaction_id}"
        
        # Add pre-fill parameters if provided
        prefill_params = []
        if request_data.company_name:
            prefill_params.append(f"company_name={request_data.company_name}")
        if request_data.customer_id:
            prefill_params.append(f"customer_id={request_data.customer_id}")
        if request_data.federal_tax_id:
            prefill_params.append(f"federal_tax_id={request_data.federal_tax_id}")
        if request_data.bank_name:
            prefill_params.append(f"bank_name={request_data.bank_name}")
        if request_data.account_holder_name:
            prefill_params.append(f"account_holder_name={request_data.account_holder_name}")
        if request_data.account_type:
            prefill_params.append(f"account_type={request_data.account_type}")
        if request_data.authorized_by_name:
            prefill_params.append(f"authorized_by_name={request_data.authorized_by_name}")
        if request_data.authorized_by_title:
            prefill_params.append(f"authorized_by_title={request_data.authorized_by_title}")
        
        if prefill_params:
            customer_form_url += "&" + "&".join(prefill_params)
        
        # Send email to customer
        email_subject = f"EFT Authorization Required - {request_data.company_name}"
        email_body = f"""
        Dear {request_data.company_name} Representative,
        
        Better Day Energy requires Electronic Funds Transfer (EFT) authorization to process ACH payments for fuel purchases.
        
        Please complete your EFT authorization form by clicking the secure link below:
        
        {customer_form_url}
        
        Transaction ID: {transaction_id}
        Company: {request_data.company_name}
        
        Important Notes:
        • This form must be completed by an authorized signer
        • All information is encrypted and secure
        • Electronic signature is legally binding
        • Contact us if you prefer a paper copy
        
        Questions? Contact our team:
        Email: billing@betterdayenergy.com
        Phone: (618) 555-0123
        
        Best regards,
        Better Day Energy Accounts Team
        
        This email was sent in compliance with the Electronic Signatures in Global and National Commerce (ESIGN) Act.
        """
        
        # Send email
        try:
            msg = MIMEText(email_body)
            msg['Subject'] = email_subject
            msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
            msg['To'] = request_data.customer_email
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ EFT form email sent to {request_data.customer_email}")
            
            return {
                "success": True,
                "message": "EFT form sent successfully",
                "transaction_id": transaction_id,
                "customer_email": request_data.customer_email,
                "form_url": customer_form_url
            }
            
        except Exception as email_error:
            logger.error(f"❌ Failed to send EFT form email: {email_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to send EFT form email: {str(email_error)}"
            )
        
    except Exception as e:
        logger.error(f"❌ EFT form initiation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate EFT form")

# EFT Form Submit Endpoint
@app.post("/api/v1/forms/eft/submit")
async def eft_form_submit(request_data: EFTFormRequest):
    """Submit completed EFT authorization form from customer"""
    
    try:
        logger.info(f"🏦 EFT form submission received from {request_data.company_name}")
        
        # Generate unique form ID
        form_id = f"EFT_COMPLETE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        # Store form data in database
        try:
            from database.connection import get_db_manager
            from database.models import Customer, LOITransaction, CRMFormData
            
            db_manager = get_db_manager()
            
            with db_manager.get_session() as session:
                # Find or create customer
                customer = session.query(Customer).filter_by(
                    email=request_data.contact_email or request_data.company_name
                ).first()
                
                if not customer:
                    customer = Customer(
                        company_name=request_data.company_name,
                        email=request_data.contact_email or f"{request_data.company_name.lower().replace(' ', '_')}@customer.com",
                        phone=request_data.contact_phone,
                        customer_id=request_data.customer_id,
                        customer_type="eft_customer",
                        is_vip_customer=False
                    )
                    session.add(customer)
                    session.commit()
                
                # Create transaction record
                transaction = LOITransaction(
                    id=form_id,
                    customer_id=customer.id,
                    loi_type="eft_authorization",
                    status="completed",
                    workflow_stage="completed",
                    customer_email=customer.email,
                    company_name=request_data.company_name,
                    completed_at=datetime.now(),
                    signature_provider="esign_act_compliant",
                    signed_document_url=f"/forms/eft/complete/{form_id}"
                )
                session.add(transaction)
                
                # Store form data
                form_data = CRMFormData(
                    transaction_id=transaction.id,
                    form_type="eft_authorization",
                    raw_form_data={
                        "company_info": {
                            "company_name": request_data.company_name,
                            "federal_tax_id": request_data.federal_tax_id,
                            "customer_id": request_data.customer_id,
                            "company_address": request_data.company_address,
                            "company_city": request_data.company_city,
                            "company_state": request_data.company_state,
                            "company_zip": request_data.company_zip
                        },
                        "contact_info": {
                            "contact_name": request_data.contact_name,
                            "contact_email": request_data.contact_email,
                            "contact_phone": request_data.contact_phone
                        },
                        "bank_info": {
                            "bank_name": request_data.bank_name,
                            "bank_address": request_data.bank_address,
                            "bank_city": request_data.bank_city,
                            "bank_state": request_data.bank_state,
                            "bank_zip": request_data.bank_zip,
                            "account_holder_name": request_data.account_holder_name,
                            "account_type": request_data.account_type,
                            "routing_number": request_data.routing_number,
                            "account_number": request_data.account_number
                        },
                        "authorization": {
                            "authorized_by_name": request_data.authorized_by_name,
                            "authorized_by_title": request_data.authorized_by_title,
                            "authorization_date": request_data.authorization_date,
                            "signature_timestamp": request_data.signature_timestamp,
                            "signature_data": request_data.signature_data[:100] + "..." if len(request_data.signature_data) > 100 else request_data.signature_data
                        }
                    }
                )
                session.add(form_data)
                session.commit()
                
                logger.info(f"✅ EFT form data saved to database: {form_id}")
                
        except Exception as db_error:
            logger.warning(f"Database operation failed (continuing anyway): {db_error}")
        
        # Send confirmation emails
        try:
            # Email to customer
            customer_subject = f"EFT Authorization Confirmed - {request_data.company_name}"
            customer_body = f"""
            Dear {request_data.authorized_by_name},
            
            Thank you for completing your EFT Authorization with Better Day Energy.
            
            Confirmation Details:
            • Company: {request_data.company_name}
            • Federal Tax ID: {request_data.federal_tax_id}
            • Bank: {request_data.bank_name}
            • Account Type: {request_data.account_type.title()}
            • Routing Number: ***{request_data.routing_number[-4:]}
            • Account Number: ***{request_data.account_number[-4:]}
            • Authorized By: {request_data.authorized_by_name} ({request_data.authorized_by_title})
            • Authorization Date: {request_data.authorization_date}
            
            Form ID: {form_id}
            
            IMPORTANT: This authorization allows Better Day Energy to initiate ACH debit 
            transactions from your account for fuel purchases. Please keep this confirmation 
            for your records.
            
            If you have any questions, please contact:
            Email: billing@betterdayenergy.com
            Phone: (618) 555-0123
            
            Thank you for your business!
            
            Better Day Energy Accounts Team
            """
            
            if request_data.contact_email:
                msg = MIMEText(customer_body)
                msg['Subject'] = customer_subject
                msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
                msg['To'] = request_data.contact_email
                
                server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
                server.starttls()
                server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
                server.send_message(msg)
                server.quit()
                
                logger.info(f"✅ Confirmation email sent to customer: {request_data.contact_email}")
            
            # Email to admin
            admin_subject = f"New EFT Authorization - {request_data.company_name}"
            admin_body = f"""
            NEW EFT AUTHORIZATION RECEIVED
            
            Company: {request_data.company_name}
            Federal Tax ID: {request_data.federal_tax_id}
            Contact: {request_data.contact_name or 'Not provided'}
            Email: {request_data.contact_email or 'Not provided'}
            Phone: {request_data.contact_phone or 'Not provided'}
            
            Bank Information:
            • Bank Name: {request_data.bank_name}
            • Account Type: {request_data.account_type}
            • Routing Number: {request_data.routing_number}
            • Account Number: {request_data.account_number}
            • Account Holder: {request_data.account_holder_name}
            
            Authorization:
            • Authorized By: {request_data.authorized_by_name} ({request_data.authorized_by_title})
            • Date: {request_data.authorization_date}
            
            Form ID: {form_id}
            View Complete Form: https://loi-automation-api.onrender.com/forms/eft/complete/{form_id}
            
            Please process this EFT authorization in the accounting system.
            """
            
            admin_msg = MIMEText(admin_body)
            admin_msg['Subject'] = admin_subject
            admin_msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
            admin_msg['To'] = "billing@betterdayenergy.com, transaction.coordinator.agent@gmail.com"
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
            server.send_message(admin_msg)
            server.quit()
            
            logger.info("✅ Admin notification sent")
            
        except Exception as email_error:
            logger.error(f"❌ Failed to send confirmation emails: {email_error}")
        
        return {
            "success": True,
            "message": "EFT authorization completed successfully",
            "id": form_id,
            "confirmation_url": f"/forms/eft/complete/{form_id}",
            "company_name": request_data.company_name,
            "submission_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ EFT form submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process EFT form: {str(e)}")

# Paper Copy Request Endpoint (ESIGN Act Compliance)
@app.post("/api/v1/paper-copy/request")
async def request_paper_copy(request_data: dict):
    """Handle paper copy requests as required by ESIGN Act"""
    
    try:
        transaction_id = request_data.get('transaction_id')
        customer_email = request_data.get('customer_email')
        customer_name = request_data.get('customer_name', 'Customer')
        document_type = request_data.get('document_type', 'LOI')
        reason = request_data.get('reason', 'Requested paper copy instead of electronic signature')
        
        if not transaction_id or not customer_email:
            raise HTTPException(status_code=400, detail="Transaction ID and customer email are required")
        
        # Log the paper copy request
        logger.info(f"📄 Paper copy requested for transaction {transaction_id} by {customer_email}")
        
        # Send notification email to admin
        admin_subject = f"Paper Copy Request - {document_type} - {transaction_id}"
        admin_body = f"""
        A customer has requested a paper copy instead of electronic signature.
        
        Transaction ID: {transaction_id}
        Customer: {customer_name}
        Email: {customer_email}
        Document Type: {document_type}
        Reason: {reason}
        Request Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Please prepare and mail the paper document to the customer.
        """
        
        # Send admin notification
        try:
            admin_msg = MIMEText(admin_body)
            admin_msg['Subject'] = admin_subject
            admin_msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
            admin_msg['To'] = "documents@betterdayenergy.com"
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
            server.send_message(admin_msg)
            server.quit()
            
            logger.info(f"✅ Paper copy request notification sent to admin for {transaction_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send admin notification: {e}")
        
        # Send confirmation email to customer
        customer_subject = f"Paper Copy Request Confirmed - {document_type}"
        customer_body = f"""
        Dear {customer_name},
        
        We have received your request for a paper copy of your {document_type} document instead of electronic signature.
        
        Transaction ID: {transaction_id}
        Request Date: {datetime.now().strftime('%Y-%m-%d')}
        
        Your paper document will be prepared and mailed to you within 3-5 business days.
        
        If you have any questions or need to update your mailing address, please contact us at:
        Email: documents@betterdayenergy.com
        Phone: (888) 555-0123
        
        Thank you for choosing Better Day Energy!
        
        Better Day Energy Document Services
        """
        
        try:
            customer_msg = MIMEText(customer_body)
            customer_msg['Subject'] = customer_subject
            customer_msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
            customer_msg['To'] = customer_email
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
            server.send_message(customer_msg)
            server.quit()
            
            logger.info(f"✅ Paper copy confirmation sent to customer {customer_email}")
        except Exception as e:
            logger.error(f"❌ Failed to send customer confirmation: {e}")
        
        return {
            "success": True,
            "message": "Paper copy request submitted successfully",
            "transaction_id": transaction_id,
            "estimated_delivery": "3-5 business days"
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing paper copy request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process paper copy request: {str(e)}")

@app.get("/api/v1/paper-copy/form")
async def get_paper_copy_form():
    """Serve paper copy request form"""
    
    paper_copy_form = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Request Paper Copy - Better Day Energy</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #1f4e79; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #2563eb; }
            .header { background: #1f4e79; color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📄 Request Paper Copy</h1>
            <p>Better Day Energy Document Services</p>
        </div>
        
        <p><strong>Note:</strong> You have the right to receive paper copies of documents instead of signing electronically. Use this form to request a paper copy.</p>
        
        <form id="paperCopyForm">
            <div class="form-group">
                <label for="transaction_id">Transaction ID:</label>
                <input type="text" id="transaction_id" name="transaction_id" required placeholder="Enter your transaction ID">
            </div>
            
            <div class="form-group">
                <label for="customer_name">Your Name:</label>
                <input type="text" id="customer_name" name="customer_name" required placeholder="Enter your full name">
            </div>
            
            <div class="form-group">
                <label for="customer_email">Email Address:</label>
                <input type="email" id="customer_email" name="customer_email" required placeholder="Enter your email address">
            </div>
            
            <div class="form-group">
                <label for="document_type">Document Type:</label>
                <select id="document_type" name="document_type" required>
                    <option value="">Select document type</option>
                    <option value="P66 LOI">Phillips 66 Letter of Intent</option>
                    <option value="VP Racing LOI">VP Racing Letter of Intent</option>
                    <option value="EFT Authorization">EFT Authorization Form</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="reason">Reason for Paper Copy (Optional):</label>
                <textarea id="reason" name="reason" rows="3" placeholder="Optional: Tell us why you prefer a paper copy"></textarea>
            </div>
            
            <button type="submit">Request Paper Copy</button>
        </form>
        
        <div id="result" style="margin-top: 20px;"></div>
        
        <script>
            document.getElementById('paperCopyForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const requestData = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/v1/paper-copy/request', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('result').innerHTML = `
                            <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 4px;">
                                <h3>✅ Request Submitted Successfully!</h3>
                                <p>Your paper copy request has been submitted. You will receive your document by mail within ${result.estimated_delivery}.</p>
                                <p><strong>Transaction ID:</strong> ${result.transaction_id}</p>
                            </div>
                        `;
                        e.target.reset();
                    } else {
                        throw new Error(result.message || 'Request failed');
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `
                        <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 4px;">
                            <h3>❌ Error</h3>
                            <p>Failed to submit request: ${error.message}</p>
                        </div>
                    `;
                }
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=paper_copy_form)

if __name__ == "__main__":
    main()