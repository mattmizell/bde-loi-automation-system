# LOI Automation System - Deployment Instructions

## 🚀 Quick Deploy to Render

**GitHub Credentials Found:**
- **User**: mattmizell
- **Token**: [REDACTED - Use environment variable]
- **Email**: mattmizell@gmail.com

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `bde-loi-automation-system`
3. Description: `Better Day Energy LOI Automation with PostgreSQL and CRM Integration`
4. Make it Public
5. **Don't** initialize with README, .gitignore, or license
6. Click "Create repository"

## Step 2: Upload Files to GitHub

### Option A: Use GitHub Web Interface
1. On the new repository page, click "uploading an existing file"
2. Drag and drop ALL files from this directory
3. Commit message: `Initial commit: Complete LOI signature system`
4. Click "Commit changes"

### Option B: Use Git Commands (if git becomes available)
```bash
git init
git add .
git commit -m "Initial commit: Complete LOI signature system"
git remote add origin https://github.com/mattmizell/bde-loi-automation-system.git
git push -u origin main
```

## Step 3: Deploy to Render

1. Go to https://render.com
2. Sign in with GitHub account (mattmizell)
3. Click "New +" → "Web Service"
4. Connect the `bde-loi-automation-system` repository
5. Render will detect the `render.yaml` file automatically

## Step 4: Configure Environment Variables

In Render dashboard, add these environment variables:

**Required Variables:**
```
CRM_API_KEY=[SET_IN_RENDER_DASHBOARD]
SMTP_USERNAME=transaction.coordinator.agent@gmail.com
SMTP_PASSWORD=[SET_IN_RENDER_DASHBOARD]
SIGNATURE_SECRET_KEY=(auto-generated by Render)
API_BASE_URL=https://loi-automation-api.onrender.com
ALLOWED_ORIGINS=https://loi-signature-service.onrender.com
SSL_REDIRECT=true
```

**Auto-Configured by Render:**
- `DATABASE_URL` (PostgreSQL connection)
- `PORT` (service port)

## Step 5: Verify Deployment

After deployment, you'll have:

1. **Main API Service**: https://loi-automation-api.onrender.com
2. **Signature Service**: https://loi-signature-service.onrender.com  
3. **PostgreSQL Database**: Automatically provisioned

## 📄 Files Ready for Deployment

**Core Application Files:**
- `integrated_pdf_signature_server.py` - Main signature server
- `signature_storage.py` - PostgreSQL tamper-evident storage
- `html_to_pdf_generator.py` - PDF generation system
- `render.yaml` - Render deployment configuration
- `requirements.txt` - Python dependencies

**Supporting Files:**
- `generate_new_loi.py` - LOI generation utility
- `send_signature_email.py` - Email notification system
- `check_crm_record.py` - CRM verification utility
- `DEPLOYMENT.md` - Production deployment guide

**Test Files:**
- `test_signed_loi.html` - Sample PDF output
- `signature_request_data.json` - Test signature data

## 🔧 Production Configuration

**Security Features:**
- SSL/HTTPS enforcement
- CSRF protection tokens
- PostgreSQL tamper-evident storage
- Cryptographic integrity hashing
- Complete audit trail logging

**CRM Integration:**
- Less Annoying CRM API integration
- Automatic contact record updates
- PDF link storage in customer records
- Complete LOI details and terms

**Email System:**
- Gmail SMTP integration
- Professional HTML email templates
- Signature link generation
- Automated notifications

## 🎯 Post-Deployment Testing

1. **Create test signature request**
2. **Send email notification**  
3. **Complete signature workflow**
4. **Verify PostgreSQL storage**
5. **Check CRM record updates**
6. **Generate PDF document**

## 📞 Support Information

- **GitHub Repository**: https://github.com/mattmizell/bde-loi-automation-system
- **Render Dashboard**: https://dashboard.render.com
- **CRM API**: Less Annoying CRM integration active
- **Email Service**: Gmail SMTP configured

## ✅ Success Criteria

- [ ] Repository uploaded to GitHub
- [ ] Render services deployed successfully  
- [ ] PostgreSQL database connected
- [ ] CRM integration functional
- [ ] Email notifications sending
- [ ] PDF generation working
- [ ] Complete signature workflow tested

Ready for production use with enterprise-grade security and compliance!