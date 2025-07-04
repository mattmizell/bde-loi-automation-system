# Comprehensive Test Cases for LOI Automation System
**Version:** 1.0  
**Last Updated:** July 4, 2025

## Test Case Overview

### Test Data Constants
```
COMPANY: "Claude's Test Gas Station LLC"
CONTACT: "Claude Test Manager"
EMAIL: "transaction.coordinator.agent@gmail.com"
PHONE: "(555) 123-TEST"
ADDRESS: "123 Test Station Drive"
CITY: "St. Louis"
STATE: "MO"
ZIP: "63101"
```

## Test Cases

### TC-001: Customer Setup Sales Initiation
**Objective:** Verify sales team can initiate customer setup process  
**URL:** `/customer-setup/initiate`  
**Steps:**
1. Navigate to sales initiation form
2. Fill in:
   - Legal Business Name: "Claude's Test Gas Station LLC"
   - Primary Contact Name: "Claude Test Manager"
   - Primary Contact Email: "transaction.coordinator.agent@gmail.com"
   - Primary Contact Phone: "(555) 123-TEST"
   - Notes: "TC-001: Testing customer setup initiation"
3. Click Submit button
4. Wait for response

**Expected Results:**
- Success message displays
- Transaction ID generated
- Email sent to customer
- Form resets for next entry

**Pass Criteria:**
- [ ] Form submits without errors
- [ ] Transaction ID returned
- [ ] Success message contains "successfully"

---

### TC-002: Customer Setup Completion
**Objective:** Verify customer can complete setup form  
**URL:** `/customer_setup_form.html`  
**Prerequisites:** TC-001 completed (need transaction ID)  
**Steps:**
1. Navigate to customer setup form
2. Complete Step 1 - Business Information:
   - Legal Business Name: "Claude's Test Gas Station LLC"
   - Business Type: "LLC"
   - Federal Tax ID: "12-3456789"
   - Years in Business: "5"
3. Click Next to Step 2 - Contact Details:
   - Primary Contact Name: "Claude Test Manager"
   - Title: "General Manager"
   - Phone: "(555) 123-TEST"
   - Email: "transaction.coordinator.agent@gmail.com"
   - AP Contact Name: "Claude Accounting"
   - AP Phone: "(555) 123-ACCT"
   - AP Email: "accounting@claudesgas.com"
4. Click Next to Step 3 - Location & Equipment:
   - Physical Address: "123 Test Station Drive"
   - City: "St. Louis"
   - State: "MO"
   - ZIP: "63101"
   - Check "Same as physical address"
   - Annual Fuel Volume: "600000"
   - Number of Dispensers: "8"
   - Number of Tanks: "3"
5. Click Next to Step 4 - Financial References:
   - Add Bank Reference:
     - Bank Name: "First National Test Bank"
     - Contact: "John Banker"
     - Phone: "(555) 123-BANK"
   - Add Trade Reference:
     - Company: "Test Fuel Distributors"
     - Contact: "Jane Supplier"
     - Phone: "(555) 123-FUEL"
6. Click Next to Step 5 - Authorization:
   - Read authorization text
   - NO SIGNATURE REQUIRED
   - Click Submit

**Expected Results:**
- Form progresses through all 5 steps
- Data persists between steps
- Final submission successful
- Customer record created in database

**Pass Criteria:**
- [ ] All 5 steps complete successfully
- [ ] Form submission without signature
- [ ] Success confirmation displayed

---

### TC-003: EFT Sales Initiation
**Objective:** Verify sales can initiate EFT authorization  
**URL:** `/eft/initiate`  
**Steps:**
1. Navigate to EFT sales initiation
2. Fill in:
   - Company Name: "Claude's Test Gas Station LLC"
   - Customer Email: "transaction.coordinator.agent@gmail.com"
   - Bank Name: "First National Test Bank"
   - Account Type: "Business Checking"
   - Routing Number: "021000021"
   - Account Number: "123456789012"
   - Notes: "TC-003: Testing EFT initiation"
3. Click Submit

**Expected Results:**
- Success message
- Transaction ID generated
- Email sent to customer for completion

**Pass Criteria:**
- [ ] Form submits successfully
- [ ] Transaction ID returned
- [ ] Routing email triggered

