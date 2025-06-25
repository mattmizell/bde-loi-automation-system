"""
Document Service Authentication API
"""

import json
import logging
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.document_service.config.settings import AUTH_CONFIG

logger = logging.getLogger(__name__)

class DocumentAuthAPI:
    """Document service authentication operations"""
    
    def __init__(self):
        self.api_keys = AUTH_CONFIG['api_keys']
    
    def verify_request_auth(self, handler) -> bool:
        """Verify request authentication"""
        try:
            # Check Authorization header
            auth_header = handler.headers.get('Authorization', '')
            
            if not auth_header:
                self._send_error_response(handler, 401, "Authorization header required")
                return False
            
            # Extract token
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            elif auth_header.startswith('ApiKey '):
                token = auth_header[7:]
            else:
                self._send_error_response(handler, 401, "Invalid authorization format")
                return False
            
            # Validate token
            if not self._is_valid_token(token):
                self._send_error_response(handler, 401, "Invalid or expired token")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying authentication: {e}")
            self._send_error_response(handler, 500, "Authentication error")
            return False
    
    def verify_token(self, handler, post_data: bytes):
        """POST /api/v1/auth/verify - Verify token validity"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            token = data.get('token', '')
            
            is_valid = self._is_valid_token(token)
            
            response_data = {
                "valid": is_valid,
                "timestamp": datetime.now().isoformat()
            }
            
            self._send_json_response(handler, 200, response_data)
            
        except json.JSONDecodeError:
            self._send_error_response(handler, 400, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            self._send_error_response(handler, 500, "Token verification failed")
    
    def _is_valid_token(self, token: str) -> bool:
        """Validate API token"""
        # Simple API key validation
        return token in self.api_keys.values()
    
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