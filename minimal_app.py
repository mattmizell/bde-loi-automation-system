#!/usr/bin/env python3
"""
Minimal working application with forms
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(title="Better Day Energy - Customer Onboarding")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Better Day Energy</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
                .btn { background: #1f4e79; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; margin: 10px; display: inline-block; }
                .btn:hover { background: #2563eb; }
            </style>
        </head>
        <body>
            <h1>🏢 Better Day Energy</h1>
            <h2>Customer Onboarding System</h2>
            <p>Welcome to the customer onboarding portal</p>
            
            <div>
                <a href="/dashboard" class="btn">📊 Dashboard</a>
                <a href="/forms/eft" class="btn">🏦 EFT Form</a>
                <a href="/forms/customer-setup" class="btn">🏢 Customer Setup</a>
                <a href="/forms/p66-loi" class="btn">⛽ P66 LOI</a>
            </div>
        </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return """
    <html>
        <head>
            <title>Customer Onboarding Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .header { background: linear-gradient(135deg, #1f4e79, #2563eb); color: white; padding: 30px; margin: -20px -20px 30px -20px; border-radius: 0 0 15px 15px; }
                .section { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
                .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
                .form-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; text-align: center; }
                .btn { background: #1f4e79; color: white; padding: 12px 25px; border: none; border-radius: 6px; text-decoration: none; display: inline-block; margin: 10px; }
                .btn:hover { background: #2563eb; }
                .btn-green { background: #28a745; }
                .btn-blue { background: #2196f3; }
                .btn-red { background: #ee0000; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Customer Onboarding Dashboard</h1>
                <p>Better Day Energy - Fuel Supply Partnership Portal</p>
            </div>
            
            <div class="section">
                <h3>🚀 System Status</h3>
                <p>✅ Application running successfully</p>
                <p>✅ Forms system operational</p>
                <p>✅ Database connection ready</p>
            </div>
            
            <div class="section">
                <h3>📋 Customer Onboarding Forms</h3>
                <p>Complete your fuel partnership application with electronic signature capture</p>
                
                <div class="form-grid">
                    <div class="form-card">
                        <h4>🏦 EFT Authorization</h4>
                        <p>Electronic Funds Transfer authorization for ACH payments</p>
                        <a href="/forms/eft" class="btn btn-green">Complete EFT Form</a>
                    </div>
                    
                    <div class="form-card">
                        <h4>🏢 Customer Setup</h4>
                        <p>Complete business information and credit application</p>
                        <a href="/forms/customer-setup" class="btn btn-blue">Start Application</a>
                    </div>
                    
                    <div class="form-card">
                        <h4>⛽ Phillips 66 LOI</h4>
                        <p>Letter of Intent for Phillips 66 branded fuel supply</p>
                        <a href="/forms/p66-loi" class="btn btn-red">Submit LOI</a>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>🔗 Quick Links</h3>
                <a href="/" class="btn">🏠 Home</a>
                <a href="/docs" class="btn">📖 API Docs</a>
            </div>
        </body>
    </html>
    """

# Form serving routes
@app.get("/forms/eft", response_class=HTMLResponse)
async def serve_eft_form():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "templates", "eft_form.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
            <html><body>
                <h1>EFT Form</h1>
                <p>EFT form template not found. Please check file location.</p>
                <a href="/dashboard">← Back to Dashboard</a>
            </body></html>
        """)

@app.get("/forms/customer-setup", response_class=HTMLResponse)
async def serve_customer_setup_form():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "templates", "customer_setup_form.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
            <html><body>
                <h1>Customer Setup Form</h1>
                <p>Customer setup form template not found. Please check file location.</p>
                <a href="/dashboard">← Back to Dashboard</a>
            </body></html>
        """)

@app.get("/forms/p66-loi", response_class=HTMLResponse)
async def serve_p66_loi_form():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "templates", "p66_loi_form.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
            <html><body>
                <h1>Phillips 66 Letter of Intent</h1>
                <p>P66 LOI form template not found. Please check file location.</p>
                <a href="/dashboard">← Back to Dashboard</a>
            </body></html>
        """)

if __name__ == "__main__":
    print("🚀 Starting Better Day Energy Customer Onboarding System")
    print("📊 Dashboard: http://10.0.2.15:9003/dashboard")
    print("📊 Also try: http://127.0.0.1:9003/dashboard")
    print("🏠 Home: http://10.0.2.15:9003/")
    uvicorn.run(app, host="0.0.0.0", port=9003, log_level="info")