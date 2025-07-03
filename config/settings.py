"""
Configuration Settings for LOI Automation System

Handles environment variables, API keys, and system configuration.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
import yaml
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class CRMConfig:
    """Less Annoying CRM configuration"""
    api_key: str = ""  # Updated to use single API key
    base_url: str = "https://api.lessannoyingcrm.com/v2/"
    timeout: int = 30
    max_retries: int = 3

@dataclass
class DocumentStorageConfig:
    """Document storage configuration (using CRM instead of Google Drive)"""
    storage_type: str = "crm"  # crm, google_drive, local
    crm_storage: bool = True  # Store documents as CRM attachments
    local_backup: bool = True  # Keep local backup copies
    backup_path: str = "./documents/backup"

@dataclass
class ESignatureConfig:
    """E-signature service configuration (PostgreSQL-based)"""
    provider: str = "postgresql"  # postgresql, sign.com, docusign
    expiration_days: int = 30
    reminder_interval_days: int = 7
    max_reminders: int = 3
    smtp_enabled: bool = True  # Email reminders enabled with working Gmail account

@dataclass
class EmailConfig:
    """Email notification configuration"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "transaction.coordinator.agent@gmail.com"
    smtp_password: str = "xmvi xvso zblo oewe"
    use_tls: bool = True
    from_email: str = "transaction.coordinator.agent@gmail.com"
    from_name: str = "Better Day Energy LOI System"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///loi_automation.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

@dataclass
class CoordinatorConfig:
    """LOI Coordinator configuration"""
    max_queue_size: int = 5000
    batch_size: int = 25
    processing_interval: float = 2.0
    max_concurrent_batches: int = 3
    document_timeout: float = 60.0
    signature_timeout: float = 604800  # 7 days
    retry_attempts: int = 3

