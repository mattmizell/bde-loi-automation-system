# Service-Oriented Architecture for BDE LOI Automation

## Overview
This document outlines the separation of the monolithic signature server into distinct services with clear boundaries and responsibilities.

## Current Problems
- **4,638-line monolithic file** with mixed responsibilities
- **Tight coupling** between CRM operations and document management
- **No clear API boundaries** between different business domains
- **Difficult testing** due to interdependencies
- **Poor scalability** - can't scale CRM and document services independently

## Proposed Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / Router                     │
│                  (main_server.py)                          │
└─────────────────┬───────────────────┬───────────────────────┘
                  │                   │
        ┌─────────▼─────────┐ ┌───────▼────────────────────────┐
        │   CRM Service     │ │  Document Management Service   │
        │   (Port 8001)     │ │       (Port 8002)             │
        └───────────────────┘ └────────────────────────────────┘
```

---

## 1. CRM Service Layer (Standalone)

### **Purpose:** 
Centralized customer relationship management with caching, sync, and multi-app support

### **Responsibilities:**
- Contact management (CRUD operations)
- Data caching and synchronization with LACRM
- Background sync operations
- Multi-application authentication (CRM Bridge API)
- Contact search and fuzzy matching
- Data validation and normalization

### **API Endpoints:**
```
POST   /api/v1/contacts              # Create contact
GET    /api/v1/contacts              # List contacts (paginated)
GET    /api/v1/contacts/{id}         # Get specific contact
PUT    /api/v1/contacts/{id}         # Update contact
DELETE /api/v1/contacts/{id}         # Delete contact
POST   /api/v1/contacts/search       # Search contacts
GET    /api/v1/contacts/sync-status  # Get sync status
POST   /api/v1/sync/trigger          # Trigger manual sync
GET    /api/v1/health                # Service health check

# Multi-app authentication (CRM Bridge)
POST   /api/v1/auth/verify           # Verify app token
GET    /api/v1/auth/permissions      # Get app permissions
```

### **Data Models:**
```python
class Contact:
    id: str
    first_name: str
    last_name: str
    company_name: str
    email: str
    phone: str
    address: dict
    custom_fields: dict
    created_at: datetime
    updated_at: datetime
    last_synced: datetime

class SyncStatus:
    last_sync: datetime
    status: str  # 'active', 'error', 'idle'
    total_contacts: int
    pending_writes: int
    error_count: int
```

---

## 2. Document Management Service

### **Purpose:**
Electronic signature workflows, document generation, and ESIGN compliance

### **Responsibilities:**
- LOI creation and management
- Electronic signature workflows
- PDF generation and storage
- ESIGN Act compliance validation
- Document integrity verification
- Email notifications for signatures
- Audit trail management

### **API Endpoints:**
```
POST   /api/v1/loi                   # Create new LOI
GET    /api/v1/loi/{id}              # Get LOI details
POST   /api/v1/signatures/{token}    # Submit electronic signature
GET    /api/v1/signatures/{code}/verify # Verify signature integrity
GET    /api/v1/documents/{code}      # Download signed document
POST   /api/v1/paper-copy/request    # Request paper copy (ESIGN)
GET    /api/v1/audit/{code}          # Get audit report
GET    /api/v1/health                # Service health check

# Admin endpoints
GET    /api/v1/admin/signatures      # List all signatures
GET    /api/v1/admin/dashboard       # Admin dashboard data
```

### **Data Models:**
```python
class LOI:
    id: str
    transaction_id: str
    contact_id: str  # References CRM service
    signer_name: str
    signer_email: str
    company_name: str
    deal_terms: dict
    status: str  # 'draft', 'sent', 'signed', 'completed'
    created_at: datetime
    signed_at: datetime
    verification_code: str

class ElectronicSignature:
    id: str
    loi_id: str
    signature_image: bytes
    signed_at: datetime
    ip_address: str
    user_agent: str
    integrity_hash: str
    esign_compliance: dict
    audit_trail: list
```

---

## 3. Service Communication

### **Inter-Service Communication:**
- **HTTP REST APIs** between services
- **Async messaging** for non-critical operations
- **Shared database** for transactional consistency (optional)
- **Service discovery** for dynamic endpoint resolution

### **Contact Lookup Pattern:**
```python
# Document service needs contact info
class ContactServiceClient:
    async def get_contact(self, contact_id: str) -> Contact:
        response = await self.http_client.get(f"{CRM_SERVICE_URL}/api/v1/contacts/{contact_id}")
        return Contact.from_dict(response.json())
    
    async def search_contacts(self, query: str) -> List[Contact]:
        response = await self.http_client.post(f"{CRM_SERVICE_URL}/api/v1/contacts/search", 
                                              json={"query": query})
        return [Contact.from_dict(c) for c in response.json()["contacts"]]
```

### **Document Storage Pattern:**
```python
# CRM service stores document metadata, not content
class DocumentReference:
    document_id: str
    document_type: str  # 'loi', 'contract', 'invoice'
    verification_code: str
    document_url: str  # Points to document service
    signed_at: datetime
    signer_contact_id: str
