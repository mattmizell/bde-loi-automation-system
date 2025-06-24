#!/bin/bash

# LOI Automation System Startup Script

echo "🚀 Starting Better Day Energy LOI Automation System Setup"
echo "=" * 60

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before running the system"
fi

# Create logs directory
mkdir -p logs

# Run database setup
echo "🗄️ Setting up database..."
python3 setup_database.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ LOI Automation System setup complete!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Edit .env file with your API keys and configuration"
    echo "   2. Update Google Drive credentials file"
    echo "   3. Configure CRM and e-signature service credentials"
    echo "   4. Run: python3 main.py"
    echo ""
    echo "🌐 The system will be available at:"
    echo "   - API: http://localhost:8000"
    echo "   - Dashboard: http://localhost:8000/dashboard"
    echo "   - Documentation: http://localhost:8000/docs"
else
    echo "❌ Database setup failed. Please check the configuration and try again."
    exit 1
fi