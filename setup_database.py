#!/usr/bin/env python3
"""
Database Setup Script for LOI Automation System

Initializes PostgreSQL database with schema, views, and default data.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now we can import directly
from database.connection import DatabaseManager
from database.models import (
    Customer, LOITransaction, CRMFormData, ProcessingEvent, 
    AIDecision, DocumentTemplate, TransactionPriority, TransactionStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main setup function"""
    
    logger.info("🚀 Starting LOI Automation Database Setup")
    logger.info("=" * 60)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        logger.info("🔧 Initializing database connection...")
        db_manager.initialize()
        
        # Test connection
        logger.info("🔍 Testing database connection...")
        connection_info = db_manager.get_connection_info()
        
        if connection_info['status'] == 'connected':
            logger.info("✅ Database connection successful!")
            logger.info(f"   Database: {connection_info['database']}")
            logger.info(f"   Host: {connection_info['host']}:{connection_info['port']}")
            logger.info(f"   Version: {connection_info['version'][:50]}...")
            logger.info(f"   Size: {connection_info['size']}")
            logger.info(f"   Tables: {connection_info['table_count']}")
        else:
            logger.error(f"❌ Database connection failed: {connection_info['error']}")
            return False
        
        # Test database operations
        logger.info("🧪 Testing database operations...")
        test_database_operations(db_manager)
        
        # Create sample data
        logger.info("📝 Creating sample data...")
        create_sample_data(db_manager)
        
        # Test dashboard stats
        logger.info("📊 Testing dashboard statistics...")
        test_dashboard_stats(db_manager)
        
        logger.info("=" * 60)
        logger.info("✅ LOI Automation Database Setup Complete!")
        logger.info("🌐 You can now start the application with: python main.py")
        logger.info("📊 Dashboard will be available at: http://localhost:8000/dashboard")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_operations(db_manager: DatabaseManager):
    """Test basic database operations"""
    
    try:
        with db_manager.get_session() as session:
            
            # Test customer creation
            test_customer = Customer(
                company_name="Test Gas Station",
                contact_name="John Test",
                contact_title="Owner",
                email="test@example.com",
                phone="(555) 123-4567",
                street_address="123 Test St",
                city="Test City",
                state="MO",
                zip_code="12345",
                is_vip_customer=False,
                customer_type="new_prospect",
                crm_contact_id="TEST_001"
            )
            
            session.add(test_customer)
            session.commit()
            
            logger.info("   ✅ Customer creation test passed")
            
            # Test transaction creation
            test_transaction = LOITransaction(
                customer_id=test_customer.id,
                priority=TransactionPriority.NORMAL,
                status=TransactionStatus.PENDING,
                complexity_score=5.0,
                ai_priority_score=5.0,
                processing_context={'source': 'test', 'test_mode': True}
            )
            
            session.add(test_transaction)
            session.commit()
            
            logger.info("   ✅ Transaction creation test passed")
            
            # Test CRM data creation
            test_crm_data = CRMFormData(
                transaction_id=test_transaction.id,
                monthly_gasoline_volume=25000,
                monthly_diesel_volume=15000,
                current_fuel_supplier="Shell",
                image_funding_amount=50000,
                incentive_funding_amount=25000,
                total_estimated_incentives=75000,
                canopy_installation_required=True,
                validation_score=95.0
            )
            
            session.add(test_crm_data)
            session.commit()
            
            logger.info("   ✅ CRM data creation test passed")
            
            # Test data retrieval
            retrieved_customer = session.query(Customer).filter_by(email="test@example.com").first()
            if retrieved_customer:
                logger.info(f"   ✅ Data retrieval test passed - Found customer: {retrieved_customer.company_name}")
            else:
                logger.warning("   ⚠️ Data retrieval test failed")
            
            # Clean up test data
            session.delete(test_crm_data)
            session.delete(test_transaction)
            session.delete(test_customer)
            session.commit()
            
            logger.info("   ✅ Test data cleanup completed")
            
    except Exception as e:
        logger.error(f"   ❌ Database operations test failed: {e}")
        raise e