---

### TC-004: EFT Customer Completion with Signature
**Objective:** Verify EFT completion and ESIGN compliance  
**URL:** `/eft_form.html`  
**Prerequisites:** TC-003 completed  
**Steps:**
1. Navigate to EFT form
2. Search for existing customer (if CRM enabled)
3. Fill/verify fields:
   - Company Information (pre-filled from TC-003)
   - Bank Account Details (pre-filled)
   - Authorization amount: "$50000"
   - Frequency: "Monthly"
4. Review Authorization Agreement
5. Check for ESIGN compliance section
6. Check consent checkbox (if present)
7. Draw signature on pad
8. Click Submit

**Expected Results:**
- Form displays pre-filled data
- ESIGN disclosure visible
- Consent checkbox required
- Signature pad functional
- Submission successful

**Pass Criteria:**
- [ ] Pre-filled data loads correctly
- [ ] ESIGN compliance section present
- [ ] Signature captured
- [ ] Form submits successfully

---

### TC-005: P66 LOI Direct Submission
**Objective:** Verify P66 LOI form submission  
**URL:** `/p66_loi_form.html`  
**Steps:**
1. Navigate to P66 LOI form
2. Fill Station Information:
   - Station Name: "Claude's Phillips 66"
   - Station Address: "123 Test Station Drive"
   - City: "St. Louis"
   - State: "MO"
   - ZIP: "63101"
3. Fill Fuel Volume:
   - Monthly Gasoline: "50000"
   - Monthly Diesel: "20000"
   - Current Brand: "Independent"
   - Brand Expiration: "12/31/2025"
4. Fill Contract Details:
   - Contract Start Date: "08/01/2025"
   - Contract Term: "10" years
   - Volume Incentive: "25000"
   - Image Funding: "15000"
   - Equipment Funding: "10000"
5. Check equipment needs:
   - [x] Canopy Replacement
   - [x] Dispenser Replacement
6. Fill Additional Info:
   - Special Requirements: "TC-005: Testing P66 submission"
7. Fill Contact Info:
   - Authorized Representative: "Claude Test Manager"
   - Title: "General Manager"
   - Email: "transaction.coordinator.agent@gmail.com"
   - Phone: "(555) 123-TEST"
8. Click "Route LOI for Signature"

**Expected Results:**
- Total calculations update automatically
- Form validates all required fields
- Submission successful
- Transaction ID generated
- Email sent for signature

**Pass Criteria:**
- [ ] Auto-calculations work
- [ ] Form validation works
- [ ] Submission successful
- [ ] Transaction ID returned

---

### TC-006: P66 LOI Signature Flow
**Objective:** Verify signature process with ESIGN compliance  
**URL:** `/api/v1/loi/sign/{transaction_id}`  
**Prerequisites:** TC-005 completed  
**Steps:**
1. Navigate to signature URL from TC-005
2. Verify document displays correctly:
   - Station information
   - Contract terms
   - Financial incentives
3. Check for ESIGN compliance section:
   - Legal disclosure
   - System requirements
   - Paper copy option
   - Consent checkbox
4. Check "I consent to electronic signatures"
5. Draw signature on pad
6. Click "Complete Signature"

**Expected Results:**
- Document displays all P66 data
- ESIGN disclosure prominent
- Consent required before signing
- Signature captured
- Success confirmation

**Pass Criteria:**
- [ ] Document data accurate
- [ ] ESIGN consent required
- [ ] Signature captured
- [ ] Submission successful

---

### TC-007: VP Racing LOI Direct Submission
**Objective:** Verify VP Racing LOI submission  
**URL:** `/forms/vp-racing-loi`  
**Steps:**
1. Navigate to VP Racing LOI form
2. Fill Station Information:
   - Station Name: "Claude's VP Racing"
   - Station Address: "123 Test Station Drive"
   - City: "St. Louis"
   - State: "MO"
   - ZIP: "63101"
3. Fill Fuel Volume:
   - Monthly Gasoline: "40000"
   - Monthly Diesel: "15000"
   - Current Brand: "Shell"
