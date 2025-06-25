-- ESIGN Act Compliance Database Migration
-- Run this script on production database to support new compliance features

-- Add signed_at_string column for integrity verification fix
ALTER TABLE electronic_signatures 
ADD COLUMN IF NOT EXISTS signed_at_string VARCHAR(50);

-- Create comment explaining the column
COMMENT ON COLUMN electronic_signatures.signed_at_string IS 
'ISO timestamp string used for integrity hash verification - ensures exact match between stored and verified timestamps';

-- Update existing records to populate signed_at_string from signed_at
UPDATE electronic_signatures 
SET signed_at_string = signed_at::text 
WHERE signed_at_string IS NULL AND signed_at IS NOT NULL;

-- Migration complete message
-- The following features are now supported:
-- 1. ESIGN Act compliance tracking
-- 2. Consumer consent validation
-- 3. Paper copy request handling
-- 4. Enhanced integrity verification
-- 5. Real-time compliance verification