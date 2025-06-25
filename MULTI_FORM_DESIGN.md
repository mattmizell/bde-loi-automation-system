# Multi-Form Signature Routing Design

## Current Forms Available

1. **VP Racing LOI** (Currently Implemented)
   - Letter of Intent for VP Racing Fuel Supply Agreement
   - Dynamic fields: volumes, incentives, contract terms

2. **Better Day EFT Form** (New)
   - Electronic Funds Transfer authorization
   - For setting up automatic payments
   - Fields needed: Bank info, account details, authorization

3. **Better Day Energy Customer Setup Document** (New)
   - Comprehensive customer onboarding form
   - Business information, contact details, service requirements
   
4. **P66 Letter of Intent** (New)
   - Phillips 66 specific LOI
   - Different terms and branding than VP Racing

## Proposed UI Design

### Home Page Update
```
Better Day Energy - Document Signature System

Select Document Type:
┌─────────────────────┐ ┌─────────────────────┐
│   VP Racing LOI     │ │    Phillips 66      │
│                     │ │       LOI           │
│  [Fuel Supply]      │ │  [Fuel Supply]      │
│                     │ │                     │
│   ► Create New      │ │   ► Create New      │
└─────────────────────┘ └─────────────────────┘

┌─────────────────────┐ ┌─────────────────────┐
│    EFT Setup        │ │  Customer Setup     │
│                     │ │    Document         │
│ [Bank Authorization]│ │   [Onboarding]      │
│                     │ │                     │
│   ► Create New      │ │   ► Create New      │
└─────────────────────┘ └─────────────────────┘
```

### Form-Specific Workflows

#### 1. VP Racing LOI (Existing)
- Step 1: Customer Search/Select
- Step 2: Customer Info
- Step 3: Deal Terms (volumes, incentives, duration)
- Step 4: Generate & Send

#### 2. EFT Form Workflow
- Step 1: Customer Search/Select
- Step 2: Bank Information
  - Bank Name
  - Routing Number
  - Account Number
  - Account Type (Checking/Savings)
- Step 3: Authorization Details
  - Authorized Amount/Frequency
  - Start Date
  - Signatory Info
- Step 4: Generate & Send

#### 3. Customer Setup Workflow
- Step 1: Business Information
  - Legal Business Name
  - DBA Name
  - Tax ID
  - Business Type
- Step 2: Contact Information
  - Primary Contact
  - Billing Contact
  - Service Location
- Step 3: Service Requirements
  - Fuel Types
  - Estimated Volumes
  - Special Requirements
- Step 4: Generate & Send

#### 4. P66 LOI Workflow
- Similar to VP Racing but with:
  - Phillips 66 branding
  - Different incentive structures
  - P66-specific terms

## Implementation Approach

### 1. Create Form Templates
- Convert DOCX to HTML templates
- Add dynamic field placeholders
- Style with appropriate branding

### 2. Update Database Schema
```sql
-- Add form_type to track different document types
ALTER TABLE signature_requests ADD COLUMN form_type VARCHAR(50);

-- Add form_data JSONB to store form-specific fields
ALTER TABLE signature_requests ADD COLUMN form_data JSONB;
```

### 3. API Endpoints
```
POST /api/create-document
{
  "form_type": "eft_form|customer_setup|p66_loi|vp_racing_loi",
  "customer_data": {...},
  "form_data": {
    // Form-specific fields
  }
}
```

### 4. Signature Page Updates
- Detect form_type
- Render appropriate template
- Apply correct branding

## Benefits of This Approach

1. **Scalable**: Easy to add new form types
2. **Consistent**: Same signature workflow for all forms
3. **Maintainable**: Form templates separate from logic
4. **User-Friendly**: Clear form selection interface
5. **Trackable**: All documents in one system

## Next Steps

1. Convert DOCX forms to HTML templates
2. Create form selection home page
3. Implement form-specific workflows
4. Update database schema
5. Test with each form type