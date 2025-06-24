# Better Day Energy CRM Bridge API

**⚡ Cache-First CRM Service for All BDE Sales Tools**

Unified API that serves cached CRM data instantly while syncing with Less Annoying CRM in the background.

## 🚀 Quick Start

### Base URL
```
http://localhost:8005
https://your-deployment.onrender.com  # Production
```

### Authentication
All requests require a Bearer token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://localhost:8005/api/v1/contacts
```

### API Tokens
Contact Better Day Energy IT for your app-specific token:
- `bde_loi_auth_[hash]` - LOI Automation System
- `bde_bolt_auth_[hash]` - Bolt Sales Tool
- `bde_adam_auth_[hash]` - Adam's Sales App

## 📖 API Endpoints

### Authentication

#### Verify API Token
```http
POST /auth/verify
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "authenticated": true,
  "app_name": "bolt_sales_tool",
  "permissions": ["read_contacts", "create_contacts", "search_contacts"],
  "rate_limit": "1000 requests/hour"
}
```

### Contacts (Cache-First)

#### Get Contacts (Lightning Fast)
```http
GET /api/v1/contacts?limit=50
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "count": 50,
  "contacts": [
    {
      "contact_id": "4035468683725586617984784099511",
      "name": "John Smith",
      "company_name": "Smith's Gas Station",
      "email": "john@smithgas.com",
      "phone": "(555) 123-4567",
      "created_at": "2025-06-16T15:26:05-05:00",
      "cache_freshness": "fresh"
    }
  ],
  "source": "cache"
}
```

#### Search Contacts
```http
POST /api/v1/contacts/search
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "query": "gas station",
  "company_filter": "shell",
  "limit": 25
}
```

**Response:**
```json
{
  "success": true,
  "query": "gas station",
  "count": 12,
  "contacts": [...]
}
```

#### Create Contact (Immediate Response)
```http
POST /api/v1/contacts/create
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Mike Johnson",
  "email": "mike@newstation.com",
  "phone": "(555) 987-6543",
  "company_name": "Johnson's Quick Stop",
  "address": "123 Main St, City, State",
  "notes": "Interested in VP Racing fuel"
}
```

**Response:**
```json
{
  "success": true,
  "contact_id": "TEMP_20250624_143022_a1b2c3d4",
  "message": "Contact created immediately in cache, syncing to CRM in background",
  "status": "cache_created_sync_pending"
}
```

### System Monitoring

#### Get CRM Statistics
```http
GET /api/v1/stats
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "total_contacts": 2500,
  "contacts_with_companies": 2486,
  "company_coverage": 99.4,
  "last_updated": "2025-06-24T18:45:00Z"
}
```

#### Check Queue Status
```http
GET /api/v1/queue/status
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "queue_stats": {
    "pending": {"count": 3, "oldest": "2025-06-24T18:40:00Z"},
    "completed": {"count": 147, "newest": "2025-06-24T18:44:30Z"},
    "failed": {"count": 0}
  },
  "failed_operations": []
}
```

#### Get Cache Health
```http
GET /api/v1/cache/info
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "total_contacts": 2500,
  "freshness": {
    "fresh_last_hour": 2456,
    "fresh_last_24h": 2500,
    "pending_sync": 3
  },
  "last_full_sync": "2025-06-24T12:00:00Z",
  "cache_health": "excellent"
}
```

#### Trigger Manual Sync
```http
POST /api/v1/sync/trigger
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Background sync triggered",
  "tasks": ["write_queue_processing", "cache_refresh"]
}
```

## 🔧 Integration Examples

### JavaScript/Node.js Example
```javascript
class BDECRMClient {
  constructor(apiToken, baseUrl = 'http://localhost:8005') {
    this.apiToken = apiToken;
    this.baseUrl = baseUrl;
  }

