"""
CRM Sync Service
Background synchronization service for LACRM integration
"""

import logging
import threading
import time
import queue
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.models.contact import Contact
from services.crm_service.data.contact_repository import ContactRepository
from services.crm_service.config.settings import LACRM_CONFIG

logger = logging.getLogger(__name__)

class CRMSyncService:
    """Background LACRM synchronization service"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for sync service"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.repository = ContactRepository()
        
        # Sync state
        self._running = False
        self._sync_thread = None
        self._last_sync = None
        self._sync_interval = 300  # 5 minutes
        
        # Operation queue for pending writes
        self._operation_queue = queue.Queue()
        self._error_count = 0
        self._max_retries = 3
        
        # LACRM API settings
        self.api_base = LACRM_CONFIG['api_base']
        self.api_token = LACRM_CONFIG['api_token']
        
        logger.info("CRM Sync Service initialized")
    
    def start_service(self):
        """Start background sync service"""
        if self._running:
            logger.warning("Sync service already running")
            return
        
        self._running = True
        self._sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self._sync_thread.start()
        
        logger.info("CRM Sync Service started")
    
    def stop_service(self):
        """Stop background sync service"""
        if not self._running:
            return
        
        self._running = False
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5)
        
        logger.info("CRM Sync Service stopped")
    
    def is_running(self) -> bool:
        """Check if sync service is running"""
        return self._running and self._sync_thread and self._sync_thread.is_alive()
    
    def get_last_sync_time(self) -> Optional[str]:
        """Get last sync timestamp"""
        return self._last_sync.isoformat() if self._last_sync else None
    
    def get_contact_count(self) -> int:
        """Get total contact count"""
        return self.repository.count_contacts()
    
    def get_pending_writes_count(self) -> int:
        """Get pending operation count"""
        return self._operation_queue.qsize()
    
    def get_error_count(self) -> int:
        """Get error count"""
        return self._error_count
    
    def trigger_manual_sync(self) -> bool:
        """Trigger manual sync"""
        try:
            self._perform_full_sync()
            return True
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            self._error_count += 1
            return False
    
    def queue_contact_operation(self, contact: Contact, operation: str):
        """Queue contact operation for sync"""
        operation_data = {
            'contact': contact,
            'operation': operation,  # 'create', 'update', 'delete'
            'timestamp': datetime.now(),
            'retries': 0
        }
        
        self._operation_queue.put(operation_data)
        logger.debug(f"Queued {operation} operation for contact {contact.id}")
    
    def _sync_worker(self):
        """Background sync worker thread"""
        logger.info("Sync worker thread started")
        
        while self._running:
            try:
                # Process pending operations
                self._process_pending_operations()
                
                # Perform periodic full sync
                if self._should_perform_full_sync():
                    self._perform_full_sync()
                
                # Sleep between cycles
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in sync worker: {e}")
                self._error_count += 1
                time.sleep(30)  # Wait longer on error
        
        logger.info("Sync worker thread stopped")
    
    def _should_perform_full_sync(self) -> bool:
        """Check if full sync should be performed"""
        if not self._last_sync:
            return True
        
        time_since_sync = datetime.now() - self._last_sync
        return time_since_sync.total_seconds() >= self._sync_interval
    
    def _perform_full_sync(self):
        """Perform full sync with LACRM"""
        logger.info("Starting full LACRM sync")
        start_time = datetime.now()
        
        try:
            # Fetch contacts from LACRM
            lacrm_contacts = self._fetch_lacrm_contacts()
            
            # Process each contact
            updated_count = 0
            created_count = 0
            
            for lacrm_contact in lacrm_contacts:
                try:
                    # Convert LACRM format to our Contact model
                    contact = self._lacrm_to_contact(lacrm_contact)
                    
                    # Check if contact exists
                    existing_contact = self.repository.get_contact_by_id(contact.id)
                    
                    if existing_contact:
                        # Update if LACRM version is newer
                        if self._is_lacrm_newer(contact, existing_contact):
                            contact.created_at = existing_contact.created_at  # Preserve creation time
                            self.repository.update_contact(contact)
                            updated_count += 1
                    else:
                        # Create new contact
                        self.repository.create_contact(contact)
                        created_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing LACRM contact: {e}")
                    self._error_count += 1
            
            self._last_sync = datetime.now()
            sync_duration = (self._last_sync - start_time).total_seconds()
            
            logger.info(f"Full sync completed in {sync_duration:.1f}s: "
                       f"created {created_count}, updated {updated_count}")
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            self._error_count += 1
            raise
    
    def _process_pending_operations(self):
        """Process pending write operations to LACRM"""
        processed = 0
        max_batch = 10  # Process max 10 operations per cycle
        
        while processed < max_batch and not self._operation_queue.empty():
            try:
                operation_data = self._operation_queue.get_nowait()
                
                if self._process_single_operation(operation_data):
                    processed += 1
                else:
                    # Requeue with retry logic
                    operation_data['retries'] += 1
                    if operation_data['retries'] < self._max_retries:
                        self._operation_queue.put(operation_data)
                    else:
                        logger.error(f"Max retries exceeded for operation: {operation_data}")
                        self._error_count += 1
                
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing operation: {e}")
                self._error_count += 1
        
        if processed > 0:
            logger.debug(f"Processed {processed} pending operations")
    
    def _process_single_operation(self, operation_data: Dict[str, Any]) -> bool:
        """Process single LACRM operation"""
        contact = operation_data['contact']
        operation = operation_data['operation']
        
        try:
            if operation == 'create':
                return self._create_lacrm_contact(contact)
            elif operation == 'update':
                return self._update_lacrm_contact(contact)
            elif operation == 'delete':
                return self._delete_lacrm_contact(contact)
            else:
                logger.error(f"Unknown operation: {operation}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing {operation} for contact {contact.id}: {e}")
            return False
    
    def _fetch_lacrm_contacts(self) -> List[Dict[str, Any]]:
        """Fetch all contacts from LACRM API"""
        contacts = []
        page = 1
        per_page = 100
        
        while True:
            try:
                response = requests.get(
                    f"{self.api_base}/contacts",
                    headers={'Authorization': f'Bearer {self.api_token}'},
                    params={'page': page, 'per_page': per_page},
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                page_contacts = data.get('contacts', [])
                
                if not page_contacts:
                    break
                
                contacts.extend(page_contacts)
                page += 1
                
                # Respect rate limits
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching LACRM contacts (page {page}): {e}")
                raise
        
        logger.info(f"Fetched {len(contacts)} contacts from LACRM")
        return contacts
    
    def _create_lacrm_contact(self, contact: Contact) -> bool:
        """Create contact in LACRM"""
        try:
            payload = self._contact_to_lacrm(contact)
            
            response = requests.post(
                f"{self.api_base}/contacts",
                headers={
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Created LACRM contact: {contact.display_name}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating LACRM contact {contact.id}: {e}")
            return False
    
    def _update_lacrm_contact(self, contact: Contact) -> bool:
        """Update contact in LACRM"""
        try:
            payload = self._contact_to_lacrm(contact)
            
            response = requests.put(
                f"{self.api_base}/contacts/{contact.id}",
                headers={
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Updated LACRM contact: {contact.display_name}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating LACRM contact {contact.id}: {e}")
            return False
    
    def _delete_lacrm_contact(self, contact: Contact) -> bool:
        """Delete contact from LACRM"""
        try:
            response = requests.delete(
                f"{self.api_base}/contacts/{contact.id}",
                headers={'Authorization': f'Bearer {self.api_token}'},
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Deleted LACRM contact: {contact.display_name}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting LACRM contact {contact.id}: {e}")
            return False
    
    def _lacrm_to_contact(self, lacrm_data: Dict[str, Any]) -> Contact:
        """Convert LACRM contact data to Contact model"""
        return Contact(
            id=str(lacrm_data.get('ContactId', '')),
            first_name=lacrm_data.get('FirstName', ''),
            last_name=lacrm_data.get('LastName', ''),
            company_name=lacrm_data.get('CompanyName'),
            email=lacrm_data.get('Email'),
            phone=lacrm_data.get('Phone'),
            address={
                'street': lacrm_data.get('Address', ''),
                'city': lacrm_data.get('City', ''),
                'state': lacrm_data.get('State', ''),
                'zip': lacrm_data.get('Zip', ''),
                'country': lacrm_data.get('Country', 'US')
            } if any([lacrm_data.get('Address'), lacrm_data.get('City')]) else None,
            custom_fields=lacrm_data.get('CustomFields', {}),
            created_at=self._parse_lacrm_date(lacrm_data.get('DateCreated')),
            updated_at=self._parse_lacrm_date(lacrm_data.get('DateUpdated')),
            last_synced=datetime.now(),
            source='lacrm'
        )
    
    def _contact_to_lacrm(self, contact: Contact) -> Dict[str, Any]:
        """Convert Contact model to LACRM format"""
        data = {
            'FirstName': contact.first_name,
            'LastName': contact.last_name,
            'Email': contact.email,
            'Phone': contact.phone,
        }
        
        if contact.company_name:
            data['CompanyName'] = contact.company_name
        
        if contact.address:
            data.update({
                'Address': contact.address.get('street', ''),
                'City': contact.address.get('city', ''),
                'State': contact.address.get('state', ''),
                'Zip': contact.address.get('zip', ''),
                'Country': contact.address.get('country', 'US')
            })
        
        if contact.custom_fields:
            data['CustomFields'] = contact.custom_fields
        
        return data
    
    def _parse_lacrm_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse LACRM date string to datetime"""
        if not date_str:
            return None
        
        try:
            # LACRM typically uses ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse LACRM date: {date_str}")
            return None
    
    def _is_lacrm_newer(self, lacrm_contact: Contact, local_contact: Contact) -> bool:
        """Check if LACRM contact is newer than local version"""
        if not lacrm_contact.updated_at or not local_contact.last_synced:
            return True
        
        return lacrm_contact.updated_at > local_contact.last_synced


# Global sync service instance
_sync_service = None

def get_sync_service() -> CRMSyncService:
    """Get singleton sync service instance"""
    global _sync_service
    if _sync_service is None:
        _sync_service = CRMSyncService()
    return _sync_service

def start_sync_service():
    """Start the global sync service"""
    service = get_sync_service()
    service.start_service()

def stop_sync_service():
    """Stop the global sync service"""
    service = get_sync_service()
    service.stop_service()