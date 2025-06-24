# LOI Automation System - Complete Setup Guide

**Better Day Energy - Letter of Intent Automation for VP Racing Supply Agreements**

This guide will walk you through setting up and running the complete LOI automation system with PostgreSQL database integration and Grok AI.

## 🎯 System Overview

The LOI Automation System uses the **Transaction Coordinator Pattern** to orchestrate:

- **CRM Integration**: Less Annoying CRM form data retrieval
- **Document Generation**: Professional PDF LOI creation
- **Google Drive Storage**: Organized document management
- **E-Signature Workflow**: DocuSign/Sign.com integration
- **AI Decision Making**: Grok API for intelligent processing
- **PostgreSQL Database**: Complete transaction tracking
- **Real-time Dashboard**: Monitoring and analytics

## 🚀 Quick Start

### 1. Prerequisites Verification

```bash
# Test database connection
python3 test_db_connection.py
```

**Expected Output:**
```
✅ PostgreSQL connection successful!
📊 Version: PostgreSQL 16.9...
📝 Database 'loi_automation' will be created during setup
```

### 2. Automated Setup

```bash
# Run complete setup script
./start.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create database schema
- ✅ Set up sample data
- ✅ Configure environment file

### 3. Manual Configuration

Edit the `.env` file with your credentials:

```env
# Already configured for your environment
DATABASE_USER=mattmizell
DATABASE_PASSWORD=training1
XAI_API_KEY=xai-730cElC0cSJcQ8KgbpaMZ32MrwhV1m563LNfxWr5zgc9UTkwBr2pYm36s86948sPHcJf8yH6rw9AgQUi

# You need to configure these
CRM_API_USER=your_crm_user
CRM_API_TOKEN=your_crm_token
GOOGLE_DRIVE_CREDENTIALS=google_drive_credentials.json
ESIGNATURE_API_KEY=your_esignature_api_key
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 4. Start the System

```bash
# Activate virtual environment
source venv/bin/activate

# Start the LOI automation system
python3 main.py
```

**System URLs:**
- 🌐 **Dashboard**: http://localhost:8000/dashboard
- 📊 **API Docs**: http://localhost:8000/docs
- 🔧 **Database Status**: http://localhost:8000/api/v1/database/status
- ❤️ **Health Check**: http://localhost:8000/api/v1/health

## 🗄️ Database Architecture

### Tables Created
- **customers** - Customer information and profiles
- **loi_transactions** - Main transaction tracking
- **crm_form_data** - CRM form submissions
- **processing_events** - Workflow event history
- **ai_decisions** - AI decision tracking
- **integration_logs** - External service logs
- **document_templates** - PDF template management
- **system_metrics** - Performance monitoring
- **queue_snapshots** - Queue state tracking

### Views Created
- **loi_dashboard_summary** - Daily LOI statistics
- **customer_summary** - Customer analytics
- **integration_performance** - API performance metrics
- **workflow_performance** - Stage processing metrics
- **ai_decision_analytics** - AI decision accuracy

## 🧠 AI Integration

### Grok API Features
- **Transaction Priority Assessment**: Intelligent priority scoring
- **Risk Factor Analysis**: Automated risk identification
- **Customer Classification**: VIP and type categorization
- **Processing Optimization**: Workflow routing recommendations
- **Completion Prediction**: Success probability analysis

### AI Decision Types
1. **initial_assessment** - First transaction evaluation
2. **processing_guidance** - Mid-workflow optimization
3. **risk_assessment** - Risk factor analysis
4. **completion_prediction** - Success probability

## 📋 API Usage Examples

### Submit LOI Request
```bash
curl -X POST "http://localhost:8000/api/v1/loi/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Demo Gas Station",
    "contact_name": "John Demo",
    "email": "john@demo.com",
    "phone": "(555) 123-4567",
    "business_address": {
      "street": "123 Demo St",
      "city": "Demo City", 
      "state": "MO",
      "zip": "12345"
    },
    "monthly_gasoline_volume": 30000,
    "monthly_diesel_volume": 20000,
    "current_fuel_supplier": "Shell",
    "image_funding_amount": 60000,
    "incentive_funding_amount": 30000,
    "total_estimated_incentives": 90000
  }'
```

### Check System Status
```bash
curl "http://localhost:8000/api/v1/status"
```

### Get Database Statistics
```bash
curl "http://localhost:8000/api/v1/database/status"
```