```

---

## 4. Directory Structure

```
bde_automation_system/
├── services/
│   ├── crm_service/
│   │   ├── main.py                    # CRM service entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── contacts.py            # Contact CRUD API
│   │   │   ├── search.py              # Search API
│   │   │   ├── sync.py                # Sync management API
│   │   │   └── auth.py                # Multi-app auth API
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── contact.py             # Contact data model
│   │   │   └── sync_status.py         # Sync status model
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── contact_service.py     # Business logic
│   │   │   ├── sync_service.py        # LACRM synchronization
│   │   │   ├── cache_service.py       # Local caching
│   │   │   └── auth_service.py        # Authentication logic
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── repositories.py        # Data access layer
│   │   │   └── database.py            # Database connection
│   │   └── config/
│   │       ├── __init__.py
│   │       └── settings.py            # CRM service config
│   │
│   └── document_service/
│       ├── main.py                    # Document service entry point
│       ├── api/
│       │   ├── __init__.py
│       │   ├── loi.py                 # LOI management API
│       │   ├── signatures.py          # Signature workflow API
│       │   ├── documents.py           # Document download API
│       │   └── admin.py               # Admin panel API
│       ├── models/
│       │   ├── __init__.py
│       │   ├── loi.py                 # LOI data model
│       │   └── signature.py           # Signature data model
│       ├── services/
│       │   ├── __init__.py
│       │   ├── loi_service.py         # LOI business logic
│       │   ├── signature_service.py   # Signature processing
│       │   ├── pdf_service.py         # PDF generation
│       │   ├── email_service.py       # Email notifications
│       │   └── esign_service.py       # ESIGN compliance
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── templates.py           # HTML templates
│       │   ├── static.py              # CSS/JS assets
│       │   └── pages.py               # Page generators
│       ├── data/
│       │   ├── __init__.py
│       │   ├── repositories.py        # Data access layer
│       │   └── signature_storage.py   # Signature storage
│       └── config/
│           ├── __init__.py
│           └── settings.py            # Document service config
│
├── shared/
│   ├── __init__.py
│   ├── models/                        # Shared data models
│   ├── clients/                       # Service clients
│   ├── auth/                          # Shared authentication
│   └── utils/                         # Common utilities
│
├── gateway/
│   ├── main.py                        # API gateway entry point
│   ├── routing.py                     # Request routing logic
│   ├── middleware.py                  # Auth, logging, CORS
│   └── config.py                      # Gateway configuration
│
└── deployment/
    ├── docker-compose.yml             # Multi-service deployment
    ├── crm-service.dockerfile         # CRM service container
    ├── document-service.dockerfile    # Document service container
    └── gateway.dockerfile             # Gateway container
```

---

## 5. Benefits of This Architecture

### **Separation of Concerns:**
- **CRM Service:** Pure customer data management
- **Document Service:** Pure document/signature workflows
- **Gateway:** Pure routing and API aggregation

### **Independent Scaling:**
- Scale CRM service for heavy contact operations
- Scale document service for signature peaks
- Scale services independently based on load

### **Technology Independence:**
- CRM service can use different database (PostgreSQL)
- Document service can use different storage (S3 for PDFs)
- Each service can use optimal tech stack

### **Team Independence:**
- CRM team owns contact management
- Document team owns signature workflows
- Clear API contracts between teams

### **Testing & Deployment:**
- Unit test each service independently
- Deploy services independently
- Rollback individual services without affecting others

### **Multi-Application Support:**
- CRM service supports LOI app, Bolt sales tool, Adam's app
- Document service can support multiple document types
- Clean API for external integrations

---

## 6. Migration Strategy

### **Phase 1: Extract CRM Service (Week 1)**
1. Create `services/crm_service/` structure
2. Move all CRM-related code from integrated server
3. Create REST API for contact operations
4. Maintain backward compatibility with current LOI system

### **Phase 2: Extract Document Service (Week 2)**
1. Create `services/document_service/` structure
2. Move signature, PDF, and ESIGN logic
3. Update to use CRM service API for contact lookups
4. Create clean document management API

### **Phase 3: Create API Gateway (Week 3)**
1. Create simple routing gateway
2. Route requests to appropriate services
3. Handle authentication and CORS
4. Maintain single entry point for clients

### **Phase 4: Deployment & Testing (Week 4)**
1. Set up multi-service deployment
2. Comprehensive integration testing
3. Performance testing
4. Production deployment

---

## 7. Service API Contracts

### **CRM Service Contract:**
```yaml
openapi: 3.0.0
info:
  title: BDE CRM Service API
  version: 1.0.0
paths:
  /api/v1/contacts:
    get:
      summary: List contacts
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        200:
          description: List of contacts
          content:
            application/json:
              schema:
                type: object
                properties:
                  contacts:
                    type: array
                    items:
                      $ref: '#/components/schemas/Contact'
                  total:
                    type: integer
                  has_more:
                    type: boolean
```

### **Document Service Contract:**
```yaml
openapi: 3.0.0
info:
  title: BDE Document Service API
  version: 1.0.0
paths:
  /api/v1/loi:
    post:
      summary: Create new LOI
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LOIRequest'
      responses:
        201:
          description: LOI created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LOI'
```

This architecture provides clean separation, independent scaling, and proper service boundaries while maintaining all current functionality.