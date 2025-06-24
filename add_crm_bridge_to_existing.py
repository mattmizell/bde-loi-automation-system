#!/usr/bin/env python3
"""
Integration script to add CRM Bridge endpoints to existing Render service

This adds the CRM bridge functionality to the existing integrated_pdf_signature_server.py
that's already running on https://loi-automation-api.onrender.com
"""

# Add these imports to the existing integrated_pdf_signature_server.py
ADDITIONAL_IMPORTS = '''
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import secrets
'''

# Add these models after existing imports
PYDANTIC_MODELS = '''
# CRM Bridge Models
class ContactCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ContactSearchRequest(BaseModel):
    query: Optional[str] = None
    company_filter: Optional[str] = None
    limit: Optional[int] = 50
'''

# Add these constants after existing configuration
API_TOKENS = '''
# CRM Bridge API Tokens
CRM_BRIDGE_TOKENS = {
    "loi_automation": "bde_loi_auth_" + hashlib.sha256("loi_automation_secret".encode()).hexdigest()[:32],
    "bolt_sales_tool": "bde_bolt_auth_" + hashlib.sha256("bolt_sales_secret".encode()).hexdigest()[:32],
    "adam_sales_app": "bde_adam_auth_" + hashlib.sha256("adam_sales_secret".encode()).hexdigest()[:32],
}

# Security
security = HTTPBearer()
'''

# Add these functions before the existing route handlers
CRM_BRIDGE_FUNCTIONS = '''
# CRM Bridge Authentication
async def verify_crm_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify CRM bridge API token"""
    token = credentials.credentials
    
    for app_name, valid_token in CRM_BRIDGE_TOKENS.items():
        if token == valid_token:
            return {"app_name": app_name, "token": token}
    
    raise HTTPException(
        status_code=401,
        detail="Invalid CRM bridge API token"
    )

def get_contacts_from_cache_fast(limit: int = 50, search_query: str = None):
    """Get contacts from production cache (fast)"""
    try:
        conn = get_database_connection()  # Use existing database function
        if not conn:
            return None
            
        cur = conn.cursor()
        
        if search_query:
            cur.execute("""
                SELECT contact_id, name, company_name, email, phone, created_at
                FROM crm_contacts_cache 
                WHERE name ILIKE %s OR company_name ILIKE %s OR email ILIKE %s
                ORDER BY name
                LIMIT %s
            """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", limit))
        else:
            cur.execute("""
                SELECT contact_id, name, company_name, email, phone, created_at
                FROM crm_contacts_cache 
                ORDER BY name
                LIMIT %s
            """, (limit,))
        
        contacts = cur.fetchall()
        conn.close()
        
        return [
            {
                "contact_id": row[0],
                "name": row[1],
                "company_name": row[2] or "",
                "email": row[3] or "",
                "phone": row[4] or "",
                "created_at": row[5].isoformat() if row[5] else None
            }
            for row in contacts
        ]
        
    except Exception as e:
        logger.error(f"Cache query failed: {e}")
        return None

def create_contact_cache_first_fast(contact_data: ContactCreateRequest):
    """Create contact in cache immediately, queue for LACRM sync"""
    try:
        conn = get_database_connection()
        if not conn:
            return {"success": False, "error": "Database unavailable"}
        
        cur = conn.cursor()
        
        # Generate temporary contact ID
        temp_contact_id = f"TEMP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        # Insert into cache immediately
        cur.execute("""
            INSERT INTO crm_contacts_cache 
            (contact_id, name, company_name, email, phone, created_at, sync_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending_sync')
        """, (
            temp_contact_id,
            contact_data.name,
            contact_data.company_name or "",
            contact_data.email or "",
            contact_data.phone or "",
            datetime.now()
        ))
        
        # Add to existing CRM write queue
        queue_data = {
            "temp_contact_id": temp_contact_id,
            "operation": "create_contact",
            "data": contact_data.dict(),
            "app_source": "crm_bridge"
        }
        
        cur.execute("""
            INSERT INTO crm_write_queue 
            (operation, data, status, created_at, max_attempts)
            VALUES (%s, %s, 'pending', %s, %s)
        """, (
            "create_contact",
            json.dumps(queue_data),
            datetime.now(),
            5
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "contact_id": temp_contact_id,
            "message": "Contact created immediately in cache, syncing to CRM in background",
            "status": "cache_created_sync_pending"
        }
        
    except Exception as e:
        logger.error(f"Cache-first creation failed: {e}")
        return {"success": False, "error": str(e)}
'''

