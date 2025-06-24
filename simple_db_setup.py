#!/usr/bin/env python3
"""
Simple Database Setup for LOI Automation System
"""

import logging
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main setup function"""
    
    logger.info("🚀 Starting Simple LOI Database Setup")
    logger.info("=" * 50)
    
    try:
        # Import required modules
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Import database models
        from database.models import Base, Customer, LOITransaction, CRMFormData, ProcessingEvent, AIDecision, DocumentTemplate
        from database.models import TransactionPriority, TransactionStatus, TransactionType
        
        # Database configuration
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'loi_automation',
            'username': 'mattmizell',
            'password': 'training1'
        }
        
        database_url = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        
        # Ensure database exists
        logger.info("🔍 Ensuring database exists...")
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['username'],
            password=db_config['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_config['database'],)
        )
        
        if not cursor.fetchone():
            cursor.execute(f'CREATE DATABASE "{db_config["database"]}"')
            logger.info(f"✅ Created database: {db_config['database']}")
        else:
            logger.info(f"✅ Database already exists: {db_config['database']}")
        
        cursor.close()
        conn.close()
        
        # Create engine and tables
        logger.info("🏗️ Creating database tables...")
        engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Create sample data
        logger.info("📝 Creating sample data...")
        
        # Sample customer
        existing_customer = session.query(Customer).filter_by(email="demo@betterdayenergy.com").first()
        if not existing_customer:
            demo_customer = Customer(
                company_name="Better Day Energy Demo Station",
                contact_name="Demo Customer",
                contact_title="Owner",
                email="demo@betterdayenergy.com",
                phone="(314) 555-0123",
                street_address="123 Demo Street",
                city="St. Louis",
                state="MO",
                zip_code="63101",
                is_vip_customer=True,
                customer_type="strategic",
                crm_contact_id="DEMO_001"
            )
            session.add(demo_customer)
            session.commit()
            logger.info("✅ Created demo customer")
            
            # Sample transaction
            demo_transaction = LOITransaction(
                customer_id=demo_customer.id,
                transaction_type=TransactionType.NEW_LOI_REQUEST,
                priority=TransactionPriority.HIGH,
                status=TransactionStatus.PENDING,
                complexity_score=7.0,
                ai_priority_score=8.0,
                processing_context={'source': 'demo', 'demo_mode': True}
            )
            session.add(demo_transaction)
            session.commit()
            
            # Sample CRM data
            demo_crm_data = CRMFormData(
                transaction_id=demo_transaction.id,
                monthly_gasoline_volume=35000,
                monthly_diesel_volume=20000,
                current_fuel_supplier="Shell",
                image_funding_amount=75000,
                incentive_funding_amount=35000,
                total_estimated_incentives=110000,
                canopy_installation_required=True,
                special_requirements_notes="High-volume demo station",
                validation_score=95.0,
                crm_form_id="DEMO_FORM_001"
            )
            session.add(demo_crm_data)
            session.commit()
            logger.info("✅ Created demo transaction data")
        
        # Test database connection
        result = session.execute(text("SELECT COUNT(*) FROM customers"))
        customer_count = result.scalar()
        logger.info(f"📊 Database test: {customer_count} customers in database")
        
        session.close()
        
        logger.info("=" * 50)
        logger.info("✅ Database setup completed successfully!")
        logger.info("🌐 You can now start the application")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)