  async getContacts(limit = 50) {
    const response = await fetch(`${this.baseUrl}/api/v1/contacts?limit=${limit}`, {
      headers: {
        'Authorization': `Bearer ${this.apiToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    return await response.json();
  }

  async searchContacts(query, companyFilter = null) {
    const response = await fetch(`${this.baseUrl}/api/v1/contacts/search`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        company_filter: companyFilter,
        limit: 50
      })
    });
    
    return await response.json();
  }

  async createContact(contactData) {
    const response = await fetch(`${this.baseUrl}/api/v1/contacts/create`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(contactData)
    });
    
    return await response.json();
  }
}

// Usage
const crm = new BDECRMClient('bde_bolt_auth_your_token_here');

// Lightning-fast contact retrieval
const contacts = await crm.getContacts(100);

// Search for gas stations
const gasStations = await crm.searchContacts('gas station');

// Create new contact (immediate response)
const newContact = await crm.createContact({
  name: 'Sarah Wilson',
  email: 'sarah@wilsongas.com',
  company_name: 'Wilson Gas & Go',
  phone: '(555) 444-3333'
});
```

### Python Example
```python
import requests

class BDECRMClient:
    def __init__(self, api_token, base_url='http://localhost:8005'):
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def get_contacts(self, limit=50):
        response = requests.get(
            f'{self.base_url}/api/v1/contacts',
            headers=self.headers,
            params={'limit': limit}
        )
        return response.json()
    
    def search_contacts(self, query, company_filter=None):
        data = {
            'query': query,
            'limit': 50
        }
        if company_filter:
            data['company_filter'] = company_filter
            
        response = requests.post(
            f'{self.base_url}/api/v1/contacts/search',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def create_contact(self, contact_data):
        response = requests.post(
            f'{self.base_url}/api/v1/contacts/create',
            headers=self.headers,
            json=contact_data
        )
        return response.json()

# Usage
crm = BDECRMClient('bde_adam_auth_your_token_here')

# Get contacts from cache (super fast)
contacts = crm.get_contacts(limit=100)

# Search by company
shell_stations = crm.search_contacts('', company_filter='shell')

# Create contact
new_contact = crm.create_contact({
    'name': 'Tom Davis',
    'email': 'tom@davisfuel.com',
    'company_name': 'Davis Fuel Center',
    'phone': '(555) 777-8888'
})
```

### cURL Examples
```bash
# Get contacts
curl -H "Authorization: Bearer bde_loi_auth_your_token" \
  "http://localhost:8005/api/v1/contacts?limit=10"

# Search contacts
curl -X POST \
  -H "Authorization: Bearer bde_bolt_auth_your_token" \
  -H "Content-Type: application/json" \
  -d '{"query": "shell", "limit": 25}' \
  "http://localhost:8005/api/v1/contacts/search"

# Create contact
curl -X POST \
  -H "Authorization: Bearer bde_adam_auth_your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lisa Brown",
    "email": "lisa@brownstation.com",
    "company_name": "Brown Station LLC",
    "phone": "(555) 333-2222"
  }' \
  "http://localhost:8005/api/v1/contacts/create"
```

## ⚡ Performance Benefits

### Cache-First Architecture
- **READS**: Sub-second response from PostgreSQL cache (2500+ contacts)
- **WRITES**: Immediate response, background sync to LACRM
- **SYNC**: Automatic background queue processing

### Response Times
- **Get Contacts**: ~50ms (from cache)
- **Search Contacts**: ~100ms (from cache with full-text search)
- **Create Contact**: ~200ms (immediate cache write)
- **LACRM Sync**: Background (no wait time)

### Data Freshness
- **Real-time**: New contacts available immediately after creation
- **Synced**: Background process syncs with LACRM every few minutes
- **Fresh**: Cache refreshed from LACRM daily
- **Reliable**: Write queue with retry logic ensures no data loss

## 🔒 Security

### Authentication
- Token-based authentication per application
- Each app gets its own secure token
- Tokens are app-specific and logged for audit

### Audit Trail
- All API requests logged with app name and timestamp
- Complete audit trail in `crm_bridge_audit_log`
- Failed operations tracked and monitored

## 🚦 Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad request (invalid data)
- `401` - Unauthorized (invalid token)
- `500` - Server error (database/API issues)

### Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 401
}
```

## 📊 Monitoring & Health

### Health Check
```http
GET /health
```

Monitors:
- Database connectivity
- LACRM API connectivity
- Service status

### Interactive API Documentation
Available at: `http://localhost:8005/docs`

## 🔄 Background Processes

### Write Queue Processing
- Processes pending LACRM syncs every few minutes
- Retry logic for failed operations
- Detailed error logging

### Cache Refresh
- Full cache refresh from LACRM daily
- Incremental updates for new/modified contacts
- Health monitoring and alerts

## 📞 Support

For API tokens, technical support, or integration help:
- Contact: Better Day Energy IT Team
- Repository: BDE LOI Automation System
- Documentation: This file + `/docs` endpoint

---

## ✨ Perfect for Adam's Sales Tools

This API is designed specifically to solve the challenges you and Adam are facing:

1. **⚡ Lightning Fast**: No more waiting for LACRM API calls
2. **🔐 Simple Auth**: One token per app, no complex OAuth
3. **🚀 Immediate Response**: Contacts available instantly after creation
4. **🔄 Always Synced**: Background processes keep everything in sync
5. **📊 Transparent**: Monitor queue status and cache health
6. **🛠️ Developer Friendly**: Simple REST API with complete examples

**Perfect for Bolt.net integration and any future sales tools!**