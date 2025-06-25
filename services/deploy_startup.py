#!/usr/bin/env python3
"""
Deployment Startup Script
Run database migrations and start services for production deployment
"""

import subprocess
import sys
import os
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_database_migration():
    """Run database migration before starting services"""
    try:
        logger.info("🔄 Running database migration...")
        
        # Run the migration script
        result = subprocess.run(
            [sys.executable, 'services/database_migration.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Database migration completed successfully")
            return True
        else:
            logger.error(f"❌ Database migration failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Database migration timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error running database migration: {e}")
        return False

def wait_for_database():
    """Wait for database to be available"""
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Try to connect to database
            import psycopg2
            
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.error("❌ DATABASE_URL environment variable not set")
                return False
            
            conn = psycopg2.connect(database_url)
            conn.close()
            
            logger.info("✅ Database connection successful")
            return True
            
        except Exception as e:
            logger.info(f"⏳ Waiting for database... ({attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    logger.error("❌ Database connection failed after all retries")
    return False

def main():
    """Main deployment startup"""
    logger.info("🚀 Starting Better Day Energy Service Deployment")
    
    # Determine which service to start based on environment or arguments
    service_type = os.getenv('SERVICE_TYPE', 'gateway')
    if len(sys.argv) > 1:
        service_type = sys.argv[1]
    
    logger.info(f"🎯 Service Type: {service_type}")
    
    # Wait for database to be available (for CRM and Document services)
    if service_type in ['crm', 'document']:
        if not wait_for_database():
            logger.error("❌ Database not available, exiting")
            sys.exit(1)
        
        # Run database migration (only once, for CRM service)
        if service_type == 'crm':
            if not run_database_migration():
                logger.error("❌ Database migration failed, exiting")
                sys.exit(1)
    
    # Start the appropriate service
    try:
        if service_type == 'gateway':
            logger.info("🚪 Starting API Gateway...")
            subprocess.run([sys.executable, 'services/api_gateway/main.py'], check=True)
        elif service_type == 'crm':
            logger.info("📱 Starting CRM Service...")
            subprocess.run([sys.executable, 'services/crm_service/main.py'], check=True)
        elif service_type == 'document':
            logger.info("📄 Starting Document Service...")
            subprocess.run([sys.executable, 'services/document_service/main.py'], check=True)
        else:
            logger.error(f"❌ Unknown service type: {service_type}")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Service failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Service interrupted")
        sys.exit(0)

if __name__ == "__main__":
    main()