-- Migration: Add company_name and federal_tax_id to eft_form_data table
-- Date: 2025-07-03
-- Description: Add missing company information fields to EFT form data

-- Add company_name column
ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);

-- Add federal_tax_id column  
ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS federal_tax_id VARCHAR(50);

-- Update existing records to populate company_name from related customer record
UPDATE eft_form_data 
SET company_name = c.company_name
FROM customers c 
WHERE eft_form_data.customer_id = c.id 
AND eft_form_data.company_name IS NULL;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_eft_company_name ON eft_form_data(company_name);
CREATE INDEX IF NOT EXISTS idx_eft_federal_tax_id ON eft_form_data(federal_tax_id);

-- Add comment to document changes
COMMENT ON COLUMN eft_form_data.company_name IS 'Company name from EFT form submission';
COMMENT ON COLUMN eft_form_data.federal_tax_id IS 'Federal Tax ID (EIN) in XX-XXXXXXX format';