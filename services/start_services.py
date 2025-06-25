#!/usr/bin/env python3
"""
Service Startup Script
Start all microservices in the correct order
"""

import subprocess
import time
import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_service(service_name, script_path, port):
    """Start a service in the background"""
    try:
        logger.info(f"Starting {service_name} on port {port}...")
        
        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Start service
        log_file = logs_dir / f"{service_name.lower().replace(' ', '_')}.log"
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(script_path)
        )
        
        logger.info(f"✅ {service_name} started (PID: {process.pid})")
        logger.info(f"📝 Logs: {log_file}")
        
        return process
        
    except Exception as e:
        logger.error(f"❌ Failed to start {service_name}: {e}")
        return None

def check_service_health(service_name, port, max_retries=10):
    """Check if service is responding to health checks"""
    import requests
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                logger.info(f"✅ {service_name} is healthy")
                return True
        except:
            pass
        
        if attempt < max_retries - 1:
            logger.info(f"⏳ Waiting for {service_name} to start ({attempt + 1}/{max_retries})...")
            time.sleep(2)
    
    logger.warning(f"⚠️  {service_name} health check failed")
    return False

def main():
    """Start all services"""
    logger.info("🚀 Starting Better Day Energy Microservices")
    
    # Service definitions
    services = [
        {
            "name": "CRM Service",
            "script": "crm_service/main.py",
            "port": 8001
        },
        {
            "name": "Document Service", 
            "script": "document_service/main.py",
            "port": 8002
        },
        {
            "name": "API Gateway",
            "script": "api_gateway/main.py", 
            "port": 8000
        }
    ]
    
    processes = []
    services_dir = Path(__file__).parent
    
    # Start each service
    for service in services:
        script_path = services_dir / service["script"]
        if not script_path.exists():
            logger.error(f"❌ Service script not found: {script_path}")
            continue
        
        process = start_service(
            service["name"],
            str(script_path),
            service["port"]
        )
        
        if process:
            processes.append((service, process))
            time.sleep(3)  # Give service time to start
    
    # Check service health
    logger.info("🔍 Checking service health...")
    for service, process in processes:
        if process.poll() is None:  # Process still running
            check_service_health(service["name"], service["port"])
        else:
            logger.error(f"❌ {service['name']} process died")
    
    # Show final status
    logger.info("📊 Service Status:")
    logger.info("=" * 50)
    logger.info("🚪 API Gateway:     http://localhost:8000")
    logger.info("📱 CRM Service:     http://localhost:8001")
    logger.info("📄 Document Service: http://localhost:8002")
    logger.info("=" * 50)
    logger.info("🌐 Main endpoint:   http://localhost:8000/status")
    logger.info("🔍 Health checks:   http://localhost:8000/health")
    logger.info("=" * 50)
    
    # Show PID information
    logger.info("📝 Process Information:")
    for service, process in processes:
        if process.poll() is None:
            logger.info(f"   {service['name']}: PID {process.pid}")
        else:
            logger.info(f"   {service['name']}: STOPPED")
    
    logger.info("✅ All services started. Check logs in ./services/logs/")
    logger.info("🛑 To stop services, run: python stop_services.py")
    
    return processes

if __name__ == "__main__":
    try:
        processes = main()
        
        # Keep main process running
        logger.info("🏃 Services running. Press Ctrl+C to stop...")
        while True:
            time.sleep(60)
            # Check if any process died
            for service, process in processes:
                if process.poll() is not None:
                    logger.warning(f"⚠️  {service['name']} process died (PID {process.pid})")
                    
    except KeyboardInterrupt:
        logger.info("🛑 Stopping all services...")
        for service, process in processes:
            if process.poll() is None:
                logger.info(f"🛑 Stopping {service['name']}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️  Force killing {service['name']}...")
                    process.kill()
        
        logger.info("✅ All services stopped")
    except Exception as e:
        logger.error(f"❌ Error running services: {e}")
        sys.exit(1)