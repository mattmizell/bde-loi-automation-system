#!/usr/bin/env python3
"""
Better Day Energy - API Gateway
Central routing service for CRM and Document Management services
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIGatewayHandler(BaseHTTPRequestHandler):
    """HTTP handler for API gateway routing"""
    
    # Service endpoints
    CRM_SERVICE_URL = "http://localhost:8001"
    DOCUMENT_SERVICE_URL = "http://localhost:8002"
    GATEWAY_PORT = 8000
    
    def do_GET(self):
        """Handle GET requests"""
        self._route_request('GET')
    
    def do_POST(self):
        """Handle POST requests"""
        self._route_request('POST')
    
    def do_PUT(self):
        """Handle PUT requests"""
        self._route_request('PUT')
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._route_request('DELETE')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def _route_request(self, method):
        """Route request to appropriate service"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Health check for gateway itself
            if path == "/health":
                self._send_gateway_health()
                return
            
            # Gateway status showing all services
            if path == "/status":
                self._send_gateway_status()
                return
            
            # Route to services based on path
            target_url = None
            service_name = None
            
            # CRM Service routes
            if (path.startswith("/api/contacts") or 
                path.startswith("/api/create_contact") or
                path.startswith("/api/search_contacts") or
                path.startswith("/api/sync")):
                target_url = self.CRM_SERVICE_URL
                service_name = "CRM Service"
            
            # Document Service routes  
            elif (path.startswith("/api/documents") or
                  path.startswith("/api/signatures") or
                  path.startswith("/api/templates") or
                  path.startswith("/signature/")):
                target_url = self.DOCUMENT_SERVICE_URL
                service_name = "Document Service"
            
            # Auth can go to either service
            elif path.startswith("/api/auth"):
                target_url = self.CRM_SERVICE_URL
                service_name = "CRM Service"
                
            else:
                self._send_error_response(404, "Endpoint not found")
                return
            
            # Forward request
            self._forward_request(method, target_url, service_name)
            
        except Exception as e:
            logger.error(f"Error routing {method} request: {e}")
            self._send_error_response(500, str(e))
    
    def _forward_request(self, method, target_url, service_name):
        """Forward request to target service"""
        try:
            # Prepare request data
            full_url = f"{target_url}{self.path}"
            headers = dict(self.headers)
            
            # Remove hop-by-hop headers
            hop_headers = ['connection', 'upgrade', 'proxy-authenticate', 'proxy-authorization',
                          'te', 'trailers', 'transfer-encoding']
            for header in hop_headers:
                headers.pop(header, None)
            
            # Read request body for POST/PUT
            body = None
            if method in ['POST', 'PUT']:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Make request to target service
            response = requests.request(
                method=method,
                url=full_url,
                headers=headers,
                data=body,
                timeout=30,
                allow_redirects=False
            )
            
            # Forward response
            self.send_response(response.status_code)
            
            # Forward response headers
            for name, value in response.headers.items():
                if name.lower() not in hop_headers:
                    self.send_header(name, value)
            
            # Add gateway headers
            self.send_header('X-Gateway-Service', service_name)
            self.send_header('X-Gateway-Timestamp', datetime.now().isoformat())
            
            self.end_headers()
            
            # Forward response body
            if response.content:
                self.wfile.write(response.content)
            
            logger.info(f"Forwarded {method} {self.path} to {service_name} -> {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to {service_name} at {target_url}")
            self._send_error_response(503, f"{service_name} unavailable")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to {service_name}")
            self._send_error_response(504, f"{service_name} timeout")
        except Exception as e:
            logger.error(f"Error forwarding to {service_name}: {e}")
            self._send_error_response(500, f"Gateway forwarding error")
    
    def _send_gateway_health(self):
        """Send gateway health check"""
        health_data = {
            "service": "api-gateway",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "routes": {
                "crm_service": f"{self.CRM_SERVICE_URL}/health",
                "document_service": f"{self.DOCUMENT_SERVICE_URL}/health"
            }
        }
        
        self._send_json_response(200, health_data)
        logger.info("Gateway health check requested")
    
    def _send_gateway_status(self):
        """Send comprehensive gateway status"""
        try:
            # Check service health
            services = {}
            
            # Check CRM Service
            try:
                response = requests.get(f"{self.CRM_SERVICE_URL}/health", timeout=5)
                services["crm_service"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": self.CRM_SERVICE_URL,
                    "response_time": response.elapsed.total_seconds() * 1000
                }
            except:
                services["crm_service"] = {
                    "status": "unavailable",
                    "url": self.CRM_SERVICE_URL,
                    "response_time": None
                }
            
            # Check Document Service
            try:
                response = requests.get(f"{self.DOCUMENT_SERVICE_URL}/health", timeout=5)
                services["document_service"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": self.DOCUMENT_SERVICE_URL,
                    "response_time": response.elapsed.total_seconds() * 1000
                }
            except:
                services["document_service"] = {
                    "status": "unavailable",
                    "url": self.DOCUMENT_SERVICE_URL,
                    "response_time": None
                }
            
            # Overall status
            all_healthy = all(s["status"] == "healthy" for s in services.values())
            overall_status = "healthy" if all_healthy else "degraded"
            
            status_data = {
                "gateway": {
                    "status": overall_status,
                    "port": self.GATEWAY_PORT,
                    "timestamp": datetime.now().isoformat()
                },
                "services": services,
                "routing": {
                    "crm_routes": ["/api/v1/contacts/*", "/api/v1/sync/*"],
                    "document_routes": ["/api/v1/documents/*", "/api/v1/signatures/*", "/api/v1/templates/*", "/signature/*"]
                }
            }
            
            self._send_json_response(200, status_data)
            logger.info("Gateway status check requested")
            
        except Exception as e:
            logger.error(f"Error getting gateway status: {e}")
            self._send_error_response(500, "Failed to get gateway status")
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _send_error_response(self, status_code: int, message: str):
        """Send error response"""
        error_data = {
            "error": message,
            "status": status_code,
            "timestamp": datetime.now().isoformat(),
            "gateway": "api-gateway"
        }
        self._send_json_response(status_code, error_data)

def main():
    """Start the API Gateway"""
    logger.info("🚪 Starting Better Day Energy API Gateway")
    
    port = APIGatewayHandler.GATEWAY_PORT
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIGatewayHandler)
    
    logger.info(f"🌐 API Gateway running on port {port}")
    logger.info(f"📊 Gateway status: http://localhost:{port}/status")
    logger.info(f"🔍 Gateway health: http://localhost:{port}/health")
    logger.info("🔗 Routing requests to:")
    logger.info(f"   📱 CRM Service: {APIGatewayHandler.CRM_SERVICE_URL}")
    logger.info(f"   📄 Document Service: {APIGatewayHandler.DOCUMENT_SERVICE_URL}")
    logger.info("🚀 Gateway ready for requests")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down API Gateway...")
        httpd.shutdown()

if __name__ == "__main__":
    main()