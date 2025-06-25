# LACRM API Integration Documentation

## Critical Issues Discovered and Fixed

### 1. API Response Format Issue (MOST IMPORTANT)
⚠️ **LACRM returns JSON data with content-type: text/html instead of application/json**

This breaks automatic JSON parsing in most libraries. You MUST manually parse:

```python
# DON'T do this (will fail):
data = response.json()

# DO this instead:
response = requests.post(url, data=params)  # Note: use data=, not json=
data = json.loads(response.text)  # Manual parsing required
```

### 2. API Authentication Format
```python
API_KEY = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
USER_CODE = API_KEY.split('-')[0]  # "1073223"

# Correct format:
params = {
    'APIToken': API_KEY,  # NOT 'Password'
    'UserCode': USER_CODE,  # NOT 'BDE_CRM_BRIDGE' or other custom values
    'Function': 'GetUser'
}
```

### 3. Pagination Limitation (CRITICAL)
⚠️ **LACRM always returns maximum 25 records per page, regardless of MaxNumberOfResults parameter**

To get all 500+ contacts, you must loop through pages:

```python
def get_all_contacts():
    all_contacts = []
    page = 1
    
    while True:
        params = {
            'APIToken': API_KEY,
            'UserCode': USER_CODE,
            'Function': 'SearchContacts',
            'SearchTerm': '',  # Empty = all contacts
            'Page': page
        }
        
        response = requests.post('https://api.lessannoyingcrm.com/v2/', data=params)
        result = json.loads(response.text)  # Manual parsing!
        
        if not result.get('Success') or not result.get('Result') or len(result['Result']) == 0:
            break
            
        all_contacts.extend(result['Result'])
        page += 1
        
        if page > 50:  # Safety limit
            break
            
    return all_contacts
```

### 4. Data Structure Quirks
LACRM uses arrays for Email, Phone, and Address fields:

```python
# Example contact structure:
{
    "ContactId": "12345",
    "CompanyName": "Better Day Energy",
    "Name": "John Smith",
    "Email": [{"Text": "john@example.com (Work)", "Type": "Work"}],
    "Phone": [{"Text": "555-123-4567 (Work)", "Type": "Work"}],
    "Address": [{
        "Street": "123 Main St",
        "City": "Springfield",
        "State": "IL",
        "Zip": "62701"
    }]
}

# Helper functions:
def get_email(contact):
    return contact.get('Email', [{}])[0].get('Text', '').split(' (')[0] or ''

def get_phone(contact):
    return contact.get('Phone', [{}])[0].get('Text', '').split(' (')[0] or ''
```

## Files Modified

### 1. `/bde_crm_bridge_service.py`
- Fixed UserCode extraction from API key
- Changed from `json=params` to `data=params` for requests
- Added proper pagination handling

### 2. `/html_to_pdf_generator.py`
- Added UserCode parsing from API key

### 3. `/services/crm_service/config/settings.py`
- Contains LACRM configuration (already had correct API key)

## Environment Variables Confirmed Working
```
LACRM_API_TOKEN=1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W
DATABASE_URL=postgresql://loi_user:21aNcRNDATESCFdgieGhknBi6InDJ11Sadpg-d1dd5nadbo4c73cmub8g-=/loi_automation
PORT=8002
```

## Current System Status

### Working:
- Main application loads (home page at /)
- Database connection is functional
- LACRM API authentication now works with correct format

### Issues Remaining:
- 502 errors on some endpoints due to unified modular server not starting properly
- Need to implement proper pagination for fetching all contacts
- Need to test full CRM sync functionality

## Testing Commands

### Test LACRM API:
```bash
curl -X POST "https://api.lessannoyingcrm.com/v2/" \
  -d "APIToken=1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W" \
  -d "UserCode=1073223" \
  -d "Function=GetUser"
```

### Test Deployed Service:
```bash
# Home page (should work)
curl https://loi-automation-api.onrender.com/

# CRM contacts (currently 502)
curl https://loi-automation-api.onrender.com/api/get-crm-contacts
```

## Next Steps

1. **Fix Unified Modular Server**: The unified_modular_server.py needs debugging to start properly in production
2. **Implement Pagination**: Update CRM sync to handle 25-record pages
3. **Test Full Workflow**: Verify signature → PDF → CRM storage pipeline
4. **Monitor Logs**: Check Render logs for specific startup errors

## Common Mistakes to Avoid

1. **Never use `response.json()`** - Always use `json.loads(response.text)`
2. **Never use custom UserCode** - Always extract from API key
3. **Never assume all records returned** - Always implement pagination
4. **Never use `json=params`** - Always use `data=params` for LACRM
5. **Never ignore array structures** - Email/Phone/Address are arrays

## Architecture Summary

The system uses a cache-first approach:
- PostgreSQL cache stores all CRM contacts locally
- Background sync keeps cache updated
- API reads from cache for fast response
- Writes go to cache immediately, sync to LACRM in background

This avoids LACRM's slow API and pagination issues for reads while maintaining data consistency.