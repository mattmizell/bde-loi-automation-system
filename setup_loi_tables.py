#!/usr/bin/env python3
"""
Quick setup script to create basic LOI tables for restored functionality
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_loi_tables():
    """Create basic LOI tables for restored functionality"""
    
    try:
        # Try production database first
        try:
            conn = psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
            logger.info("🌐 Using production database")
        except:
            # Fallback to local database
            conn = psycopg2.connect("postgresql://mattmizell:training1@localhost:5432/loi_automation")
            logger.info("🏠 Using local database")
        
        cur = conn.cursor()
        
        # Create loi_transactions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS loi_transactions (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(255) UNIQUE NOT NULL,
                company_name VARCHAR(255),
                contact_name VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                loi_data JSONB,
                signature_data TEXT,
                status VARCHAR(50) DEFAULT 'pending_signature',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                signed_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Create index on transaction_id for fast lookups
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_loi_transaction_id 
            ON loi_transactions(transaction_id)
        """)
        
        # Create index on status for dashboard queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_loi_status 
            ON loi_transactions(status)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("✅ LOI tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating LOI tables: {e}")
        return False

if __name__ == "__main__":
    setup_loi_tables()