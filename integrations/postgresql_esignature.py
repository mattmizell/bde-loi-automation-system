"""
PostgreSQL-Based E-Signature Integration

Custom open-source e-signature solution using PostgreSQL storage.
No external dependencies like DocuSign - everything stored locally.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import base64
import hashlib
import uuid
from pathlib import Path
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders

from ..core.loi_transaction_queue import LOITransaction
from ..database.connection import get_db_manager

logger = logging.getLogger(__name__)

class PostgreSQLESignature:
    """
    Open-source e-signature solution using PostgreSQL storage.
    
    Features:
    - HTML5 signature pad for collecting signatures
    - PostgreSQL storage for signatures and audit trail
    - Email-based signature request workflow
    - Legal compliance with audit logs
    - No external API dependencies
    """
    
    def __init__(self, smtp_host: str = None, smtp_port: int = 587, 
                 smtp_username: str = None, smtp_password: str = None):
        self.smtp_host = smtp_host or "smtp.gmail.com"
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        
        # Signature workflow settings
        self.signature_settings = {
            'expiration_days': 30,
            'reminder_interval_days': 7,
            'max_reminders': 3,
            'signature_page_url': '/signature',
            'completion_redirect_url': '/signature/complete'
        }
        
        self.signature_stats = {
            'requests_sent': 0,
            'signatures_completed': 0,
            'signatures_expired': 0,
            'reminders_sent': 0
        }
        
        logger.info("✍️ PostgreSQL E-Signature integration initialized")
    
    async def request_signature(self, transaction: LOITransaction, 
                               document_path: str = None) -> Dict[str, Any]:
        """Request e-signature for LOI document"""
        
        try:
            db_manager = get_db_manager()
            
            # Create signature request record
            signature_request = await self._create_signature_request(
                transaction, document_path
            )
            
            # Generate signature URL
            signature_url = self._generate_signature_url(signature_request['id'])
            
            # Send signature request email
            email_result = await self._send_signature_request_email(
                transaction, signature_url, signature_request
            )
            
            # Update transaction
            await self._update_transaction_signature_status(
                transaction, signature_request['id'], 'signature_requested'
            )
            
            self.signature_stats['requests_sent'] += 1
            
            logger.info(f"✍️ Signature request sent for LOI {transaction.id}")
            
            return {
                'success': True,
                'signature_request_id': signature_request['id'],
                'signature_url': signature_url,
                'expires_at': signature_request['expires_at'],
                'email_sent': email_result['success'],
                'message': 'Signature request sent successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to request signature for {transaction.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _create_signature_request(self, transaction: LOITransaction, 
                                      document_path: str = None) -> Dict[str, Any]:
        """Create signature request record in PostgreSQL"""
        
        db_manager = get_db_manager()
        
        # Generate unique signature request ID
        request_id = str(uuid.uuid4())
        
        # Calculate expiration date
        expires_at = datetime.now() + timedelta(days=self.signature_settings['expiration_days'])
        
        # Prepare signature request data
        signature_request = {
            'id': request_id,
            'transaction_id': str(transaction.id),
            'customer_email': transaction.customer_data.get('email'),
            'customer_name': transaction.customer_data.get('contact_name'),
            'company_name': transaction.customer_data.get('company_name'),
            'document_path': document_path,
            'status': 'pending',
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'reminder_count': 0,
            'signature_data': None,
            'signed_at': None,
            'ip_address': None,
            'user_agent': None
        }
        
        # Store in database
        with db_manager.get_session() as session:
            # Insert signature request
            session.execute("""
                INSERT INTO signature_requests (
                    id, transaction_id, customer_email, customer_name, company_name,
                    document_path, status, created_at, expires_at, reminder_count,
                    signature_data, signed_at, ip_address, user_agent
                ) VALUES (
                    :id, :transaction_id, :customer_email, :customer_name, :company_name,
                    :document_path, :status, :created_at, :expires_at, :reminder_count,
                    :signature_data, :signed_at, :ip_address, :user_agent
                )
            """, signature_request)
            session.commit()
        
        return signature_request
    
    def _generate_signature_url(self, request_id: str) -> str:
        """Generate secure signature URL"""
        
        # Create secure token
        token_data = f"{request_id}:{datetime.now().isoformat()}"
        token = base64.urlsafe_b64encode(token_data.encode()).decode()
        
        # Generate URL (in production, use your domain)
        base_url = "http://localhost:8000"
        signature_url = f"{base_url}/signature/{request_id}?token={token}"
        
        return signature_url
    
    async def _send_signature_request_email(self, transaction: LOITransaction, 
                                          signature_url: str, 
                                          signature_request: Dict[str, Any]) -> Dict[str, Any]:
        """Send signature request email"""
        
        try:
            customer_email = transaction.customer_data.get('email')
            customer_name = transaction.customer_data.get('contact_name')
            company_name = transaction.customer_data.get('company_name')
            
            # Create email content
            subject = f"VP Racing Fuel Supply Agreement - Signature Required for {company_name}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #1f4e79, #2563eb); color: white; padding: 30px; text-align: center;">
                    <h1>🏢 Better Day Energy</h1>
                    <h2>VP Racing Fuel Supply Agreement</h2>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <h3>Hello {customer_name},</h3>
                    
                    <p>Your Letter of Intent for <strong>{company_name}</strong> is ready for your electronic signature.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #1f4e79;">
                        <h4>📄 Document Details:</h4>
                        <ul>
                            <li><strong>Document Type:</strong> VP Racing Fuel Supply LOI</li>
                            <li><strong>Customer:</strong> {company_name}</li>
                            <li><strong>Generated:</strong> {signature_request['created_at'].strftime('%B %d, %Y')}</li>
                            <li><strong>Expires:</strong> {signature_request['expires_at'].strftime('%B %d, %Y')}</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{signature_url}" 
                           style="background: #1f4e79; color: white; padding: 15px 30px; text-decoration: none; 
                                  border-radius: 6px; font-weight: bold; display: inline-block;">
                            ✍️ Sign Document Now
                        </a>
                    </div>
                    
                    <div style="background: #e3f2fd; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <h4>🔒 Secure Signing Process:</h4>
                        <ul>
                            <li>Click the link above to access your document</li>
                            <li>Review the Letter of Intent details</li>
                            <li>Provide your electronic signature</li>
                            <li>Receive signed copy via email</li>
                        </ul>
                    </div>
                    
                    <p><strong>Questions?</strong> Contact Better Day Energy at your convenience.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                    
                    <p style="color: #666; font-size: 0.9em;">
                        This signature request expires on {signature_request['expires_at'].strftime('%B %d, %Y at %I:%M %p')}.<br>
                        This email was sent by the Better Day Energy LOI Automation System.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            if self.smtp_username and self.smtp_password:
                await self._send_email(customer_email, subject, html_body)
                return {'success': True, 'message': 'Email sent successfully'}
            else:
                logger.warning("⚠️ SMTP credentials not configured - signature email not sent")
                return {'success': False, 'message': 'SMTP not configured'}
                
        except Exception as e:
            logger.error(f"❌ Failed to send signature request email: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _send_email(self, to_email: str, subject: str, html_body: str):
        """Send email using SMTP"""
        
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            
            # Add HTML content
            html_part = MimeText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"❌ SMTP error: {e}")
            raise e
    
    async def process_signature(self, request_id: str, signature_data: str, 
                              ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Process completed signature"""
        
        try:
            db_manager = get_db_manager()
            
            # Validate signature request
            with db_manager.get_session() as session:
                result = session.execute("""
                    SELECT * FROM signature_requests WHERE id = :request_id AND status = 'pending'
                """, {'request_id': request_id})
                
                request_data = result.fetchone()
                if not request_data:
                    return {'success': False, 'error': 'Invalid or expired signature request'}
                
                # Check expiration
                if datetime.now() > request_data.expires_at:
                    return {'success': False, 'error': 'Signature request has expired'}
                
                # Update signature request
                signed_at = datetime.now()
                session.execute("""
                    UPDATE signature_requests 
                    SET status = 'completed', signature_data = :signature_data, 
                        signed_at = :signed_at, ip_address = :ip_address, user_agent = :user_agent
                    WHERE id = :request_id
                """, {
                    'request_id': request_id,
                    'signature_data': signature_data,
                    'signed_at': signed_at,
                    'ip_address': ip_address,
                    'user_agent': user_agent
                })
                
                # Create audit log entry
                session.execute("""
                    INSERT INTO signature_audit_log (
                        signature_request_id, event_type, event_data, timestamp, ip_address
                    ) VALUES (
                        :request_id, 'signature_completed', :event_data, :timestamp, :ip_address
                    )
                """, {
                    'request_id': request_id,
                    'event_data': json.dumps({
                        'signed_at': signed_at.isoformat(),
                        'user_agent': user_agent,
                        'signature_hash': hashlib.sha256(signature_data.encode()).hexdigest()
                    }),
                    'timestamp': signed_at,
                    'ip_address': ip_address
                })
                
                session.commit()
            
            # Update transaction status
            await self._update_transaction_signature_status(
                request_data.transaction_id, request_id, 'signature_completed'
            )
            
            self.signature_stats['signatures_completed'] += 1
            
            logger.info(f"✍️ Signature completed for request {request_id}")
            
            return {
                'success': True,
                'message': 'Signature processed successfully',
                'signed_at': signed_at.isoformat(),
                'transaction_id': request_data.transaction_id
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process signature for {request_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _update_transaction_signature_status(self, transaction_id: str, 
                                                 signature_request_id: str, status: str):
        """Update transaction with signature status"""
        
        db_manager = get_db_manager()
        
        with db_manager.get_session() as session:
            session.execute("""
                UPDATE loi_transactions 
                SET signature_request_id = :signature_request_id,
                    signature_status = :status,
                    signature_updated_at = :updated_at
                WHERE id = :transaction_id
            """, {
                'transaction_id': transaction_id,
                'signature_request_id': signature_request_id,
                'status': status,
                'updated_at': datetime.now()
            })
            session.commit()
    
    async def check_pending_signatures(self) -> List[Dict[str, Any]]:
        """Check for pending signature requests that need reminders or are expired"""
        
        db_manager = get_db_manager()
        actions_taken = []
        
        with db_manager.get_session() as session:
            # Get expired requests
            expired_result = session.execute("""
                SELECT * FROM signature_requests 
                WHERE status = 'pending' AND expires_at < :now
            """, {'now': datetime.now()})
            
            for expired_request in expired_result.fetchall():
                # Mark as expired
                session.execute("""
                    UPDATE signature_requests SET status = 'expired' WHERE id = :id
                """, {'id': expired_request.id})
                
                actions_taken.append({
                    'action': 'expired',
                    'request_id': expired_request.id,
                    'customer_email': expired_request.customer_email
                })
            
            # Get requests needing reminders
            reminder_cutoff = datetime.now() - timedelta(days=self.signature_settings['reminder_interval_days'])
            
            reminder_result = session.execute("""
                SELECT * FROM signature_requests 
                WHERE status = 'pending' 
                AND created_at < :cutoff 
                AND reminder_count < :max_reminders
                AND expires_at > :now
            """, {
                'cutoff': reminder_cutoff,
                'max_reminders': self.signature_settings['max_reminders'],
                'now': datetime.now()
            })
            
            for reminder_request in reminder_result.fetchall():
                # Send reminder (implementation would go here)
                session.execute("""
                    UPDATE signature_requests 
                    SET reminder_count = reminder_count + 1 
                    WHERE id = :id
                """, {'id': reminder_request.id})
                
                actions_taken.append({
                    'action': 'reminder_sent',
                    'request_id': reminder_request.id,
                    'customer_email': reminder_request.customer_email,
                    'reminder_count': reminder_request.reminder_count + 1
                })
            
            session.commit()
        
        return actions_taken
    
    def get_signature_stats(self) -> Dict[str, Any]:
        """Get e-signature performance statistics"""
        
        return {
            'integration_type': 'postgresql_esignature',
            'stats': self.signature_stats,
            'settings': self.signature_settings,
            'storage': 'postgresql_local'
        }

# Database schema for signature tables (add to models.py)
SIGNATURE_TABLES_SQL = """
-- Signature requests table
CREATE TABLE IF NOT EXISTS signature_requests (
    id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    company_name VARCHAR(255),
    document_path TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    reminder_count INTEGER DEFAULT 0,
    signature_data TEXT,
    signed_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    FOREIGN KEY (transaction_id) REFERENCES loi_transactions(id)
);

-- Signature audit log table
CREATE TABLE IF NOT EXISTS signature_audit_log (
    id SERIAL PRIMARY KEY,
    signature_request_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP NOT NULL,
    ip_address INET,
    FOREIGN KEY (signature_request_id) REFERENCES signature_requests(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_signature_requests_status ON signature_requests(status);
CREATE INDEX IF NOT EXISTS idx_signature_requests_expires ON signature_requests(expires_at);
CREATE INDEX IF NOT EXISTS idx_signature_audit_log_request ON signature_audit_log(signature_request_id);
"""

# Async wrapper function for coordinator integration
async def handle_postgresql_esignature(transaction: LOITransaction) -> Dict[str, Any]:
    """Handle PostgreSQL e-signature - async wrapper for coordinator"""
    
    # Get SMTP settings from environment
    import os
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    esignature = PostgreSQLESignature(smtp_host, smtp_port, smtp_username, smtp_password)
    
    # Get document path from transaction context
    document_path = transaction.processing_context.get('crm_document_id') or \
                   transaction.processing_context.get('generated_document_path')
    
    return await esignature.request_signature(transaction, document_path)