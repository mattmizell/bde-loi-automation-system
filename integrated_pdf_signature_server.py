#!/usr/bin/env python3
"""
REPLACED WITH NEW CUSTOMER ONBOARDING DASHBOARD
This file serves the new dashboard instead of the old signature system
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedSignatureHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves the new dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.serve_home()
        elif self.path == '/test':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "NEW DASHBOARD ACTIVE", "message": "Customer onboarding system"}')
        elif self.path.endswith('.html'):
            # Serve HTML files
            filename = self.path[1:]  # Remove leading /
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.send_error(404)
        else:
            self.send_error(404)
    
    def serve_home(self):
        """Serve the new customer onboarding dashboard"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Better Day Energy - Customer Onboarding Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #1f4e79, #2563eb);
            color: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .alert {
            background: #fff3cd;
            border: 2px solid #ffc107;
            color: #856404;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .forms-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }
        
        .form-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 3px solid transparent;
        }
        
        .form-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        
        .form-card.eft {
            border-color: #4caf50;
            background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        }
        
        .form-card.setup {
            border-color: #2196f3;
            background: linear-gradient(135deg, #e3f2fd, #f0f7ff);
        }
        
        .form-card.loi {
            border-color: #ee0000;
            background: linear-gradient(135deg, #fee, #fff0f0);
        }
        
        .form-card .icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        .form-card h3 {
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: #333;
        }
        
        .form-card p {
            color: #666;
            margin-bottom: 25px;
            line-height: 1.6;
        }
        
        .btn {
            display: inline-block;
            padding: 15px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .btn-green {
            background: #4caf50;
            color: white;
        }
        
        .btn-green:hover {
            background: #45a049;
            transform: translateY(-2px);
        }
        
        .btn-blue {
            background: #2196f3;
            color: white;
        }
        
        .btn-blue:hover {
            background: #1976d2;
            transform: translateY(-2px);
        }
        
        .btn-red {
            background: #ee0000;
            color: white;
        }
        
        .btn-red:hover {
            background: #cc0000;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 Better Day Energy</h1>
            <p>Customer Onboarding Portal - Fuel Supply Partnership</p>
        </div>
        
        <div class="alert">
            <strong>📋 Welcome to the Customer Onboarding System!</strong><br>
            Complete the forms below to start your fuel supply partnership with Better Day Energy. Each form includes electronic signature capture for a seamless experience.
        </div>
        
        <div class="forms-grid">
            <div class="form-card eft">
                <div class="icon">🏦</div>
                <h3>EFT Authorization</h3>
                <p>Electronic Funds Transfer authorization for ACH payments. Set up automatic billing for fuel purchases with bank-level security.</p>
                <a href="eft_form.html" class="btn btn-green">Complete EFT Form</a>
            </div>
            
            <div class="form-card setup">
                <div class="icon">🏢</div>
                <h3>Customer Setup Document</h3>
                <p>Complete business information and credit application. Multi-step process covering company details, references, and equipment specifications.</p>
                <a href="customer_setup_form.html" class="btn btn-blue">Start Application</a>
            </div>
            
            <div class="form-card loi">
                <div class="icon">⛽</div>
                <h3>Phillips 66 Letter of Intent</h3>
                <p>Letter of Intent for Phillips 66 branded fuel supply agreement. Includes volume commitments and incentive package calculations.</p>
                <a href="p66_loi_form.html" class="btn btn-red">Submit LOI</a>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

def main():
    """Run the server"""
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), IntegratedSignatureHandler)
    logger.info(f"🚀 NEW Customer Onboarding Dashboard running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    main()