"""
Search API Handler
Advanced contact search with fuzzy matching and ranking
"""

import json
import logging
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.services.search_service import SearchService
from services.crm_service.api.auth import AuthAPI

logger = logging.getLogger(__name__)

class SearchAPI:
    """Contact search API operations"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.auth_api = AuthAPI()
    
    def search_contacts(self, handler, post_data: bytes):
        """POST /api/v1/contacts/search - Search contacts with advanced filtering"""
        try:
            # Verify authentication
            if not self.auth_api.verify_request_auth(handler):
                return
            
            # Parse request data
            data = json.loads(post_data.decode('utf-8'))
            
            query = data.get('query', '').strip()
            if not query:
                self._send_error_response(handler, 400, "Search query is required")
                return
            
            # Parse search options
            options = {
                'limit': min(int(data.get('limit', 20)), 100),  # Max 100 results
                'fuzzy_threshold': float(data.get('fuzzy_threshold', 0.6)),
                'include_score': data.get('include_score', True),
                'fields': data.get('fields', ['all']),  # Which fields to search
                'sort_by': data.get('sort_by', 'score'),  # 'score', 'name', 'company'
            }
            
            # Perform search
            search_results = self.search_service.search_contacts(query, options)
            
            # Format response
            response_data = {
                "query": query,
                "results": [result.to_dict() for result in search_results],
                "total_found": len(search_results),
                "search_options": options,
                "timestamp": datetime.now().isoformat()
            }
            
            self._send_json_response(handler, 200, response_data)
            logger.info(f"Search for '{query}' returned {len(search_results)} results")
            
        except json.JSONDecodeError:
            self._send_error_response(handler, 400, "Invalid JSON in request body")
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            self._send_error_response(handler, 500, "Search failed")
    
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