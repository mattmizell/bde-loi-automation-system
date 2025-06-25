"""
Contact API Handler
RESTful contact management endpoints
"""

import json
import logging
from datetime import datetime
from typing import List, Optional
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.models.contact import Contact
from services.crm_service.services.contact_service import ContactService
from services.crm_service.api.auth import AuthAPI

logger = logging.getLogger(__name__)

class ContactAPI:
    """Contact CRUD API operations"""
    
    def __init__(self):
        self.contact_service = ContactService()
        self.auth_api = AuthAPI()
    
    def list_contacts(self, handler, query_params):
        """GET /api/v1/contacts - List contacts with pagination"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Parse pagination parameters
            limit = int(query_params.get('limit', [50])[0])
            offset = int(query_params.get('offset', [0])[0])
            
            # Enforce reasonable limits
            limit = min(limit, 500)
            offset = max(offset, 0)
            
            # Get contacts from service
            contacts, total_count = self.contact_service.list_contacts(limit=limit, offset=offset)
            
            # Convert to API format
            contact_data = [contact.to_dict() for contact in contacts]
            
            response_data = {
                "contacts": contact_data,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
            
            self._send_json_response(handler, 200, response_data)
            logger.info(f"Listed {len(contacts)} contacts (offset={offset}, limit={limit})")
            
        except Exception as e:
            logger.error(f"Error listing contacts: {e}")
            self._send_error_response(handler, 500, "Failed to list contacts")
    
    def get_contact(self, handler, contact_id: str):
        """GET /api/v1/contacts/{id} - Get specific contact"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Get contact from service
            contact = self.contact_service.get_contact(contact_id)
            
            if not contact:
                self._send_error_response(handler, 404, "Contact not found")
                return
            
            self._send_json_response(handler, 200, contact.to_dict())
            logger.info(f"Retrieved contact {contact_id}")
            
        except Exception as e:
            logger.error(f"Error getting contact {contact_id}: {e}")
            self._send_error_response(handler, 500, "Failed to get contact")
    
    def create_contact(self, handler, post_data: bytes):
        """POST /api/v1/contacts - Create new contact"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Parse request data
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate required fields
            if not data.get('first_name') and not data.get('company_name'):
                self._send_error_response(handler, 400, "Either first_name or company_name is required")
                return
            
            # Create contact through service
            contact = self.contact_service.create_contact(data)
            
            if not contact:
                self._send_error_response(handler, 500, "Failed to create contact")
                return
            
            self._send_json_response(handler, 201, contact.to_dict())
            logger.info(f"Created contact {contact.id}: {contact.display_name}")
            
        except json.JSONDecodeError:
            self._send_error_response(handler, 400, "Invalid JSON in request body")
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            self._send_error_response(handler, 500, "Failed to create contact")
    
    def update_contact(self, handler, contact_id: str, post_data: bytes):
        """PUT /api/v1/contacts/{id} - Update contact"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Parse request data
            data = json.loads(post_data.decode('utf-8'))
            
            # Update contact through service
            contact = self.contact_service.update_contact(contact_id, data)
            
            if not contact:
                self._send_error_response(handler, 404, "Contact not found")
                return
            
            self._send_json_response(handler, 200, contact.to_dict())
            logger.info(f"Updated contact {contact_id}: {contact.display_name}")
            
        except json.JSONDecodeError:
            self._send_error_response(handler, 400, "Invalid JSON in request body")
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            self._send_error_response(handler, 500, "Failed to update contact")
    
    def delete_contact(self, handler, contact_id: str):
        """DELETE /api/v1/contacts/{id} - Delete contact"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Delete contact through service
            success = self.contact_service.delete_contact(contact_id)
            
            if not success:
                self._send_error_response(handler, 404, "Contact not found")
                return
            
            self._send_json_response(handler, 200, {"message": "Contact deleted successfully"})
            logger.info(f"Deleted contact {contact_id}")
            
        except Exception as e:
            logger.error(f"Error deleting contact {contact_id}: {e}")
            self._send_error_response(handler, 500, "Failed to delete contact")
    
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