"""
Sync API Handler
LACRM synchronization management endpoints
"""

import json
import logging
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.api.auth import AuthAPI

logger = logging.getLogger(__name__)

class SyncAPI:
    """Sync management API operations"""
    
    def __init__(self):
        self.auth_api = AuthAPI()
    
    def get_sync_status(self, handler):
        """GET /api/v1/sync/status - Get sync status"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Get sync service instance
            from services.crm_service.services.sync_service import CRMSyncService
            sync_service = CRMSyncService()
            
            status_data = {
                "sync_active": sync_service.is_running(),
                "last_sync": sync_service.get_last_sync_time(),
                "total_contacts": sync_service.get_contact_count(),
                "pending_writes": sync_service.get_pending_writes_count(),
                "error_count": sync_service.get_error_count(),
                "service": "crm-service",
                "timestamp": datetime.now().isoformat()
            }
            
            self._send_json_response(handler, 200, status_data)
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            self._send_error_response(handler, 500, "Failed to get sync status")
    
    def trigger_sync(self, handler):
        """POST /api/v1/sync/trigger - Trigger manual sync"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Get sync service instance
            from services.crm_service.services.sync_service import CRMSyncService
            sync_service = CRMSyncService()
            
            # Trigger manual sync
            success = sync_service.trigger_manual_sync()
            
            if success:
                response_data = {
                    "message": "Manual sync triggered successfully",
                    "timestamp": datetime.now().isoformat()
                }
                self._send_json_response(handler, 200, response_data)
            else:
                self._send_error_response(handler, 500, "Failed to trigger sync")
            
        except Exception as e:
            logger.error(f"Error triggering sync: {e}")
            self._send_error_response(handler, 500, "Failed to trigger sync")
    
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