"""
Contact Repository
Data access layer for contact operations
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
import json
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.models.contact import Contact
from services.crm_service.config.settings import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class ContactRepository:
    """Data access layer for contacts"""
    
    def __init__(self):
        self.connection_string = DATABASE_CONFIG['url']
        self._ensure_tables()
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def _ensure_tables(self):
        """Ensure contact tables exist"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Create contacts cache table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crm_contacts_cache (
                    contact_id VARCHAR(50) PRIMARY KEY,
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    company_name VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    address JSONB,
                    custom_fields JSONB,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE,
                    last_synced TIMESTAMP WITH TIME ZONE,
                    source VARCHAR(50) DEFAULT 'lacrm'
                )
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_email ON crm_contacts_cache(email)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_company ON crm_contacts_cache(company_name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_name ON crm_contacts_cache(first_name, last_name)")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error ensuring tables: {e}")
    
    def get_contacts(self, limit: int = 50, offset: int = 0) -> List[Contact]:
        """Get contacts with pagination"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM crm_contacts_cache 
                ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            return [self._row_to_contact(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    def count_contacts(self) -> int:
        """Count total contacts"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM crm_contacts_cache")
            count = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting contacts: {e}")
            return 0
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Contact]:
        """Get contact by ID"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM crm_contacts_cache 
                WHERE contact_id = %s
            """, (contact_id,))
            
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            return self._row_to_contact(row) if row else None
            
        except Exception as e:
            logger.error(f"Error getting contact by ID {contact_id}: {e}")
            return None
    
    def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Get contact by email"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM crm_contacts_cache 
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1
            """, (email,))
            
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            return self._row_to_contact(row) if row else None
            
        except Exception as e:
            logger.error(f"Error getting contact by email {email}: {e}")
            return None
    
    def create_contact(self, contact: Contact) -> Optional[Contact]:
        """Create new contact"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO crm_contacts_cache (
                    contact_id, first_name, last_name, company_name, email, phone,
                    address, custom_fields, created_at, updated_at, last_synced, source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                contact.id, contact.first_name, contact.last_name, contact.company_name,
                contact.email, contact.phone, json.dumps(contact.address or {}),
                json.dumps(contact.custom_fields or {}), contact.created_at,
                contact.updated_at, contact.last_synced, contact.source
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return contact
            
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None
    
    def update_contact(self, contact: Contact) -> Optional[Contact]:
        """Update existing contact"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE crm_contacts_cache SET
                    first_name = %s, last_name = %s, company_name = %s, email = %s,
                    phone = %s, address = %s, custom_fields = %s, updated_at = %s,
                    last_synced = %s, source = %s
                WHERE contact_id = %s
            """, (
                contact.first_name, contact.last_name, contact.company_name, contact.email,
                contact.phone, json.dumps(contact.address or {}),
                json.dumps(contact.custom_fields or {}), contact.updated_at,
                contact.last_synced, contact.source, contact.id
            ))
            
            if cur.rowcount == 0:
                cur.close()
                conn.close()
                return None
            
            conn.commit()
            cur.close()
            conn.close()
            
            return contact
            
        except Exception as e:
            logger.error(f"Error updating contact {contact.id}: {e}")
            return None
    
    def delete_contact(self, contact_id: str) -> bool:
        """Delete contact"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("DELETE FROM crm_contacts_cache WHERE contact_id = %s", (contact_id,))
            
            success = cur.rowcount > 0
            conn.commit()
            cur.close()
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting contact {contact_id}: {e}")
            return False
    
    def search_contacts(self, query: str, limit: int = 20) -> List[Contact]:
        """Search contacts by query"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Use PostgreSQL full-text search for better performance
            search_query = f"%{query.lower()}%"
            
            cur.execute("""
                SELECT * FROM crm_contacts_cache 
                WHERE 
                    LOWER(first_name) LIKE %s OR
                    LOWER(last_name) LIKE %s OR
                    LOWER(company_name) LIKE %s OR
                    LOWER(email) LIKE %s OR
                    phone LIKE %s
                ORDER BY 
                    CASE 
                        WHEN LOWER(company_name) = %s THEN 1
                        WHEN LOWER(email) = %s THEN 2
                        WHEN LOWER(company_name) LIKE %s THEN 3
                        WHEN LOWER(first_name) LIKE %s OR LOWER(last_name) LIKE %s THEN 4
                        ELSE 5
                    END,
                    company_name, first_name, last_name
                LIMIT %s
            """, (
                search_query, search_query, search_query, search_query, search_query,
                query.lower(), query.lower(), search_query, search_query, search_query,
                limit
            ))
            
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            return [self._row_to_contact(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []
    
    def _row_to_contact(self, row) -> Contact:
        """Convert database row to Contact object"""
        return Contact(
            id=row['contact_id'],
            first_name=row['first_name'] or '',
            last_name=row['last_name'] or '',
            company_name=row['company_name'],
            email=row['email'],
            phone=row['phone'],
            address=row['address'] if isinstance(row['address'], dict) else None,
            custom_fields=row['custom_fields'] if isinstance(row['custom_fields'], dict) else None,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_synced=row['last_synced'],
            source=row['source'] or 'lacrm'
        )