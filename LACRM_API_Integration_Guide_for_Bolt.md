# Less Annoying CRM (LACRM) API Integration Guide for Bolt.net

## CRITICAL: API Response Format Issue
**⚠️ LACRM returns JSON data with `content-type: text/html` instead of `application/json`**

This causes most HTTP libraries to fail JSON parsing. You MUST manually parse the response:

```javascript
// DON'T rely on automatic JSON parsing
const response = await fetch(apiUrl + '?' + params);
const jsonData = JSON.parse(response.text()); // Manual parsing required

// Python example:
import json
response = requests.get(crm_url, params=params)
result_data = json.loads(response.text)  # Manual parsing required
```

## API Configuration
```javascript
const API_KEY = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W";
const api_parts = API_KEY.split('-', 1);
const USER_CODE = api_parts[0]; // "1073223"
const CRM_URL = "https://api.lessannoyingcrm.com";
```

## CRITICAL: Pagination Limitation
**⚠️ LACRM limits ALL responses to 25 records per page, regardless of MaxNumberOfResults parameter**

To get all 500+ contacts, you MUST paginate:

```javascript
async function getAllContacts() {
    const allContacts = [];
    let page = 1;
    let hasMoreResults = true;
    
    while (hasMoreResults) {
        const params = new URLSearchParams({
            'APIToken': API_KEY,
            'UserCode': USER_CODE,
            'Function': 'SearchContacts',
            'SearchTerm': '', // Empty = get all
            'MaxNumberOfResults': 10000, // Will be ignored, always returns max 25
            'Page': page
        });
        
        try {
            const response = await fetch(`${CRM_URL}?${params}`);
            
            // CRITICAL: Manual JSON parsing required
            const result = JSON.parse(await response.text());
            
            if (!result.Success) {
                console.error('API Error:', result.Error);
                break;
            }
            
            const contacts = result.Result || [];
            
            // If we get 0 contacts, we've reached the end
            if (contacts.length === 0) {
                hasMoreResults = false;
                break;
            }
            
            allContacts.push(...contacts);
            console.log(`Page ${page}: Retrieved ${contacts.length} contacts (Total: ${allContacts.length})`);
            
            page++;
            
            // Safety limit to prevent infinite loops
            if (page > 50) {
                console.warn('Safety limit reached - stopping pagination');
                break;
            }
            
        } catch (error) {
            console.error(`Page ${page} failed:`, error);
            break;
        }
    }
    
    return allContacts;
}
```

## LACRM Data Structure (Very Important!)
LACRM uses a unique data format for contact fields:

```javascript
// Example contact from LACRM API:
{
    "ContactId": "12345",
    "CompanyName": "Better Day Energy",
    "Name": "John Smith",
    
    // Email is an ARRAY of objects with Text field
    "Email": [
        {
            "Text": "john@example.com (Work)",
            "Type": "Work"
        }
    ],
    
    // Phone is an ARRAY of objects with Text field
    "Phone": [
        {
            "Text": "555-123-4567 (Work)", 
            "Type": "Work"
        }
    ],
    
    // Address is an ARRAY of objects with structured fields
    "Address": [
        {
            "Street": "123 Main St",
            "City": "Springfield", 
            "State": "IL",
            "Zip": "62701",
            "Type": "Work"
        }
    ],
    
    "BackgroundInfo": "Additional notes",
    "Industry": "Energy",
    "Website": "https://example.com",
    "CreationDate": "2025-01-15T10:30:00",
    "EditedDate": "2025-01-20T14:22:00",
    "AssignedTo": "Matt Mizell"
}
```

## Data Extraction Helper Functions
```javascript
function extractEmail(contact) {
    const emailRaw = contact.Email;
    if (Array.isArray(emailRaw) && emailRaw.length > 0) {
        const firstEmail = emailRaw[0];
        if (firstEmail && firstEmail.Text) {
            // Remove "(Work)" suffix if present
            return firstEmail.Text.split(' (')[0];
        }
    }
    return '';
}

function extractPhone(contact) {
    const phoneRaw = contact.Phone;
    if (Array.isArray(phoneRaw) && phoneRaw.length > 0) {
        const firstPhone = phoneRaw[0];
        if (firstPhone && firstPhone.Text) {
            // Remove "(Work)" suffix if present
            return firstPhone.Text.split(' (')[0];
        }
    }
    return '';
}

function extractAddress(contact) {
    const addressRaw = contact.Address;
    if (Array.isArray(addressRaw) && addressRaw.length > 0) {
        const firstAddress = addressRaw[0];
        if (firstAddress) {
            const parts = [
                firstAddress.Street,
                firstAddress.City,
                firstAddress.State,
                firstAddress.Zip
            ].filter(part => part && part.trim());
            return parts.join(', ');
        }
    }
    return '';
}

// Usage:
function processContact(contact) {
    return {
        id: contact.ContactId,
        name: contact.Name || contact.CompanyName || 'Unknown',
        company: contact.CompanyName || '',
        email: extractEmail(contact),
        phone: extractPhone(contact),
        address: extractAddress(contact),
        notes: contact.BackgroundInfo || '',
        industry: contact.Industry || '',
        website: contact.Website || '',
        created: contact.CreationDate,
        modified: contact.EditedDate,
        assignedTo: contact.AssignedTo || ''
    };
}
```

