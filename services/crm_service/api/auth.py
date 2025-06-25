"""
Authentication API Handler
Multi-application authentication for CRM service
"""

import json
import logging
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.config.settings import CRM_BRIDGE_TOKENS, APP_PERMISSIONS

logger = logging.getLogger(__name__)

class AuthAPI:
    """Authentication and authorization for CRM service"""
    
    def verify_token(self, handler, post_data: bytes):
        """POST /api/v1/auth/verify - Verify application token"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            token = data.get('token')
            
            if not token:
                self._send_error_response(handler, 400, "Token is required")
                return
            
            # Verify token
            app_info = self._get_app_from_token(token)
            
            if not app_info:
                self._send_error_response(handler, 401, "Invalid token")
                return
            
            response_data = {
                "authenticated": True,
                "app_name": app_info["app_name"],
                "permissions": app_info["permissions"],
                "service": "CRM Service",
                "timestamp": datetime.now().isoformat()
            }
            
            self._send_json_response(handler, 200, response_data)
            logger.info(f"Token verified for app: {app_info['app_name']}")
            
        except json.JSONDecodeError:
            self._send_error_response(handler, 400, "Invalid JSON in request body")
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            self._send_error_response(handler, 500, "Token verification failed")
    
    def get_permissions(self, handler):
        """GET /api/v1/auth/permissions - Get permissions for authenticated app"""
        try:
            # Verify authentication
            app_info = self.verify_request_auth(handler, return_info=True)
            if not app_info:
                return
            
            response_data = {
                "app_name": app_info["app_name"],
                "permissions": app_info["permissions"],
                "token_valid": True,
                "timestamp": datetime.now().isoformat()
            }
            
            self._send_json_response(handler, 200, response_data)
            
        except Exception as e:
            logger.error(f"Error getting permissions: {e}")
            self._send_error_response(handler, 500, "Failed to get permissions")
    
    def verify_request_auth(self, handler, return_info=False):
        """Verify authentication for incoming request"""
        try:
            # Check Authorization header
            auth_header = handler.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self._send_error_response(handler, 401, "Missing or invalid Authorization header")
                return None if return_info else False
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            app_info = self._get_app_from_token(token)
            
            if not app_info:
                self._send_error_response(handler, 401, "Invalid token")
                return None if return_info else False
            
            return app_info if return_info else True
            
        except Exception as e:
            logger.error(f"Error verifying request auth: {e}")
            self._send_error_response(handler, 500, "Authentication verification failed")
            return None if return_info else False
    
    def _get_app_from_token(self, token: str):
        """Get application info from token"""
        for app_name, app_token in CRM_BRIDGE_TOKENS.items():
            if token == app_token:
                return {
                    "app_name": app_name,
                    "permissions": APP_PERMISSIONS.get(app_name, []),
                    "token": token
                }
        return None
    
    def check_permission(self, app_info: dict, required_permission: str) -> bool:
        """Check if app has required permission"""
        return required_permission in app_info.get("permissions", [])
    
    def _send_json_response(self, handler, status_code: int, data: dict):
        """Send JSON response"""
        handler.send_response(status_code)
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(data, default=str).encode())
    
    def _send_error_response(self, handler, status_code: int, message: str):
        """Send error response"""
        error_data = {
            "error": message,
            "status": status_code,
            "timestamp": datetime.now().isoformat()
        }
        self._send_json_response(handler, status_code, error_data)