#!/usr/bin/env python3
"""
Test PostgreSQL database connection on Render
"""

import os
import psycopg2
from datetime import datetime

def test_database_connection():
    """Test the database connection and create required tables"""
    
    # Test the external database URL you provided
    database_url = "postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation"
    
    print("🗄️ Testing PostgreSQL Database Connection")
    print("=" * 50)
    print(f"📍 Database URL: {database_url.split('@')[0]}@***/{database_url.split('/')[-1]}")
    
    try:
        # Test connection
        print("\n🔗 Connecting to database...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Test basic query
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"✅ Connection successful!")
        print(f"📊 PostgreSQL version: {version}")
        
        # Create signature tables
        print("\n🏗️ Creating signature tables...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS electronic_signatures (
                id SERIAL PRIMARY KEY,
                verification_code VARCHAR(50) UNIQUE NOT NULL,
                transaction_id VARCHAR(100) NOT NULL,
                signature_token VARCHAR(255) UNIQUE NOT NULL,
                signer_name VARCHAR(255) NOT NULL,
                signer_email VARCHAR(255) NOT NULL,
                company_name VARCHAR(255),
                document_name VARCHAR(500) NOT NULL,
                signature_image BYTEA,
                signature_hash VARCHAR(64),
                ip_address INET,
                user_agent TEXT,
                browser_fingerprint VARCHAR(255),
                signed_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                document_hash VARCHAR(64),
                integrity_hash VARCHAR(64)
            )
        """)
        
        # Create CRM write queue table
        print("🗃️ Creating CRM write queue table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crm_write_queue (
                id SERIAL PRIMARY KEY,
                operation VARCHAR(50) NOT NULL,
                data JSONB NOT NULL,
                priority VARCHAR(20) DEFAULT 'normal',
                status VARCHAR(20) DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                local_id VARCHAR(100)
            )
        """)
        
        # Create CRM contacts cache table
        print("👥 Creating CRM contacts cache table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crm_contacts_cache (
                contact_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                company_name VARCHAR(255),
                phone VARCHAR(50),
                address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_sync TIMESTAMP,
                sync_status VARCHAR(20) DEFAULT 'pending'
            )
        """)
        
        # Create CRM sync log table
        print("📋 Creating CRM sync log table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crm_sync_log (
                id SERIAL PRIMARY KEY,
                last_sync_time TIMESTAMP,
                sync_type VARCHAR(50),
                records_updated INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ All tables created successfully!")
        
        # Test table counts
        print("\n📊 Database Status:")
        
        tables = [
            'electronic_signatures',
            'crm_write_queue', 
            'crm_contacts_cache',
            'crm_sync_log'
        ]
        
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  📋 {table}: {count} records")
        
        # Insert test data
        print("\n🧪 Inserting test data...")
        cur.execute("""
            INSERT INTO crm_sync_log (sync_type, records_updated)
            VALUES ('initial_setup', 0)
            ON CONFLICT DO NOTHING
        """)
        conn.commit()
        
        cur.close()
        conn.close()
        
        print("\n🎉 Database test completed successfully!")
        print("✅ PostgreSQL database is ready for production use")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    exit(0 if success else 1)