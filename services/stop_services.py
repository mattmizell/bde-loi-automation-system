#!/usr/bin/env python3
"""
Service Stop Script
Stop all running microservices
"""

import subprocess
import logging
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_service_processes():
    """Find running service processes"""
    try:
        # Find processes running our services
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        processes = []
        for line in result.stdout.split('\n'):
            if 'python' in line and any(service in line for service in [
                'crm_service/main.py',
                'document_service/main.py', 
                'api_gateway/main.py',
                'start_services.py'
            ]):
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    cmd = ' '.join(parts[10:])
                    processes.append((pid, cmd))
        
        return processes
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error finding processes: {e}")
        return []

def stop_process(pid, cmd):
    """Stop a process by PID"""
    try:
        logger.info(f"Stopping process {pid}: {cmd}")
        
        # Try graceful termination first
        subprocess.run(["kill", "-TERM", pid], check=True)
        time.sleep(2)
        
        # Check if still running
        try:
            subprocess.run(["kill", "-0", pid], check=True, stderr=subprocess.DEVNULL)
            # Still running, force kill
            logger.warning(f"Force killing process {pid}")
            subprocess.run(["kill", "-KILL", pid], check=True)
        except subprocess.CalledProcessError:
            # Process is dead
            pass
        
        logger.info(f"✅ Stopped process {pid}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to stop process {pid}: {e}")
        return False

def stop_services_by_port():
    """Stop services by killing processes on known ports"""
    ports = [8000, 8001, 8002]  # Gateway, CRM, Document
    
    for port in ports:
        try:
            # Find process using port
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        logger.info(f"Stopping process {pid} on port {port}")
                        stop_process(pid, f"service on port {port}")
            
        except FileNotFoundError:
            # lsof not available, skip port-based stopping
            pass
        except Exception as e:
            logger.error(f"Error stopping service on port {port}: {e}")

def main():
    """Stop all services"""
    logger.info("🛑 Stopping Better Day Energy Microservices")
    
    # Method 1: Find and stop known service processes
    processes = find_service_processes()
    
    if processes:
        logger.info(f"Found {len(processes)} service processes")
        for pid, cmd in processes:
            stop_process(pid, cmd)
    else:
        logger.info("No service processes found by name")
    
    # Method 2: Stop services by port
    logger.info("🔍 Checking ports for remaining services...")
    stop_services_by_port()
    
    # Clean up log files (optional)
    logs_dir = Path(__file__).parent / "logs"
    if logs_dir.exists():
        logger.info(f"📝 Service logs available in: {logs_dir}")
    
    logger.info("✅ Service shutdown complete")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Stop script interrupted")
    except Exception as e:
        logger.error(f"❌ Error stopping services: {e}")
        sys.exit(1)