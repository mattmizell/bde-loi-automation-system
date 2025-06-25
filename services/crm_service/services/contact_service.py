"""
Contact Service
Business logic for contact management operations
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.models.contact import Contact
from services.crm_service.data.contact_repository import ContactRepository

logger = logging.getLogger(__name__)

class ContactService:
    """Business logic for contact operations"""
    
    def __init__(self):
        self.repository = ContactRepository()
    
    def list_contacts(self, limit: int = 50, offset: int = 0) -> Tuple[List[Contact], int]:
        """List contacts with pagination"""
        try:
            contacts = self.repository.get_contacts(limit=limit, offset=offset)
            total_count = self.repository.count_contacts()
            
            logger.info(f"Retrieved {len(contacts)} contacts (total: {total_count})")
            return contacts, total_count
            
        except Exception as e:
            logger.error(f"Error listing contacts: {e}")
            return [], 0
    
    def get_contact(self, contact_id: str) -> Optional[Contact]:
        """Get specific contact by ID"""
        try:
            contact = self.repository.get_contact_by_id(contact_id)
            
            if contact:
                logger.info(f"Retrieved contact {contact_id}: {contact.display_name}")
            else:
                logger.warning(f"Contact not found: {contact_id}")
            
            return contact
            
        except Exception as e:
            logger.error(f"Error getting contact {contact_id}: {e}")
            return None
    
    def create_contact(self, contact_data: dict) -> Optional[Contact]:
        """Create new contact"""
        try:
            # Validate and normalize data
            normalized_data = self._normalize_contact_data(contact_data)
            
            # Check for duplicates
            if self._is_duplicate_contact(normalized_data):
                logger.warning(f"Duplicate contact detected: {normalized_data.get('email')}")
                return None
            
            # Create contact
            contact = Contact.from_dict(normalized_data)
            contact.created_at = datetime.now()
            contact.updated_at = datetime.now()
            
            # Save to repository
            saved_contact = self.repository.create_contact(contact)
            
            if saved_contact:
                logger.info(f"Created contact {saved_contact.id}: {saved_contact.display_name}")
                
                # Queue for LACRM sync
                self._queue_crm_sync(saved_contact, 'create')
            
            return saved_contact
            
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None
    
    def update_contact(self, contact_id: str, update_data: dict) -> Optional[Contact]:
        """Update existing contact"""
        try:
            # Get existing contact
            existing_contact = self.repository.get_contact_by_id(contact_id)
            if not existing_contact:
                logger.warning(f"Contact not found for update: {contact_id}")
                return None
            
            # Normalize and validate update data
            normalized_data = self._normalize_contact_data(update_data, partial=True)
            
            # Apply updates
            updated_contact = self._apply_contact_updates(existing_contact, normalized_data)
            updated_contact.updated_at = datetime.now()
            
            # Save to repository
            saved_contact = self.repository.update_contact(updated_contact)
            
            if saved_contact:
                logger.info(f"Updated contact {contact_id}: {saved_contact.display_name}")
                
                # Queue for LACRM sync
                self._queue_crm_sync(saved_contact, 'update')
            
            return saved_contact
            
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            return None
    
    def delete_contact(self, contact_id: str) -> bool:
        """Delete contact"""
        try:
            # Get contact for logging
            contact = self.repository.get_contact_by_id(contact_id)
            if not contact:
                logger.warning(f"Contact not found for deletion: {contact_id}")
                return False
            
            # Delete from repository
            success = self.repository.delete_contact(contact_id)
            
            if success:
                logger.info(f"Deleted contact {contact_id}: {contact.display_name}")
                
                # Queue for LACRM sync
                self._queue_crm_sync(contact, 'delete')
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting contact {contact_id}: {e}")
            return False
    
    def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Get contact by email address"""
        try:
            contact = self.repository.get_contact_by_email(email)
            
            if contact:
                logger.info(f"Found contact by email {email}: {contact.display_name}")
            
            return contact
            
        except Exception as e:
            logger.error(f"Error getting contact by email {email}: {e}")
            return None
    
    def _normalize_contact_data(self, data: dict, partial: bool = False) -> dict:
        """Normalize and validate contact data"""
        normalized = {}
        
        # String fields
        string_fields = ['first_name', 'last_name', 'company_name', 'email', 'phone']
        for field in string_fields:
            if field in data:
                value = data[field]
                if value is not None:
                    normalized[field] = str(value).strip()
        
        # Email validation
        if 'email' in normalized and normalized['email']:
            email = normalized['email'].lower()
            if '@' not in email:
                raise ValueError(f"Invalid email format: {email}")
            normalized['email'] = email
        
        # Phone normalization (remove formatting)
        if 'phone' in normalized and normalized['phone']:
            phone = ''.join(c for c in normalized['phone'] if c.isdigit())
            if len(phone) >= 10:  # Minimum valid phone length
                normalized['phone'] = phone
        
        # Address handling
        if 'address' in data and isinstance(data['address'], dict):
            normalized['address'] = {
                'street': str(data['address'].get('street', '')).strip(),
                'city': str(data['address'].get('city', '')).strip(),
                'state': str(data['address'].get('state', '')).strip(),
                'zip': str(data['address'].get('zip', '')).strip(),
                'country': str(data['address'].get('country', 'US')).strip(),
            }
        
        # Custom fields
        if 'custom_fields' in data and isinstance(data['custom_fields'], dict):
            normalized['custom_fields'] = data['custom_fields']
        
        # Validation for non-partial updates
        if not partial:
            if not normalized.get('first_name') and not normalized.get('company_name'):
                raise ValueError("Either first_name or company_name is required")
        
        return normalized
    
    def _is_duplicate_contact(self, contact_data: dict) -> bool:
        """Check if contact is a duplicate"""
        if not contact_data.get('email'):
            return False
        
        existing = self.repository.get_contact_by_email(contact_data['email'])
        return existing is not None
    
    def _apply_contact_updates(self, contact: Contact, updates: dict) -> Contact:
        """Apply updates to contact object"""
        for field, value in updates.items():
            if hasattr(contact, field):
                setattr(contact, field, value)
        
        return contact
    
    def _queue_crm_sync(self, contact: Contact, operation: str):
        """Queue contact for LACRM synchronization"""
        try:
            # Import here to avoid circular dependencies
            from services.crm_service.services.sync_service import CRMSyncService
            
            sync_service = CRMSyncService()
            sync_service.queue_contact_operation(contact, operation)
            
        except Exception as e:
            logger.error(f"Error queuing CRM sync for contact {contact.id}: {e}")