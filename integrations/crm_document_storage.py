"""
Less Annoying CRM Document Storage Integration

Handles document storage using CRM file attachments instead of Google Drive.
Much simpler than OAuth - just uses the existing CRM API key.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import base64
from pathlib import Path

from ..core.loi_transaction_queue import LOITransaction

logger = logging.getLogger(__name__)

class CRMDocumentStorage:
    """
    Document storage using Less Annoying CRM file attachments.
    
    Capabilities:
    - Store LOI PDFs as contact attachments
    - Organize documents by contact
    - Add document metadata as notes
    - Retrieve documents when needed
    - Much simpler than Google Drive OAuth
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.lessannoyingcrm.com/v2/"):
        self.api_key = api_key
        self.base_url = base_url
        
        # Document organization settings
        self.document_types = {
            'loi_draft': 'LOI Draft Document',
            'loi_final': 'LOI Final Document', 
            'loi_signed': 'LOI Signed Document',
            'supporting_docs': 'Supporting Documents'
        }
        
        self.storage_stats = {
            'documents_stored': 0,
            'documents_retrieved': 0,
            'storage_errors': 0,
            'last_operation': None
        }
        
        logger.info("📁 CRM Document Storage initialized")
    
    async def store_loi_document(self, transaction: LOITransaction, document_path: str, 
                                document_type: str = 'loi_final') -> Dict[str, Any]:
        """Store LOI document as CRM contact attachment"""
        
        try:
            # Get customer CRM contact ID
            crm_contact_id = await self._get_contact_id(transaction)
            if not crm_contact_id:
                raise Exception("No CRM contact ID found for customer")
            
            # Read document file
            if not os.path.exists(document_path):
                raise Exception(f"Document file not found: {document_path}")
            
            # Prepare file for upload
            file_name = f"{self.document_types.get(document_type, 'LOI Document')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Upload file to CRM contact
            attachment_result = await self._upload_file_to_contact(
                contact_id=crm_contact_id,
                file_path=document_path,
                file_name=file_name,
                description=f"LOI Document - Transaction ID: {transaction.id}"
            )
            
            if attachment_result['success']:
                # Add document metadata as contact note
                await self._add_document_note(
                    contact_id=crm_contact_id,
                    transaction_id=transaction.id,
                    document_type=document_type,
                    file_name=file_name,
                    attachment_id=attachment_result.get('attachment_id')
                )
                
                # Update stats
                self.storage_stats['documents_stored'] += 1
                self.storage_stats['last_operation'] = datetime.now()
                
                logger.info(f"📁 Successfully stored LOI document for {transaction.id}")
                
                return {
                    'success': True,
                    'document_id': attachment_result.get('attachment_id'),
                    'file_name': file_name,
                    'storage_location': f"CRM Contact {crm_contact_id}",
                    'document_type': document_type,
                    'stored_at': datetime.now().isoformat(),
                    'crm_contact_id': crm_contact_id
                }
            else:
                raise Exception(f"Failed to upload file: {attachment_result.get('error')}")
                
        except Exception as e:
            self.storage_stats['storage_errors'] += 1
            logger.error(f"❌ Failed to store LOI document for {transaction.id}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'fallback_location': self._get_fallback_storage_path(transaction, document_type)
            }
    
    async def _get_contact_id(self, transaction: LOITransaction) -> Optional[str]:
        """Get CRM contact ID for the transaction customer"""
        
        # Check if we already have it in transaction data
        if hasattr(transaction, 'crm_form_data') and transaction.crm_form_data:
            contact_id = transaction.crm_form_data.get('crm_contact_id')
            if contact_id:
                return contact_id
        
        # Try to find by customer email
        customer_email = transaction.customer_data.get('email')
        if customer_email:
            return await self._find_contact_by_email(customer_email)
        
        return None
    
    async def _find_contact_by_email(self, email: str) -> Optional[str]:
        """Find CRM contact by email address"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": self.api_key
                }
                
                body = {
                    "Function": "SearchContacts",
                    "Parameters": {
                        "SearchTerm": email,
                        "SearchField": "Email"
                    }
                }
                
                async with session.post(self.base_url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'ErrorCode' not in data and data:
                            if isinstance(data, list) and data:
                                return data[0].get('ContactId')
                            elif isinstance(data, dict) and data.get('ContactId'):
                                return data.get('ContactId')
                    
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error finding contact by email {email}: {e}")
            return None
    
    async def _upload_file_to_contact(self, contact_id: str, file_path: str, 
                                     file_name: str, description: str) -> Dict[str, Any]:
        """Upload file as attachment to CRM contact"""
        
        try:
            # Read file and encode as base64
            with open(file_path, 'rb') as file:
                file_content = file.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": self.api_key
                }
                
                body = {
                    "Function": "CreateFile",
                    "Parameters": {
                        "ContactId": contact_id,
                        "FileName": file_name,
                        "FileData": file_base64,
                        "Description": description
                    }
                }
                
                async with session.post(self.base_url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'ErrorCode' not in data:
                            return {
                                'success': True,
                                'attachment_id': data.get('FileId'),
                                'file_name': file_name
                            }
                        else:
                            return {
                                'success': False,
                                'error': f"CRM API error {data.get('ErrorCode')}: {data.get('ErrorDescription')}"
                            }
                    else:
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}"
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _add_document_note(self, contact_id: str, transaction_id: str, 
                               document_type: str, file_name: str, attachment_id: str):
        """Add a note to the contact about the document"""
        
        try:
            note_text = f"""LOI Document Stored
