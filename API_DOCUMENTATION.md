# Better Day Energy LOI Automation System API Documentation

## 🚀 New Modular Architecture (January 2025)
**API Gateway**: `http://localhost:8000` (Development) | `https://bde-api-gateway.onrender.com` (Production)

The system has been modularized into microservices while maintaining full backward compatibility.

### 🌐 Production Service URLs
- **API Gateway**: `https://bde-api-gateway.onrender.com`
- **CRM Service**: `https://bde-crm-service.onrender.com` 
- **Document Service**: `https://bde-document-service.onrender.com`
- **Legacy LOI**: `https://bde-loi-legacy.onrender.com` (backward compatibility)

### 🏗️ Service Architecture
- **API Gateway (Port 8000)**: Central routing and load balancing
- **CRM Service (Port 8001)**: Contact management and LACRM synchronization  
- **Document Service (Port 8002)**: Document processing and digital signatures

### 📋 Quick Reference for Adam & Bolt.new
- **Development**: `http://localhost:8000`
- **Production**: `https://bde-api-gateway.onrender.com`
- **Auth Header**: `Authorization: ApiKey loi-service-key`
- **Legacy Endpoints**: All existing endpoints work unchanged (just change URL)
- **Health Check**: `GET /status` - Shows all service health
- **Contact Search**: `POST /api/search_contacts` - Advanced fuzzy search
- **Create Contact**: `POST /api/create_contact` - Add new contacts

