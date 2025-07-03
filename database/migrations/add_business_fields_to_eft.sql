-- Migration: Add business address and contact fields to eft_form_data table
-- Date: 2025-07-03
-- Description: Add missing business address and contact fields for data rationalization

-- Add business address columns
ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS company_address VARCHAR(500);

ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS company_city VARCHAR(100);

ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS company_state VARCHAR(50);

ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS company_zip VARCHAR(20);

-- Add contact information columns
ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255);

ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);

ALTER TABLE eft_form_data 
ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_eft_company_address ON eft_form_data(company_address);
CREATE INDEX IF NOT EXISTS idx_eft_contact_email ON eft_form_data(contact_email);

-- Add comments to document changes
COMMENT ON COLUMN eft_form_data.company_address IS 'Business address for rationalization with customer setup';
COMMENT ON COLUMN eft_form_data.company_city IS 'Business city for rationalization with customer setup';
COMMENT ON COLUMN eft_form_data.company_state IS 'Business state for rationalization with customer setup';
COMMENT ON COLUMN eft_form_data.company_zip IS 'Business ZIP code for rationalization with customer setup';
COMMENT ON COLUMN eft_form_data.contact_name IS 'Primary contact name for rationalization with customer setup';
COMMENT ON COLUMN eft_form_data.contact_email IS 'Primary contact email for rationalization with customer setup';
COMMENT ON COLUMN eft_form_data.contact_phone IS 'Primary contact phone for rationalization with customer setup';