Transaction ID: {transaction_id}
Document Type: {document_type}
File Name: {file_name}
Attachment ID: {attachment_id}
Stored: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: Better Day Energy LOI Automation"""
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": self.api_key
                }
                
                body = {
                    "Function": "CreateNote",
                    "Parameters": {
                        "ContactId": contact_id,
                        "Note": note_text
                    }
                }
                
                async with session.post(self.base_url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'ErrorCode' not in data:
                            logger.info(f"📝 Added document note to contact {contact_id}")
                        else:
                            logger.warning(f"⚠️ Failed to add note: {data.get('ErrorDescription')}")
                            
        except Exception as e:
            logger.error(f"❌ Error adding document note: {e}")
    
    async def retrieve_loi_documents(self, transaction: LOITransaction) -> List[Dict[str, Any]]:
        """Retrieve LOI documents for a transaction"""
        
        try:
            crm_contact_id = await self._get_contact_id(transaction)
            if not crm_contact_id:
                return []
            
            # Get contact files
            files = await self._get_contact_files(crm_contact_id)
            
            # Filter for LOI documents
            loi_documents = []
            for file_info in files:
                if self._is_loi_document(file_info, transaction.id):
                    loi_documents.append({
                        'file_id': file_info.get('FileId'),
                        'file_name': file_info.get('FileName'),
                        'description': file_info.get('Description'),
                        'created_date': file_info.get('CreatedDate'),
                        'file_size': file_info.get('FileSize'),
                        'download_url': f"{self.base_url}GetFile?FileId={file_info.get('FileId')}"
                    })
            
            self.storage_stats['documents_retrieved'] += len(loi_documents)
            
            return loi_documents
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve LOI documents for {transaction.id}: {e}")
            return []
    
    async def _get_contact_files(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get all files attached to a contact"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": self.api_key
                }
                
                body = {
                    "Function": "GetContact",
                    "Parameters": {
                        "ContactId": contact_id
                    }
                }
                
                async with session.post(self.base_url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'ErrorCode' not in data:
                            return data.get('Files', [])
                    
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error getting contact files: {e}")
            return []
    
    def _is_loi_document(self, file_info: Dict[str, Any], transaction_id: str) -> bool:
        """Check if a file is an LOI document for this transaction"""
        
        file_name = file_info.get('FileName', '').lower()
        description = file_info.get('Description', '').lower()
        
        # Check if it's an LOI document
        loi_indicators = ['loi', 'letter of intent']
        has_loi_indicator = any(indicator in file_name or indicator in description 
                              for indicator in loi_indicators)
        
        # Check if it's for this transaction
        has_transaction_id = str(transaction_id).lower() in description
        
        return has_loi_indicator or has_transaction_id
    
    def _get_fallback_storage_path(self, transaction: LOITransaction, document_type: str) -> str:
        """Get fallback local storage path if CRM storage fails"""
        
        fallback_dir = Path("./documents/fallback")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        
        customer_name = transaction.customer_data.get('company_name', 'unknown').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return str(fallback_dir / f"{customer_name}_{document_type}_{timestamp}.pdf")
    
    async def create_shareable_link(self, transaction: LOITransaction, file_id: str) -> Dict[str, Any]:
        """Create a shareable link for a document (CRM doesn't support public links)"""
        
        return {
            'success': True,
            'message': 'CRM documents are accessible through the CRM interface',
            'access_method': 'crm_login_required',
            'file_id': file_id,
            'instructions': 'Document can be accessed by logging into Less Annoying CRM and viewing the contact attachments'
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get document storage statistics"""
        
        return {
            'storage_type': 'less_annoying_crm',
            'stats': self.storage_stats,
            'document_types': self.document_types,
            'api_endpoint': self.base_url
        }

# Async wrapper function for coordinator integration
async def handle_document_storage(transaction: LOITransaction, document_path: str, 
                                 document_type: str = 'loi_final') -> Dict[str, Any]:
    """Handle document storage - async wrapper for coordinator"""
    
    # Get API key from environment
    import os
    api_key = os.getenv('CRM_API_KEY', '1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W')
    
    storage = CRMDocumentStorage(api_key)
    return await storage.store_loi_document(transaction, document_path, document_type)