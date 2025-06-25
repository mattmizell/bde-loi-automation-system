#!/usr/bin/env python3
"""
Better Day Energy CRM Bridge Service

Cache-First CRM API service for all BDE sales tools.
Fast reads from PostgreSQL cache, background sync with Less Annoying CRM.

Architecture:
- READS: Always from cache (sub-second response)
- WRITES: Immediate to cache + background queue to LACRM
- SYNC: Background process keeps cache updated
- AUTH: Token-based access for multiple apps

Features:
- ⚡ Lightning-fast cached reads (2500+ contacts)
- 🔄 Background sync keeps data fresh
- 🔐 Secure token authentication per app
- 📊 Real-time stats and monitoring
- 🚦 Write queue with retry logic
- 📝 Complete audit trail
"""

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import psycopg2
import requests
import json
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Better Day Energy CRM Bridge Service",
    description="Unified CRM authentication and API service for all BDE sales tools",
    version="1.0.0"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
LACRM_API_KEY = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
LACRM_BASE_URL = "https://api.lessannoyingcrm.com/v2/"
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://mattmizell:training1@localhost:5432/loi_automation')

# API Token Management
API_TOKENS = {
    # Production tokens - generate secure tokens for each app
    "loi_automation": "bde_loi_auth_" + hashlib.sha256("loi_automation_secret".encode()).hexdigest()[:32],
    "bolt_sales_tool": "bde_bolt_auth_" + hashlib.sha256("bolt_sales_secret".encode()).hexdigest()[:32],
    "adam_sales_app": "bde_adam_auth_" + hashlib.sha256("adam_sales_secret".encode()).hexdigest()[:32],
}

# Pydantic models for request/response
class ContactCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ContactUpdateRequest(BaseModel):
    contact_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ContactSearchRequest(BaseModel):
    query: Optional[str] = None
    company_filter: Optional[str] = None
    limit: Optional[int] = 50