# Add these new routes to the existing FastAPI app
NEW_ROUTES = '''
# CRM Bridge API Routes

@app.get("/api/v1/crm-bridge/contacts")
async def crm_bridge_get_contacts(
    limit: int = 50,
    auth_info: dict = Depends(verify_crm_token)
):
    """⚡ Get contacts from cache (lightning fast)"""
    
    contacts = get_contacts_from_cache_fast(limit=limit)
    
    if contacts is None:
        raise HTTPException(status_code=500, detail="Cache unavailable")
    
    return {
        "success": True,
        "count": len(contacts),
        "contacts": contacts,
        "source": "cache",
        "app": auth_info["app_name"]
    }

@app.post("/api/v1/crm-bridge/contacts/search")
async def crm_bridge_search_contacts(
    search_request: ContactSearchRequest,
    auth_info: dict = Depends(verify_crm_token)
):
    """⚡ Search contacts in cache"""
    
    contacts = get_contacts_from_cache_fast(
        limit=search_request.limit or 50,
        search_query=search_request.query
    )
    
    if contacts is None:
        raise HTTPException(status_code=500, detail="Search unavailable")
    
    return {
        "success": True,
        "query": search_request.query,
        "count": len(contacts),
        "contacts": contacts,
        "app": auth_info["app_name"]
    }

@app.post("/api/v1/crm-bridge/contacts/create")
async def crm_bridge_create_contact(
    contact_request: ContactCreateRequest,
    auth_info: dict = Depends(verify_crm_token)
):
    """🚀 Create contact immediately in cache, sync to CRM in background"""
    
    result = create_contact_cache_first_fast(contact_request)
    
    return result

@app.get("/api/v1/crm-bridge/stats")
async def crm_bridge_stats(auth_info: dict = Depends(verify_crm_token)):
    """Get CRM cache statistics"""
    
    try:
        conn = get_database_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        cur = conn.cursor()
        
        # Total contacts
        cur.execute("SELECT COUNT(*) FROM crm_contacts_cache")
        total_contacts = cur.fetchone()[0]
        
        # Contacts with companies
        cur.execute("""
            SELECT COUNT(*) FROM crm_contacts_cache 
            WHERE company_name IS NOT NULL AND company_name != '' AND company_name != 'N/A'
        """)
        contacts_with_companies = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "total_contacts": total_contacts,
            "contacts_with_companies": contacts_with_companies,
            "company_coverage": round(contacts_with_companies / total_contacts * 100, 1) if total_contacts > 0 else 0,
            "last_updated": datetime.now().isoformat(),
            "app": auth_info["app_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {e}")

@app.post("/api/v1/crm-bridge/auth/verify")
async def crm_bridge_verify_auth(auth_info: dict = Depends(verify_crm_token)):
    """Verify CRM bridge authentication"""
    return {
        "authenticated": True,
        "app_name": auth_info["app_name"],
        "permissions": ["read_contacts", "create_contacts", "search_contacts"],
        "service": "CRM Bridge on LOI Automation API"
    }
'''

print("🔧 Integration Instructions for Render Deployment")
print("=" * 60)
print()
print("To add CRM Bridge to your existing Render service:")
print()
print("1. Add the following to integrated_pdf_signature_server.py:")
print()
print("   # Add to imports section:")
print(ADDITIONAL_IMPORTS)
print()
print("   # Add models after existing models:")
print(PYDANTIC_MODELS)
print()
print("   # Add tokens after existing configuration:")
print(API_TOKENS)
print()
print("   # Add functions before route handlers:")
print(CRM_BRIDGE_FUNCTIONS)
print()
print("   # Add routes at the end of the file:")
print(NEW_ROUTES)
print()
print("2. Deploy to Render (automatic via GitHub)")
print()
print("3. Access CRM bridge at:")
print("   https://loi-automation-api.onrender.com/api/v1/crm-bridge/")
print()
print("4. API Tokens:")
for app, token in [
    ("loi_automation", "bde_loi_auth_" + "abc123..."),
    ("bolt_sales_tool", "bde_bolt_auth_" + "def456..."),
    ("adam_sales_app", "bde_adam_auth_" + "ghi789...")
]:
    print(f"   {app}: {token}")
print()
print("✅ This leverages your existing 2,500+ contact cache!")
print("⚡ All reads will be lightning fast from the cache")
print("🔄 Writes use your existing background sync queue")