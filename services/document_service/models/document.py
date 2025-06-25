"""
Document Models
Core data models for document management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import uuid

class DocumentType(Enum):
    """Document type enumeration"""
    LOI = "loi"
    CONTRACT = "contract"
    PROPOSAL = "proposal"
    AGREEMENT = "agreement"
    FORM = "form"
    CERTIFICATE = "certificate"
    OTHER = "other"

class DocumentStatus(Enum):
    """Document status enumeration"""
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class SignatureStatus(Enum):
    """Signature status enumeration"""
    PENDING = "pending"
    SIGNED = "signed"
    DECLINED = "declined"
    EXPIRED = "expired"

@dataclass
class Document:
    """Document model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    document_type: DocumentType = DocumentType.OTHER
    status: DocumentStatus = DocumentStatus.DRAFT
    content_html: Optional[str] = None
    template_id: Optional[str] = None
    customer_id: Optional[str] = None
    contact_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'document_type': self.document_type.value,
            'status': self.status.value,
            'content_html': self.content_html,
            'template_id': self.template_id,
            'customer_id': self.customer_id,
            'contact_email': self.contact_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create from dictionary"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            document_type=DocumentType(data.get('document_type', 'other')),
            status=DocumentStatus(data.get('status', 'draft')),
            content_html=data.get('content_html'),
            template_id=data.get('template_id'),
            customer_id=data.get('customer_id'),
            contact_email=data.get('contact_email'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            metadata=data.get('metadata', {})
        )

@dataclass 
class SignatureRequest:
    """Signature request model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    signer_name: str = ""
    signer_email: str = ""
    status: SignatureStatus = SignatureStatus.PENDING
    signature_data: Optional[str] = None  # Base64 encoded signature
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    consent_data: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'signer_name': self.signer_name,
            'signer_email': self.signer_email,
            'status': self.status.value,
            'signature_data': self.signature_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'consent_data': self.consent_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignatureRequest':
        """Create from dictionary"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            document_id=data.get('document_id', ''),
            signer_name=data.get('signer_name', ''),
            signer_email=data.get('signer_email', ''),
            status=SignatureStatus(data.get('status', 'pending')),
            signature_data=data.get('signature_data'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            signed_at=datetime.fromisoformat(data['signed_at']) if data.get('signed_at') else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            consent_data=data.get('consent_data', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )

@dataclass
class AuditTrail:
    """Audit trail model for document operations"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    action: str = ""  # created, updated, signed, sent, etc.
    actor: str = ""  # email or system
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'action': self.action,
            'actor': self.actor,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

@dataclass
class Template:
    """Document template model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    document_type: DocumentType = DocumentType.OTHER
    content_html: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)  # Form fields/placeholders
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'document_type': self.document_type.value,
            'content_html': self.content_html,
            'fields': self.fields,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }