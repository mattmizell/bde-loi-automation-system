# Better Day Energy LOI Automation System API Documentation

## Base URL
Production: `https://loi-automation-api.onrender.com`

## Table of Contents
1. [Authentication](#authentication)
2. [LOI Management](#loi-management)
3. [CRM Operations](#crm-operations)
4. [CRM Bridge API](#crm-bridge-api)
5. [Document & Signature Endpoints](#document--signature-endpoints)
6. [Admin Endpoints](#admin-endpoints)

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

## Support

For API support or to report issues:
- Email: support@betterdayenergy.com
- GitHub: https://github.com/mattmizell/bde-loi-automation-system

---

*Last updated: January 30, 2025*