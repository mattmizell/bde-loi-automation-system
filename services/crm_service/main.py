#!/usr/bin/env python3
"""
Better Day Energy - CRM Service
Standalone customer relationship management service with caching and multi-app support
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

from services.crm_service.api.contacts import ContactAPI
from services.crm_service.api.search import SearchAPI  
from services.crm_service.api.sync import SyncAPI
from services.crm_service.api.auth import AuthAPI
from services.crm_service.services.sync_service import CRMSyncService
from services.crm_service.config.settings import CRM_SERVICE_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CRMServiceHandler(BaseHTTPRequestHandler):
    """HTTP handler for CRM service requests"""
    
    def __init__(self, *args, **kwargs):
        # Initialize API handlers
        self.contact_api = ContactAPI()
        self.search_api = SearchAPI()
        self.sync_api = SyncAPI()
        self.auth_api = AuthAPI()
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
            
            # API routes
            if path == "/api/contacts":
                self.contact_api.list_contacts(self, query_params)
            elif path.startswith("/api/contacts/") and path.count('/') == 3:
                contact_id = path.split('/')[-1]
                self.contact_api.get_contact(self, contact_id)
            elif path == "/api/sync/status":
                self.sync_api.get_sync_status(self)
            elif path == "/api/auth/permissions":
                self.auth_api.get_permissions(self)
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
            
            # API routes
            if path == "/api/contacts" or path == "/api/create_contact":
                self.contact_api.create_contact(self, post_data)
            elif path == "/api/contacts/search" or path == "/api/search_contacts":
                self.search_api.search_contacts(self, post_data)
            elif path == "/api/sync/trigger":
                self.sync_api.trigger_sync(self)
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
            
            if path.startswith("/api/contacts/") and path.count('/') == 3:
                contact_id = path.split('/')[-1]
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length) if content_length > 0 else b''
                self.contact_api.update_contact(self, contact_id, post_data)
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
            
            if path.startswith("/api/contacts/") and path.count('/') == 3:
                contact_id = path.split('/')[-1]
                self.contact_api.delete_contact(self, contact_id)
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling DELETE request: {e}")
            self.send_error(500, str(e))
    
    def send_health_check(self):
        """Send health check response"""
        health_data = {
            "service": "crm-service",
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
    """Start the CRM service"""
    logger.info("🚀 Starting Better Day Energy CRM Service")
    
    # Start background sync service
    sync_service = CRMSyncService()
    sync_service.start_service()
    
    # Start HTTP server
    port = CRM_SERVICE_CONFIG['port']
    server_address = ('', port)
    httpd = HTTPServer(server_address, CRMServiceHandler)
    
    logger.info(f"🌐 CRM Service running on port {port}")
    logger.info(f"📊 API endpoint: http://localhost:{port}/api/")
    logger.info(f"🔍 Health check: http://localhost:{port}/health")
    logger.info("📋 Ready for multi-application CRM requests")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down CRM service...")
        sync_service.stop_service()
        httpd.shutdown()

if __name__ == "__main__":
    main()