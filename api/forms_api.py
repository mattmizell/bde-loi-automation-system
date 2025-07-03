"""
Forms API endpoints for customer onboarding forms
Handles EFT, Customer Setup, and P66 LOI form submissions
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid
import base64
import logging
import json

# Database imports - simplified for now
try:
    from sqlalchemy.orm import Session
    from database.connection import DatabaseManager
    from database.models import (
        Customer, EFTFormData, CustomerSetupFormData, P66LOIFormData,
        LOITransaction, TransactionType, TransactionStatus, WorkflowStage
    )
    
    # Create get_db dependency function
    def get_db():
        db_manager = DatabaseManager()
        db_manager.initialize()
        db = db_manager.get_session()
        try:
            yield db
        finally:
            db.close()
            
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database not available: {e}")
    DATABASE_AVAILABLE = False
    
    # Mock classes for when database is not available
    class Session: pass
    class Customer: pass
    class EFTFormData: pass
    class CustomerSetupFormData: pass
    class P66LOIFormData: pass
    class LOITransaction: pass
    
    def get_db():
        return None

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/forms", tags=["Forms"])

# Pydantic models for request validation
class EFTFormRequest(BaseModel):
    company_name: str
    customer_id: Optional[str] = None
    bank_name: str
    bank_address: Optional[str] = None
    bank_city: Optional[str] = None
    bank_state: Optional[str] = None
    bank_zip: Optional[str] = None
    account_holder_name: str
    account_type: str  # checking, savings
    routing_number: str
    account_number: str
    authorized_by_name: str
    authorized_by_title: str
    authorization_date: str
    signature_data: str
    signature_timestamp: str

    @validator('account_type')
    def validate_account_type(cls, v):
        if v not in ['checking', 'savings']:
            raise ValueError('Account type must be checking or savings')
        return v

    @validator('routing_number')
    def validate_routing_number(cls, v):
        if len(v) != 9 or not v.isdigit():
            raise ValueError('Routing number must be 9 digits')
        return v

class SalesInitiatedEFTRequest(BaseModel):
    """Minimal EFT form data for sales-initiated workflow"""
    company_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    customer_id: Optional[str] = None
    # Pre-fill fields (all optional for sales person)
    bank_name: Optional[str] = None
    bank_address: Optional[str] = None
    bank_city: Optional[str] = None
    bank_state: Optional[str] = None
    bank_zip: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_type: Optional[str] = None
    authorized_by_name: Optional[str] = None
    authorized_by_title: Optional[str] = None
    federal_tax_id: Optional[str] = None
    # Sales person info
    initiated_by: Optional[str] = None
    notes: Optional[str] = None

class SalesInitiatedCustomerSetupRequest(BaseModel):
    """Minimal Customer Setup form data for sales-initiated workflow"""
    # Required fields - only company name and email required for sales initiation
    legal_business_name: str
    primary_contact_email: EmailStr
    
    # Basic contact info (optional for sales person to pre-fill)
    primary_contact_name: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    dba_name: Optional[str] = None
    
    # Business details (optional)
    business_type: Optional[str] = None
    years_in_business: Optional[int] = None
    federal_tax_id: Optional[str] = None
    state_tax_id: Optional[str] = None
    
    # Location info (optional)
    physical_address: Optional[str] = None
    physical_city: Optional[str] = None
    physical_state: Optional[str] = None
    physical_zip: Optional[str] = None
    mailing_address: Optional[str] = None
    mailing_city: Optional[str] = None
    mailing_state: Optional[str] = None
    mailing_zip: Optional[str] = None
    
    # Business details (optional)
    annual_fuel_volume: Optional[float] = None
    number_of_locations: Optional[int] = None
    current_fuel_brands: Optional[List[str]] = []
    
    # Sales person info
    initiated_by: Optional[str] = None
    notes: Optional[str] = None

class CustomerSetupFormRequest(BaseModel):
    # Support both simplified and full form field names
    legal_business_name: Optional[str] = None
    business_name: Optional[str] = None  # Simplified form
    dba_name: Optional[str] = None
    federal_tax_id: Optional[str] = None
    state_tax_id: Optional[str] = None
    business_type: str
    years_in_business: Optional[int] = None
    years_business: Optional[int] = None  # Simplified form
    physical_address: Optional[str] = None
    physical_city: Optional[str] = None
    physical_state: Optional[str] = None
    physical_zip: Optional[str] = None
    mailing_address: Optional[str] = None
    mailing_city: Optional[str] = None
    mailing_state: Optional[str] = None
    mailing_zip: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_name: Optional[str] = None  # Simplified form
    primary_contact_title: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    contact_phone: Optional[str] = None  # Simplified form
    primary_contact_email: Optional[EmailStr] = None
    contact_email: Optional[EmailStr] = None  # Simplified form
    accounts_payable_contact: Optional[str] = None
    accounts_payable_email: Optional[EmailStr] = None
    accounts_payable_phone: Optional[str] = None
    annual_fuel_volume: Optional[float] = None
    fuel_volume: Optional[float] = None  # Simplified form
    number_of_locations: Optional[int] = 1
    locations: Optional[int] = None  # Simplified form
    current_fuel_brands: Optional[List[str]] = []
    tank_sizes: Optional[List[Dict[str, Any]]] = []
    dispenser_count: Optional[int] = None
    pos_system: Optional[str] = None
    bank_references: Optional[List[Dict[str, str]]] = []
    trade_references: Optional[List[Dict[str, str]]] = []
    authorized_signer_name: Optional[str] = None
    authorized_signer_title: Optional[str] = None
    signature_data: Optional[str] = None
    signature_date: Optional[str] = None
    notes: Optional[str] = None  # Additional notes field

    @validator('business_type')
    def validate_business_type(cls, v):
        valid_types = ['corporation', 'llc', 'partnership', 'sole_proprietor']
        if v not in valid_types:
            raise ValueError(f'Business type must be one of: {valid_types}')
        return v

    @validator('years_in_business')
    def validate_years_in_business(cls, v):
        if v < 0 or v > 200:
            raise ValueError('Years in business must be between 0 and 200')
        return v

class P66LOIFormRequest(BaseModel):
    station_name: str
    station_address: str
    station_city: str
    station_state: str
    station_zip: str
    current_brand: str
    brand_expiration_date: Optional[str] = None
    monthly_gasoline_gallons: float
    monthly_diesel_gallons: float
    total_monthly_gallons: float
    contract_start_date: str
    contract_term_years: int = 10
    volume_incentive_requested: float
    image_funding_requested: float
    equipment_funding_requested: float = 0
    total_incentives_requested: float
    canopy_replacement: bool = False
    dispenser_replacement: bool = False
    tank_replacement: bool = False
    pos_upgrade: bool = False
    special_requirements: Optional[str] = None
    authorized_representative: str
    representative_title: str
    signature_data: str
    signature_date: str

    @validator('contract_term_years')
    def validate_contract_term(cls, v):
        if v not in [5, 7, 10]:
            raise ValueError('Contract term must be 5, 7, or 10 years')
        return v

    @validator('monthly_gasoline_gallons', 'monthly_diesel_gallons')
    def validate_fuel_volumes(cls, v):
        if v < 0:
            raise ValueError('Fuel volumes must be positive')
        return v

# Helper functions
def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def create_or_get_customer(db: Session, company_name: str, email: str = None, phone: str = None) -> Customer:
    """Create or retrieve customer record"""
    # First try to find existing customer
    customer = db.query(Customer).filter(Customer.company_name == company_name).first()
    
    if not customer:
        customer = Customer(
            id=uuid.uuid4(),
            company_name=company_name,
            contact_name="TBD",  # Will be updated later
            email=email or "tbd@example.com",
            phone=phone,
            customer_type="new_prospect",
            created_at=datetime.utcnow()
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        logger.info(f"Created new customer: {company_name}")
    
    return customer

def generate_eft_completion_form(transaction_id: str, pre_filled_data: dict) -> str:
    """Generate HTML form with pre-filled data for customer completion"""
    # Extract pre-filled values
    company_name = pre_filled_data.get('company_name', '')
    bank_name = pre_filled_data.get('bank_name', '')
    bank_address = pre_filled_data.get('bank_address', '')
    bank_city = pre_filled_data.get('bank_city', '')
    bank_state = pre_filled_data.get('bank_state', '')
    bank_zip = pre_filled_data.get('bank_zip', '')
    account_holder_name = pre_filled_data.get('account_holder_name', '')
    account_type = pre_filled_data.get('account_type', '')
    authorized_by_name = pre_filled_data.get('authorized_by_name', '')
    authorized_by_title = pre_filled_data.get('authorized_by_title', '')
    federal_tax_id = pre_filled_data.get('federal_tax_id', '')
    notes = pre_filled_data.get('notes', '')
    
    # Read the EFT form template
    import os
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'eft_completion_form.html')
    
    # For now, return a simple form with pre-filled data
    # In production, this would use a proper template engine
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complete EFT Authorization - Better Day Energy</title>
        <script>
            window.TRANSACTION_ID = '{transaction_id}';
            window.PRE_FILLED_DATA = {json.dumps(pre_filled_data)};
        </script>
    </head>
    <body>
        <h1>Complete Your EFT Authorization</h1>
        <p>Transaction ID: {transaction_id}</p>
        <script src="/static/eft_completion.js"></script>
    </body>
    </html>
    """