## Available API Functions
```javascript
// Search contacts (use this for getting all contacts)
{
    'Function': 'SearchContacts',
    'SearchTerm': 'search_term_here', // Empty string gets all
    'MaxNumberOfResults': 25, // Always limited to 25 regardless of value
    'Page': 1 // Required for pagination
}

// Create new contact
{
    'Function': 'CreateContact',
    'Name': 'John Smith',
    'CompanyName': 'Better Day Energy',
    'Email': 'john@example.com',
    'Phone': '555-123-4567',
    'Address': '123 Main St, Springfield, IL 62701',
    'Notes': 'Additional information'
}

// Update existing contact
{
    'Function': 'UpdateContact',
    'ContactId': '12345',
    'CompanyName': 'Updated Company Name',
    'Notes': 'Updated notes'
}

// Create note for contact
{
    'Function': 'CreateNote',
    'ContactId': '12345',
    'Note': 'Follow-up call scheduled'
}
```

## Complete Working Example
```javascript
class LACRMIntegration {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.userCode = apiKey.split('-')[0];
        this.baseUrl = 'https://api.lessannoyingcrm.com';
    }
    
    async makeApiCall(params) {
        const urlParams = new URLSearchParams({
            'APIToken': this.apiKey,
            'UserCode': this.userCode,
            ...params
        });
        
        try {
            const response = await fetch(`${this.baseUrl}?${urlParams}`);
            
            // CRITICAL: Manual JSON parsing
            const result = JSON.parse(await response.text());
            
            if (!result.Success) {
                throw new Error(`LACRM API Error: ${result.Error}`);
            }
            
            return result.Result;
            
        } catch (error) {
            console.error('LACRM API call failed:', error);
            throw error;
        }
    }
    
    async getAllContacts() {
        const allContacts = [];
        let page = 1;
        
        while (true) {
            const contacts = await this.makeApiCall({
                'Function': 'SearchContacts',
                'SearchTerm': '',
                'MaxNumberOfResults': 10000, // Will be ignored
                'Page': page
            });
            
            if (!contacts || contacts.length === 0) {
                break; // No more results
            }
            
            allContacts.push(...contacts);
            console.log(`Retrieved page ${page}: ${contacts.length} contacts (Total: ${allContacts.length})`);
            
            page++;
            
            if (page > 50) break; // Safety limit
        }
        
        return allContacts;
    }
    
    async createContact(contactData) {
        return await this.makeApiCall({
            'Function': 'CreateContact',
            'Name': contactData.name || '',
            'CompanyName': contactData.company || '',
            'Email': contactData.email || '',
            'Phone': contactData.phone || '',
            'Address': contactData.address || '',
            'Notes': contactData.notes || ''
        });
    }
    
    async searchContacts(searchTerm) {
        const allResults = [];
        let page = 1;
        
        while (true) {
            const results = await this.makeApiCall({
                'Function': 'SearchContacts',
                'SearchTerm': searchTerm,
                'MaxNumberOfResults': 10000,
                'Page': page
            });
            
            if (!results || results.length === 0) break;
            
            allResults.push(...results);
            page++;
            
            if (page > 20) break; // Reasonable limit for searches
        }
        
        return allResults;
    }
}

// Usage:
const lacrm = new LACRMIntegration("1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W");

// Get all contacts (will retrieve all 500+)
const allContacts = await lacrm.getAllContacts();
console.log(`Total contacts retrieved: ${allContacts.length}`);

// Create new contact
const newContact = await lacrm.createContact({
    name: 'Test Contact',
    company: 'Test Company',
    email: 'test@example.com',
    phone: '555-TEST-123',
    address: '123 Test St, Test City, TS 12345',
    notes: 'Created via API integration'
});
```

## Key Troubleshooting Points

1. **JSON Parsing**: Always use `JSON.parse(response.text())` - never rely on automatic parsing
2. **Pagination**: Expect exactly 25 results per page, plan accordingly  
3. **Data Structure**: Email/Phone/Address are arrays of objects with Text fields
4. **Rate Limiting**: Add delays between requests if you hit rate limits
5. **Error Handling**: Check `result.Success` before accessing `result.Result`
6. **Field Mapping**: LACRM uses specific field names (CompanyName, not Company)

## Common Errors and Solutions

**"Unexpected token" or JSON parsing errors**
- Solution: Use manual JSON parsing, don't rely on content-type

**Only getting 25 contacts when expecting 500+**  
- Solution: Implement proper pagination loop

**Email/Phone showing as "[object Object]"**
- Solution: Extract .Text field from array elements

**Company names not saving**
- Solution: Use 'CompanyName' parameter, not 'Company'

**API calls timing out**
- Solution: Add proper timeout handling and retry logic

This guide contains all the hard-learned lessons from integrating with LACRM API. The key is handling the unique response format and pagination correctly.