#!/usr/bin/env python3
"""
Quick database connection test for LOI Automation System
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def test_connection():
    """Test PostgreSQL connection with provided credentials"""
    
    print("🔍 Testing PostgreSQL connection...")
    
    try:
        # Connection parameters
        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'user': 'mattmizell',
            'password': 'training1',
            'database': 'postgres'  # Connect to default database first
        }
        
        # Test connection to PostgreSQL server
        print(f"🔗 Connecting to PostgreSQL server at {connection_params['host']}:{connection_params['port']}...")
        
        conn = psycopg2.connect(**connection_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connection successful!")
        print(f"📊 Version: {version[:80]}...")
        
        # Check if loi_automation database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            ('loi_automation',)
        )
        
        if cursor.fetchone():
            print("✅ Database 'loi_automation' exists")
        else:
            print("📝 Database 'loi_automation' will be created during setup")
        
        # List existing databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
        databases = [row[0] for row in cursor.fetchall()]
        print(f"📋 Available databases: {', '.join(databases)}")
        
        cursor.close()
        conn.close()
        
        print("✅ Database connection test passed!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("💡 Please check:")
        print("   - PostgreSQL server is running")
        print("   - Username and password are correct")
        print("   - Host and port are accessible")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if not success:
        print("\n🔧 To install PostgreSQL (if not installed):")
        print("   Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib")
        print("   CentOS/RHEL: sudo yum install postgresql-server postgresql-contrib")
        print("   macOS: brew install postgresql")
        print("   Windows: Download from https://www.postgresql.org/download/")
        
        print("\n⚙️ To configure PostgreSQL user:")
        print("   sudo -u postgres createuser --interactive mattmizell")
        print("   sudo -u postgres psql -c \"ALTER USER mattmizell PASSWORD 'training1';\"")
    
    exit(0 if success else 1)