def generate_customer_setup_completion_form(transaction_id: str, pre_filled_data: dict) -> str:
    """Generate HTML form with pre-filled data for customer setup completion"""
    # Extract pre-filled values
    legal_business_name = pre_filled_data.get('legal_business_name', '')
    primary_contact_email = pre_filled_data.get('primary_contact_email', '')
    primary_contact_name = pre_filled_data.get('primary_contact_name', '')
    primary_contact_phone = pre_filled_data.get('primary_contact_phone', '')
    dba_name = pre_filled_data.get('dba_name', '')
    business_type = pre_filled_data.get('business_type', '')
    years_in_business = pre_filled_data.get('years_in_business', '')
    federal_tax_id = pre_filled_data.get('federal_tax_id', '')
    state_tax_id = pre_filled_data.get('state_tax_id', '')
    physical_address = pre_filled_data.get('physical_address', '')
    physical_city = pre_filled_data.get('physical_city', '')
    physical_state = pre_filled_data.get('physical_state', '')
    physical_zip = pre_filled_data.get('physical_zip', '')
    mailing_address = pre_filled_data.get('mailing_address', '')
    mailing_city = pre_filled_data.get('mailing_city', '')
    mailing_state = pre_filled_data.get('mailing_state', '')
    mailing_zip = pre_filled_data.get('mailing_zip', '')
    annual_fuel_volume = pre_filled_data.get('annual_fuel_volume', '')
    number_of_locations = pre_filled_data.get('number_of_locations', '')
    notes = pre_filled_data.get('notes', '')
    initiated_by = pre_filled_data.get('initiated_by', 'Better Day Energy Sales Team')
    
    # For now, return a simple form with pre-filled data
    # In production, this would use a proper template engine
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complete Customer Setup - Better Day Energy</title>
        <script>
            window.TRANSACTION_ID = '{transaction_id}';
            window.PRE_FILLED_DATA = {json.dumps(pre_filled_data)};
        </script>
    </head>
    <body>
        <h1>Complete Your Customer Setup</h1>
        <p>Transaction ID: {transaction_id}</p>
        <p>Initiated by: {initiated_by}</p>
        {f'<p><strong>Note:</strong> {notes}</p>' if notes else ''}
        <script src="/static/customer_setup_completion.js"></script>
    </body>
    </html>
    """

def save_signature_image(signature_data: str, form_type: str, form_id: str) -> str:
    """Save base64 signature image and return file path"""
    try:
        # Remove data URL prefix if present
        if ',' in signature_data:
            signature_data = signature_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(signature_data)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{form_type}_signature_{form_id}_{timestamp}.png"
        
        # In production, you'd save to cloud storage (S3, Google Cloud, etc.)
        # For now, we'll just return the filename and store base64 in database
        return filename
        
    except Exception as e:
        logger.error(f"Error processing signature image: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature data")

# API Endpoints

@router.post("/eft/submit")
async def submit_eft_form(
    form_data: EFTFormRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit EFT authorization form"""
    try:
        # Create or get customer
        customer = create_or_get_customer(
            db, 
            form_data.company_name,
            phone=None  # No email in EFT form
        )
        
        # Create EFT form record
        eft_form = EFTFormData(
            id=uuid.uuid4(),
            customer_id=customer.id,
            bank_name=form_data.bank_name,
            bank_address=form_data.bank_address,
            bank_city=form_data.bank_city,
            bank_state=form_data.bank_state,
            bank_zip=form_data.bank_zip,
            account_holder_name=form_data.account_holder_name,
            account_type=form_data.account_type,
            account_number=form_data.account_number,  # Should be encrypted in production
            routing_number=form_data.routing_number,  # Should be encrypted in production
            authorized_by_name=form_data.authorized_by_name,
            authorized_by_title=form_data.authorized_by_title,
            authorization_date=datetime.fromisoformat(form_data.authorization_date.replace('Z', '+00:00')),
            signature_data=form_data.signature_data,
            signature_ip=get_client_ip(request),
            signature_timestamp=datetime.fromisoformat(form_data.signature_timestamp.replace('Z', '+00:00')),
            form_status='completed',
            created_at=datetime.utcnow()
        )
        
        db.add(eft_form)
        db.commit()
        db.refresh(eft_form)
        
        logger.info(f"EFT form submitted successfully: {eft_form.id}")
        
        return {
            "success": True,
            "id": str(eft_form.id),
            "message": "EFT authorization form submitted successfully",
            "form_type": "eft"
        }
        
    except Exception as e:
        logger.error(f"Error submitting EFT form: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit EFT form")