def create_sample_data(db_manager: DatabaseManager):
    """Create sample data for demonstration"""
    
    try:
        with db_manager.get_session() as session:
            
            # Sample customers
            sample_customers = [
                {
                    'company_name': 'Better Day Energy Demo Station',
                    'contact_name': 'Demo Customer',
                    'contact_title': 'Owner',
                    'email': 'demo@betterdayenergy.com',
                    'phone': '(314) 555-0123',
                    'street_address': '123 Demo Street',
                    'city': 'St. Louis',
                    'state': 'MO',
                    'zip_code': '63101',
                    'is_vip_customer': True,
                    'customer_type': 'strategic',
                    'crm_contact_id': 'DEMO_001'
                },
                {
                    'company_name': 'Sample Fuel Stop',
                    'contact_name': 'Jane Sample',
                    'contact_title': 'Manager',
                    'email': 'jane@samplefuel.com',
                    'phone': '(314) 555-0456',
                    'street_address': '456 Sample Ave',
                    'city': 'Springfield',
                    'state': 'MO',
                    'zip_code': '65801',
                    'is_vip_customer': False,
                    'customer_type': 'new_prospect',
                    'crm_contact_id': 'DEMO_002'
                },
                {
                    'company_name': 'VP Racing Test Site',
                    'contact_name': 'Bob Tester',
                    'contact_title': 'Owner',
                    'email': 'bob@vptest.com',
                    'phone': '(314) 555-0789',
                    'street_address': '789 Racing Blvd',
                    'city': 'Kansas City',
                    'state': 'MO',
                    'zip_code': '64111',
                    'is_vip_customer': True,
                    'customer_type': 'existing_customer',
                    'crm_contact_id': 'DEMO_003'
                }
            ]
            
            # Create sample customers and transactions
            for i, customer_data in enumerate(sample_customers):
                
                # Check if customer already exists
                existing = session.query(Customer).filter_by(email=customer_data['email']).first()
                if existing:
                    logger.info(f"   📋 Customer already exists: {customer_data['company_name']}")
                    continue
                
                # Create customer
                customer = Customer(**customer_data)
                session.add(customer)
                session.flush()  # Get the ID
                
                # Create sample LOI transaction
                transaction = LOITransaction(
                    customer_id=customer.id,
                    priority=TransactionPriority.HIGH if customer.is_vip_customer else TransactionPriority.NORMAL,
                    status=TransactionStatus.PENDING if i == 0 else (TransactionStatus.COMPLETED if i == 1 else TransactionStatus.PROCESSING),
                    complexity_score=6.0 + i,
                    ai_priority_score=7.0 + i,
                    processing_context={
                        'source': 'sample_data',
                        'created_by': 'setup_script',
                        'demo_mode': True
                    }
                )
                session.add(transaction)
                session.flush()
                
                # Create sample CRM data
                crm_data = CRMFormData(
                    transaction_id=transaction.id,
                    monthly_gasoline_volume=20000 + (i * 10000),
                    monthly_diesel_volume=10000 + (i * 5000),
                    current_fuel_supplier=['Shell', 'Exxon', 'BP'][i],
                    image_funding_amount=40000 + (i * 20000),
                    incentive_funding_amount=20000 + (i * 10000),
                    total_estimated_incentives=60000 + (i * 30000),
                    canopy_installation_required=i % 2 == 0,
                    special_requirements_notes=f"Sample requirements for {customer.company_name}",
                    validation_score=90.0 + i * 2,
                    crm_form_id=f"SAMPLE_FORM_{i+1:03d}"
                )
                session.add(crm_data)
                
                # Create sample processing events
                event = ProcessingEvent(
                    transaction_id=transaction.id,
                    event_type='initial_assessment',
                    event_stage='initial',
                    event_data={
                        'assessment': 'sample_assessment',
                        'priority_assigned': transaction.priority.value
                    },
                    processing_time=1.5 + i * 0.5,
                    success=True,
                    handler_name='sample_handler'
                )
                session.add(event)
                
                # Create sample AI decision
                ai_decision = AIDecision(
                    transaction_id=transaction.id,
                    decision_type='initial_assessment',
                    decision_id=f'sample_decision_{i+1}',
                    ai_provider='grok',
                    model_name='grok-3-latest',
                    decision_data={
                        'priority_score': 7.0 + i,
                        'complexity_score': 6.0 + i,
                        'risk_factors': ['sample_risk'],
                        'recommendations': ['sample_recommendation']
                    },
                    reasoning=f'Sample AI reasoning for {customer.company_name}',
                    confidence=0.85 + (i * 0.05),
                    complexity_assessment=6.0 + i,
                    priority_score=7.0 + i
                )
                session.add(ai_decision)
                
                logger.info(f"   📋 Created sample data for: {customer.company_name}")
            
            session.commit()
            logger.info("   ✅ Sample data creation completed")
            
    except Exception as e:
        logger.error(f"   ❌ Sample data creation failed: {e}")
        # Don't raise - sample data is optional

def test_dashboard_stats(db_manager: DatabaseManager):
    """Test dashboard statistics functionality"""
    
    try:
        stats = db_manager.get_dashboard_stats()
        
        if 'error' in stats:
            logger.warning(f"   ⚠️ Dashboard stats error: {stats['error']}")
        else:
            logger.info("   ✅ Dashboard statistics test passed")
            logger.info(f"      Total LOIs: {stats['loi_stats']['total']}")
            logger.info(f"      Total Customers: {stats['customer_stats']['total']}")
            logger.info(f"      VIP Customers: {stats['customer_stats']['vip']}")
            
            if stats['workflow_stages']:
                logger.info(f"      Workflow Stages: {stats['workflow_stages']}")
        
    except Exception as e:
        logger.error(f"   ❌ Dashboard stats test failed: {e}")

def check_prerequisites():
    """Check if prerequisites are met"""
    
    logger.info("🔍 Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        logger.error(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        return False
    
    logger.info(f"   ✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check required packages
    required_packages = [
        'sqlalchemy', 'psycopg2', 'alembic', 'fastapi', 'uvicorn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"   ❌ {package} not installed")
    
    if missing_packages:
        logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
        logger.info("💡 Install with: pip install -r requirements.txt")
        return False
    
    return True

if __name__ == "__main__":
    # Check prerequisites first
    if not check_prerequisites():
        sys.exit(1)
    
    # Run setup
    success = main()
    sys.exit(0 if success else 1)