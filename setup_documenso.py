#!/usr/bin/env python3
"""
Setup Documenso for LOI Signature Routing

Install and configure Documenso (open-source DocuSign alternative) for our LOI automation system.
"""

import subprocess
import logging
import os
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_documenso():
    """Set up Documenso for signature routing"""
    
    try:
        logger.info("🚀 Setting up Documenso for LOI signature routing...")
        
        # Create documenso directory
        documenso_dir = Path("./documenso")
        documenso_dir.mkdir(exist_ok=True)
        
        logger.info("📁 Created Documenso directory")
        
        # Step 1: Clone Documenso repository
        logger.info("📥 Cloning Documenso repository...")
        clone_result = subprocess.run([
            "git", "clone", 
            "https://github.com/documenso/documenso.git",
            str(documenso_dir)
        ], capture_output=True, text=True)
        
        if clone_result.returncode == 0:
            logger.info("✅ Documenso repository cloned successfully")
        else:
            logger.error(f"❌ Failed to clone Documenso: {clone_result.stderr}")
            return False
        
        # Step 2: Create environment configuration
        logger.info("⚙️ Creating environment configuration...")
        create_environment_config(documenso_dir)
        
        # Step 3: Create Docker setup for easy deployment
        logger.info("🐳 Creating Docker configuration...")
        create_docker_setup(documenso_dir)
        
        # Step 4: Create integration configuration
        logger.info("🔗 Creating integration configuration...")
        create_integration_config()
        
        logger.info("🎉 Documenso setup completed!")
        print_setup_instructions()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Documenso setup failed: {e}")
        return False

def create_environment_config(documenso_dir):
    """Create environment configuration for Documenso"""
    
    env_content = """# Documenso Environment Configuration for BDE LOI System

# Database Configuration (PostgreSQL)
DATABASE_URL="postgresql://mattmizell:training1@localhost:5432/documenso_loi"

# Application Settings
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-super-secret-nextauth-key-here"

# Email Configuration (using transaction coordinator Gmail)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USERNAME="transaction.coordinator.agent@gmail.com"
SMTP_PASSWORD="xmvi xvso zblo oewe"
SMTP_FROM="Better Day Energy LOI System <transaction.coordinator.agent@gmail.com>"

# File Storage (local for testing)
NEXT_PRIVATE_UPLOAD_TRANSPORT="local"
NEXT_PRIVATE_UPLOAD_PATH="./uploads"

# PDF Generation
NEXT_PRIVATE_PDF_PROVIDER="node-pdf"

# Security
ENCRYPTION_KEY="your-32-character-encryption-key-here"
ENCRYPTION_SECONDARY_KEY="your-32-character-secondary-key"

# Feature Flags
NEXT_PUBLIC_ALLOW_SIGNUP="false"
NEXT_PUBLIC_DISABLE_SIGNUP="true"

# Branding
NEXT_PUBLIC_APP_NAME="Better Day Energy LOI System"
NEXT_PUBLIC_APP_URL="http://localhost:3000"

# Webhook Configuration for LOI Integration
WEBHOOK_URL="http://localhost:8000/api/v1/webhooks/documenso"

# Development Settings
NODE_ENV="development"
NEXT_TELEMETRY_DISABLED="1"
"""
    
    env_file = documenso_dir / ".env.local"
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    logger.info(f"📝 Created environment file: {env_file}")

def create_docker_setup(documenso_dir):
    """Create Docker setup for easy deployment"""
    
    docker_compose_content = """version: '3.8'

services:
  documenso:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://mattmizell:training1@postgres:5432/documenso_loi
      - NEXTAUTH_URL=http://localhost:3000
      - NEXTAUTH_SECRET=your-super-secret-nextauth-key-here
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USERNAME=transaction.coordinator.agent@gmail.com
      - SMTP_PASSWORD=xmvi xvso zblo oewe
      - SMTP_FROM=Better Day Energy LOI System <transaction.coordinator.agent@gmail.com>
    depends_on:
      - postgres
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: documenso_loi
      POSTGRES_USER: mattmizell
      POSTGRES_PASSWORD: training1
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # Different port to avoid conflict with existing PostgreSQL
    restart: unless-stopped

volumes:
  postgres_data:
"""
    
    docker_file = documenso_dir / "docker-compose.yml"
    with open(docker_file, 'w') as f:
        f.write(docker_compose_content)
    
    logger.info(f"🐳 Created Docker Compose file: {docker_file}")

