"""
Database Connection and Session Management

Handles PostgreSQL connection, session management, and database operations
for the LOI Automation System.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any, List
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from database.models import Base, Customer, LOITransaction, CRMFormData, ProcessingEvent, AIDecision

# Database connection doesn't need complex settings - just DATABASE_URL
# Forms only need database access, not LACRM API access

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for LOI Automation System"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
        
        # Database configuration from environment variables or defaults
        import os
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        
        # Log which database URL we're using (without password)
        safe_url = self.database_url.replace('2laNcRN0ATESCFQg1mGhknBielnDJfiS', '***')
        logger.info(f"🗄️ Using database URL: {safe_url}")
        
        # Parse database URL for individual components (if needed)
        if self.database_url.startswith('postgresql://'):
            # Parse URL: postgresql://username:password@host:port/database
            import re
            url_pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):?(\d+)?/(.+)'
            match = re.match(url_pattern, self.database_url)
            
            if match:
                username, password, host, port, database = match.groups()
                self.db_config = {
                    'database': database,
                    'host': host,
                    'port': int(port) if port else 5432,
                    'username': username,
                    'password': password  # Keep real password for connections
                }
            else:
                # Fallback parsing
                url_parts = self.database_url.replace('postgresql://', '').split('/')
                user_host_part = url_parts[0]
                self.db_config = {
                    'database': url_parts[1] if len(url_parts) > 1 else 'loi_automation',
                    'host': 'production' if 'DATABASE_URL' in os.environ else 'localhost',
                    'port': 5432,
                    'username': user_host_part.split('@')[0].split(':')[0] if '@' in user_host_part else 'mattmizell',
                    'password': '2laNcRN0ATESCFQg1mGhknBielnDJfiS'  # Use actual password
                }
        else:
            # Use environment variables for database configuration
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'loi_automation'),
                'username': os.getenv('DB_USER', 'loi_user'),
                'password': os.getenv('DB_PASSWORD', '')
            }
        
        logger.info("🗄️ Database manager initialized")
    
    def initialize(self):
        """Initialize database connection and create tables"""
        
        try:
            # DISABLED: Database already exists in production
            # self._ensure_database_exists()
            
            # Create engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # DISABLED: Tables already exist in production
            # self._create_tables()
            
            # Create database views
            self._create_views()
            
            # Insert default data
            self._insert_default_data()
            
            self._initialized = True
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise e
    
    def _ensure_database_exists(self):
        """Ensure the LOI automation database exists"""
        
        try:
            # Connect to PostgreSQL server (not to specific database)
            server_url = f"postgresql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/postgres"
            
            # Use psycopg2 directly for database creation
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['username'],
                password=self.db_config['password'],
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (self.db_config['database'],)
            )
            
            if not cursor.fetchone():
                # Create database
                cursor.execute(f'CREATE DATABASE "{self.db_config["database"]}"')
                logger.info(f"🗄️ Created database: {self.db_config['database']}")
            else:
                logger.info(f"🗄️ Database already exists: {self.db_config['database']}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error ensuring database exists: {e}")
            raise e
    
    def _create_tables(self):
        """Create all database tables"""
        
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("🏗️ Database tables created successfully")
            
            # Log table information
            with self.get_session() as session:
                # Get table names
                result = session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """))
                
                tables = [row[0] for row in result.fetchall()]
                logger.info(f"📋 Created tables: {', '.join(tables)}")
                
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise e
    
    def _create_views(self):
        """Create database views for reporting and analytics"""
        
        views = {
            'loi_dashboard_summary': """
                CREATE OR REPLACE VIEW loi_dashboard_summary AS
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_lois,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_lois,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_lois,
                    COUNT(CASE WHEN status = 'waiting_signature' THEN 1 END) as pending_signature_lois,
                    AVG(CASE 
                        WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (completed_at - started_at)) 
                    END) as avg_completion_time_seconds,
                    AVG(complexity_score) as avg_complexity_score,
                    AVG(ai_priority_score) as avg_ai_priority_score
                FROM loi_transactions 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """,
            
            'customer_summary': """
                CREATE OR REPLACE VIEW customer_summary AS
                SELECT 
                    c.id,
                    c.company_name,
                    c.email,
                    c.is_vip_customer,
                    c.customer_type,
                    COUNT(lt.id) as total_lois,
                    COUNT(CASE WHEN lt.status = 'completed' THEN 1 END) as completed_lois,
                    COUNT(CASE WHEN lt.status = 'failed' THEN 1 END) as failed_lois,
                    MAX(lt.created_at) as last_loi_date,
                    COALESCE(SUM(cfd.total_estimated_incentives), 0) as total_incentives,
                    COALESCE(SUM(cfd.monthly_gasoline_volume + cfd.monthly_diesel_volume), 0) as total_monthly_volume
                FROM customers c
                LEFT JOIN loi_transactions lt ON c.id = lt.customer_id
                LEFT JOIN crm_form_data cfd ON lt.id = cfd.transaction_id
                GROUP BY c.id, c.company_name, c.email, c.is_vip_customer, c.customer_type
            """,
            
            'integration_performance': """
                CREATE OR REPLACE VIEW integration_performance AS
                SELECT 
                    integration_type,
                    operation,
                    DATE(timestamp) as date,
                    COUNT(*) as total_calls,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_calls,
                    ROUND(AVG(response_time)::numeric, 3) as avg_response_time,
                    ROUND(MAX(response_time)::numeric, 3) as max_response_time,
                    ROUND((COUNT(CASE WHEN success = true THEN 1 END)::float / COUNT(*) * 100)::numeric, 2) as success_rate
                FROM integration_logs 
                WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY integration_type, operation, DATE(timestamp)
                ORDER BY date DESC, integration_type, operation
            """,
            
            'workflow_performance': """
                CREATE OR REPLACE VIEW workflow_performance AS
                SELECT 
                    workflow_stage,
                    DATE(timestamp) as date,
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_events,
                    ROUND(AVG(processing_time)::numeric, 3) as avg_processing_time,
                    ROUND(MAX(processing_time)::numeric, 3) as max_processing_time
                FROM processing_events 
                WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY workflow_stage, DATE(timestamp)
                ORDER BY date DESC, workflow_stage
            """,
            
            'ai_decision_analytics': """
                CREATE OR REPLACE VIEW ai_decision_analytics AS
                SELECT 
                    ai_provider,
                    decision_type,
                    DATE(created_at) as date,
                    COUNT(*) as total_decisions,
                    ROUND(AVG(confidence)::numeric, 3) as avg_confidence,
                    COUNT(CASE WHEN outcome_success = true THEN 1 END) as successful_outcomes,
                    ROUND(AVG(decision_accuracy)::numeric, 3) as avg_accuracy
                FROM ai_decisions 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY ai_provider, decision_type, DATE(created_at)
                ORDER BY date DESC, ai_provider, decision_type
            """
        }
        
        try:
            with self.get_session() as session:
                for view_name, view_sql in views.items():
                    session.execute(text(view_sql))
                    session.commit()
                    logger.info(f"📊 Created view: {view_name}")
                    
        except Exception as e:
            logger.error(f"❌ Error creating views: {e}")
            # Don't raise - views are optional for basic functionality
    
    def _insert_default_data(self):
        """Insert default data and templates"""
        
        try:
            with self.get_session() as session:
                
                # Insert default document template
                from .models import DocumentTemplate
                
                existing_template = session.query(DocumentTemplate).filter_by(
                    template_name='vp_racing_loi',
                    version='1.0'
                ).first()
                
                if not existing_template:
                    default_template = DocumentTemplate(
                        template_name='vp_racing_loi',
                        template_type='loi',
                        version='1.0',
                        description='Standard Letter of Intent for VP Racing Fuel Supply Agreements',
                        field_mappings={
                            'customer_site_name': {'source': 'customer_data.company_name', 'required': True},
                            'dealer_name': {'source': 'customer_data.contact_name', 'required': True},
                            'monthly_gasoline_volume': {'source': 'crm_form_data.monthly_gasoline_volume', 'format': 'number_with_commas'},
                            'monthly_diesel_volume': {'source': 'crm_form_data.monthly_diesel_volume', 'format': 'number_with_commas'},
                            'total_estimated_incentives': {'source': 'crm_form_data.total_estimated_incentives', 'format': 'currency'}
                        },
                        format_settings={
                            'page_size': 'letter',
                            'margins': {'top': 0.75, 'bottom': 0.75, 'left': 1.0, 'right': 1.0},
                            'font_sizes': {'title': 16, 'heading': 14, 'body': 11}
                        },
                        is_active=True,
                        is_default=True
                    )
                    
                    session.add(default_template)
                    session.commit()
                    logger.info("📄 Inserted default VP Racing LOI template")
                
        except Exception as e:
            logger.error(f"❌ Error inserting default data: {e}")
            # Don't raise - default data is optional
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        
        if not self._initialized:
            self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database session error: {e}")
            raise e
        finally:
            session.close()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information"""
        
        try:
            with self.get_session() as session:
                # Test connection and get database info
                result = session.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                
                # Get database size
                result = session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """))
                size = result.fetchone()[0]
                
                # Get table count
                result = session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                table_count = result.fetchone()[0]
                
                return {
                    'status': 'connected',
                    'database': self.db_config['database'],
                    'host': self.db_config['host'],
                    'port': self.db_config['port'],
                    'version': version,
                    'size': size,
                    'table_count': table_count,
                    'connection_url': self.database_url.replace(self.db_config['password'], '***')
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'database': self.db_config['database'],
                'host': self.db_config['host'],
                'port': self.db_config['port']
            }
    
    def health_check(self) -> bool:
        """Check database health"""
        
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics from database"""
        
        try:
            with self.get_session() as session:
                
                # Get LOI summary stats
                loi_stats = session.execute(text("""
                    SELECT 
                        COUNT(*) as total_lois,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_lois,
                        COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_lois,
                        COUNT(CASE WHEN status = 'waiting_signature' THEN 1 END) as pending_signature_lois,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_lois,
                        ROUND(AVG(CASE 
                            WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                            THEN EXTRACT(EPOCH FROM (completed_at - started_at)) 
                        END)::numeric, 2) as avg_completion_time_seconds
                    FROM loi_transactions 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                """)).fetchone()
                
                # Get customer stats
                customer_stats = session.execute(text("""
                    SELECT 
                        COUNT(*) as total_customers,
                        COUNT(CASE WHEN is_vip_customer = true THEN 1 END) as vip_customers,
                        COUNT(CASE WHEN customer_type = 'new_prospect' THEN 1 END) as new_prospects
                    FROM customers
                """)).fetchone()
                
                # Get recent activity
                recent_activity = session.execute(text("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as loi_count
                    FROM loi_transactions 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    LIMIT 7
                """)).fetchall()
                
                # Get workflow stage distribution
                workflow_stages = session.execute(text("""
                    SELECT 
                        workflow_stage,
                        COUNT(*) as count
                    FROM loi_transactions 
                    WHERE status NOT IN ('completed', 'failed', 'cancelled')
                    GROUP BY workflow_stage
                """)).fetchall()
                
                return {
                    'loi_stats': {
                        'total': loi_stats[0] if loi_stats[0] else 0,
                        'completed': loi_stats[1] if loi_stats[1] else 0,
                        'processing': loi_stats[2] if loi_stats[2] else 0,
                        'pending_signature': loi_stats[3] if loi_stats[3] else 0,
                        'failed': loi_stats[4] if loi_stats[4] else 0,
                        'avg_completion_time': float(loi_stats[5]) if loi_stats[5] else 0.0
                    },
                    'customer_stats': {
                        'total': customer_stats[0] if customer_stats[0] else 0,
                        'vip': customer_stats[1] if customer_stats[1] else 0,
                        'new_prospects': customer_stats[2] if customer_stats[2] else 0
                    },
                    'recent_activity': [
                        {'date': str(row[0]), 'count': row[1]} 
                        for row in recent_activity
                    ],
                    'workflow_stages': {
                        row[0]: row[1] for row in workflow_stages
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {e}")
            return {
                'error': str(e),
                'loi_stats': {},
                'customer_stats': {},
                'recent_activity': [],
                'workflow_stages': {}
            }
    
    def cleanup_old_data(self, days_old: int = 90):
        """Clean up old data from database"""
        
        try:
            with self.get_session() as session:
                
                # Clean up old completed/failed transactions
                cutoff_date = text(f"CURRENT_DATE - INTERVAL '{days_old} days'")
                
                # Delete old processing events
                result = session.execute(text(f"""
                    DELETE FROM processing_events 
                    WHERE timestamp < {cutoff_date}
                    AND transaction_id IN (
                        SELECT id FROM loi_transactions 
                        WHERE status IN ('completed', 'failed', 'cancelled')
                        AND completed_at < {cutoff_date}
                    )
                """))
                events_deleted = result.rowcount
                
                # Delete old integration logs
                result = session.execute(text(f"""
                    DELETE FROM integration_logs 
                    WHERE timestamp < {cutoff_date}
                """))
                logs_deleted = result.rowcount
                
                # Delete old system metrics
                result = session.execute(text(f"""
                    DELETE FROM system_metrics 
                    WHERE timestamp < {cutoff_date}
                """))
                metrics_deleted = result.rowcount
                
                # Delete old queue snapshots
                result = session.execute(text(f"""
                    DELETE FROM queue_snapshots 
                    WHERE timestamp < {cutoff_date}
                """))
                snapshots_deleted = result.rowcount
                
                session.commit()
                
                logger.info(f"🧹 Cleaned up old data: {events_deleted} events, {logs_deleted} logs, {metrics_deleted} metrics, {snapshots_deleted} snapshots")
                
                return {
                    'events_deleted': events_deleted,
                    'logs_deleted': logs_deleted,
                    'metrics_deleted': metrics_deleted,
                    'snapshots_deleted': snapshots_deleted
                }
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up old data: {e}")
            return {'error': str(e)}

# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return db_manager

def get_db_session():
    """Dependency function for FastAPI to get database session"""
    with db_manager.get_session() as session:
        yield session