"""
CRM Service Configuration
Centralized configuration for the standalone CRM service
"""

import os
import hashlib

# Service configuration
CRM_SERVICE_CONFIG = {
    'port': int(os.getenv('CRM_SERVICE_PORT', 8001)),
    'debug': os.getenv('DEBUG', 'False').lower() == 'true',
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
}

# Database configuration
DATABASE_CONFIG = {
    'url': os.getenv('DATABASE_URL', "postgresql://mattmizell:training1@localhost/loi_automation"),
    'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
    'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20)),
}

# LACRM API configuration
LACRM_CONFIG = {
    'api_key': "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W",
    'base_url': "https://api.lessannoyingcrm.com/v2/",
    'timeout': int(os.getenv('LACRM_TIMEOUT', 30)),
    'retry_attempts': int(os.getenv('LACRM_RETRY_ATTEMPTS', 3)),
}

# Cache configuration
CACHE_CONFIG = {
    'enabled': True,
    'refresh_interval_minutes': int(os.getenv('CACHE_REFRESH_INTERVAL', 5)),
    'max_contacts': int(os.getenv('CACHE_MAX_CONTACTS', 10000)),
}

# Sync service configuration
SYNC_CONFIG = {
    'enabled': True,
    'read_interval_seconds': int(os.getenv('SYNC_READ_INTERVAL', 300)),  # 5 minutes
    'write_interval_seconds': int(os.getenv('SYNC_WRITE_INTERVAL', 30)),  # 30 seconds
    'batch_size': int(os.getenv('SYNC_BATCH_SIZE', 100)),
    'max_retry_attempts': int(os.getenv('SYNC_MAX_RETRIES', 3)),
}

# Multi-application authentication tokens
CRM_BRIDGE_TOKENS = {
    "loi_automation": "bde_loi_auth_" + hashlib.sha256("loi_automation_secret_key_2025".encode()).hexdigest()[:32],
    "bolt_sales_tool": "bde_bolt_auth_" + hashlib.sha256("bolt_sales_secret_key_2025".encode()).hexdigest()[:32], 
    "adam_sales_app": "bde_adam_auth_" + hashlib.sha256("adam_sales_secret_key_2025".encode()).hexdigest()[:32],
    "rooster_operations": "bde_rooster_auth_" + hashlib.sha256("rooster_operations_secret_key_2025".encode()).hexdigest()[:32],
}

# Application permissions
APP_PERMISSIONS = {
    "loi_automation": ["read_contacts", "create_contacts", "update_contacts", "search_contacts"],
    "bolt_sales_tool": ["read_contacts", "search_contacts"],
    "adam_sales_app": ["read_contacts", "create_contacts", "update_contacts", "search_contacts"],
    "rooster_operations": ["read_contacts", "search_contacts"],
}

# API rate limiting
RATE_LIMIT_CONFIG = {
    'enabled': True,
    'requests_per_minute': int(os.getenv('RATE_LIMIT_RPM', 300)),
    'burst_limit': int(os.getenv('RATE_LIMIT_BURST', 50)),
}

# Security settings
SECURITY_CONFIG = {
    'require_https': os.getenv('REQUIRE_HTTPS', 'False').lower() == 'true',
    'allowed_origins': os.getenv('ALLOWED_ORIGINS', '*').split(','),
    'token_expiry_hours': int(os.getenv('TOKEN_EXPIRY_HOURS', 24)),
}