@dataclass
class APIConfig:
    """FastAPI configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    cors_origins: list = field(default_factory=lambda: ["*"])
    api_prefix: str = "/api/v1"

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = ""
    api_key_header: str = "X-API-Key"
    api_keys: list = field(default_factory=list)
    cors_enabled: bool = True
    rate_limit_per_minute: int = 100

class Settings:
    """Main settings class for LOI Automation System"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/loi_config.yaml"
        
        # Initialize configurations
        self.crm = CRMConfig()
        self.document_storage = DocumentStorageConfig()
        self.esignature = ESignatureConfig()
        self.email = EmailConfig()
        self.database = DatabaseConfig()
        self.coordinator = CoordinatorConfig()
        self.api = APIConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        
        # Load configuration
        self._load_from_environment()
        self._load_from_file()
        self._validate_configuration()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        
        # CRM Configuration
        self.crm.api_key = os.getenv("LACRM_API_TOKEN", os.getenv("CRM_API_KEY", self.crm.api_key))
        self.crm.base_url = os.getenv("LACRM_API_BASE", os.getenv("CRM_BASE_URL", self.crm.base_url))
        
        # Document Storage Configuration (CRM-based)
        self.document_storage.storage_type = os.getenv("DOCUMENT_STORAGE_TYPE", self.document_storage.storage_type)
        
        # E-Signature Configuration (PostgreSQL-based)
        self.esignature.provider = os.getenv("ESIGNATURE_PROVIDER", self.esignature.provider)
        self.esignature.expiration_days = int(os.getenv("ESIGNATURE_EXPIRATION_DAYS", str(self.esignature.expiration_days)))
        self.esignature.reminder_interval_days = int(os.getenv("ESIGNATURE_REMINDER_INTERVAL_DAYS", str(self.esignature.reminder_interval_days)))
        self.esignature.max_reminders = int(os.getenv("ESIGNATURE_MAX_REMINDERS", str(self.esignature.max_reminders)))
        
        # Email Configuration
        self.email.smtp_host = os.getenv("SMTP_HOST", self.email.smtp_host)
        self.email.smtp_port = int(os.getenv("SMTP_PORT", str(self.email.smtp_port)))
        self.email.smtp_username = os.getenv("SMTP_USERNAME", self.email.smtp_username)
        self.email.smtp_password = os.getenv("SMTP_PASSWORD", self.email.smtp_password)
        self.email.from_email = os.getenv("FROM_EMAIL", self.email.from_email)
        
        # Database Configuration
        self.database.url = os.getenv("DATABASE_URL", self.database.url)
        
        # API Configuration
        self.api.host = os.getenv("API_HOST", self.api.host)
        self.api.port = int(os.getenv("API_PORT", str(self.api.port)))
        self.api.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Security Configuration
        self.security.secret_key = os.getenv("SECRET_KEY", self.security.secret_key)
        api_keys_env = os.getenv("API_KEYS", "")
        if api_keys_env:
            self.security.api_keys = [key.strip() for key in api_keys_env.split(",")]
        
        # Logging Configuration
        self.logging.level = os.getenv("LOG_LEVEL", self.logging.level)
        self.logging.file_path = os.getenv("LOG_FILE_PATH")
    
    def _load_from_file(self):
        """Load configuration from YAML file"""
        
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                if not config_data:
                    return
                
                # Update configurations from file
                if 'crm' in config_data:
                    self._update_config(self.crm, config_data['crm'])
                
                if 'google_drive' in config_data:
                    self._update_config(self.google_drive, config_data['google_drive'])
                
                if 'esignature' in config_data:
                    self._update_config(self.esignature, config_data['esignature'])
                
                if 'email' in config_data:
                    self._update_config(self.email, config_data['email'])
                
                if 'database' in config_data:
                    self._update_config(self.database, config_data['database'])
                
                if 'coordinator' in config_data:
                    self._update_config(self.coordinator, config_data['coordinator'])
                
                if 'api' in config_data:
                    self._update_config(self.api, config_data['api'])
                
                if 'logging' in config_data:
                    self._update_config(self.logging, config_data['logging'])
                
                if 'security' in config_data:
                    self._update_config(self.security, config_data['security'])
                
            except Exception as e:
                print(f"Warning: Could not load configuration file {config_path}: {e}")
    
    def _update_config(self, config_obj, config_data: Dict[str, Any]):
        """Update configuration object with data from file"""
        
        for key, value in config_data.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
    
    def _validate_configuration(self):
        """Validate required configuration values for our current architecture"""
        
        errors = []
        warnings = []
        
        # Validate CRM configuration (REQUIRED - our primary integration)
        if not self.crm.api_key:
            errors.append("CRM API key is required")
        
        # Document Storage validation (CRM-based, no Google Drive needed)
        if self.document_storage.storage_type == "crm":
            if not self.crm.api_key:
                errors.append("CRM API key required for document storage")
        
        # E-Signature validation (PostgreSQL-based, no external API needed)
        if self.esignature.provider == "postgresql":
            # No external validation needed for PostgreSQL e-signatures
            pass
        elif self.esignature.provider in ["docusign", "sign.com"]:
            warnings.append(f"External e-signature provider {self.esignature.provider} configured but PostgreSQL solution is recommended")
        
        # Email configuration (OPTIONAL for signature reminders)
        if self.esignature.smtp_enabled:
            if not self.email.smtp_username:
                warnings.append("SMTP username recommended for signature email reminders")
            if not self.email.smtp_password:
                warnings.append("SMTP password recommended for signature email reminders")
        
        # Database validation (REQUIRED)
        if not self.database.url and not (self.database.host and self.database.name and self.database.user):
            errors.append("Database connection information is required")
        
        # Security configuration
        if not self.security.secret_key:
            # Generate a default secret key if none provided
            import secrets
            self.security.secret_key = secrets.token_urlsafe(32)
            warnings.append("Generated default secret key. Set SECRET_KEY environment variable for production.")
        
        # Print warnings
        for warning in warnings:
            print(f"⚠️  Warning: {warning}")
        
        # Only fail on actual errors, not warnings
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def create_sample_config_file(self, file_path: str = "config/loi_config.yaml"):
        """Create a sample configuration file"""
        
        sample_config = {
            'crm': {
                'api_user': 'your_crm_user',
                'api_token': 'your_crm_token',
                'base_url': 'https://api.lessannoyingcrm.com',
                'timeout': 30,
                'max_retries': 3
            },
            'google_drive': {
                'credentials_file': 'google_drive_credentials.json',
                'root_folder_id': None,
                'folder_structure': {
                    'pending_signature': 'LOI Documents - Pending Signature',
                    'completed': 'LOI Documents - Completed',
                    'failed': 'LOI Documents - Failed',
                    'templates': 'LOI Templates',
                    'archive': 'LOI Archive'
                }
            },
            'esignature': {
                'provider': 'sign.com',
                'api_key': 'your_esignature_api_key',
                'api_secret': 'your_esignature_api_secret',
                'webhook_url': None,
                'reminder_frequency_hours': 72,
                'expiration_days': 14,
                'max_reminders': 3
            },
            'email': {
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': 'your_email@gmail.com',
                'smtp_password': 'your_app_password',
                'use_tls': True,
                'from_email': 'your_email@gmail.com',
                'from_name': 'Better Day Energy LOI System'
            },
            'database': {
                'url': 'sqlite:///loi_automation.db',
                'pool_size': 5,
                'max_overflow': 10,
                'echo': False
            },
            'coordinator': {
                'max_queue_size': 5000,
                'batch_size': 25,
                'processing_interval': 2.0,
                'max_concurrent_batches': 3,
                'document_timeout': 60.0,
                'signature_timeout': 604800,
                'retry_attempts': 3
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'debug': False,
                'workers': 1,
                'cors_origins': ['*'],
                'api_prefix': '/api/v1'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': None,
                'max_bytes': 10485760,
                'backup_count': 5
            },
            'security': {
                'secret_key': 'your_secret_key_here',
                'api_key_header': 'X-API-Key',
                'api_keys': ['your_api_key_1', 'your_api_key_2'],
                'cors_enabled': True,
                'rate_limit_per_minute': 100
            }
        }
        
        # Create config directory if it doesn't exist
        config_dir = Path(file_path).parent
        config_dir.mkdir(exist_ok=True)
        
        # Write sample config file
        with open(file_path, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
        
        print(f"Sample configuration file created: {file_path}")
        print("Please update the configuration values before running the system.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive information)"""
        
        return {
            'crm': {
                'api_user': self.crm.api_user,
                'base_url': self.crm.base_url,
                'timeout': self.crm.timeout,
                'max_retries': self.crm.max_retries
            },
            'google_drive': {
                'credentials_file': self.google_drive.credentials_file,
                'root_folder_id': self.google_drive.root_folder_id,
                'folder_structure': self.google_drive.folder_structure
            },
            'esignature': {
                'provider': self.esignature.provider,
                'webhook_url': self.esignature.webhook_url,
                'reminder_frequency_hours': self.esignature.reminder_frequency_hours,
                'expiration_days': self.esignature.expiration_days,
                'max_reminders': self.esignature.max_reminders
            },
            'coordinator': {
                'max_queue_size': self.coordinator.max_queue_size,
                'batch_size': self.coordinator.batch_size,
                'processing_interval': self.coordinator.processing_interval,
                'max_concurrent_batches': self.coordinator.max_concurrent_batches,
                'document_timeout': self.coordinator.document_timeout,
                'signature_timeout': self.coordinator.signature_timeout,
                'retry_attempts': self.coordinator.retry_attempts
            },
            'api': {
                'host': self.api.host,
                'port': self.api.port,
                'debug': self.api.debug,
                'workers': self.api.workers,
                'cors_origins': self.api.cors_origins,
                'api_prefix': self.api.api_prefix
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_bytes': self.logging.max_bytes,
                'backup_count': self.logging.backup_count
            }
        }

# Global settings instance
settings = Settings()

# Function to get settings instance
def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings