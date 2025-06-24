# LOI Automation System

**Better Day Energy - Letter of Intent Automation for VP Racing Supply Agreements**

An automated system that generates customized Letters of Intent (LOI) for VP Racing Branded Supply Agreements by integrating Less Annoying CRM form data with standardized templates, facilitating electronic signature collection, and managing the complete workflow.

## 🏗️ Architecture Overview

The system is built using the **Transaction Coordinator Pattern** with the following components:

### Core Components
- **LOI Transaction Coordinator**: Main orchestration engine managing the complete workflow
- **Transaction Queue**: Priority-based queue system for processing LOI requests
- **Integration Handlers**: Modular handlers for CRM, Google Drive, e-signature, and email services
- **Document Generator**: PDF template engine with field mapping capabilities
- **Workflow Management**: Status tracking, notifications, and completion monitoring

### Integration Points
- **Less Annoying CRM**: Form data retrieval and customer information
- **Google Drive**: Document storage and management
- **E-Signature Services**: DocuSign, Sign.com, or Adobe Sign integration
- **Email Notifications**: SMTP-based notification system

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Google Drive API credentials
- Less Annoying CRM API access
- E-signature service API key (Sign.com, DocuSign, or Adobe Sign)
- SMTP email configuration

### Installation

1. **Clone/Copy the project**
```bash
cd loi_automation_system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the system**
```bash
# Create configuration file
python -c "from config.settings import Settings; Settings().create_sample_config_file()"

# Edit the configuration
nano config/loi_config.yaml
```

4. **Set environment variables**
```bash
# Copy the sample environment file
cp .env.example .env

# Edit environment variables
nano .env
```

5. **Initialize templates directory**
```bash
mkdir -p templates
```

6. **Run the system**
```bash
python main.py
```

The system will be available at:
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard
- **Documentation**: http://localhost:8000/docs

## 📋 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# CRM Configuration
CRM_API_USER=your_crm_user
CRM_API_TOKEN=your_crm_token

# Google Drive Configuration  
GOOGLE_DRIVE_CREDENTIALS=google_drive_credentials.json
GOOGLE_DRIVE_ROOT_FOLDER_ID=optional_root_folder_id

# E-Signature Configuration
ESIGNATURE_PROVIDER=sign.com  # or docusign, adobe_sign
ESIGNATURE_API_KEY=your_esignature_api_key
ESIGNATURE_API_SECRET=your_esignature_api_secret

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# Database Configuration
DATABASE_URL=sqlite:///loi_automation.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Security Configuration
SECRET_KEY=your_secret_key_here
API_KEYS=api_key_1,api_key_2

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/loi_automation.log
```

### Configuration File

The system uses a YAML configuration file (`config/loi_config.yaml`) for detailed settings:

```yaml
crm:
  api_user: your_crm_user
  api_token: your_crm_token
  base_url: https://api.lessannoyingcrm.com
  timeout: 30
  max_retries: 3

google_drive:
  credentials_file: google_drive_credentials.json
  root_folder_id: null
  folder_structure:
    pending_signature: "LOI Documents - Pending Signature"
    completed: "LOI Documents - Completed"
    failed: "LOI Documents - Failed"
    templates: "LOI Templates"
    archive: "LOI Archive"

esignature:
  provider: sign.com
  api_key: your_esignature_api_key
  api_secret: your_esignature_api_secret
  reminder_frequency_hours: 72
  expiration_days: 14
  max_reminders: 3

coordinator:
  max_queue_size: 5000
  batch_size: 25
  processing_interval: 2.0
  max_concurrent_batches: 3
  document_timeout: 60.0
  signature_timeout: 604800  # 7 days
  retry_attempts: 3
```

## 🔧 API Usage

### Submit LOI Request

```bash
curl -X POST "http://localhost:8000/api/v1/loi/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Example Gas Station",
    "contact_name": "John Smith",
    "contact_title": "Owner",
    "email": "john@example.com",
    "phone": "(555) 123-4567",
    "business_address": {
      "street": "123 Main St",
      "city": "Springfield",
      "state": "MO",
      "zip": "65801"
    },
    "monthly_gasoline_volume": 25000,
    "monthly_diesel_volume": 15000,
    "current_fuel_supplier": "Shell",
    "estimated_conversion_date": "2024-03-01",
    "image_funding_amount": 50000,
    "incentive_funding_amount": 25000,
    "total_estimated_incentives": 75000,
    "canopy_installation_required": true,
    "current_branding_to_remove": "Shell branding",
    "special_requirements_notes": "Need 24/7 fuel delivery",
    "priority": "normal"
  }'
```

### Check LOI Status

```bash
curl "http://localhost:8000/api/v1/loi/{transaction_id}"
```

### List All LOIs