@router.post("/eft/initiate")
async def initiate_eft_form(
    form_data: SalesInitiatedEFTRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Sales-initiated EFT form for customer completion"""
    try:
        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Database must be available for production use
        if not DATABASE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Database service unavailable. Cannot process form.")
        
        # Create or get customer
        customer = create_or_get_customer(
            db, 
            form_data.company_name,
            email=form_data.customer_email,
            phone=form_data.customer_phone
        )
        
        # Create LOI transaction record for tracking
        loi_transaction = LOITransaction(
            id=transaction_id,
            transaction_type=TransactionType.EFT_FORM,
            customer_id=customer.id,
            workflow_stage=WorkflowStage.PENDING_CUSTOMER_COMPLETION,
            status=TransactionStatus.PENDING,
            processing_context={
                "initiated_by": form_data.initiated_by or "Sales Team",
                "customer_email": form_data.customer_email,
                "customer_phone": form_data.customer_phone,
                "form_data": form_data.dict()  # Store pre-filled data
            },
            created_at=datetime.utcnow()
        )
        
        if DATABASE_AVAILABLE:
            db.add(loi_transaction)
            db.commit()
            
        # Send email to customer with completion link
        if hasattr(request.app.state, 'send_eft_completion_email'):
            await request.app.state.send_eft_completion_email(
                customer_email=form_data.customer_email,
                customer_name=form_data.company_name,
                transaction_id=transaction_id,
                pre_filled_data=form_data.dict()
            )
        
        logger.info(f"EFT form initiated for {form_data.company_name}: {transaction_id}")
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "message": "EFT form initiated successfully. Email sent to customer.",
            "completion_url": f"/forms/eft/complete/{transaction_id}"
        }
        
    except Exception as e:
        logger.error(f"Error initiating EFT form: {e}")
        if DATABASE_AVAILABLE:
            db.rollback()
        raise HTTPException(status_code=500, detail="Failed to initiate EFT form")

@router.post("/customer-setup/initiate")
async def initiate_customer_setup_form(
    form_data: SalesInitiatedCustomerSetupRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Sales-initiated Customer Setup form for customer completion"""
    try:
        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Database must be available for production use
        if not DATABASE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Database service unavailable. Cannot process form.")
        
        # Create or get customer
        customer = create_or_get_customer(
            db, 
            form_data.legal_business_name,
            email=form_data.primary_contact_email,
            phone=form_data.primary_contact_phone
        )
        
        # Create LOI transaction record for tracking
        loi_transaction = LOITransaction(
            id=transaction_id,
            transaction_type=TransactionType.CUSTOMER_SETUP_FORM,
            customer_id=customer.id,
            workflow_stage=WorkflowStage.PENDING_CUSTOMER_COMPLETION,
            status=TransactionStatus.PENDING,
            processing_context={
                "initiated_by": form_data.initiated_by or "Sales Team",
                "customer_email": form_data.primary_contact_email,
                "customer_phone": form_data.primary_contact_phone,
                "form_data": form_data.dict()  # Store pre-filled data
            },
            created_at=datetime.utcnow()
        )
        
        if DATABASE_AVAILABLE:
            db.add(loi_transaction)
            db.commit()
            
        # Send email to customer with completion link
        if hasattr(request.app.state, 'send_customer_setup_completion_email'):
            await request.app.state.send_customer_setup_completion_email(
                customer_email=form_data.primary_contact_email,
                customer_name=form_data.legal_business_name,
                transaction_id=transaction_id,
                pre_filled_data=form_data.dict()
            )
        
        logger.info(f"Customer Setup form initiated for {form_data.legal_business_name}: {transaction_id}")
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "message": "Customer Setup form initiated successfully. Email sent to customer.",
            "completion_url": f"/forms/customer-setup/complete/{transaction_id}"
        }
        
    except Exception as e:
        logger.error(f"Error initiating Customer Setup form: {e}")
        if DATABASE_AVAILABLE:
            db.rollback()
        raise HTTPException(status_code=500, detail="Failed to initiate Customer Setup form")