def create_integration_config():
    """Create integration configuration for LOI system"""
    
    integration_config = {
        "documenso": {
            "base_url": "http://localhost:3000",
            "api_endpoint": "http://localhost:3000/api",
            "webhook_endpoint": "http://localhost:8000/api/v1/webhooks/documenso",
            "features": {
                "signature_routing": True,
                "multi_signer": True,
                "templates": True,
                "audit_trail": True,
                "pdf_generation": True
            },
            "integration_points": {
                "create_document": "/api/documents",
                "send_for_signature": "/api/documents/{id}/send",
                "check_status": "/api/documents/{id}/status",
                "download_signed": "/api/documents/{id}/download"
            }
        },
        "loi_workflow": {
            "document_template": "loi_template_v1",
            "signature_fields": [
                {
                    "name": "customer_signature",
                    "type": "signature",
                    "required": True,
                    "signer_email": "matt.mizell@gmail.com"
                },
                {
                    "name": "customer_name",
                    "type": "text",
                    "required": True,
                    "value": "Farely Barnhart"
                },
                {
                    "name": "date_signed",
                    "type": "date",
                    "required": True,
                    "auto_fill": True
                }
            ],
            "routing_order": [
                {
                    "step": 1,
                    "signer": "customer",
                    "email": "matt.mizell@gmail.com",
                    "name": "Farely Barnhart",
                    "role": "Customer/Owner"
                }
            ]
        }
    }
    
    config_file = Path("./documenso_integration_config.json")
    with open(config_file, 'w') as f:
        json.dump(integration_config, f, indent=2)
    
    logger.info(f"🔗 Created integration config: {config_file}")

def print_setup_instructions():
    """Print setup instructions for Documenso"""
    
    instructions = """
🎉 DOCUMENSO SETUP COMPLETED!

📋 NEXT STEPS TO RUN DOCUMENSO:

1. 📁 Navigate to Documenso directory:
   cd documenso

2. 📦 Install dependencies:
   npm install
   # or
   yarn install

3. 🗄️ Set up database:
   npx prisma generate
   npx prisma db push

4. 🚀 Start Documenso:
   npm run dev
   # or
   yarn dev

5. 🌐 Access Documenso at:
   http://localhost:3000

📋 OR USE DOCKER (EASIER):

1. 📁 Navigate to Documenso directory:
   cd documenso

2. 🐳 Start with Docker:
   docker-compose up -d

3. 🌐 Access at http://localhost:3000

⚙️ CONFIGURATION DETAILS:

• Database: PostgreSQL (using existing credentials)
• Email: transaction.coordinator.agent@gmail.com
• Port: 3000 (Documenso web interface)
• API: http://localhost:3000/api
• Webhook: http://localhost:8000/api/v1/webhooks/documenso

🔗 INTEGRATION FEATURES:

✅ Document upload and management
✅ Signature field placement
✅ Multi-signer routing
✅ Email notifications
✅ Audit trail
✅ PDF generation
✅ API integration with LOI system
✅ Webhook notifications

📧 TEST WORKFLOW:

1. Upload LOI document to Documenso
2. Add signature fields for Farely Barnhart
3. Send for signature to matt.mizell@gmail.com
4. Farely reviews and signs document
5. Webhook notifies LOI system of completion
6. Download signed document

🔄 READY FOR LOI AUTOMATION INTEGRATION!
"""
    
    print(instructions)

if __name__ == "__main__":
    setup_documenso()