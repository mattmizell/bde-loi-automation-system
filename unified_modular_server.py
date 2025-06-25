#!/usr/bin/env python3
"""
Unified Modular Server
Single service that runs the API Gateway with embedded CRM and Document services
This keeps all the modular benefits while running in a single Render service
"""

import os
import sys
import threading
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_database_migration():
    """Run database migration on startup"""
    try:
        logger.info("🔄 Running database migration...")
        
        # Import and run migration
        sys.path.append('services')
        from database_migration import DatabaseMigration
        
        migration = DatabaseMigration()
        migration.run_all_migrations()
        
        logger.info("✅ Database migration completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False

def start_crm_service():
    """Start CRM service in background thread"""
    try:
        logger.info("📱 Starting CRM Service thread...")
        
        # Set environment for CRM service
        os.environ['PORT'] = '8001'
        
        # Import and start CRM service
        from services.crm_service.main import main as crm_main
        crm_main()
        
    except Exception as e:
        logger.error(f"❌ CRM Service error: {e}")

def start_document_service():
    """Start Document service in background thread"""
    try:
        logger.info("📄 Starting Document Service thread...")
        
        # Set environment for Document service
        os.environ['PORT'] = '8002'
        
        # Import and start Document service
        from services.document_service.main import main as doc_main
        doc_main()
        
    except Exception as e:
        logger.error(f"❌ Document Service error: {e}")

def start_api_gateway():
    """Start API Gateway (main service)"""
    try:
        logger.info("🚪 Starting API Gateway...")
        
        # Set environment for API Gateway
        gateway_port = int(os.getenv('PORT', 8002))  # Use Render's PORT
        os.environ['PORT'] = str(gateway_port)
        
        # Set service URLs to localhost since they're running locally
        os.environ['CRM_SERVICE_URL'] = 'http://localhost:8001'
        os.environ['DOCUMENT_SERVICE_URL'] = 'http://localhost:8002'
        
        # Import and start API Gateway
        from services.api_gateway.main import main as gateway_main
        gateway_main()
        
    except Exception as e:
        logger.error(f"❌ API Gateway error: {e}")

def main():
    """Start unified modular server"""
    logger.info("🚀 Starting Unified Better Day Energy Modular Server")
    logger.info("=" * 60)
    
    # Run database migration first
    if not run_database_migration():
        logger.error("❌ Cannot start without database migration")
        sys.exit(1)
    
    # Start background services
    logger.info("🔄 Starting background services...")
    
    # Start CRM service in background thread
    crm_thread = threading.Thread(target=start_crm_service, daemon=True)
    crm_thread.start()
    
    # Start Document service in background thread  
    doc_thread = threading.Thread(target=start_document_service, daemon=True)
    doc_thread.start()
    
    # Wait a moment for services to initialize
    time.sleep(3)
    
    # Start API Gateway in main thread (this is what Render monitors)
    logger.info("🌐 Starting main API Gateway service...")
    start_api_gateway()

if __name__ == "__main__":
    main()