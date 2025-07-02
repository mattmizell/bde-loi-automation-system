"""
Database Models for LOI Automation System

SQLAlchemy models for storing LOI transaction data, customer information,
and processing history in PostgreSQL database.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    JSON, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class TransactionStatus(enum.Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_SIGNATURE = "waiting_signature"
    SIGNED = "signed"

class TransactionType(enum.Enum):
    """Transaction type enumeration"""
    NEW_LOI_REQUEST = "new_loi_request"
    DOCUMENT_GENERATION = "document_generation"
    STORAGE_UPLOAD = "storage_upload"
    SIGNATURE_REQUEST = "signature_request"
    STATUS_UPDATE = "status_update"
    COMPLETION_NOTIFICATION = "completion_notification"
    EFT_FORM = "eft_form"  # EFT authorization form workflow

class TransactionPriority(enum.Enum):
    """Transaction priority enumeration"""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

class WorkflowStage(enum.Enum):
    """Workflow stage enumeration"""
    INITIAL = "initial"
    CRM_DATA_RETRIEVED = "crm_data_retrieved"
    DOCUMENT_GENERATED = "document_generated"
    STORED_IN_DRIVE = "stored_in_drive"
    SIGNATURE_REQUESTED = "signature_requested"
    SIGNATURE_COMPLETED = "signature_completed"
    NOTIFICATION_SENT = "notification_sent"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING_CUSTOMER_COMPLETION = "pending_customer_completion"  # For EFT forms awaiting customer input

class Customer(Base):
    """Customer information table"""
    __tablename__ = 'customers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=False)
    contact_title = Column(String(100))
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    
    # Address information
    street_address = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    
    # Customer metadata
    is_vip_customer = Column(Boolean, default=False)
    customer_type = Column(String(50))  # existing_customer, new_prospect, competitor_customer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # CRM integration
    crm_contact_id = Column(String(100), unique=True)
    crm_last_sync = Column(DateTime)
    
    # Relationships
    loi_transactions = relationship("LOITransaction", back_populates="customer")
    
    # Indexes
    __table_args__ = (
        Index('idx_customer_email', 'email'),
        Index('idx_customer_crm_id', 'crm_contact_id'),
        Index('idx_customer_company', 'company_name'),
    )

class LOITransaction(Base):
    """Main LOI transaction table"""
    __tablename__ = 'loi_transactions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic transaction info
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    priority = Column(SQLEnum(TransactionPriority), default=TransactionPriority.NORMAL)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    workflow_stage = Column(SQLEnum(WorkflowStage), default=WorkflowStage.INITIAL)
    
    # Customer relationship
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    customer = relationship("Customer", back_populates="loi_transactions")
    
    # Processing metadata
    complexity_score = Column(Float, default=0.0)
    ai_priority_score = Column(Float, default=0.0)
    estimated_processing_time = Column(Float, default=0.0)
    risk_factors = Column(JSONB)  # Array of risk factors
    
    # Timing information
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Processing context
    processing_context = Column(JSONB)  # Source, IP, user agent, etc.
    
    # Document tracking
    document_id = Column(String(255))
    document_file_path = Column(String(500))
    google_drive_url = Column(String(500))
    google_drive_file_id = Column(String(255))
    
    # E-signature tracking
    signature_request_id = Column(String(255))
    signature_provider = Column(String(50))  # sign.com, docusign, adobe_sign
    signature_url = Column(String(500))
    signature_expires_at = Column(DateTime)
    signed_document_url = Column(String(500))
    
    # Dependencies
    parent_transaction_id = Column(UUID(as_uuid=True), ForeignKey('loi_transactions.id'))
    dependency_ids = Column(JSONB)  # Array of transaction IDs this depends on
    
    # Relationships
    parent_transaction = relationship("LOITransaction", remote_side=[id])
    crm_form_data = relationship("CRMFormData", back_populates="transaction", uselist=False)
    processing_events = relationship("ProcessingEvent", back_populates="transaction")
    ai_decisions = relationship("AIDecision", back_populates="transaction")
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_status', 'status'),
        Index('idx_transaction_stage', 'workflow_stage'),
        Index('idx_transaction_customer', 'customer_id'),
        Index('idx_transaction_created', 'created_at'),
        Index('idx_transaction_priority', 'priority'),
        Index('idx_signature_request', 'signature_request_id'),
    )

class CRMFormData(Base):
    """CRM form data table"""
    __tablename__ = 'crm_form_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('loi_transactions.id'), nullable=False)
    
    # Fuel supply details
    monthly_gasoline_volume = Column(Float, default=0.0)
    monthly_diesel_volume = Column(Float, default=0.0)
    current_fuel_supplier = Column(String(255))
    estimated_conversion_date = Column(DateTime)
    
    # Financial information
    image_funding_amount = Column(Float, default=0.0)
    incentive_funding_amount = Column(Float, default=0.0)
    total_estimated_incentives = Column(Float, default=0.0)
    
    # Project specifications
    canopy_installation_required = Column(Boolean, default=False)
    current_branding_to_remove = Column(String(255))
    special_requirements_notes = Column(Text)
    
    # CRM metadata
    crm_form_id = Column(String(100))
    crm_retrieved_at = Column(DateTime)
    crm_last_modified = Column(DateTime)
    validation_score = Column(Float, default=0.0)
    validation_errors = Column(JSONB)  # Array of validation errors
    validation_warnings = Column(JSONB)  # Array of validation warnings
    
    # Raw CRM data
    raw_crm_data = Column(JSONB)  # Complete raw data from CRM
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transaction = relationship("LOITransaction", back_populates="crm_form_data")

class ProcessingEvent(Base):
    """Processing event history table"""
    __tablename__ = 'processing_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('loi_transactions.id'), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # crm_data_retrieved, document_generated, etc.
    event_stage = Column(String(50))  # workflow stage when event occurred
    event_data = Column(JSONB)  # Event-specific data
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)  # Time taken for this event in seconds
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    error_details = Column(JSONB)
    
    # Context
    handler_name = Column(String(100))
    integration_used = Column(String(50))
    
    # Relationships
    transaction = relationship("LOITransaction", back_populates="processing_events")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_transaction', 'transaction_id'),
        Index('idx_event_type', 'event_type'),
        Index('idx_event_timestamp', 'timestamp'),
        Index('idx_event_success', 'success'),
    )

class AIDecision(Base):
    """AI decision tracking table"""
    __tablename__ = 'ai_decisions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('loi_transactions.id'), nullable=False)
    
    # Decision details
    decision_type = Column(String(100), nullable=False)  # initial_assessment, processing_guidance
    decision_id = Column(String(255))  # External AI system decision ID
    
    # AI model info
    ai_provider = Column(String(50))  # grok, deepseek, etc.
    model_name = Column(String(100))
    model_version = Column(String(50))
    
    # Decision content
    decision_data = Column(JSONB)  # Complete decision data
    reasoning = Column(Text)
    confidence = Column(Float)
    expected_outcome = Column(String(255))
    alternatives_considered = Column(JSONB)
    
    # Context
    complexity_assessment = Column(Float)
    priority_score = Column(Float)
    risk_assessment = Column(Text)
    routing_recommendation = Column(String(255))
    
    # Outcome tracking
    actual_outcome = Column(JSONB)
    outcome_success = Column(Boolean)
    outcome_recorded_at = Column(DateTime)
    decision_accuracy = Column(Float)  # How accurate was this decision
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transaction = relationship("LOITransaction", back_populates="ai_decisions")
    
    # Indexes
    __table_args__ = (
        Index('idx_ai_decision_transaction', 'transaction_id'),
        Index('idx_ai_decision_type', 'decision_type'),
        Index('idx_ai_decision_timestamp', 'created_at'),
        Index('idx_ai_decision_provider', 'ai_provider'),
    )

class SystemMetrics(Base):
    """System performance metrics table"""
    __tablename__ = 'system_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric details
    metric_type = Column(String(100), nullable=False)  # queue_stats, processing_performance, etc.
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_data = Column(JSONB)  # Additional metric data
    
    # Context
    component = Column(String(100))  # coordinator, queue, handler, integration
    instance_id = Column(String(100))  # For distributed systems
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_type_name', 'metric_type', 'metric_name'),
        Index('idx_metrics_timestamp', 'timestamp'),
        Index('idx_metrics_component', 'component'),
    )

class IntegrationLog(Base):
    """Integration service logs table"""
    __tablename__ = 'integration_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('loi_transactions.id'))
    
    # Integration details
    integration_type = Column(String(50), nullable=False)  # crm, google_drive, esignature
    operation = Column(String(100), nullable=False)  # retrieve_data, upload_document, send_signature
    
    # Request/Response
    request_data = Column(JSONB)
    response_data = Column(JSONB)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Performance
    response_time = Column(Float)  # Response time in seconds
    retry_count = Column(Integer, default=0)
    
    # External references
    external_id = Column(String(255))  # ID from external system
    external_url = Column(String(500))
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_integration_type', 'integration_type'),
        Index('idx_integration_transaction', 'transaction_id'),
        Index('idx_integration_timestamp', 'timestamp'),
        Index('idx_integration_success', 'success'),
        Index('idx_integration_external_id', 'external_id'),
    )

class DocumentTemplate(Base):
    """Document template management table"""
    __tablename__ = 'document_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template details
    template_name = Column(String(255), nullable=False)
    template_type = Column(String(100), nullable=False)  # loi, contract, etc.
    version = Column(String(50), nullable=False)
    
    # Template configuration
    field_mappings = Column(JSONB)  # Field mapping configuration
    format_settings = Column(JSONB)  # Formatting settings
    template_data = Column(JSONB)  # Template structure and content
    
    # Metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    
    # Indexes
    __table_args__ = (
        Index('idx_template_name_version', 'template_name', 'version'),
        Index('idx_template_type', 'template_type'),
        Index('idx_template_active', 'is_active'),
    )

class QueueSnapshot(Base):
    """Queue state snapshots for monitoring"""
    __tablename__ = 'queue_snapshots'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Queue state
    queue_size = Column(Integer, default=0)
    processing_size = Column(Integer, default=0)
    completed_size = Column(Integer, default=0)
    failed_size = Column(Integer, default=0)
    
    # Performance metrics
    throughput_tps = Column(Float, default=0.0)
    average_processing_time = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    queue_utilization = Column(Float, default=0.0)
    
    # Workflow stage distribution
    workflow_stage_counts = Column(JSONB)
    priority_distribution = Column(JSONB)
    
    # System info
    active_workers = Column(Integer, default=0)
    system_load = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_queue_snapshot_timestamp', 'timestamp'),
    )

# Database views (these would be created via migration scripts)
"""
CREATE VIEW loi_dashboard_summary AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_lois,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_lois,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_lois,
    AVG(CASE 
        WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (completed_at - started_at)) 
    END) as avg_completion_time_seconds,
    AVG(complexity_score) as avg_complexity_score