@router.get("/eft/complete/{transaction_id}")
async def get_eft_completion_page(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Get pre-filled EFT form for customer completion"""
    try:
        if not DATABASE_AVAILABLE:
            # Return mock data for testing
            return HTMLResponse(content="<h1>EFT Completion Form</h1><p>Database not available</p>")
            
        # Get transaction record
        transaction = db.query(LOITransaction).filter(
            LOITransaction.id == transaction_id,
            LOITransaction.transaction_type == TransactionType.EFT_FORM
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
            
        if transaction.status == TransactionStatus.COMPLETED:
            return HTMLResponse(content="<h1>Already Completed</h1><p>This EFT form has already been completed.</p>")
            
        # Extract form data from processing context
        form_data = transaction.processing_context.get('form_data', {}) if transaction.processing_context else {}
        
        # Generate pre-filled form HTML
        form_html = generate_eft_completion_form(transaction_id, form_data)
        
        return HTMLResponse(content=form_html)
        
    except Exception as e:
        logger.error(f"Error retrieving EFT completion form: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve form")

@router.post("/eft/complete/{transaction_id}")
async def complete_eft_form(
    transaction_id: str,
    form_data: EFTFormRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Complete EFT form with full validation and signature"""
    try:
        if not DATABASE_AVAILABLE:
            return {"success": True, "message": "Test mode - form completed"}
            
        # Get transaction record
        transaction = db.query(LOITransaction).filter(
            LOITransaction.id == transaction_id,
            LOITransaction.transaction_type == TransactionType.EFT_FORM
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
            
        if transaction.status == TransactionStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Form already completed")
        
        # Get customer info from processing context
        processing_context = transaction.processing_context or {}
        customer_email = processing_context.get('customer_email', '')
        customer_phone = processing_context.get('customer_phone', '')
        
        # Create or get customer
        customer = create_or_get_customer(
            db, 
            form_data.company_name,
            email=customer_email,
            phone=customer_phone
        )
        
        # Create EFT form record with complete data
        eft_form = EFTFormData(
            id=uuid.uuid4(),
            customer_id=customer.id,
            transaction_id=transaction_id,
            bank_name=form_data.bank_name,
            bank_address=form_data.bank_address,
            bank_city=form_data.bank_city,
            bank_state=form_data.bank_state,
            bank_zip=form_data.bank_zip,
            account_holder_name=form_data.account_holder_name,
            account_type=form_data.account_type,
            account_number=form_data.account_number,
            routing_number=form_data.routing_number,
            authorized_by_name=form_data.authorized_by_name,
            authorized_by_title=form_data.authorized_by_title,
            authorization_date=datetime.fromisoformat(form_data.authorization_date.replace('Z', '+00:00')),
            signature_data=form_data.signature_data,
            signature_ip=get_client_ip(request),
            signature_timestamp=datetime.fromisoformat(form_data.signature_timestamp.replace('Z', '+00:00')),
            form_status='completed',
            created_at=datetime.utcnow()
        )
        
        # Update transaction status
        transaction.status = TransactionStatus.COMPLETED
        transaction.workflow_stage = WorkflowStage.COMPLETED
        transaction.completed_at = datetime.utcnow()
        
        db.add(eft_form)
        db.commit()
        
        logger.info(f"EFT form completed: {eft_form.id} for transaction {transaction_id}")
        
        return {
            "success": True,
            "id": str(eft_form.id),
            "transaction_id": transaction_id,
            "message": "EFT authorization completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error completing EFT form: {e}")
        if DATABASE_AVAILABLE:
            db.rollback()
        raise HTTPException(status_code=500, detail="Failed to complete EFT form")

@router.get("/customer-setup/complete/{transaction_id}")
async def get_customer_setup_completion_page(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Get pre-filled Customer Setup form for customer completion"""
    try:
        if not DATABASE_AVAILABLE:
            # Return mock data for testing
            return HTMLResponse(content="<h1>Customer Setup Completion Form</h1><p>Database not available</p>")
            
        # Get transaction record
        transaction = db.query(LOITransaction).filter(
            LOITransaction.id == transaction_id,
            LOITransaction.transaction_type == TransactionType.CUSTOMER_SETUP_FORM
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
            
        if transaction.status == TransactionStatus.COMPLETED:
            return HTMLResponse(content="<h1>Already Completed</h1><p>This Customer Setup form has already been completed.</p>")
            
        # Extract form data from processing context
        form_data = transaction.processing_context.get('form_data', {}) if transaction.processing_context else {}
        
        # Generate pre-filled form HTML
        form_html = generate_customer_setup_completion_form(transaction_id, form_data)
        
        return HTMLResponse(content=form_html)
        
    except Exception as e:
        logger.error(f"Error retrieving Customer Setup completion form: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve form")

@router.post("/customer-setup/complete/{transaction_id}")
async def complete_customer_setup_form(
    transaction_id: str,
    form_data: CustomerSetupFormRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Complete Customer Setup form with full validation and signature"""
    try:
        if not DATABASE_AVAILABLE:
            return {"success": True, "message": "Test mode - form completed"}
            
        # Get transaction record
        transaction = db.query(LOITransaction).filter(
            LOITransaction.id == transaction_id,
            LOITransaction.transaction_type == TransactionType.CUSTOMER_SETUP_FORM
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
            
        if transaction.status == TransactionStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Form already completed")
        
        # Get customer info from processing context
        processing_context = transaction.processing_context or {}
        customer_email = processing_context.get('customer_email', '')
        customer_phone = processing_context.get('customer_phone', '')
        
        # Create or get customer
        customer = create_or_get_customer(
            db, 
            form_data.legal_business_name or form_data.business_name,
            email=customer_email,
            phone=customer_phone
        )
        
        # Create customer setup form record
        customer_setup_data = CustomerSetupFormData(
            customer_id=customer.id,
            legal_business_name=form_data.legal_business_name or form_data.business_name,
            dba_name=form_data.dba_name,
            federal_tax_id=form_data.federal_tax_id,
            state_tax_id=form_data.state_tax_id,
            business_type=form_data.business_type,
            years_in_business=form_data.years_in_business or form_data.years_business,
            physical_address=form_data.physical_address,
            physical_city=form_data.physical_city,
            physical_state=form_data.physical_state,
            physical_zip=form_data.physical_zip,
            mailing_address=form_data.mailing_address,
            mailing_city=form_data.mailing_city,
            mailing_state=form_data.mailing_state,
            mailing_zip=form_data.mailing_zip,
            primary_contact_name=form_data.primary_contact_name or form_data.contact_name,
            primary_contact_title=form_data.primary_contact_title,
            primary_contact_phone=form_data.primary_contact_phone or form_data.contact_phone,
            primary_contact_email=form_data.primary_contact_email or form_data.contact_email,
            accounts_payable_contact=form_data.accounts_payable_contact,
            accounts_payable_email=form_data.accounts_payable_email,
            accounts_payable_phone=form_data.accounts_payable_phone,
            annual_fuel_volume=form_data.annual_fuel_volume or form_data.fuel_volume,
            number_of_locations=form_data.number_of_locations or form_data.locations,
            current_fuel_brands=form_data.current_fuel_brands,
            dispenser_count=form_data.dispenser_count,
            pos_system=form_data.pos_system,
            authorized_signer_name=form_data.authorized_signer_name,
            authorized_signer_title=form_data.authorized_signer_title,
            signature_data=form_data.signature_data,
            signature_date=datetime.fromisoformat(form_data.signature_date.replace('Z', '+00:00')) if form_data.signature_date else None,
            signature_ip=get_client_ip(request),
            form_status='completed',
            created_at=datetime.utcnow()
        )
        
        db.add(customer_setup_data)
        
        # Update transaction status
        transaction.status = TransactionStatus.COMPLETED
        transaction.workflow_stage = WorkflowStage.COMPLETED
        transaction.completed_at = datetime.utcnow()
        # Update processing context with final form data
        if transaction.processing_context:
            transaction.processing_context['final_form_data'] = form_data.dict()
        else:
            transaction.processing_context = {'final_form_data': form_data.dict()}
        
        db.commit()
        
        logger.info(f"Customer Setup form completed for {form_data.legal_business_name}: {transaction_id}")
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "message": "Customer Setup form completed successfully!",
            "customer_id": customer.id
        }
        
    except Exception as e:
        logger.error(f"Error completing Customer Setup form: {e}")
        if DATABASE_AVAILABLE:
            db.rollback()
        raise HTTPException(status_code=500, detail="Failed to complete Customer Setup form")

@router.post("/customer-setup/submit")
async def submit_customer_setup_form(
    form_data: CustomerSetupFormRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit customer setup document form"""
    try:
        # Map simplified form fields to full field names
        business_name = form_data.legal_business_name or form_data.business_name
        contact_name = form_data.primary_contact_name or form_data.contact_name
        contact_email = form_data.primary_contact_email or form_data.contact_email
        contact_phone = form_data.primary_contact_phone or form_data.contact_phone
        years_in_business = form_data.years_in_business or form_data.years_business
        annual_fuel_volume = form_data.annual_fuel_volume or form_data.fuel_volume
        number_of_locations = form_data.number_of_locations or form_data.locations or 1
        
        # Create or get customer
        customer = create_or_get_customer(
            db,
            business_name,
            email=contact_email,
            phone=contact_phone
        )
        
        # Update customer record with complete information
        customer.contact_name = contact_name
        customer.email = contact_email
        customer.phone = contact_phone
        customer.street_address = form_data.physical_address
        customer.city = form_data.physical_city
        customer.state = form_data.physical_state
        customer.zip_code = form_data.physical_zip
        
        # Create customer setup form record
        setup_form = CustomerSetupFormData(
            id=uuid.uuid4(),
            customer_id=customer.id,
            legal_business_name=business_name,
            dba_name=form_data.dba_name,
            federal_tax_id=form_data.federal_tax_id,  # Should be encrypted in production
            state_tax_id=form_data.state_tax_id,  # Should be encrypted in production
            business_type=form_data.business_type,
            physical_address=form_data.physical_address,
            physical_city=form_data.physical_city,
            physical_state=form_data.physical_state,
            physical_zip=form_data.physical_zip,
            mailing_address=form_data.mailing_address,
            mailing_city=form_data.mailing_city,
            mailing_state=form_data.mailing_state,
            mailing_zip=form_data.mailing_zip,
            primary_contact_name=contact_name,
            primary_contact_title=form_data.primary_contact_title,
            primary_contact_phone=contact_phone,
            primary_contact_email=contact_email,
            accounts_payable_contact=form_data.accounts_payable_contact,
            accounts_payable_email=form_data.accounts_payable_email,
            accounts_payable_phone=form_data.accounts_payable_phone,
            years_in_business=years_in_business,
            annual_fuel_volume=annual_fuel_volume,
            number_of_locations=number_of_locations,
            current_fuel_brands=form_data.current_fuel_brands,
            tank_sizes=form_data.tank_sizes,
            dispenser_count=form_data.dispenser_count,
            pos_system=form_data.pos_system,
            bank_references=form_data.bank_references,
            trade_references=form_data.trade_references,
            authorized_signer_name=form_data.authorized_signer_name,
            authorized_signer_title=form_data.authorized_signer_title,
            signature_data=form_data.signature_data,
            signature_date=datetime.fromisoformat(form_data.signature_date.replace('Z', '+00:00')) if form_data.signature_date else None,
            signature_ip=get_client_ip(request),
            form_status='completed',
            created_at=datetime.utcnow()
        )
        
        db.add(setup_form)
        db.commit()
        db.refresh(setup_form)
        
        logger.info(f"Customer setup form submitted successfully: {setup_form.id}")
        
        return {
            "success": True,
            "id": str(setup_form.id),
            "message": "Customer setup form submitted successfully",
            "form_type": "customer_setup"
        }
        
    except Exception as e:
        logger.error(f"Error submitting customer setup form: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit customer setup form")

@router.post("/p66-loi/submit")
async def submit_p66_loi_form(
    form_data: P66LOIFormRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit Phillips 66 Letter of Intent form"""
    try:
        # Create or get customer (use station name as company name for LOI)
        customer = create_or_get_customer(
            db,
            form_data.station_name
        )
        
        # Update customer address with station address
        customer.street_address = form_data.station_address
        customer.city = form_data.station_city
        customer.state = form_data.station_state
        customer.zip_code = form_data.station_zip
        
        # Create LOI transaction record
        loi_transaction = LOITransaction(
            id=uuid.uuid4(),
            transaction_type=TransactionType.NEW_LOI_REQUEST,
            status=TransactionStatus.PENDING,
            workflow_stage=WorkflowStage.INITIAL,
            customer_id=customer.id,
            created_at=datetime.utcnow()
        )
        
        db.add(loi_transaction)
        db.flush()  # Get the transaction ID
        
        # Create P66 LOI form record
        p66_loi_form = P66LOIFormData(
            id=uuid.uuid4(),
            customer_id=customer.id,
            transaction_id=loi_transaction.id,
            station_name=form_data.station_name,
            station_address=form_data.station_address,
            station_city=form_data.station_city,
            station_state=form_data.station_state,
            station_zip=form_data.station_zip,
            current_brand=form_data.current_brand,
            brand_expiration_date=datetime.fromisoformat(form_data.brand_expiration_date) if form_data.brand_expiration_date else None,
            monthly_gasoline_gallons=form_data.monthly_gasoline_gallons,
            monthly_diesel_gallons=form_data.monthly_diesel_gallons,
            total_monthly_gallons=form_data.total_monthly_gallons,
            contract_start_date=datetime.fromisoformat(form_data.contract_start_date),
            contract_term_years=form_data.contract_term_years,
            volume_incentive_requested=form_data.volume_incentive_requested,
            image_funding_requested=form_data.image_funding_requested,
            equipment_funding_requested=form_data.equipment_funding_requested,
            total_incentives_requested=form_data.total_incentives_requested,
            canopy_replacement=form_data.canopy_replacement,
            dispenser_replacement=form_data.dispenser_replacement,
            tank_replacement=form_data.tank_replacement,
            pos_upgrade=form_data.pos_upgrade,
            special_requirements=form_data.special_requirements,
            authorized_representative=form_data.authorized_representative,
            representative_title=form_data.representative_title,
            signature_data=form_data.signature_data,
            signature_date=datetime.fromisoformat(form_data.signature_date.replace('Z', '+00:00')),
            signature_ip=get_client_ip(request),
            form_status='completed',
            created_at=datetime.utcnow(),
            submitted_at=datetime.utcnow()
        )
        
        db.add(p66_loi_form)
        
        # Update transaction status
        loi_transaction.status = TransactionStatus.PROCESSING
        loi_transaction.workflow_stage = WorkflowStage.DOCUMENT_GENERATED
        loi_transaction.started_at = datetime.utcnow()
        
        db.commit()
        db.refresh(p66_loi_form)
        
        logger.info(f"P66 LOI form submitted successfully: {p66_loi_form.id}")
        
        return {
            "success": True,
            "id": str(p66_loi_form.id),
            "transaction_id": str(loi_transaction.id),
            "message": "Phillips 66 Letter of Intent submitted successfully",
            "form_type": "p66_loi"
        }
        
    except Exception as e:
        logger.error(f"Error submitting P66 LOI form: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit P66 LOI form")

# Form completion pages
@router.get("/eft/complete/{form_id}", response_class=HTMLResponse)
async def eft_completion_page(form_id: str, db: Session = Depends(get_db)):
    """EFT form completion page"""
    try:
        form = db.query(EFTFormData).filter(EFTFormData.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EFT Authorization Complete</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success-box {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; }}
                .details {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="success-box">
                <h2>✅ EFT Authorization Complete</h2>
                <p>Your Electronic Funds Transfer authorization has been successfully submitted and processed.</p>
                
                <div class="details">
                    <h4>Authorization Details:</h4>
                    <p><strong>Company:</strong> {form.customer.company_name}</p>
                    <p><strong>Bank:</strong> {form.bank_name}</p>
                    <p><strong>Account Holder:</strong> {form.account_holder_name}</p>
                    <p><strong>Authorized By:</strong> {form.authorized_by_name}, {form.authorized_by_title}</p>
                    <p><strong>Submitted:</strong> {form.created_at.strftime("%B %d, %Y at %I:%M %p")}</p>
                    <p><strong>Reference ID:</strong> {form_id}</p>
                </div>
                
                <p>Better Day Energy will now process your authorization. You will receive confirmation via email once setup is complete.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error loading EFT completion page: {e}")
        raise HTTPException(status_code=500, detail="Error loading completion page")

@router.get("/customer-setup/complete/{form_id}", response_class=HTMLResponse)
async def customer_setup_completion_page(form_id: str, db: Session = Depends(get_db)):
    """Customer setup completion page"""
    try:
        form = db.query(CustomerSetupFormData).filter(CustomerSetupFormData.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Customer Setup Complete</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success-box {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; }}
                .details {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                .next-steps {{ background: #cfe2ff; border: 1px solid #b6d4fe; padding: 15px; border-radius: 6px; }}
            </style>
        </head>
        <body>
            <div class="success-box">
                <h2>✅ Customer Setup Complete</h2>
                <p>Your customer setup application has been successfully submitted!</p>
                
                <div class="details">
                    <h4>Application Details:</h4>
                    <p><strong>Business:</strong> {form.legal_business_name}</p>
                    <p><strong>Contact:</strong> {form.primary_contact_name}, {form.primary_contact_title}</p>
                    <p><strong>Email:</strong> {form.primary_contact_email}</p>
                    <p><strong>Annual Volume:</strong> {form.annual_fuel_volume:,.0f} gallons</p>
                    <p><strong>Submitted:</strong> {form.created_at.strftime("%B %d, %Y at %I:%M %p")}</p>
                    <p><strong>Application ID:</strong> {form_id}</p>
                </div>
                
                <div class="next-steps">
                    <h4>Next Steps:</h4>
                    <ol>
                        <li>Credit application review (2-3 business days)</li>
                        <li>Reference verification</li>
                        <li>Account setup and approval notification</li>
                        <li>Fuel supply agreement execution</li>
                    </ol>
                    <p>You will receive updates via email at {form.primary_contact_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error loading customer setup completion page: {e}")
        raise HTTPException(status_code=500, detail="Error loading completion page")

@router.get("/p66-loi/complete/{form_id}", response_class=HTMLResponse)
async def p66_loi_completion_page(form_id: str, db: Session = Depends(get_db)):
    """P66 LOI completion page"""
    try:
        form = db.query(P66LOIFormData).filter(P66LOIFormData.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phillips 66 LOI Complete</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success-box {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; }}
                .details {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                .incentives {{ background: #e8f5e9; border: 1px solid #4caf50; padding: 15px; border-radius: 6px; }}
                .brand-header {{ background: #ee0000; color: white; padding: 15px; text-align: center; border-radius: 6px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="brand-header">
                <h2>Phillips 66 Letter of Intent Submitted</h2>
            </div>
            
            <div class="success-box">
                <h3>✅ Your Letter of Intent has been successfully submitted!</h3>
                
                <div class="details">
                    <h4>Station Information:</h4>
                    <p><strong>Station:</strong> {form.station_name}</p>
                    <p><strong>Location:</strong> {form.station_address}, {form.station_city}, {form.station_state} {form.station_zip}</p>
                    <p><strong>Current Brand:</strong> {form.current_brand}</p>
                    <p><strong>Monthly Volume:</strong> {form.total_monthly_gallons:,.0f} gallons</p>
                    <p><strong>Contract Term:</strong> {form.contract_term_years} years</p>
                    <p><strong>Start Date:</strong> {form.contract_start_date.strftime("%B %d, %Y")}</p>
                    <p><strong>Representative:</strong> {form.authorized_representative}, {form.representative_title}</p>
                    <p><strong>LOI ID:</strong> {form_id}</p>
                </div>
                
                <div class="incentives">
                    <h4>💰 Requested Incentive Package:</h4>
                    <p><strong>Volume Incentive:</strong> ${form.volume_incentive_requested:,.2f}</p>
                    <p><strong>Image Funding:</strong> ${form.image_funding_requested:,.2f}</p>
                    <p><strong>Equipment Funding:</strong> ${form.equipment_funding_requested:,.2f}</p>
                    <p><strong>Total Package:</strong> ${form.total_incentives_requested:,.2f}</p>
                </div>
                
                <h4>What happens next?</h4>
                <ol>
                    <li><strong>Review Process</strong> - Phillips 66 will review your application (5-7 business days)</li>
                    <li><strong>Site Evaluation</strong> - Potential site visit and market analysis</li>
                    <li><strong>Approval Decision</strong> - Final approval and incentive package confirmation</li>
                    <li><strong>Contract Execution</strong> - Formal fuel supply agreement signing</li>
                    <li><strong>Implementation</strong> - Branding conversion and fuel supply setup</li>
                </ol>
                
                <p><strong>Important:</strong> This Letter of Intent is non-binding and subject to Phillips 66 approval and final contract negotiation.</p>
                
                <p>You will receive status updates throughout the review process. Thank you for choosing Phillips 66 and Better Day Energy!</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error loading P66 LOI completion page: {e}")
        raise HTTPException(status_code=500, detail="Error loading completion page")

# Form status and management endpoints
@router.get("/status/{form_type}/{form_id}")
async def get_form_status(form_type: str, form_id: str, db: Session = Depends(get_db)):
    """Get form submission status"""
    try:
        if form_type == "eft":
            form = db.query(EFTFormData).filter(EFTFormData.id == form_id).first()
        elif form_type == "customer-setup":
            form = db.query(CustomerSetupFormData).filter(CustomerSetupFormData.id == form_id).first()
        elif form_type == "p66-loi":
            form = db.query(P66LOIFormData).filter(P66LOIFormData.id == form_id).first()
        else:
            raise HTTPException(status_code=400, detail="Invalid form type")
        
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        return {
            "success": True,
            "form_id": form_id,
            "form_type": form_type,
            "status": form.form_status,
            "submitted_at": form.created_at.isoformat(),
            "customer_name": form.customer.company_name if hasattr(form, 'customer') else None
        }
        
    except Exception as e:
        logger.error(f"Error getting form status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving form status")