#!/usr/bin/env python3
"""
Minimal server startup script for Render deployment
This ensures the FastAPI app starts properly
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Import the app
        logger.info("🔄 Importing FastAPI app...")
        from main import app
        logger.info("✅ FastAPI app imported successfully")
        
        # Get port from environment
        port = int(os.environ.get("PORT", 8002))
        logger.info(f"🚀 Starting server on port {port}")
        
        # Start uvicorn
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()