#!/usr/bin/env python3
"""
Database Migration for Modular Architecture
Ensure all services have their required database tables
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handle database migrations for modular services"""
    
    def __init__(self):
        # Use same connection string as existing system
        self.connection_string = os.getenv('DATABASE_URL', "postgresql://mattmizell:training1@localhost/loi_automation")
        
    def get_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(self.connection_string)
    
    def run_all_migrations(self):
        """Run all required database migrations"""
        logger.info("🚀 Starting database migration for modular architecture")
        
        try:
            # Create migration tracking table
            self._ensure_migration_tracking()
            
            # Run individual service migrations
            self._migrate_crm_service()
            self._migrate_document_service()
            self._ensure_existing_tables()
            
            logger.info("✅ All database migrations completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    def _ensure_migration_tracking(self):
        """Create migration tracking table"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS database_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    service_name VARCHAR(100),
                    description TEXT
                )
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info("✅ Migration tracking table ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to create migration tracking: {e}")
            raise
    
    def _migrate_crm_service(self):
        """Ensure CRM service tables exist"""
        migration_name = "crm_service_tables_v1"
        
        if self._is_migration_applied(migration_name):
            logger.info("⏩ CRM service migration already applied")
            return
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # CRM contacts cache table (already exists in contact_repository.py)
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
            
            # Create indexes for performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_email ON crm_contacts_cache(email)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_company ON crm_contacts_cache(company_name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_name ON crm_contacts_cache(first_name, last_name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_updated ON crm_contacts_cache(updated_at)")
            
            # CRM sync status table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crm_sync_status (
                    id SERIAL PRIMARY KEY,
                    service_type VARCHAR(50) NOT NULL DEFAULT 'lacrm',
                    last_sync_start TIMESTAMP WITH TIME ZONE,
                    last_sync_end TIMESTAMP WITH TIME ZONE,
                    last_sync_status VARCHAR(20), -- 'success', 'error', 'running'
                    contacts_synced INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    error_details JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # CRM sync queue for pending operations
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crm_sync_queue (
                    id SERIAL PRIMARY KEY,
                    contact_id VARCHAR(50) NOT NULL,
                    operation VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete'
                    contact_data JSONB,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processed_at TIMESTAMP WITH TIME ZONE
                )
            """)
            
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON crm_sync_queue(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sync_queue_created ON crm_sync_queue(created_at)")
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Mark migration as applied
            self._mark_migration_applied(
                migration_name, 
                "crm_service", 
                "CRM service tables with contact cache, sync status, and queue"
            )
            
            logger.info("✅ CRM service database migration completed")
            
        except Exception as e:
            logger.error(f"❌ CRM service migration failed: {e}")
            raise
    
    def _migrate_document_service(self):
        """Ensure Document service tables exist"""
        migration_name = "document_service_tables_v1"
        
        if self._is_migration_applied(migration_name):
            logger.info("⏩ Document service migration already applied")
            return
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Document templates table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_templates (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    document_type VARCHAR(50) NOT NULL,
                    content_html TEXT NOT NULL,
                    fields JSONB, -- Form fields/placeholders
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Documents table (separate from existing electronic_signatures)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    document_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'draft',
                    content_html TEXT,
                    template_id VARCHAR(50),
                    customer_id VARCHAR(50),
                    contact_email VARCHAR(255),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_customer ON documents(customer_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_email ON documents(contact_email)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at)")
            
            # Document signature requests (links documents to electronic_signatures)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_signature_requests (
                    id VARCHAR(50) PRIMARY KEY,
                    document_id VARCHAR(50) NOT NULL,
                    signature_token VARCHAR(255) UNIQUE NOT NULL,
                    signer_name VARCHAR(255) NOT NULL,
                    signer_email VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    signature_data TEXT, -- Base64 encoded signature
                    ip_address INET,
                    user_agent TEXT,
                    signed_at TIMESTAMP WITH TIME ZONE,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    consent_data JSONB, -- ESIGN Act compliance data
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sig_requests_document ON document_signature_requests(document_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sig_requests_status ON document_signature_requests(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sig_requests_token ON document_signature_requests(signature_token)")
            
            # Document audit trail
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_audit_trail (
                    id VARCHAR(50) PRIMARY KEY,
                    document_id VARCHAR(50),
                    signature_request_id VARCHAR(50),
                    action VARCHAR(100) NOT NULL,
                    actor VARCHAR(255) NOT NULL,
                    details JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (signature_request_id) REFERENCES document_signature_requests(id) ON DELETE CASCADE
                )
            """)
            
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_document ON document_audit_trail(document_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON document_audit_trail(timestamp)")
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Mark migration as applied
            self._mark_migration_applied(
                migration_name,
                "document_service", 
                "Document service tables with templates, documents, signatures, and audit trail"
            )
            
            logger.info("✅ Document service database migration completed")
            
        except Exception as e:
            logger.error(f"❌ Document service migration failed: {e}")
            raise
    
    def _ensure_existing_tables(self):
        """Ensure existing signature tables are preserved"""
        migration_name = "preserve_existing_signatures_v1"
        
        if self._is_migration_applied(migration_name):
            logger.info("⏩ Existing tables preservation already confirmed")
            return
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Check if existing electronic_signatures table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'electronic_signatures'
                )
            """)
            
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                logger.info("✅ Existing electronic_signatures table preserved")
            else:
                logger.warning("⚠️  Electronic signatures table not found - may need to run original migration")
            
            cur.close()
            conn.close()
            
            # Mark migration as applied
            self._mark_migration_applied(
                migration_name,
                "legacy_system",
                "Confirmed preservation of existing signature tables"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to check existing tables: {e}")
            raise
    
    def _is_migration_applied(self, migration_name):
        """Check if migration has already been applied"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM database_migrations WHERE migration_name = %s)",
                (migration_name,)
            )
            
            result = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            return result
            
        except Exception:
            # If migration table doesn't exist yet, migration hasn't been applied
            return False
    
    def _mark_migration_applied(self, migration_name, service_name, description):
        """Mark migration as applied"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO database_migrations (migration_name, service_name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (migration_name) DO NOTHING
            """, (migration_name, service_name, description))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to mark migration as applied: {e}")
            raise
    
    def show_migration_status(self):
        """Show current migration status"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT migration_name, service_name, description, applied_at
                FROM database_migrations
                ORDER BY applied_at DESC
            """)
            
            migrations = cur.fetchall()
            
            if migrations:
                logger.info("📊 Applied Database Migrations:")
                logger.info("=" * 80)
                for migration in migrations:
                    logger.info(f"✅ {migration['migration_name']}")
                    logger.info(f"   Service: {migration['service_name']}")
                    logger.info(f"   Applied: {migration['applied_at']}")
                    logger.info(f"   Description: {migration['description']}")
                    logger.info("-" * 40)
            else:
                logger.info("📊 No migrations have been applied yet")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to show migration status: {e}")

def main():
    """Run database migration"""
    migration = DatabaseMigration()
    
    try:
        logger.info("🔍 Checking current migration status...")
        migration.show_migration_status()
        
        logger.info("🚀 Running database migrations...")
        migration.run_all_migrations()
        
        logger.info("📊 Final migration status:")
        migration.show_migration_status()
        
        logger.info("✅ Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())