4. Fill Contact Info:
   - Contact Name: "Claude Test Manager"
   - Title: "General Manager"
   - Email: "transaction.coordinator.agent@gmail.com"
   - Phone: "(555) 123-TEST"
5. Additional Info:
   - Comments: "TC-007: Testing VP Racing submission"
6. Click Submit

**Expected Results:**
- Form validates
- Submission successful
- Transaction ID generated
- Signature email sent

**Pass Criteria:**
- [ ] Form submits successfully
- [ ] Transaction ID returned
- [ ] Email triggered

---

### TC-008: VP Racing LOI Signature Flow
**Objective:** Verify VP Racing signature with ESIGN  
**URL:** `/api/v1/loi/sign/{transaction_id}`  
**Prerequisites:** TC-007 completed  
**Steps:**
1. Navigate to signature URL from TC-007
2. Verify VP Racing branding/colors
3. Check document content
4. Verify ESIGN compliance
5. Check consent checkbox
6. Sign and submit

**Expected Results:**
- VP Racing specific styling
- ESIGN compliance active
- Signature successful

**Pass Criteria:**
- [ ] Correct branding displayed
- [ ] ESIGN compliance works
- [ ] Signature completes

---

### TC-009: Paper Copy Request
**Objective:** Verify paper copy request per ESIGN Act  
**URL:** `/api/v1/paper-copy/form`  
**Steps:**
1. Navigate to paper copy form
2. Fill fields:
   - Transaction ID: Use from any previous test
   - Your Name: "Claude Test Manager"
   - Email: "transaction.coordinator.agent@gmail.com"
   - Document Type: "Phillips 66 Letter of Intent"
   - Reason: "TC-009: Testing paper copy request"
3. Submit form

**Expected Results:**
- Form submits successfully
- Confirmation message
- Admin notification sent
- Customer confirmation sent

**Pass Criteria:**
- [ ] Form submission works
- [ ] Success message displayed
- [ ] Estimated delivery time shown

---

### TC-010: Database Verification
**Objective:** Verify all data captured correctly  
**Steps:**
1. Query customers table for test customer
2. Query p66_loi_form_data for P66 submission
3. Query eft_form_data for EFT submission
4. Query loi_transactions for all transactions
5. Query electronic_signatures for signature data
6. Verify ESIGN compliance data in compliance_flags

**Expected Results:**
- Customer record exists with correct data
- All form submissions stored
- Transaction records present
- Signatures with ESIGN data
- Compliance flags populated

**Pass Criteria:**
- [ ] Customer data accurate
- [ ] Form data complete
- [ ] Transactions tracked
- [ ] Signatures stored
- [ ] ESIGN data captured

## Test Execution Log

### Run 1: Discovery Run
**Date:** ___________  
**Tester:** Automated Browser Tests  
**Environment:** Production (Render)  

| Test Case | Status | Issues Found | Notes |
|-----------|--------|--------------|-------|
| TC-001 | | | |
| TC-002 | | | |
| TC-003 | | | |
| TC-004 | | | |
| TC-005 | | | |
| TC-006 | | | |
| TC-007 | | | |
| TC-008 | | | |
| TC-009 | | | |
| TC-010 | | | |

### Run 2: Post-Fix Validation
**Date:** ___________  
**Fixes Applied:** ___________  

| Test Case | Status | Issues Found | Notes |
|-----------|--------|--------------|-------|
| TC-001 | | | |
| TC-002 | | | |
| TC-003 | | | |
| TC-004 | | | |
| TC-005 | | | |
| TC-006 | | | |
| TC-007 | | | |
| TC-008 | | | |
| TC-009 | | | |
| TC-010 | | | |

### Run 3: Final Validation
**Date:** ___________  
**Target:** 100% Pass Rate  

| Test Case | Status | Issues Found | Notes |
|-----------|--------|--------------|-------|
| TC-001 | | | |
| TC-002 | | | |
| TC-003 | | | |
| TC-004 | | | |
| TC-005 | | | |
| TC-006 | | | |
| TC-007 | | | |
| TC-008 | | | |
| TC-009 | | | |
| TC-010 | | | |

## Success Criteria
- All test cases pass without errors
- All forms submit successfully
- All data captured in database
- ESIGN compliance on all signature forms
- No critical issues remaining