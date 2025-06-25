-- Migration to add support for multiple form types in the signature system
-- Run this script to update your database schema

-- Add form_type column to signature_requests table
ALTER TABLE signature_requests 
ADD COLUMN IF NOT EXISTS form_type VARCHAR(50) DEFAULT 'vp_racing_loi';

-- Add form_data column to store form-specific data as JSON
ALTER TABLE signature_requests 
ADD COLUMN IF NOT EXISTS form_data JSONB;

-- Create index on form_type for better query performance
CREATE INDEX IF NOT EXISTS idx_signature_requests_form_type 
ON signature_requests(form_type);

-- Update existing records to have the correct form_type
UPDATE signature_requests 
SET form_type = 'vp_racing_loi' 
WHERE form_type IS NULL;

-- Create a table to track available form types
CREATE TABLE IF NOT EXISTS form_types (
    id SERIAL PRIMARY KEY,
    form_type_code VARCHAR(50) UNIQUE NOT NULL,
    form_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert the available form types
INSERT INTO form_types (form_type_code, form_name, description) VALUES
('vp_racing_loi', 'VP Racing LOI', 'Letter of Intent for VP Racing fuel supply agreement'),
('p66_loi', 'Phillips 66 LOI', 'Letter of Intent for Phillips 66 fuel supply agreement'),
('eft_form', 'EFT Setup Form', 'Electronic Funds Transfer authorization form'),
('customer_setup', 'Customer Setup Document', 'Comprehensive customer onboarding form')
ON CONFLICT (form_type_code) DO NOTHING;

-- Add form_type to the audit log for tracking
ALTER TABLE signature_audit_log 
ADD COLUMN IF NOT EXISTS form_type VARCHAR(50);