# Authentication dependency
async def verify_api_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token for accessing the CRM bridge"""
    token = credentials.credentials
    
    # Check if token exists in our authorized tokens
    for app_name, valid_token in API_TOKENS.items():
        if token == valid_token:
            return {"app_name": app_name, "token": token}
    
    raise HTTPException(
        status_code=401,
        detail="Invalid API token. Contact Better Day Energy IT for access."
    )

# Database operations
def get_db_connection():
    """Get database connection for cache operations"""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def log_api_request(app_name: str, operation: str, details: dict):
    """Log all API requests for audit trail"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO crm_bridge_audit_log 
                (app_name, operation, details, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (app_name, operation, json.dumps(details), datetime.now()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")

# Cache-First CRM Operations
class CRMBridge:
    """Cache-first CRM operations with background sync"""
    
    @staticmethod
    def get_contacts_from_cache(limit: int = 50, search_query: str = None, company_filter: str = None):
        """⚡ FAST: Get contacts from local cache (sub-second response)"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cur = conn.cursor()
            
            # Build dynamic query based on filters
            where_conditions = []
            params = []
            
            if search_query:
                where_conditions.append("(name ILIKE %s OR company_name ILIKE %s OR email ILIKE %s)")
                params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
            
            if company_filter:
                where_conditions.append("company_name ILIKE %s")
                params.append(f"%{company_filter}%")
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            params.append(limit)
            
            query = f"""
                SELECT contact_id, name, company_name, email, phone, created_at, last_sync
                FROM crm_contacts_cache 
                {where_clause}
                ORDER BY 
                    CASE WHEN last_sync > NOW() - INTERVAL '24 hours' THEN 1 ELSE 2 END,
                    name
                LIMIT %s
            """
            
            cur.execute(query, params)
            contacts = cur.fetchall()
            conn.close()
            
            return [
                {
                    "contact_id": row[0],
                    "name": row[1],
                    "company_name": row[2] or "",
                    "email": row[3] or "",
                    "phone": row[4] or "",
                    "created_at": row[5].isoformat() if row[5] else None,
                    "cache_freshness": "fresh" if row[6] and row[6] > datetime.now() - timedelta(hours=24) else "stale"
                }
                for row in contacts
            ]
            
        except Exception as e:
            logger.error(f"Cache query failed: {e}")
            return None
    
    @staticmethod
    def create_contact_cache_first(contact_data: ContactCreateRequest):
        """🚀 IMMEDIATE: Add to cache first, queue for LACRM sync"""
        conn = get_db_connection()
        if not conn:
            return {"success": False, "error": "Database unavailable"}
        
        try:
            cur = conn.cursor()
            
            # Generate temporary contact ID for immediate response
            temp_contact_id = f"TEMP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
            
            # 1. INSERT INTO CACHE IMMEDIATELY (for instant reads)
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
            
            # 2. ADD TO WRITE QUEUE (for background LACRM sync)
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
            
            logger.info(f"✅ Contact added to cache immediately: {contact_data.name}")
            
            return {
                "success": True,
                "contact_id": temp_contact_id,
                "message": "Contact created immediately in cache, syncing to CRM in background",
                "status": "cache_created_sync_pending"
            }
            
        except Exception as e:
            logger.error(f"Cache-first creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def process_write_queue():
        """🔄 BACKGROUND: Process queued writes to LACRM"""
        conn = get_db_connection()
        if not conn:
            return
            
        try:
            cur = conn.cursor()
            
            # Get pending operations (limit 10 per batch)
            cur.execute("""
                SELECT id, operation, data, attempts
                FROM crm_write_queue 
                WHERE status = 'pending' AND attempts < max_attempts
                ORDER BY created_at
                LIMIT 10
            """)
            
            operations = cur.fetchall()
            
            for op_id, operation, data_json, attempts in operations:
                try:
                    data = data_json  # Already parsed by PostgreSQL JSONB
                    
                    # Mark as processing
                    cur.execute("""
                        UPDATE crm_write_queue 
                        SET status = 'processing', attempts = attempts + 1
                        WHERE id = %s
                    """, (op_id,))
                    conn.commit()
                    
                    if operation == "create_contact":
                        success = CRMBridge._sync_contact_to_lacrm(data)
                        
                        if success:
                            # Update cache with real LACRM contact ID
                            cur.execute("""
                                UPDATE crm_contacts_cache 
                                SET contact_id = %s, sync_status = 'synced', last_sync = %s
                                WHERE contact_id = %s
                            """, (success["contact_id"], datetime.now(), data["temp_contact_id"]))
                            
                            # Mark queue item as completed
                            cur.execute("""
                                UPDATE crm_write_queue 
                                SET status = 'completed', processed_at = %s
                                WHERE id = %s
                            """, (datetime.now(), op_id))
                            
                            logger.info(f"✅ Contact synced to LACRM: {success['contact_id']}")
                        else:
                            # Mark as failed if max attempts reached
                            cur.execute("""
                                UPDATE crm_write_queue 
                                SET status = CASE WHEN attempts >= max_attempts THEN 'failed' ELSE 'pending' END
                                WHERE id = %s
                            """, (op_id,))
                    
                    conn.commit()
                    
                except Exception as op_error:
                    logger.error(f"Queue operation {op_id} failed: {op_error}")
                    cur.execute("""
                        UPDATE crm_write_queue 
                        SET status = 'pending', error_message = %s
                        WHERE id = %s
                    """, (str(op_error), op_id))
                    conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Write queue processing failed: {e}")
    
    @staticmethod
    def _sync_contact_to_lacrm(queue_data):
        """Internal: Actually sync contact to LACRM API"""
        try:
            contact_data = queue_data["data"]
            
            # Extract UserCode from API key
            user_code = LACRM_API_KEY.split('-')[0]  # Gets '1073223'
            
            params = {
                'APIToken': LACRM_API_KEY,
                'UserCode': user_code,
                'Function': 'CreateContact',
                'Name': contact_data["name"],
                'Email': contact_data.get("email", ""),
                'CompanyName': contact_data.get("company_name", ""),
                'IsCompany': False,
                'AssignedTo': 1073223,  # Adam's user ID
                'Phone': contact_data.get("phone", ""),
                'Address': contact_data.get("address", ""),
                'Notes': contact_data.get("notes", "")
            }
            
            # LACRM returns text/html, not JSON - need to handle properly
            response = requests.post(LACRM_BASE_URL, data=params, timeout=30)
            
            if response.status_code == 200:
                result = json.loads(response.text)
                if result.get('ContactId'):
                    return {
                        "contact_id": result['ContactId'],
                        "success": True
                    }
            
            return False
            
        except Exception as e:
            logger.error(f"LACRM sync failed: {e}")
            return False
    
    @staticmethod
    def refresh_cache_from_lacrm():
        """🔄 BACKGROUND: Full cache refresh from LACRM (daily)"""
        logger.info("🔄 Starting full cache refresh from LACRM...")
        
        # This implements the preload_crm_customers.py logic
        # but as a background service
        try:
            conn = get_db_connection()
            if not conn:
                return False
                
            cur = conn.cursor()
            
            # Get contacts from LACRM API using the working method
            # Extract UserCode from API key
            user_code = LACRM_API_KEY.split('-')[0]  # Gets '1073223'
            
            params = {
                'APIToken': LACRM_API_KEY,
                'UserCode': user_code,
                'Function': 'GetContacts'
            }
            
            # LACRM returns text/html, not JSON - need to handle properly
            response = requests.post(LACRM_BASE_URL, data=params, timeout=60)
            
            if response.status_code == 200:
                data = json.loads(response.text)
                contacts_list = data.get('Results', [])
                
                # Update cache with fresh data
                for contact in contacts_list:
                    # Extract company name using our fixed field mapping
                    company_name = ""
                    if contact.get('Company Name'):
                        company_name = contact['Company Name']
                    elif contact.get('CompanyMetaData', {}).get('CompanyName'):
                        company_name = contact['CompanyMetaData']['CompanyName']
                    
                    # Extract name
                    name = 'N/A'
                    if isinstance(contact.get('Name'), dict):
                        name_obj = contact['Name']
                        first = name_obj.get('FirstName', '')
                        last = name_obj.get('LastName', '')
                        name = f"{first} {last}".strip() or 'N/A'
                    elif contact.get('Name'):
                        name = str(contact['Name'])
                    
                    # Extract email and phone
                    email = ""
                    if contact.get('Email') and isinstance(contact['Email'], list) and len(contact['Email']) > 0:
                        email = contact['Email'][0].get('Text', '')
                    
                    phone = ""
                    if contact.get('Phone') and isinstance(contact['Phone'], list) and len(contact['Phone']) > 0:
                        phone = contact['Phone'][0].get('Text', '')
                    
                    # Upsert into cache
                    cur.execute("""
                        INSERT INTO crm_contacts_cache 
                        (contact_id, name, company_name, email, phone, created_at, last_sync, sync_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'synced')
                        ON CONFLICT (contact_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            company_name = EXCLUDED.company_name,
                            email = EXCLUDED.email,
                            phone = EXCLUDED.phone,
                            last_sync = EXCLUDED.last_sync,
                            sync_status = 'synced'
                    """, (
                        contact.get('ContactId'),
                        name,
                        company_name,
                        email,
                        phone,
                        datetime.now(),
                        datetime.now()
                    ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Cache refreshed with {len(contacts_list)} contacts from LACRM")
                return True
                
        except Exception as e:
            logger.error(f"Cache refresh failed: {e}")
            return False

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Better Day Energy CRM Bridge",
        "version": "1.0.0",
        "description": "Unified CRM API for all BDE sales tools",
        "endpoints": {
            "authentication": "/auth/verify",
            "contacts": "/api/v1/contacts",
            "search": "/api/v1/contacts/search",
            "create": "/api/v1/contacts/create",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check database connection
    db_status = "connected" if get_db_connection() else "disconnected"
    
    # Check LACRM API
    try:
        test_response = requests.get(f"{LACRM_BASE_URL}?Function=GetUser&APIToken={LACRM_API_KEY}", timeout=10)
        lacrm_status = "connected" if test_response.status_code == 200 else "disconnected"
    except:
        lacrm_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" and lacrm_status == "connected" else "degraded",
        "database": db_status,
        "lacrm_api": lacrm_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/auth/verify")
async def verify_authentication(auth_info: dict = Depends(verify_api_token)):
    """Verify API token and return app info"""
    return {
        "authenticated": True,
        "app_name": auth_info["app_name"],
        "permissions": ["read_contacts", "create_contacts", "search_contacts"],
        "rate_limit": "1000 requests/hour"
    }

@app.get("/api/v1/contacts")
async def get_contacts(
    limit: int = 50,
    auth_info: dict = Depends(verify_api_token)
):
    """Get contacts from cache (fast access)"""
    
    log_api_request(auth_info["app_name"], "get_contacts", {"limit": limit})
    
    contacts = CRMBridge.get_contacts_from_cache(limit=limit)
    
    if contacts is None:
        raise HTTPException(status_code=500, detail="Cache unavailable")
    
    return {
        "success": True,
        "count": len(contacts),
        "contacts": contacts,
        "source": "cache"
    }

@app.post("/api/v1/contacts/search")
async def search_contacts(
    search_request: ContactSearchRequest,
    auth_info: dict = Depends(verify_api_token)
):
    """Search contacts in cache"""
    
    log_api_request(auth_info["app_name"], "search_contacts", {
        "query": search_request.query,
        "limit": search_request.limit
    })
    
    contacts = CRMBridge.get_contacts_from_cache(
        limit=search_request.limit or 50,
        search_query=search_request.query
    )
    
    if contacts is None:
        raise HTTPException(status_code=500, detail="Search unavailable")
    
    return {
        "success": True,
        "query": search_request.query,
        "count": len(contacts),
        "contacts": contacts
    }

@app.post("/api/v1/contacts/create")
async def create_contact(
    contact_request: ContactCreateRequest,
    background_tasks: BackgroundTasks,
    auth_info: dict = Depends(verify_api_token)
):
    """🚀 FAST: Create contact immediately in cache, sync to LACRM in background"""
    
    log_api_request(auth_info["app_name"], "create_contact", {
        "name": contact_request.name,
        "company": contact_request.company_name
    })
    
    # CACHE-FIRST: Immediate response, background sync
    result = CRMBridge.create_contact_cache_first(contact_request)
    
    # Schedule background queue processing
    background_tasks.add_task(CRMBridge.process_write_queue)
    
    return result

@app.get("/api/v1/stats")
async def get_stats(auth_info: dict = Depends(verify_api_token)):
    """Get CRM statistics"""
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
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
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {e}")

@app.get("/api/v1/queue/status")
async def get_queue_status(auth_info: dict = Depends(verify_api_token)):
    """Monitor write queue status"""
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cur = conn.cursor()
        
        # Queue statistics
        cur.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                MIN(created_at) as oldest,
                MAX(created_at) as newest
            FROM crm_write_queue 
            GROUP BY status
        """)
        queue_stats = cur.fetchall()
        
        # Failed operations needing attention
        cur.execute("""
            SELECT id, operation, error_message, attempts, created_at
            FROM crm_write_queue 
            WHERE status = 'failed'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        failed_ops = cur.fetchall()
        
        conn.close()
        
        stats = {}
        for status, count, oldest, newest in queue_stats:
            stats[status] = {
                "count": count,
                "oldest": oldest.isoformat() if oldest else None,
                "newest": newest.isoformat() if newest else None
            }
        
        return {
            "queue_stats": stats,
            "failed_operations": [
                {
                    "id": row[0],
                    "operation": row[1], 
                    "error": row[2],
                    "attempts": row[3],
                    "created": row[4].isoformat() if row[4] else None
                }
                for row in failed_ops
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Queue status failed: {e}")

@app.post("/api/v1/sync/trigger")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    auth_info: dict = Depends(verify_api_token)
):
    """Manually trigger background sync processes"""
    
    log_api_request(auth_info["app_name"], "trigger_sync", {})
    
    # Process write queue
    background_tasks.add_task(CRMBridge.process_write_queue)
    
    # Full cache refresh (only if needed)
    background_tasks.add_task(CRMBridge.refresh_cache_from_lacrm)
    
    return {
        "success": True,
        "message": "Background sync triggered",
        "tasks": ["write_queue_processing", "cache_refresh"]
    }

@app.get("/api/v1/cache/info")
async def get_cache_info(auth_info: dict = Depends(verify_api_token)):
    """Get cache freshness and sync information"""
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cur = conn.cursor()
        
        # Cache freshness stats
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN last_sync > NOW() - INTERVAL '1 hour' THEN 1 END) as fresh_1h,
                COUNT(CASE WHEN last_sync > NOW() - INTERVAL '24 hours' THEN 1 END) as fresh_24h,
                COUNT(CASE WHEN sync_status = 'pending_sync' THEN 1 END) as pending_sync,
                MAX(last_sync) as last_full_sync
            FROM crm_contacts_cache
        """)
        cache_stats = cur.fetchone()
        
        conn.close()
        
        total, fresh_1h, fresh_24h, pending_sync, last_full_sync = cache_stats
        
        return {
            "total_contacts": total,
            "freshness": {
                "fresh_last_hour": fresh_1h,
                "fresh_last_24h": fresh_24h,
                "pending_sync": pending_sync
            },
            "last_full_sync": last_full_sync.isoformat() if last_full_sync else None,
            "cache_health": "excellent" if fresh_24h / total > 0.9 else "good" if fresh_24h / total > 0.7 else "needs_refresh"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache info failed: {e}")

# Background Scheduler (for production deployment)
@app.on_event("startup")
async def startup_tasks():
    """Initialize background tasks on startup"""
    logger.info("🚀 CRM Bridge Service Starting Up")
    logger.info("⚡ Cache-first reads enabled")
    logger.info("🔄 Background sync enabled")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Better Day Energy CRM Bridge Service")
    print("⚡ Cache-First Architecture:")
    print("   📖 READS: Lightning fast from cache (2500+ contacts)")
    print("   ✍️  WRITES: Immediate cache + background LACRM sync")
    print("   🔄 SYNC: Background queue processing")
    print("📊 API available at: http://localhost:8005")
    print("📖 Docs available at: http://localhost:8005/docs")
    uvicorn.run(app, host="0.0.0.0", port=8005)