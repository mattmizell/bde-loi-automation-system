#!/usr/bin/env python3
"""
Better Day Energy - Document Management Service
Standalone document processing service with PDF generation and signature management
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.document_service.api.documents import DocumentAPI
from services.document_service.api.signatures import SignatureAPI  
from services.document_service.api.templates import TemplateAPI
from services.document_service.api.pdf import PDFAPI
from services.document_service.api.auth import DocumentAuthAPI
from services.document_service.config.settings import DOCUMENT_SERVICE_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentServiceHandler(BaseHTTPRequestHandler):
    """HTTP handler for document service requests"""
    
    def __init__(self, *args, **kwargs):
        # Initialize API handlers
        self.document_api = DocumentAPI()
        self.signature_api = SignatureAPI()
        self.template_api = TemplateAPI()
        self.pdf_api = PDFAPI()
        self.auth_api = DocumentAuthAPI()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query_params = parse_qs(parsed_path.query)
            
            # Health check
            if path == "/health":
                self.send_health_check()
                return
            
            # Document routes
            if path == "/api/documents":
                self.document_api.list_documents(self, query_params)
            elif path.startswith("/api/documents/") and path.count('/') == 3:
                document_id = path.split('/')[-1]
                self.document_api.get_document(self, document_id)
            
            # Signature routes
            elif path.startswith("/api/documents/") and path.endswith("/signatures"):
                document_id = path.split('/')[-2]
                self.signature_api.list_document_signatures(self, document_id)
            elif path.startswith("/api/signatures/"):
                signature_id = path.split('/')[-1]
                self.signature_api.get_signature(self, signature_id)
            
            # Template routes
            elif path == "/api/templates":
                self.template_api.list_templates(self, query_params)
            elif path.startswith("/api/templates/") and path.count('/') == 3:
                template_id = path.split('/')[-1]
                self.template_api.get_template(self, template_id)
            
            # PDF routes
            elif path.startswith("/api/documents/") and path.endswith("/pdf"):
                document_id = path.split('/')[-2]
                self.pdf_api.generate_pdf(self, document_id, query_params)
            
            # Signature UI routes
            elif path.startswith("/signature/"):
                signature_id = path.split('/')[-1]
                self.signature_api.serve_signature_page(self, signature_id)
            
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Document routes
            if path == "/api/documents":
                self.document_api.create_document(self, post_data)
            elif path.startswith("/api/documents/") and path.endswith("/send"):
                document_id = path.split('/')[-2]
                self.document_api.send_document(self, document_id, post_data)
            
            # Signature routes
            elif path.startswith("/api/documents/") and path.endswith("/signatures"):
                document_id = path.split('/')[-2]
                self.signature_api.create_signature_request(self, document_id, post_data)
            elif path.startswith("/api/signatures/") and path.endswith("/sign"):
                signature_id = path.split('/')[-2]
                self.signature_api.submit_signature(self, signature_id, post_data)
            
            # Template routes
            elif path == "/api/templates":
                self.template_api.create_template(self, post_data)
            elif path.startswith("/api/templates/") and path.endswith("/generate"):
                template_id = path.split('/')[-2]
                self.template_api.generate_document(self, template_id, post_data)
            
            # Authentication routes
            elif path == "/api/auth/verify":
                self.auth_api.verify_token(self, post_data)
            
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.send_error(500, str(e))
    
    def do_PUT(self):
        """Handle PUT requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Document routes
            if path.startswith("/api/documents/") and path.count('/') == 3:
                document_id = path.split('/')[-1]
                self.document_api.update_document(self, document_id, post_data)
            
            # Template routes
            elif path.startswith("/api/templates/") and path.count('/') == 3:
                template_id = path.split('/')[-1]
                self.template_api.update_template(self, template_id, post_data)
            
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling PUT request: {e}")
            self.send_error(500, str(e))
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Document routes
            if path.startswith("/api/documents/") and path.count('/') == 3:
                document_id = path.split('/')[-1]
                self.document_api.delete_document(self, document_id)
            
            # Template routes
            elif path.startswith("/api/templates/") and path.count('/') == 3:
                template_id = path.split('/')[-1]
                self.template_api.delete_template(self, template_id)
            
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling DELETE request: {e}")
            self.send_error(500, str(e))
    
    def send_health_check(self):
        """Send health check response"""
        health_data = {
            "service": "document-service",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(health_data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

def main():
    """Start the Document Management service"""
    logger.info("📄 Starting Better Day Energy Document Management Service")
    
    # Start HTTP server
    port = int(os.getenv('PORT', DOCUMENT_SERVICE_CONFIG['port']))
    server_address = ('', port)
    httpd = HTTPServer(server_address, DocumentServiceHandler)
    
    logger.info(f"🌐 Document Service running on port {port}")
    logger.info(f"📊 API endpoint: http://localhost:{port}/api/")
    logger.info(f"🔍 Health check: http://localhost:{port}/health")
    logger.info(f"✍️  Signature UI: http://localhost:{port}/signature/{{id}}")
    logger.info("📋 Ready for document processing requests")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Document service...")
        httpd.shutdown()

if __name__ == "__main__":
    main()