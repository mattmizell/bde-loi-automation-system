"""
Google Drive Integration

Handles document storage and management in Google Drive for LOI documents.
Provides folder organization, permission management, and file versioning.
"""

import asyncio
import aiofiles
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import io

from ..core.loi_transaction_queue import LOITransaction

logger = logging.getLogger(__name__)

class GoogleDriveIntegration:
    """
    Integration with Google Drive for LOI document storage and management.
    
    Capabilities:
    - Upload LOI documents to organized folder structure
    - Set appropriate sharing permissions
    - Generate shareable links
    - Manage file versions and metadata
    - Organize by customer, date, and status
    """
    
    def __init__(self, credentials_file: str, root_folder_id: Optional[str] = None):
        self.credentials_file = credentials_file
        self.root_folder_id = root_folder_id
        self.service = None
        
        # Folder structure configuration
        self.folder_structure = {
            'pending_signature': 'LOI Documents - Pending Signature',
            'completed': 'LOI Documents - Completed', 
            'failed': 'LOI Documents - Failed',
            'templates': 'LOI Templates',
            'archive': 'LOI Archive'
        }
        
        # File naming convention
        self.naming_convention = "LOI_{company_name}_{date}_{transaction_id}"
        
        self.integration_stats = {
            'documents_uploaded': 0,
            'folders_created': 0,
            'permissions_set': 0,
            'errors_encountered': 0,
            'last_upload': None
        }
        
        # Initialize Google Drive service
        self._initialize_service()
        
        logger.info("☁️ Google Drive Integration initialized")
    
    def _initialize_service(self):
        """Initialize Google Drive API service"""
        
        try:
            # Load service account credentials
            if os.path.exists(self.credentials_file):
                creds = ServiceAccountCredentials.from_service_account_file(
                    self.credentials_file,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                
                self.service = build('drive', 'v3', credentials=creds)
                logger.info("✅ Google Drive service initialized with service account")
            else:
                logger.error(f"❌ Credentials file not found: {self.credentials_file}")
                raise Exception(f"Google Drive credentials file not found: {self.credentials_file}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Drive service: {e}")
            raise e
    
    async def upload_loi_document(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Upload LOI document to Google Drive"""
        
        try:
            # Get document file path from transaction
            document_path = transaction.document_data.get('file_path')
            if not document_path or not os.path.exists(document_path):
                raise Exception("Document file not found for upload")
            
            # Determine target folder
            target_folder_id = await self._get_or_create_folder(
                self.folder_structure['pending_signature']
            )
            
            # Create customer-specific subfolder
            customer_folder_id = await self._get_or_create_customer_folder(
                target_folder_id, 
                transaction.customer_data.get('company_name', 'Unknown')
            )
            
            # Generate file name
            file_name = self._generate_file_name(transaction)
            
            # Upload document
            file_metadata = {
                'name': file_name,
                'parents': [customer_folder_id],
                'description': f"LOI for {transaction.customer_data.get('company_name')} - Transaction {transaction.id}"
            }
            
            # Upload file
            media = MediaFileUpload(
                document_path,
                mimetype='application/pdf',
                resumable=True
            )
            
            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            ).execute()
            
            # Set sharing permissions
            sharing_result = await self._set_document_permissions(
                uploaded_file['id'],
                transaction.customer_data.get('email')
            )
            
            # Update stats
            self.integration_stats['documents_uploaded'] += 1
            self.integration_stats['last_upload'] = datetime.now()
            
            result = {
                'success': True,
                'file_id': uploaded_file['id'],
                'file_name': uploaded_file['name'],
                'web_view_link': uploaded_file['webViewLink'],
                'download_link': uploaded_file['webContentLink'],
                'drive_url': uploaded_file['webViewLink'],
                'folder_id': customer_folder_id,
                'sharing_configured': sharing_result['success'],
                'uploaded_at': datetime.now().isoformat()
            }
            
            logger.info(f"☁️ Successfully uploaded LOI document for {transaction.id}")
            return result
            
        except Exception as e:
            self.integration_stats['errors_encountered'] += 1
            logger.error(f"❌ Failed to upload document for {transaction.id}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'retry_recommended': True
            }
    
    async def _get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Get existing folder or create new one"""
        
        try:
            # Search for existing folder
            parent_query = f"and '{parent_id}' in parents" if parent_id else ""
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' {parent_query}"
            
            results = self.service.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                # Folder exists
                return folders[0]['id']
            else:
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                if parent_id:
                    folder_metadata['parents'] = [parent_id]
                elif self.root_folder_id:
                    folder_metadata['parents'] = [self.root_folder_id]
                
                created_folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                self.integration_stats['folders_created'] += 1
                logger.info(f"📁 Created folder: {folder_name}")
                
                return created_folder['id']
                
        except HttpError as e:
            logger.error(f"❌ Error managing folder {folder_name}: {e}")
            raise e
    
    async def _get_or_create_customer_folder(self, parent_folder_id: str, company_name: str) -> str:
        """Get or create customer-specific folder"""
        
        # Clean company name for folder name
        clean_name = self._clean_folder_name(company_name)
        folder_name = f"{clean_name}_{datetime.now().strftime('%Y')}"
        
        return await self._get_or_create_folder(folder_name, parent_folder_id)
    
    def _clean_folder_name(self, name: str) -> str:
        """Clean company name for use as folder name"""
        
        if not name:
            return "Unknown_Company"
        
        # Remove/replace invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        clean_name = name
        
        for char in invalid_chars:
            clean_name = clean_name.replace(char, '_')
        
        # Limit length and remove extra spaces
        clean_name = clean_name.strip()[:50]
        
        return clean_name if clean_name else "Unknown_Company"
    
    def _generate_file_name(self, transaction: LOITransaction) -> str:
        """Generate standardized file name for LOI document"""
        
        company_name = self._clean_folder_name(
            transaction.customer_data.get('company_name', 'Unknown')
        )
        
        date_str = datetime.now().strftime('%Y%m%d')
        transaction_short = transaction.id[:8]
        
        return f"LOI_{company_name}_{date_str}_{transaction_short}.pdf"
    
    async def _set_document_permissions(self, file_id: str, customer_email: Optional[str]) -> Dict[str, Any]:
        """Set sharing permissions for LOI document"""
        
        try:
            permissions_set = []
            
            # Make file viewable by anyone with link (for e-signature service)
            public_permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=public_permission
            ).execute()
            
            permissions_set.append('public_read')
            
            # If customer email provided, give them edit access
            if customer_email and '@' in customer_email:
                customer_permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': customer_email
                }
                
                try:
                    self.service.permissions().create(
                        fileId=file_id,
                        body=customer_permission,
                        sendNotificationEmail=False
                    ).execute()
                    
                    permissions_set.append('customer_write')
                except HttpError as e:
                    logger.warning(f"⚠️ Could not set customer permissions for {customer_email}: {e}")
            
            self.integration_stats['permissions_set'] += len(permissions_set)
            
            return {
                'success': True,
                'permissions_set': permissions_set
            }
            
        except Exception as e:
            logger.error(f"❌ Error setting permissions for file {file_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def move_document_to_completed(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Move document to completed folder after signature"""
        
        try:
            if not transaction.google_drive_url:
                raise Exception("No Google Drive URL found for transaction")
            
            # Extract file ID from URL
            file_id = self._extract_file_id_from_url(transaction.google_drive_url)
            if not file_id:
                raise Exception("Could not extract file ID from Google Drive URL")
            
            # Get completed folder
            completed_folder_id = await self._get_or_create_folder(
                self.folder_structure['completed']
            )
            
            # Get customer subfolder in completed
            customer_folder_id = await self._get_or_create_customer_folder(
                completed_folder_id,
                transaction.customer_data.get('company_name', 'Unknown')
            )
            
            # Move file
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ','.join(file.get('parents', []))
            
            self.service.files().update(
                fileId=file_id,
                addParents=customer_folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            # Update file name to indicate completion
            current_file = self.service.files().get(fileId=file_id, fields='name').execute()
            completed_name = current_file['name'].replace('.pdf', '_COMPLETED.pdf')
            
            self.service.files().update(
                fileId=file_id,
                body={'name': completed_name}
            ).execute()
            
            logger.info(f"📁 Moved document to completed folder for {transaction.id}")
            
            return {
                'success': True,
                'new_folder_id': customer_folder_id,
                'new_file_name': completed_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error moving document to completed for {transaction.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_file_id_from_url(self, drive_url: str) -> Optional[str]:
        """Extract file ID from Google Drive URL"""
        
        try:
            # Handle different Google Drive URL formats
            if '/file/d/' in drive_url:
                # Format: https://drive.google.com/file/d/FILE_ID/view
                start = drive_url.find('/file/d/') + 8
                end = drive_url.find('/', start)
                if end == -1:
                    end = len(drive_url)
                return drive_url[start:end]
            
            elif 'id=' in drive_url:
                # Format: https://drive.google.com/open?id=FILE_ID
                start = drive_url.find('id=') + 3
                end = drive_url.find('&', start)
                if end == -1:
                    end = len(drive_url)
                return drive_url[start:end]
            
            return None
            
        except Exception:
            return None
    
    async def create_shared_folder_for_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shared folder for ongoing customer collaboration"""
        
        try:
            company_name = customer_data.get('company_name', 'Unknown')
            clean_name = self._clean_folder_name(company_name)
            
            # Create customer folder
            folder_name = f"{clean_name}_LOI_Collaboration"
            
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if self.root_folder_id:
                folder_metadata['parents'] = [self.root_folder_id]
            
            created_folder = self.service.files().create(
                body=folder_metadata,
                fields='id,webViewLink'
            ).execute()
            
            # Set permissions for customer
            customer_email = customer_data.get('email')
            if customer_email:
                permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': customer_email
                }
                
                self.service.permissions().create(
                    fileId=created_folder['id'],
                    body=permission,
                    sendNotificationEmail=True
                ).execute()
            
            self.integration_stats['folders_created'] += 1
            
            return {
                'success': True,
                'folder_id': created_folder['id'],
                'folder_url': created_folder['webViewLink'],
                'customer_access_granted': customer_email is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating customer folder: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration performance statistics"""
        
        return {
            'integration_type': 'google_drive',
            'stats': self.integration_stats,
            'folder_structure': self.folder_structure,
            'root_folder_id': self.root_folder_id
        }
    
    async def cleanup_old_documents(self, days_old: int = 365) -> Dict[str, Any]:
        """Clean up old LOI documents (archive old files)"""
        
        try:
            # Get archive folder
            archive_folder_id = await self._get_or_create_folder(
                self.folder_structure['archive']
            )
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cutoff_str = cutoff_date.isoformat()
            
            # Search for old files
            query = f"createdTime < '{cutoff_str}' and name contains 'LOI_'"
            
            results = self.service.files().list(
                q=query,
                fields='files(id, name, parents, createdTime)'
            ).execute()
            
            old_files = results.get('files', [])
            archived_count = 0
            
            for file in old_files:
                try:
                    # Move to archive folder
                    previous_parents = ','.join(file.get('parents', []))
                    
                    self.service.files().update(
                        fileId=file['id'],
                        addParents=archive_folder_id,
                        removeParents=previous_parents
                    ).execute()
                    
                    archived_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not archive file {file['name']}: {e}")
            
            logger.info(f"🗂️ Archived {archived_count} old LOI documents")
            
            return {
                'success': True,
                'files_archived': archived_count,
                'archive_folder_id': archive_folder_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Async wrapper function for coordinator integration
async def handle_google_drive_integration(transaction: LOITransaction) -> Dict[str, Any]:
    """Handle Google Drive integration - async wrapper for coordinator"""
    
    # Note: In production, this would come from configuration
    credentials_file = "google_drive_credentials.json"  # Configure via environment
    root_folder_id = None  # Optional root folder ID
    
    drive_integration = GoogleDriveIntegration(credentials_file, root_folder_id)
    return await drive_integration.upload_loi_document(transaction)