### List All LOIs
```bash
curl "http://localhost:8000/api/v1/loi/list?limit=50"
```

## 🔧 Configuration Details

### Database Configuration
- **Host**: localhost
- **Port**: 5432
- **Database**: loi_automation
- **User**: mattmizell
- **Password**: training1

### AI Configuration
- **Provider**: Grok (xAI)
- **Model**: grok-3-latest
- **API Key**: xai-730cElC0cSJcQ8KgbpaMZ32MrwhV1m563LNfxWr5zgc9UTkwBr2pYm36s86948sPHcJf8yH6rw9AgQUi
- **Temperature**: 0.1 (deterministic)
- **Max Tokens**: 1000

### Queue Configuration
- **Max Queue Size**: 5000 transactions
- **Batch Size**: 25 transactions
- **Processing Interval**: 2.0 seconds
- **Concurrent Batches**: 3

## 📊 Dashboard Features

### Real-time Metrics
- ✅ Total LOIs processed
- ✅ Queue utilization
- ✅ Processing status distribution
- ✅ Workflow stage tracking
- ✅ Completion rates
- ✅ Average processing times
- ✅ AI decision accuracy

### Performance Monitoring
- ✅ Integration response times
- ✅ Error rates by component
- ✅ Customer analytics
- ✅ Financial incentive tracking
- ✅ Geographic distribution

## 🛠️ Troubleshooting

### Database Issues
```bash
# Check database connection
python3 test_db_connection.py

# Recreate database
python3 setup_database.py

# Check database status via API
curl "http://localhost:8000/api/v1/database/status"
```

### AI Integration Issues
```bash
# Check AI integration status
curl "http://localhost:8000/api/v1/status" | grep ai

# Test AI directly in Python
python3 -c "
from integrations.ai_integration import GrokAIIntegration
ai = GrokAIIntegration()
print(ai.get_ai_stats())
"
```

### Queue Issues
```bash
# Check queue status
curl "http://localhost:8000/api/v1/status" | grep queue

# Monitor queue via dashboard
open http://localhost:8000/dashboard
```

### Common Error Solutions

**"ModuleNotFoundError"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**"Database connection failed"**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in `.env` file
- Run `python3 test_db_connection.py`

**"AI API Error"**
- Check Grok API key in `.env` file
- Verify internet connection
- Check rate limits

## 🚀 Production Deployment

### Environment Setup
1. **Production Database**: Use managed PostgreSQL
2. **Load Balancer**: nginx reverse proxy
3. **Process Manager**: systemd or supervisor
4. **SSL/TLS**: Let's Encrypt certificates
5. **Monitoring**: Prometheus + Grafana

### Security Checklist
- [ ] Change default SECRET_KEY
- [ ] Use environment-specific API keys
- [ ] Enable database connection pooling
- [ ] Configure proper CORS settings
- [ ] Set up rate limiting
- [ ] Enable request logging
- [ ] Use HTTPS in production

### Scaling Considerations
- **Database**: Connection pooling, read replicas
- **Queue**: Redis for distributed queuing
- **Processing**: Multiple worker instances
- **Storage**: CDN for document delivery
- **Monitoring**: Centralized logging and metrics

## 📞 Support & Monitoring

### Health Endpoints
- `/api/v1/health` - System health check
- `/api/v1/status` - Detailed system status
- `/api/v1/database/status` - Database connection and stats

### Log Files
- `logs/loi_automation.log` - Application logs
- Database query logs - PostgreSQL logs
- Integration logs - Stored in database

### Performance Alerts
- High queue utilization (>80%)
- High error rates (>10%)
- Low AI confidence scores (<0.5)
- Database connection issues
- Integration timeouts

---

## 🎉 Success!

Your LOI Automation System is now ready to process VP Racing fuel supply agreements with:

✅ **Intelligent Priority Management** via Grok AI
✅ **Complete Transaction Tracking** in PostgreSQL  
✅ **Professional Document Generation** with branding
✅ **Automated E-signature Workflow**
✅ **Real-time Performance Dashboard**
✅ **Enterprise-grade Architecture**

**Next Steps:**
1. Configure your CRM, Google Drive, and e-signature credentials
2. Test with a sample LOI request
3. Monitor the dashboard for real-time processing
4. Scale up for production workloads

**Better Day Energy LOI Automation v1.0.0**  
*Streamlining VP Racing fuel supply agreement processing*