## Table of Contents
1. [🔑 Authentication](#authentication)
2. [📱 Modular CRM API](#modular-crm-api) **← NEW**
3. [📄 Document Management API](#document-management-api) **← NEW**
4. [🏥 Service Health & Monitoring](#service-health--monitoring) **← NEW**
5. [🔄 Legacy API (Preserved)](#legacy-api-preserved)
6. [💡 Usage Examples](#usage-examples)

---

## Authentication

### User Login
**POST** `/api/login`

Login to the system with email and password.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "matt.mizell@gmail.com",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "success": true,
  "session_token": "your-session-token-here",
  "user": {
    "email": "matt.mizell@gmail.com",
    "name": "Matt Mizell",
    "role": "admin"
  }
}
```

### CRM Bridge Authentication
The CRM Bridge API uses Bearer token authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer bde_loi_auth_e6db5173a4393421ffadae85f9a3513e
```

Available tokens:
- **LOI Automation**: `bde_loi_auth_e6db5173a4393421ffadae85f9a3513e`
- **Bolt Sales Tool**: `bde_bolt_auth_3c0a8f9c5e7d4a2b1f6e8d7c9a5b3e1f`
- **Adam Sales App**: `bde_adam_auth_7f2e4a6b8d1c9e5a3f7b2d8e6c4a1f9d`

---

## 📱 Modular CRM API

The new CRM service provides enhanced contact management with advanced search, background synchronization, and improved performance.

### Contact Operations

#### List All Contacts
```http
GET /api/contacts?limit=50&offset=0
```

**Query Parameters:**
- `limit`: Number of contacts (default: 50, max: 100)
- `offset`: Pagination offset (default: 0)

**Example:**
```bash
curl "http://localhost:8000/api/contacts?limit=25" \
  -H "Authorization: ApiKey loi-service-key"
```

**Response:**
```json
{
  "contacts": [
    {
      "id": "12345",
      "first_name": "John",
      "last_name": "Doe", 
      "company_name": "Doe's Gas Station",
      "email": "john@doesgas.com",
      "phone": "5551234567",
      "full_name": "John Doe",
      "display_name": "John Doe (Doe's Gas Station)",
      "address": {
        "street": "123 Main St",
        "city": "Springfield", 
        "state": "IL",
        "zip": "62701",
        "country": "US"
      },
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z",
      "last_synced": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "timestamp": "2025-01-25T12:00:00Z"
}
```

#### Get Specific Contact
```http
GET /api/contacts/{contact_id}
```

**Example:**
```bash
curl "http://localhost:8000/api/contacts/12345" \
  -H "Authorization: ApiKey loi-service-key"
```

#### Create New Contact
```http
POST /api/contacts
POST /api/create_contact  (legacy endpoint - same functionality)
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "company_name": "Smith's Fuel Center", 
  "email": "jane@smithsfuel.com",
  "phone": "555-0123",
  "address": {
    "street": "456 Oak Ave",
    "city": "Chicago",
    "state": "IL", 
    "zip": "60601",
    "country": "US"
  },
  "custom_fields": {
    "lead_source": "website",
    "annual_fuel_volume": "50000"
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/contacts" \
  -H "Authorization: ApiKey loi-service-key" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith", 
    "company_name": "Smith Fuel Center",
    "email": "jane@smithfuel.com",
    "phone": "555-0123"
  }'
```

**Response:**
```json
{
  "id": "67890",
  "first_name": "Jane",
  "last_name": "Smith",
  "company_name": "Smith Fuel Center",
  "email": "jane@smithfuel.com",
  "phone": "5550123",
  "created_at": "2025-01-25T12:00:00Z",
  "updated_at": "2025-01-25T12:00:00Z",
  "source": "api"
}
```

#### Update Contact
```http
PUT /api/contacts/{contact_id}
```

**Request Body:** (partial updates supported)
```json
{
  "phone": "555-9999",
  "custom_fields": {
    "status": "qualified_lead",
    "last_contact": "2025-01-25"
  }
}
```

**Example:**
```bash
curl -X PUT "http://localhost:8000/api/contacts/12345" \
  -H "Authorization: ApiKey loi-service-key" \
  -H "Content-Type: application/json" \
  -d '{"phone": "555-9999"}'
```

#### Delete Contact
```http
DELETE /api/contacts/{contact_id}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/contacts/12345" \
  -H "Authorization: ApiKey loi-service-key"
```

### Advanced Contact Search

#### Fuzzy Search with Ranking
```http
POST /api/contacts/search
POST /api/search_contacts  (legacy endpoint - same functionality)
```

**Request Body:**
```json
{
  "query": "smith fuel",
  "limit": 20,
  "fuzzy_threshold": 0.6,
  "include_score": true,
  "sort_by": "score"
}
```

**Parameters:**
- `query`: Search term (searches name, company, email, phone)
- `limit`: Max results (default: 20, max: 100) 
- `fuzzy_threshold`: Minimum similarity score 0.0-1.0 (default: 0.6)
- `include_score`: Include relevance scores (default: true)
- `sort_by`: Sort order ("score", "name", "company", default: "score")

**Example:**
```bash
curl -X POST "http://localhost:8000/api/contacts/search" \
  -H "Authorization: ApiKey loi-service-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fuel station",
    "limit": 10,
    "fuzzy_threshold": 0.7
  }'
```

**Response:**
```json
{
  "query": "fuel station",
  "results": [
    {
      "contact": {
        "id": "12345",
        "first_name": "John",
        "last_name": "Doe",
        "company_name": "Doe's Fuel Station",
        "email": "john@doesfuel.com",
        "phone": "5551234567",
        "full_name": "John Doe",
        "display_name": "John Doe (Doe's Fuel Station)"
      },
      "score": 0.95,
      "match_fields": ["company_name"]
    },
    {
      "contact": {
        "id": "67890", 
        "first_name": "Jane",
        "last_name": "Smith",
        "company_name": "Smith Gas Station",
        "email": "jane@smithgas.com",
        "phone": "5550123",
        "full_name": "Jane Smith",
        "display_name": "Jane Smith (Smith Gas Station)"
      },
      "score": 0.87,
      "match_fields": ["company_name"]
    }
  ],
  "total_found": 2,
  "search_options": {
    "limit": 10,
    "fuzzy_threshold": 0.7,
    "include_score": true
  },
  "timestamp": "2025-01-25T12:00:00Z"
}
```

### LACRM Synchronization

#### Get Sync Status
```http
GET /api/sync/status
```

**Example:**
```bash
curl "http://localhost:8000/api/sync/status" \
  -H "Authorization: ApiKey loi-service-key"
```

**Response:**
```json
{
  "sync_active": true,
  "last_sync": "2025-01-25T11:45:00Z",
  "total_contacts": 1247,
  "pending_writes": 3,
  "error_count": 0,
  "service": "crm-service",
  "timestamp": "2025-01-25T12:00:00Z"
}
```

#### Trigger Manual Sync
```http
POST /api/sync/trigger
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/sync/trigger" \
  -H "Authorization: ApiKey loi-service-key"
```

**Response:**
```json
{
  "message": "Manual sync triggered successfully",
  "timestamp": "2025-01-25T12:00:00Z"
}
```

---

## 📄 Document Management API

The document service handles LOI creation, PDF generation, and digital signature workflows.

### Document Operations

#### List Documents
```http
GET /api/documents?limit=50&status=all
```

**Query Parameters:**
- `limit`: Number of documents (default: 50)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status ("draft", "pending_signature", "signed", "completed", "all")

**Example:**
```bash
curl "http://localhost:8000/api/documents?status=pending_signature" \
  -H "Authorization: ApiKey loi-service-key"
```

#### Create Document
```http
POST /api/documents
```

**Request Body:**
```json
{
  "title": "VP Racing Fuel Supply Agreement - LOI",
  "document_type": "loi",
  "customer_id": "12345",
  "contact_email": "john@doesfuel.com", 
  "content_html": "<html>...</html>",
  "expires_at": "2025-02-25T12:00:00Z",
  "metadata": {
    "fuel_volume": 50000,
    "contract_term": 36,
    "pricing_tier": "premium"
  }
}
```

#### Generate PDF
```http
GET /api/documents/{document_id}/pdf
```

**Example:**
```bash
curl "http://localhost:8000/api/documents/doc-123/pdf" \
  -H "Authorization: ApiKey loi-service-key" \
  --output document.pdf
```

### Digital Signatures

#### Create Signature Request
```http
POST /api/documents/{document_id}/signatures
```

**Request Body:**
```json
{
  "signer_name": "John Doe",
  "signer_email": "john@doesfuel.com",
  "expires_in_days": 7,
  "require_consent": true
}
```

**Response:**
```json
{
  "signature_request_id": "sig-789",
  "signature_url": "http://localhost:8000/signature/sig-789",
  "expires_at": "2025-02-01T12:00:00Z",
  "status": "pending"
}
```

#### Submit Signature
```http
POST /api/signatures/{signature_id}/sign
```

**Request Body:**
```json
{
  "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "consent_given": true,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

#### Signature Page (Browser)
```http
GET /signature/{signature_id}
```

This serves the HTML signature page for end users.

**Example:**
```
http://localhost:8000/signature/sig-789
```

---

## 🏥 Service Health & Monitoring

### Gateway Health Check
```http
GET /health
```

**Example:**
```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "service": "api-gateway",
  "status": "healthy",
  "timestamp": "2025-01-25T12:00:00Z",
  "version": "1.0.0"
}
```

### Comprehensive Service Status
```http
GET /status
```

**Example:**
```bash
curl "http://localhost:8000/status"
```

**Response:**
```json
{
  "gateway": {
    "status": "healthy",
    "port": 8000,
    "timestamp": "2025-01-25T12:00:00Z"
  },
  "services": {
    "crm_service": {
      "status": "healthy",
      "url": "http://localhost:8001", 
      "response_time": 45.2
    },
    "document_service": {
      "status": "healthy",
      "url": "http://localhost:8002",
      "response_time": 38.7
    }
  },
  "routing": {
    "crm_routes": ["/api/contacts/*", "/api/sync/*"],
    "document_routes": ["/api/documents/*", "/api/signatures/*"]
  }
}
```

---

## 🔄 Legacy API (Preserved)

All original endpoints continue to work exactly as before. Only the port number changes from 8080 to 8000.

## LOI Management

### Create LOI
**POST** `/api/create-loi`

Create a new Letter of Intent with deal terms and customer information.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/create-loi \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-ABC123",
    "signature_token": "550e8400-e29b-41d4-a716-446655440000",
    "signer_name": "John Smith",
    "signer_email": "john@smithgas.com",
    "company_name": "Smith Gas Station",
    "crm_contact_id": "12345",
    "document_name": "VP Racing Fuel Supply Agreement - Letter of Intent",
    "status": "pending",
    "created_at": "2025-01-30T10:00:00Z",
    "expires_at": "2025-02-29T10:00:00Z",
    "deal_terms": {
      "customer": {
        "id": "12345",
        "name": "John Smith",
        "email": "john@smithgas.com",
        "company": "Smith Gas Station",
        "phone": "314-555-1234",
        "address": "123 Main St, St. Louis, MO 63101"
      },
      "gasoline_volume": 50000,
      "diesel_volume": 20000,
      "image_funding": 75000,
      "volume_incentives": 50000,
      "contract_duration": 36,
      "conversion_date": "2025-08-01",
      "pricing_structure": "competitive",
      "special_terms": "24/7 emergency fuel supply included"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "LOI created successfully",
  "transaction_id": "TXN-ABC123",
  "signature_token": "550e8400-e29b-41d4-a716-446655440000",
  "signature_url": "https://loi-automation-api.onrender.com/sign/550e8400-e29b-41d4-a716-446655440000"
}
```

### Submit Signature
**POST** `/api/submit-signature`

Submit an electronic signature for an LOI.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/submit-signature \
  -H "Content-Type: application/json" \
  -d '{
    "signature_token": "550e8400-e29b-41d4-a716-446655440000",
    "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Signature workflow completed successfully",
  "verification_code": "VRF-123456",
  "completion_url": "https://loi-automation-api.onrender.com/signature-complete/VRF-123456"
}
```

---

## CRM Operations

### Search CRM Contacts
**POST** `/api/search-crm`

Search for contacts in the CRM database.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/search-crm \
  -H "Content-Type: application/json" \
  -d '{
    "query": "smith gas"
  }'
```

**Response:**
```json
{
  "success": true,
  "customers": [
    {
      "id": "12345",
      "name": "John Smith",
      "email": "john@smithgas.com",
      "company": "Smith Gas Station",
      "phone": "314-555-1234",
      "address": "123 Main St, St. Louis, MO 63101"
    }
  ],
  "total": 1,
  "source": "database_cache"
}
```

### Create CRM Contact
**POST** `/api/create-crm-contact`

Create a new contact in the CRM.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/create-crm-contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@doesfuel.com",
    "company": "Doe\'s Fuel Stop",
    "phone": "314-555-5678",
    "address": "456 Oak St, St. Louis, MO 63102"
  }'
```

**Response:**
```json
{
  "success": true,
  "contact_id": "LOCAL_20250130_120000_001",
  "message": "Contact created in local cache and queued for CRM sync"
}
```

### Update CRM Contact
**POST** `/api/update-crm-contact`

Update an existing CRM contact.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/update-crm-contact \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "12345",
    "name": "John Smith Jr.",
    "email": "john.jr@smithgas.com",
    "company_name": "Smith Gas Station LLC",
    "phone": "314-555-1234",
    "address": "123 Main St, Suite 100, St. Louis, MO 63101"
  }'
```

### Get All CRM Contacts
**POST** `/api/get-crm-contacts`

Retrieve all contacts from the CRM cache.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/get-crm-contacts
```

### Refresh CRM Cache
**POST** `/api/refresh-crm-cache`

Force a refresh of the local CRM cache from Less Annoying CRM.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/refresh-crm-cache
```

### Get Sync Status
**POST** `/api/sync-status`

Check the status of CRM synchronization.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/sync-status
```

---

## CRM Bridge API

The CRM Bridge API provides a unified interface for all Better Day Energy sales applications to access CRM data.

### Verify Authentication
**GET** `/api/v1/crm-bridge/auth/verify`

Verify your authentication token.

```bash
curl https://loi-automation-api.onrender.com/api/v1/crm-bridge/auth/verify \
  -H "Authorization: Bearer bde_loi_auth_e6db5173a4393421ffadae85f9a3513e"
```

**Response:**
```json
{
  "authenticated": true,
  "app_name": "loi_automation",
  "permissions": ["read", "write"]
}
```

### Get All Contacts
**GET** `/api/v1/crm-bridge/contacts`

Retrieve all contacts with optional pagination.

```bash
curl https://loi-automation-api.onrender.com/api/v1/crm-bridge/contacts?limit=50&offset=0 \
  -H "Authorization: Bearer bde_loi_auth_e6db5173a4393421ffadae85f9a3513e"
```

**Response:**
```json
{
  "success": true,
  "contacts": [
    {
      "id": "12345",
      "name": "John Smith",
      "email": "john@smithgas.com",
      "company": "Smith Gas Station",
      "phone": "314-555-1234",
      "address": "123 Main St, St. Louis, MO 63101"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Search Contacts
**POST** `/api/v1/crm-bridge/contacts/search`

Search contacts with fuzzy matching across all fields.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/v1/crm-bridge/contacts/search \
  -H "Authorization: Bearer bde_loi_auth_e6db5173a4393421ffadae85f9a3513e" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "smith",
    "limit": 10
  }'
```

### Create Contact
**POST** `/api/v1/crm-bridge/contacts/create`

Create a new contact through the bridge.

```bash
curl -X POST https://loi-automation-api.onrender.com/api/v1/crm-bridge/contacts/create \
  -H "Authorization: Bearer bde_loi_auth_e6db5173a4393421ffadae85f9a3513e" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob Johnson",
    "email": "bob@johnsonfuel.com",
    "company": "Johnson Fuel Center",
    "phone": "314-555-9999",
    "address": "789 Elm St, St. Louis, MO 63103",
    "notes": "Interested in VP Racing partnership"
  }'
```

### Get CRM Statistics
**GET** `/api/v1/crm-bridge/stats`

Get statistics about the CRM data.

```bash
curl https://loi-automation-api.onrender.com/api/v1/crm-bridge/stats \
  -H "Authorization: Bearer bde_loi_auth_e6db5173a4393421ffadae85f9a3513e"
```

**Response:**
```json
{
  "total_contacts": 2500,
  "contacts_with_email": 2350,
  "contacts_with_phone": 2400,
  "contacts_with_company": 2480,
  "last_sync": "2025-01-30T09:30:00Z",
  "cache_hit_rate": 0.95
}
```

---

## Document & Signature Endpoints

### View Signature Page
**GET** `/sign/{signature_token}`

Display the LOI document for electronic signature.

```bash
# Open in browser
https://loi-automation-api.onrender.com/sign/550e8400-e29b-41d4-a716-446655440000
```

### View Signed Document
**GET** `/signed-loi/{verification_code}`

View the completed signed LOI document.

```bash
# Open in browser
https://loi-automation-api.onrender.com/signed-loi/VRF-123456
```

### Get Signature Image
**GET** `/signature-image/{verification_code}`

Retrieve the signature image for a completed LOI.

```bash
curl https://loi-automation-api.onrender.com/signature-image/VRF-123456
```

### View Audit Report
**GET** `/audit-report/{verification_code}`

View the complete audit trail for a signed document.

```bash
# Open in browser
https://loi-automation-api.onrender.com/audit-report/VRF-123456
```

---

## Admin Endpoints

### Admin Dashboard
**GET** `/admin`

Access the admin dashboard (requires authentication).

```bash
# Open in browser with session cookie
https://loi-automation-api.onrender.com/admin
```

### Login Page
**GET** `/login`

Display the login page.

```bash
# Open in browser
https://loi-automation-api.onrender.com/login
```

### Logout
**GET** `/logout`

Logout and clear session.

```bash
curl https://loi-automation-api.onrender.com/logout
```

---

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message here",
  "details": "Additional error details if available"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing or invalid auth)
- `404` - Not Found
- `500` - Internal Server Error

---

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Default limit**: 100 requests per minute per IP
- **CRM Bridge**: 1000 requests per minute per token

---

## 💡 Usage Examples

### For Adam's Sales Application

#### Python Integration Example
```python
import requests
import json

class BDEAPIClient:
    def __init__(self, base_url="http://localhost:8000", api_key="loi-service-key"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json"
        }
    
    def search_customers(self, query, limit=10):
        """Search for customers with fuzzy matching"""
        response = requests.post(
            f"{self.base_url}/api/search_contacts",  # Legacy endpoint
            headers=self.headers,
            json={"query": query, "limit": limit}
        )
        
        if response.status_code == 200:
            return response.json()["results"]
        else:
            print(f"Search error: {response.json()}")
            return []
    
    def create_customer(self, customer_data):
        """Create a new customer"""
        response = requests.post(
            f"{self.base_url}/api/create_contact",  # Legacy endpoint
            headers=self.headers,
            json=customer_data
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Create error: {response.json()}")
            return None
    
    def get_all_customers(self, limit=50):
        """Get all customers with pagination"""
        response = requests.get(
            f"{self.base_url}/api/contacts?limit={limit}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()["contacts"]
        else:
            print(f"Get error: {response.json()}")
            return []

# Usage Example
client = BDEAPIClient()

# Search for fuel stations
results = client.search_customers("fuel station", limit=5)
for result in results:
    contact = result["contact"]
    print(f"Found: {contact['display_name']} (Score: {result['score']:.2f})")

# Create new customer
new_customer = {
    "first_name": "Mike",
    "last_name": "Johnson",
    "company_name": "Johnson's Quick Stop",
    "email": "mike@johnsonquickstop.com",
    "phone": "314-555-7777"
}

created = client.create_customer(new_customer)
if created:
    print(f"Created customer: {created['id']}")
```

### For Bolt.new Integration

#### JavaScript/Node.js Example
```javascript
// BDE API Client for Bolt.new projects
class BDEClient {
    constructor(baseUrl = 'http://localhost:8000', apiKey = 'loi-service-key') {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `ApiKey ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async searchContacts(query, options = {}) {
        const searchData = {
            query,
            limit: options.limit || 20,
            fuzzy_threshold: options.threshold || 0.6,
            include_score: true
        };
        
        const response = await fetch(`${this.baseUrl}/api/contacts/search`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(searchData)
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async createContact(contactData) {
        const response = await fetch(`${this.baseUrl}/api/contacts`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(contactData)
        });
        
        if (!response.ok) {
            throw new Error(`Create failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async getServiceStatus() {
        const response = await fetch(`${this.baseUrl}/status`);
        return await response.json();
    }
}

// Usage in a Bolt.new React component
import React, { useState, useEffect } from 'react';

function CustomerSearch() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    
    const bdeClient = new BDEClient();
    
    const handleSearch = async () => {
        if (!query.trim()) return;
        
        setLoading(true);
        try {
            const response = await bdeClient.searchContacts(query, { limit: 10 });
            setResults(response.results || []);
        } catch (error) {
            console.error('Search error:', error);
            setResults([]);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div className="customer-search">
            <div className="search-input">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search customers..."
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                <button onClick={handleSearch} disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </div>
            
            <div className="search-results">
                {results.map((result) => (
                    <div key={result.contact.id} className="customer-card">
                        <h3>{result.contact.display_name}</h3>
                        <p>Email: {result.contact.email}</p>
                        <p>Score: {(result.score * 100).toFixed(0)}%</p>
                        <p>Matched: {result.match_fields.join(', ')}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default CustomerSearch;
```

#### React Hook for BDE API
```javascript
// Custom hook for BDE API integration
import { useState, useEffect } from 'react';

function useBDEAPI(baseUrl = 'http://localhost:8000') {
    const [isConnected, setIsConnected] = useState(false);
    const [loading, setLoading] = useState(false);
    
    const apiKey = 'loi-service-key';
    const headers = {
        'Authorization': `ApiKey ${apiKey}`,
        'Content-Type': 'application/json'
    };
    
    // Check API connectivity
    useEffect(() => {
        const checkConnection = async () => {
            try {
                const response = await fetch(`${baseUrl}/health`);
                setIsConnected(response.ok);
            } catch (error) {
                setIsConnected(false);
            }
        };
        
        checkConnection();
        const interval = setInterval(checkConnection, 30000); // Check every 30s
        return () => clearInterval(interval);
    }, [baseUrl]);
    
    const searchContacts = async (query, options = {}) => {
        setLoading(true);
        try {
            const response = await fetch(`${baseUrl}/api/contacts/search`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    query,
                    limit: options.limit || 20,
                    fuzzy_threshold: options.threshold || 0.6
                })
            });
            
            if (!response.ok) throw new Error('Search failed');
            return await response.json();
        } finally {
            setLoading(false);
        }
    };
    
    const createContact = async (contactData) => {
        setLoading(true);
        try {
            const response = await fetch(`${baseUrl}/api/contacts`, {
                method: 'POST',
                headers,
                body: JSON.stringify(contactData)
            });
            
            if (!response.ok) throw new Error('Create failed');
            return await response.json();
        } finally {
            setLoading(false);
        }
    };
    
    return {
        isConnected,
        loading,
        searchContacts,
        createContact
    };
}

export default useBDEAPI;
```

### Quick Start for Adam

#### 1. Update Your Configuration
```python
# Old configuration
BASE_URL = "http://localhost:8080"

# New configuration (only change needed!)
BASE_URL = "http://localhost:8000"
API_KEY = "loi-service-key"

headers = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}
```

#### 2. Test Your Connection
```python
import requests

response = requests.get("http://localhost:8000/status")
if response.status_code == 200:
    status = response.json()
    print("✅ API Gateway is healthy")
    print(f"CRM Service: {status['services']['crm_service']['status']}")
    print(f"Document Service: {status['services']['document_service']['status']}")
else:
    print("❌ API Gateway not responding")
```

#### 3. Use Enhanced Search
```python
# Enhanced search with scoring
search_data = {
    "query": "gas station",
    "limit": 10,
    "fuzzy_threshold": 0.7,  # Higher threshold for better matches
    "include_score": True
}

response = requests.post(
    "http://localhost:8000/api/contacts/search",
    headers=headers,
    json=search_data
)

results = response.json()["results"]
for result in results:
    contact = result["contact"]
    score = result["score"]
    print(f"{contact['display_name']} (Score: {score:.2f})")
```

### Error Handling Best Practices

```python
def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with retry logic"""
    import time
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = func(*args, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # Service unavailable, retry
                print(f"Service unavailable, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                print(f"API error {response.status_code}: {response.json()}")
                return None
                
        except requests.exceptions.ConnectionError:
            print(f"Connection failed, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
            continue
    
    print("API call failed after all retries")
    return None

# Usage
result = safe_api_call(
    requests.post,
    "http://localhost:8000/api/contacts/search",
    headers=headers,
    json={"query": "fuel"}
)
```

---

## 🚀 Quick Migration Guide

### For Existing Code (Adam)
1. **Change port**: `8080` → `8000`
2. **Add API key**: `Authorization: ApiKey loi-service-key`
3. **All endpoints work the same**

### For New Projects (Bolt.new)
1. **Start here**: `http://localhost:8000/status`
2. **Search contacts**: `POST /api/contacts/search`
3. **Create contacts**: `POST /api/contacts`
4. **Monitor health**: `GET /status`

---

## 🛠️ Development Setup

### Start All Services
```bash
cd services
python3 start_services.py
```

### Check Service Status
```bash
curl http://localhost:8000/status
```

### View Logs
```bash
tail -f services/logs/*.log
```

### Stop Services
```bash
python3 services/stop_services.py
```

---

## Example Integration

### Python Example
```python
import requests

# Configuration
BASE_URL = "https://loi-automation-api.onrender.com"
AUTH_TOKEN = "bde_loi_auth_e6db5173a4393421ffadae85f9a3513e"

# Search for a customer
response = requests.post(
    f"{BASE_URL}/api/v1/crm-bridge/contacts/search",
    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    json={"query": "smith gas", "limit": 5}
)

if response.status_code == 200:
    customers = response.json()["contacts"]
    for customer in customers:
        print(f"{customer['name']} - {customer['company']}")
```

### JavaScript Example
```javascript
const BASE_URL = 'https://loi-automation-api.onrender.com';
const AUTH_TOKEN = 'bde_loi_auth_e6db5173a4393421ffadae85f9a3513e';

// Create a new LOI
async function createLOI(dealData) {
    const response = await fetch(`${BASE_URL}/api/create-loi`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dealData)
    });
    
    if (response.ok) {
        const result = await response.json();
        console.log('LOI created:', result.signature_url);
        return result;
    } else {
        throw new Error('Failed to create LOI');
    }
}
```

---

## 📞 Support & Resources

### API Support
- **Check service status**: `http://localhost:8000/status`
- **View service logs**: `services/logs/`
- **Restart services**: `python3 services/stop_services.py && python3 services/start_services.py`

### Development Resources
- **GitHub Repository**: https://github.com/mattmizell/bde-loi-automation-system
- **Service Architecture**: See `SERVICE_ARCHITECTURE.md` 
- **Modularization Guide**: See `MODULARIZATION_COMPLETE.md`

### Common Issues

#### Service Not Responding
```bash
# Check if services are running
curl http://localhost:8000/status

# Start services if needed
cd services && python3 start_services.py
```

#### Authentication Errors
```bash
# Verify API key format
curl -H "Authorization: ApiKey loi-service-key" http://localhost:8000/api/contacts
```

#### Database Connection Issues
```bash
# Run database migration
cd services && python3 database_migration.py
```

### Performance Tips
- Use pagination for large result sets (`limit` and `offset` parameters)
- Implement client-side caching for frequently accessed data
- Use fuzzy search thresholds (0.6-0.8) for optimal results
- Monitor `/status` endpoint for service health

---

## 🔄 Version History

### v2.0.0 (January 2025) - Modular Architecture
- ✅ Microservices architecture with API Gateway
- ✅ Enhanced CRM service with advanced search
- ✅ Document service with signature workflows
- ✅ Background LACRM synchronization
- ✅ Full backward compatibility
- ✅ Comprehensive health monitoring

### v1.0.0 (2024) - Monolithic System
- Basic LOI automation
- Simple CRM integration
- Document signature workflows

---

*Last updated: January 25, 2025*
*API Version: 2.0.0 (Modular Architecture)*