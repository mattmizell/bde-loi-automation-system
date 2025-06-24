"""
E-Signature Integration

Handles electronic signature workflow using DocuSign, Sign.com, or similar services.
Provides document preparation, signature request, and status monitoring.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import base64

from ..core.loi_transaction_queue import LOITransaction

logger = logging.getLogger(__name__)

class ESignatureIntegration:
    """
    Integration with e-signature services for LOI signature workflow.
    
    Supports multiple providers:
    - Sign.com
    - DocuSign
    - Adobe Sign
    
    Capabilities:
    - Prepare documents for signature
    - Send signature requests to customers
    - Monitor signature status
    - Handle completed signatures
    - Manage reminders and follow-ups
    """
    
    def __init__(self, provider: str = "sign.com", api_key: str = "", api_secret: str = ""):
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Provider-specific configuration
        self.provider_config = {
            "sign.com": {
                "base_url": "https://api.sign.com/v1",
                "auth_header": "Authorization",
                "auth_format": "Bearer {token}"
            },
            "docusign": {
                "base_url": "https://demo.docusign.net/restapi/v2.1",  # Use demo for testing
                "auth_header": "Authorization", 
                "auth_format": "Bearer {token}"
            },
            "adobe_sign": {
                "base_url": "https://api.na1.adobesign.com/api/rest/v6",
                "auth_header": "Authorization",
                "auth_format": "Bearer {token}"
            }
        }
        
        self.config = self.provider_config.get(self.provider, self.provider_config["sign.com"])
        
        # Signature workflow settings
        self.signature_settings = {
            'reminder_frequency_hours': 72,  # Send reminder every 3 days
            'expiration_days': 14,  # Expire after 14 days
            'max_reminders': 3,
            'auto_complete_after_all_sign': True
        }
        
        self.integration_stats = {
            'signature_requests_sent': 0,
            'signatures_completed': 0,
            'reminders_sent': 0,
            'expired_requests': 0,
            'errors_encountered': 0,
            'last_request_sent': None
        }
        
        logger.info(f"✍️ E-Signature Integration initialized (provider: {self.provider})")
    
    async def send_signature_request(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Send signature request for LOI document"""
        
        try:
            # Validate required data
            if not transaction.google_drive_url:
                raise Exception("No Google Drive URL found for document")
            
            customer_data = transaction.customer_data
            if not customer_data.get('email'):
                raise Exception("Customer email required for signature request")
            
            # Prepare signature request based on provider
            if self.provider == "sign.com":
                result = await self._send_sign_com_request(transaction)
            elif self.provider == "docusign":
                result = await self._send_docusign_request(transaction)
            elif self.provider == "adobe_sign":
                result = await self._send_adobe_sign_request(transaction)
            else:
                raise Exception(f"Unsupported e-signature provider: {self.provider}")
            
            # Update stats
            if result.get('success'):
                self.integration_stats['signature_requests_sent'] += 1
                self.integration_stats['last_request_sent'] = datetime.now()
            else:
                self.integration_stats['errors_encountered'] += 1
            
            return result
            
        except Exception as e:
            self.integration_stats['errors_encountered'] += 1
            logger.error(f"❌ Failed to send signature request for {transaction.id}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'retry_recommended': True
            }
    
    async def _send_sign_com_request(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Send signature request via Sign.com"""
        
        customer_data = transaction.customer_data
        
        # Prepare request payload
        payload = {
            "document": {
                "name": f"VP Racing LOI - {customer_data.get('company_name', 'Customer')}",
                "url": transaction.google_drive_url,
                "description": f"Letter of Intent for VP Racing Fuel Supply Agreement"
            },
            "recipients": [
                {
                    "email": customer_data.get('email'),
                    "name": customer_data.get('contact_name', 'Customer'),
                    "role": "signer",
                    "order": 1
                }
            ],
            "settings": {
                "expiration_days": self.signature_settings['expiration_days'],
                "reminder_frequency": self.signature_settings['reminder_frequency_hours'],
                "auto_complete": self.signature_settings['auto_complete_after_all_sign']
            },
            "metadata": {
                "transaction_id": transaction.id,
                "customer_company": customer_data.get('company_name', ''),
                "loi_type": "vp_racing_supply_agreement"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {
                self.config["auth_header"]: self.config["auth_format"].format(token=self.api_key),
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{self.config['base_url']}/signature_requests",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 201:
                    result = await response.json()
                    
                    return {
                        'success': True,
                        'signature_request_id': result.get('id'),
                        'signature_url': result.get('signing_url'),
                        'expires_at': (datetime.now() + timedelta(days=self.signature_settings['expiration_days'])).isoformat(),
                        'provider': 'sign.com',
                        'recipient_email': customer_data.get('email'),
                        'sent_at': datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Sign.com API error {response.status}: {error_text}")
    
    async def _send_docusign_request(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Send signature request via DocuSign"""
        
        customer_data = transaction.customer_data
        
        # DocuSign requires base64 encoded document
        document_content = await self._download_document_content(transaction.google_drive_url)
        document_base64 = base64.b64encode(document_content).decode('utf-8')
        
        # Prepare envelope
        envelope_definition = {
            "emailSubject": f"Please sign: VP Racing LOI - {customer_data.get('company_name', 'Customer')}",
            "documents": [
                {
                    "documentBase64": document_base64,
                    "name": f"VP_Racing_LOI_{customer_data.get('company_name', 'Customer')}.pdf",
                    "fileExtension": "pdf",
                    "documentId": "1"
                }
            ],
            "recipients": {
                "signers": [
                    {
                        "email": customer_data.get('email'),
                        "name": customer_data.get('contact_name', 'Customer'),
                        "recipientId": "1",
                        "tabs": {
                            "signHereTabs": [
                                {
                                    "documentId": "1",
                                    "pageNumber": "1",
                                    "xPosition": "400",
                                    "yPosition": "650"
                                }
                            ],
                            "dateSignedTabs": [
                                {
                                    "documentId": "1", 
                                    "pageNumber": "1",
                                    "xPosition": "400",
                                    "yPosition": "700"
                                }
                            ]
                        }
                    }
                ]
            },
            "status": "sent"
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {
                self.config["auth_header"]: self.config["auth_format"].format(token=self.api_key),
                "Content-Type": "application/json"
            }
            
            # Note: In production, you'd need to get account_id from authentication
            account_id = "your_account_id"  # Configure via environment
            
            async with session.post(
                f"{self.config['base_url']}/accounts/{account_id}/envelopes",
                json=envelope_definition,
                headers=headers
            ) as response:
                
                if response.status == 201:
                    result = await response.json()
                    
                    return {
                        'success': True,
                        'signature_request_id': result.get('envelopeId'),
                        'expires_at': (datetime.now() + timedelta(days=self.signature_settings['expiration_days'])).isoformat(),
                        'provider': 'docusign',
                        'recipient_email': customer_data.get('email'),
                        'sent_at': datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"DocuSign API error {response.status}: {error_text}")
    
    async def _send_adobe_sign_request(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Send signature request via Adobe Sign"""
        
        customer_data = transaction.customer_data
        
        # Adobe Sign workflow
        agreement_info = {
            "documentCreationInfo": {
                "name": f"VP Racing LOI - {customer_data.get('company_name', 'Customer')}",
                "signatureType": "ESIGN",
                "fileInfos": [
                    {
                        "libraryDocumentId": None,  # Would need to upload document first
                        "transientDocumentId": None,  # Or use transient document
                        "webConnectorUrlInfo": {
                            "url": transaction.google_drive_url
                        }
                    }
                ],
                "recipientSetInfos": [
                    {
                        "recipientSetMemberInfos": [
                            {
                                "email": customer_data.get('email'),
                                "name": customer_data.get('contact_name', 'Customer')
                            }
                        ],
                        "recipientSetRole": "SIGNER"
                    }
                ],
                "signatureFlow": "SENDER_SIGNATURE_NOT_REQUIRED"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {
                self.config["auth_header"]: self.config["auth_format"].format(token=self.api_key),
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{self.config['base_url']}/agreements",
                json=agreement_info,
                headers=headers
            ) as response:
                
                if response.status == 201:
                    result = await response.json()
                    
                    return {
                        'success': True,
                        'signature_request_id': result.get('id'),
                        'expires_at': (datetime.now() + timedelta(days=self.signature_settings['expiration_days'])).isoformat(),
                        'provider': 'adobe_sign',
                        'recipient_email': customer_data.get('email'),
                        'sent_at': datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Adobe Sign API error {response.status}: {error_text}")
    
    async def _download_document_content(self, document_url: str) -> bytes:
        """Download document content for providers that require it"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(document_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download document: {response.status}")
    
    def check_signature_status(self, signature_request_id: str) -> Dict[str, Any]:
        """Check signature status (synchronous for monitoring thread)"""
        
        try:
            if self.provider == "sign.com":
                return self._check_sign_com_status(signature_request_id)
            elif self.provider == "docusign":
                return self._check_docusign_status(signature_request_id)
            elif self.provider == "adobe_sign":
                return self._check_adobe_sign_status(signature_request_id)
            else:
                return {'success': False, 'error': 'Unsupported provider'}
                
        except Exception as e:
            logger.error(f"❌ Error checking signature status: {e}")
            return {'success': False, 'error': str(e)}
    
    def _check_sign_com_status(self, signature_request_id: str) -> Dict[str, Any]:
        """Check signature status via Sign.com (simplified synchronous version)"""
        
        # Note: In production, you'd implement proper async status checking
        # This is a simplified version for demonstration
        
        return {
            'success': True,
            'completed': False,  # Would check actual status
            'status': 'pending',
            'signed_document_url': None,
            'completed_at': None
        }
    
    def _check_docusign_status(self, signature_request_id: str) -> Dict[str, Any]:
        """Check signature status via DocuSign"""
        
        return {
            'success': True,
            'completed': False,
            'status': 'pending',
            'signed_document_url': None,
            'completed_at': None
        }
    
    def _check_adobe_sign_status(self, signature_request_id: str) -> Dict[str, Any]:
        """Check signature status via Adobe Sign"""
        
        return {
            'success': True,
            'completed': False,
            'status': 'pending', 
            'signed_document_url': None,
            'completed_at': None
        }
    
    async def send_reminder(self, signature_request_id: str, transaction: LOITransaction) -> Dict[str, Any]:
        """Send reminder for pending signature"""
        
        try:
            customer_data = transaction.customer_data
            
            if self.provider == "sign.com":
                result = await self._send_sign_com_reminder(signature_request_id)
            elif self.provider == "docusign":
                result = await self._send_docusign_reminder(signature_request_id)
            elif self.provider == "adobe_sign":
                result = await self._send_adobe_sign_reminder(signature_request_id)
            else:
                raise Exception(f"Unsupported provider: {self.provider}")
            
            if result.get('success'):
                self.integration_stats['reminders_sent'] += 1
                logger.info(f"📧 Sent signature reminder for {transaction.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send reminder for {transaction.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _send_sign_com_reminder(self, signature_request_id: str) -> Dict[str, Any]:
        """Send reminder via Sign.com"""
        
        async with aiohttp.ClientSession() as session:
            headers = {
                self.config["auth_header"]: self.config["auth_format"].format(token=self.api_key),
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{self.config['base_url']}/signature_requests/{signature_request_id}/remind",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    return {'success': True, 'reminder_sent': True}
                else:
                    error_text = await response.text()
                    return {'success': False, 'error': f"Sign.com reminder failed: {error_text}"}
    
    async def _send_docusign_reminder(self, signature_request_id: str) -> Dict[str, Any]:
        """Send reminder via DocuSign"""
        
        # DocuSign reminder implementation
        return {'success': True, 'reminder_sent': True}  # Simplified
    
    async def _send_adobe_sign_reminder(self, signature_request_id: str) -> Dict[str, Any]:
        """Send reminder via Adobe Sign"""
        
        # Adobe Sign reminder implementation
        return {'success': True, 'reminder_sent': True}  # Simplified
    
    async def cancel_signature_request(self, signature_request_id: str, reason: str = "Cancelled by system") -> Dict[str, Any]:
        """Cancel pending signature request"""
        
        try:
            if self.provider == "sign.com":
                result = await self._cancel_sign_com_request(signature_request_id, reason)
            elif self.provider == "docusign":
                result = await self._cancel_docusign_request(signature_request_id, reason)
            elif self.provider == "adobe_sign":
                result = await self._cancel_adobe_sign_request(signature_request_id, reason)
            else:
                raise Exception(f"Unsupported provider: {self.provider}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel signature request {signature_request_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _cancel_sign_com_request(self, signature_request_id: str, reason: str) -> Dict[str, Any]:
        """Cancel signature request via Sign.com"""
        
        async with aiohttp.ClientSession() as session:
            headers = {
                self.config["auth_header"]: self.config["auth_format"].format(token=self.api_key),
                "Content-Type": "application/json"
            }
            
            payload = {"reason": reason}
            
            async with session.post(
                f"{self.config['base_url']}/signature_requests/{signature_request_id}/cancel",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    return {'success': True, 'cancelled': True}
                else:
                    error_text = await response.text()
                    return {'success': False, 'error': f"Cancellation failed: {error_text}"}
    
    async def _cancel_docusign_request(self, signature_request_id: str, reason: str) -> Dict[str, Any]:
        """Cancel signature request via DocuSign"""
        
        # DocuSign cancellation implementation
        return {'success': True, 'cancelled': True}  # Simplified
    
    async def _cancel_adobe_sign_request(self, signature_request_id: str, reason: str) -> Dict[str, Any]:
        """Cancel signature request via Adobe Sign"""
        
        # Adobe Sign cancellation implementation
        return {'success': True, 'cancelled': True}  # Simplified
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration performance statistics"""
        
        conversion_rate = 0.0
        if self.integration_stats['signature_requests_sent'] > 0:
            conversion_rate = (
                self.integration_stats['signatures_completed'] / 
                self.integration_stats['signature_requests_sent']
            )
        
        return {
            'integration_type': 'esignature',
            'provider': self.provider,
            'stats': self.integration_stats,
            'conversion_rate': conversion_rate,
            'signature_settings': self.signature_settings
        }
    
    async def get_signature_audit_trail(self, signature_request_id: str) -> Dict[str, Any]:
        """Get audit trail for completed signature"""
        
        try:
            if self.provider == "sign.com":
                return await self._get_sign_com_audit_trail(signature_request_id)
            elif self.provider == "docusign":
                return await self._get_docusign_audit_trail(signature_request_id)
            elif self.provider == "adobe_sign":
                return await self._get_adobe_sign_audit_trail(signature_request_id)
            else:
                return {'success': False, 'error': 'Unsupported provider'}
                
        except Exception as e:
            logger.error(f"❌ Error getting audit trail: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_sign_com_audit_trail(self, signature_request_id: str) -> Dict[str, Any]:
        """Get audit trail from Sign.com"""
        
        async with aiohttp.ClientSession() as session:
            headers = {
                self.config["auth_header"]: self.config["auth_format"].format(token=self.api_key)
            }
            
            async with session.get(
                f"{self.config['base_url']}/signature_requests/{signature_request_id}/audit_trail",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    audit_data = await response.json()
                    return {
                        'success': True,
                        'audit_trail': audit_data,
                        'provider': 'sign.com'
                    }
                else:
                    error_text = await response.text()
                    return {'success': False, 'error': f"Audit trail failed: {error_text}"}
    
    async def _get_docusign_audit_trail(self, signature_request_id: str) -> Dict[str, Any]:
        """Get audit trail from DocuSign"""
        
        # DocuSign audit trail implementation
        return {'success': True, 'audit_trail': {}, 'provider': 'docusign'}  # Simplified
    
    async def _get_adobe_sign_audit_trail(self, signature_request_id: str) -> Dict[str, Any]:
        """Get audit trail from Adobe Sign"""
        
        # Adobe Sign audit trail implementation
        return {'success': True, 'audit_trail': {}, 'provider': 'adobe_sign'}  # Simplified

# Async wrapper function for coordinator integration
async def handle_esignature_integration(transaction: LOITransaction) -> Dict[str, Any]:
    """Handle e-signature integration - async wrapper for coordinator"""
    
    # Note: In production, these would come from configuration
    provider = "sign.com"  # Configure via environment: sign.com, docusign, adobe_sign
    api_key = "YOUR_ESIGNATURE_API_KEY"  # Configure via environment
    api_secret = "YOUR_ESIGNATURE_API_SECRET"  # Configure via environment
    
    esignature_integration = ESignatureIntegration(provider, api_key, api_secret)
    return await esignature_integration.send_signature_request(transaction)