```bash
curl "http://localhost:8000/api/v1/loi/list?limit=50"
```

### System Status

```bash
curl "http://localhost:8000/api/v1/status"
```

## 🔄 Workflow Process

The LOI automation follows this workflow:

1. **LOI Request Received**
   - Customer data validation
   - Priority assignment
   - Queue placement

2. **CRM Data Retrieval**
   - Fetch form data from Less Annoying CRM
   - Data validation and standardization
   - Risk assessment

3. **Document Generation**
   - Template population with customer data
   - PDF creation with branding
   - Quality validation

4. **Google Drive Storage**
   - Upload to organized folder structure
   - Set appropriate permissions
   - Generate shareable links

5. **E-Signature Request**
   - Send document for customer signature
   - Configure reminders and expiration
   - Monitor signature status

6. **Completion & Notification**
   - Move completed documents
   - Send completion notifications
   - Update CRM records

## 📊 Monitoring & Dashboard

### Dashboard Features
- Real-time processing statistics
- Queue utilization metrics
- Workflow stage tracking
- Performance alerts
- Transaction history

### Performance Metrics
- Documents processed per hour
- Average completion time
- Signature conversion rate
- Error rates by stage
- Queue utilization

### Health Monitoring
- System status endpoint: `/api/v1/health`
- Performance alerts for:
  - High queue utilization (>80%)
  - Low conversion rates (<70%)
  - High error rates (>10%)
  - Processing delays

## 🔌 Integration Setup

### Less Annoying CRM
1. Get API credentials from CRM settings
2. Configure user and token in environment variables
3. Map custom fields to LOI template fields

### Google Drive
1. Create Google Cloud project
2. Enable Google Drive API
3. Create service account credentials
4. Download credentials JSON file
5. Share root folder with service account email

### E-Signature Services

#### Sign.com
1. Create Sign.com account
2. Generate API key from developer settings
3. Configure webhook URL for status updates

#### DocuSign
1. Create DocuSign developer account
2. Get API credentials and account ID
3. Configure OAuth for production

#### Adobe Sign
1. Create Adobe Sign account
2. Generate API key from account settings
3. Configure webhook for completion events

## 🛠️ Development

### Project Structure
```
loi_automation_system/
├── core/                    # Core coordination logic
│   ├── loi_coordinator.py
│   └── loi_transaction_queue.py
├── handlers/                # Business logic handlers
│   └── document_generator.py
├── integrations/           # External service integrations
│   ├── crm_integration.py
│   ├── google_drive_integration.py
│   └── esignature_integration.py
├── config/                 # Configuration management
│   └── settings.py
├── templates/              # Document templates
├── logs/                   # Application logs
├── tests/                  # Unit and integration tests
├── main.py                 # FastAPI application
└── requirements.txt        # Python dependencies
```

### Key Design Patterns
- **Transaction Coordinator Pattern**: Central orchestration
- **Handler Registry**: Pluggable integration handlers
- **Event-Driven Architecture**: Callbacks for workflow events
- **Priority Queue Processing**: Efficient transaction management
- **Async/Await**: High-performance concurrent processing

### Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=loi_automation_system tests/

# Run integration tests
pytest tests/integration/
```

## 🚨 Troubleshooting

### Common Issues

**Queue Backlog**
- Monitor queue utilization in dashboard
- Increase batch size or concurrent batches
- Check for integration API rate limits

**Document Generation Failures**
- Verify template file exists
- Check customer data completeness
- Review field mapping configuration

**E-Signature Issues**
- Validate API credentials
- Check webhook configuration
- Monitor signature expiration settings

**Google Drive Errors**
- Verify service account permissions
- Check folder structure exists
- Validate credentials file path

### Logs
- Application logs: `logs/loi_automation.log`
- Error tracking in dashboard
- Integration-specific error details in API responses

## 📈 Scaling & Production

### Performance Tuning
- Increase queue size for high volume
- Adjust batch processing settings
- Configure multiple worker processes
- Use Redis for distributed queuing

### Production Deployment
- Use production database (PostgreSQL)
- Configure reverse proxy (nginx)
- Set up monitoring and alerting
- Implement backup strategies
- Use environment-specific configurations

### Security Considerations
- Secure API key storage
- Enable HTTPS in production
- Configure proper CORS settings
- Implement rate limiting
- Regular security updates

## 📝 License

This LOI Automation System is proprietary software developed for Better Day Energy.

## 🤝 Support

For technical support or questions:
- Internal documentation: `/docs` endpoint
- System status: `/api/v1/status`
- Dashboard monitoring: `/dashboard`

---

**Better Day Energy LOI Automation System v1.0.0**  
*Streamlining VP Racing fuel supply agreement processing*# bde-loi-automation-system