FROM loi_transactions 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

CREATE VIEW customer_summary AS
SELECT 
    c.id,
    c.company_name,
    c.email,
    c.is_vip_customer,
    COUNT(lt.id) as total_lois,
    COUNT(CASE WHEN lt.status = 'completed' THEN 1 END) as completed_lois,
    MAX(lt.created_at) as last_loi_date,
    SUM(cfd.total_estimated_incentives) as total_incentives
FROM customers c
LEFT JOIN loi_transactions lt ON c.id = lt.customer_id
LEFT JOIN crm_form_data cfd ON lt.id = cfd.transaction_id
GROUP BY c.id, c.company_name, c.email, c.is_vip_customer;

CREATE VIEW integration_performance AS
SELECT 
    integration_type,
    operation,
    COUNT(*) as total_calls,
    COUNT(CASE WHEN success = true THEN 1 END) as successful_calls,
    AVG(response_time) as avg_response_time,
    MAX(response_time) as max_response_time,
    DATE(timestamp) as date
FROM integration_logs 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY integration_type, operation, DATE(timestamp)
ORDER BY date DESC, integration_type, operation;
"""

# =====================================================
# E-SIGNATURE MODELS (PostgreSQL-based solution)
# =====================================================

class SignatureRequest(Base):
    """E-signature requests for LOI documents"""
    __tablename__ = 'signature_requests'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('loi_transactions.id'), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(255))
    company_name = Column(String(255))
    document_path = Column(Text)
    status = Column(String(50), default='pending')  # pending, completed, expired
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    reminder_count = Column(Integer, default=0)
    signature_data = Column(Text)  # Base64 encoded signature image
    signed_at = Column(DateTime)
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Relationships
    transaction = relationship("LOITransaction", back_populates="signature_requests")
    audit_logs = relationship("SignatureAuditLog", back_populates="signature_request")
    
    def __repr__(self):
        return f"<SignatureRequest(id={self.id}, customer_email={self.customer_email}, status={self.status})>"

class SignatureAuditLog(Base):
    """Audit trail for signature requests"""
    __tablename__ = 'signature_audit_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    signature_request_id = Column(UUID(as_uuid=True), ForeignKey('signature_requests.id'), nullable=False)
    event_type = Column(String(100), nullable=False)  # request_sent, reminder_sent, signature_completed, etc.
    event_data = Column(JSONB)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(INET)
    
    # Relationships
    signature_request = relationship("SignatureRequest", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<SignatureAuditLog(id={self.id}, event_type={self.event_type}, timestamp={self.timestamp})>"

# Update LOITransaction to include signature relationship
LOITransaction.signature_requests = relationship("SignatureRequest", back_populates="transaction")

# Indexes for performance
Index('idx_signature_requests_status', SignatureRequest.status)
Index('idx_signature_requests_expires', SignatureRequest.expires_at)
Index('idx_signature_requests_customer_email', SignatureRequest.customer_email)
Index('idx_signature_audit_log_request', SignatureAuditLog.signature_request_id)
Index('idx_signature_audit_log_timestamp', SignatureAuditLog.timestamp)

# =====================================================
# CUSTOMER ONBOARDING FORM MODELS
# =====================================================

class EFTFormData(Base):
    """Electronic Funds Transfer (EFT) authorization form data"""
    __tablename__ = 'eft_form_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    transaction_id = Column(String(255))  # Link to LOI transaction for tracking
    
    # Bank Account Information
    bank_name = Column(String(255), nullable=False)
    bank_address = Column(String(500))
    bank_city = Column(String(100))
    bank_state = Column(String(50))
    bank_zip = Column(String(20))
    account_holder_name = Column(String(255), nullable=False)
    account_type = Column(String(50))  # checking, savings
    account_number = Column(String(100))  # Encrypted
    routing_number = Column(String(50))  # Encrypted
    
    # Authorization Details
    authorized_by_name = Column(String(255), nullable=False)
    authorized_by_title = Column(String(100))
    authorization_date = Column(DateTime, nullable=False)
    
    # Signature
    signature_data = Column(Text)  # Base64 encoded signature image
    signature_ip = Column(INET)
    signature_timestamp = Column(DateTime)
    
    # Metadata
    form_status = Column(String(50), default='draft')  # draft, pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", backref="eft_forms")
    
    # Indexes
    __table_args__ = (
        Index('idx_eft_customer', 'customer_id'),
        Index('idx_eft_status', 'form_status'),
        Index('idx_eft_created', 'created_at'),
    )

class CustomerSetupFormData(Base):
    """Customer setup document form data"""
    __tablename__ = 'customer_setup_form_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    
    # Business Information
    legal_business_name = Column(String(255), nullable=False)
    dba_name = Column(String(255))
    federal_tax_id = Column(String(50))  # Encrypted
    state_tax_id = Column(String(50))  # Encrypted
    business_type = Column(String(100))  # corporation, llc, partnership, sole_proprietor
    
    # Location Details
    physical_address = Column(String(500))
    physical_city = Column(String(100))
    physical_state = Column(String(50))
    physical_zip = Column(String(20))
    mailing_address = Column(String(500))
    mailing_city = Column(String(100))
    mailing_state = Column(String(50))
    mailing_zip = Column(String(20))
    
    # Contact Information
    primary_contact_name = Column(String(255))
    primary_contact_title = Column(String(100))
    primary_contact_phone = Column(String(50))
    primary_contact_email = Column(String(255))
    accounts_payable_contact = Column(String(255))
    accounts_payable_email = Column(String(255))
    accounts_payable_phone = Column(String(50))
    
    # Business Details
    years_in_business = Column(Integer)
    annual_fuel_volume = Column(Float)
    number_of_locations = Column(Integer, default=1)
    current_fuel_brands = Column(JSONB)  # Array of current brands
    
    # Equipment Information
    tank_sizes = Column(JSONB)  # Array of tank configurations
    dispenser_count = Column(Integer)
    pos_system = Column(String(100))
    
    # Financial Information
    bank_references = Column(JSONB)  # Array of bank reference objects
    trade_references = Column(JSONB)  # Array of trade reference objects
    
    # Agreements and Signatures
    authorized_signer_name = Column(String(255))
    authorized_signer_title = Column(String(100))
    signature_data = Column(Text)  # Base64 encoded signature
    signature_date = Column(DateTime)
    signature_ip = Column(INET)
    
    # Form Status
    form_status = Column(String(50), default='draft')  # draft, pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", backref="setup_forms")
    
    # Indexes
    __table_args__ = (
        Index('idx_setup_customer', 'customer_id'),
        Index('idx_setup_status', 'form_status'),
        Index('idx_setup_created', 'created_at'),
    )

class P66LOIFormData(Base):
    """Phillips 66 Letter of Intent form data"""
    __tablename__ = 'p66_loi_form_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('loi_transactions.id'))
    
    # Station Information
    station_name = Column(String(255), nullable=False)
    station_address = Column(String(500))
    station_city = Column(String(100))
    station_state = Column(String(50))
    station_zip = Column(String(20))
    
    # Current Operation Details
    current_brand = Column(String(100))
    brand_expiration_date = Column(DateTime)
    
    # Fuel Volume Commitments
    monthly_gasoline_gallons = Column(Float)
    monthly_diesel_gallons = Column(Float)
    total_monthly_gallons = Column(Float)
    
    # Contract Terms
    contract_start_date = Column(DateTime)
    contract_term_years = Column(Integer, default=10)
    
    # Incentive Programs
    volume_incentive_requested = Column(Float)
    image_funding_requested = Column(Float)
    equipment_funding_requested = Column(Float)
    total_incentives_requested = Column(Float)
    
    # Additional Requirements
    canopy_replacement = Column(Boolean, default=False)
    dispenser_replacement = Column(Boolean, default=False)
    tank_replacement = Column(Boolean, default=False)
    pos_upgrade = Column(Boolean, default=False)
    special_requirements = Column(Text)
    
    # Signature Section
    authorized_representative = Column(String(255))
    representative_title = Column(String(100))
    signature_data = Column(Text)  # Base64 encoded signature
    signature_date = Column(DateTime)
    signature_ip = Column(INET)
    
    # Form Management
    form_status = Column(String(50), default='draft')  # draft, pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", backref="p66_loi_forms")
    transaction = relationship("LOITransaction", backref="p66_loi_form")
    
    # Indexes
    __table_args__ = (
        Index('idx_p66_loi_customer', 'customer_id'),
        Index('idx_p66_loi_transaction', 'transaction_id'),
        Index('idx_p66_loi_status', 'form_status'),
        Index('idx_p66_loi_created', 'created_at'),
    )