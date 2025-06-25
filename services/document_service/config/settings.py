"""
Document Service Configuration
"""

import os
from typing import Dict, Any

# Document Service Configuration
DOCUMENT_SERVICE_CONFIG = {
    'port': int(os.getenv('DOCUMENT_SERVICE_PORT', 8002)),
    'host': os.getenv('DOCUMENT_SERVICE_HOST', 'localhost'),
    'debug': os.getenv('DOCUMENT_SERVICE_DEBUG', 'false').lower() == 'true'
}

# Database Configuration
DATABASE_CONFIG = {
    'url': os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/bde_onboarding'),
    'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
    'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20))
}

# PDF Generation Configuration  
PDF_CONFIG = {
    'wkhtmltopdf_path': os.getenv('WKHTMLTOPDF_PATH', '/usr/local/bin/wkhtmltopdf'),
    'temp_dir': os.getenv('PDF_TEMP_DIR', '/tmp/pdf_generation'),
    'max_file_size': int(os.getenv('PDF_MAX_FILE_SIZE', 50 * 1024 * 1024)),  # 50MB
    'timeout': int(os.getenv('PDF_TIMEOUT', 30))  # 30 seconds
}

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'smtp_username': os.getenv('SMTP_USERNAME', ''),
    'smtp_password': os.getenv('SMTP_PASSWORD', ''),
    'from_email': os.getenv('FROM_EMAIL', 'noreply@betterdayenergy.com'),
    'from_name': os.getenv('FROM_NAME', 'Better Day Energy')
}

# Authentication Configuration
AUTH_CONFIG = {
    'jwt_secret': os.getenv('JWT_SECRET', 'your-secret-key-here'),
    'jwt_algorithm': 'HS256',
    'jwt_expiration': int(os.getenv('JWT_EXPIRATION', 3600)),  # 1 hour
    'api_keys': {
        'loi_service': os.getenv('LOI_SERVICE_API_KEY', 'loi-service-key'),
        'admin_service': os.getenv('ADMIN_SERVICE_API_KEY', 'admin-service-key')
    }
}

# File Storage Configuration
STORAGE_CONFIG = {
    'documents_path': os.getenv('DOCUMENTS_PATH', './documents'),
    'signatures_path': os.getenv('SIGNATURES_PATH', './signatures'),
    'templates_path': os.getenv('TEMPLATES_PATH', './templates'),
    'max_upload_size': int(os.getenv('MAX_UPLOAD_SIZE', 10 * 1024 * 1024))  # 10MB
}

# ESIGN Act Compliance Configuration
ESIGN_CONFIG = {
    'require_consent': True,
    'require_paper_copy_notice': True,
    'consent_retention_years': 7,
    'audit_trail_enabled': True
}