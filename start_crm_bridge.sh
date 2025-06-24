#!/bin/bash

# Better Day Energy CRM Bridge Service Startup Script

echo "🚀 Starting Better Day Energy CRM Bridge Service"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import fastapi, psycopg2, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install fastapi uvicorn psycopg2-binary requests python-multipart
fi

# Check database connection
echo "🗄️ Testing database connection..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://mattmizell:training1@localhost:5432/loi_automation')
    print('✅ Local database connected')
    conn.close()
except Exception as e:
    print(f'❌ Local database connection failed: {e}')
    print('🌐 Will try production database...')
    try:
        conn = psycopg2.connect('postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation')
        print('✅ Production database connected')
        conn.close()
    except Exception as e2:
        print(f'❌ Production database connection failed: {e2}')
        exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Exiting."
    exit 1
fi

# Start the service
echo ""
echo "🚀 Starting CRM Bridge Service on port 8005..."
echo "📖 API Documentation will be available at: http://localhost:8005/docs"
echo "⚡ Cache-first reads, background LACRM sync enabled"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the service with auto-reload for development
python3 bde_crm_bridge_service.py