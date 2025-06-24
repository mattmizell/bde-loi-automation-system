# BOLT.NET PROMPT: LACRM API Integration

Copy and paste this prompt into Bolt.net to help it successfully integrate with Less Annoying CRM:

---

## PROMPT FOR BOLT.NET:

I need you to integrate with the Less Annoying CRM (LACRM) API. This API has several unique quirks that cause most integrations to fail. Here are the CRITICAL details you must follow exactly:

### 1. API RESPONSE FORMAT ISSUE (MOST IMPORTANT)
⚠️ **LACRM returns JSON data with `content-type: text/html` instead of `application/json`**

This breaks automatic JSON parsing in most libraries. You MUST manually parse:

```javascript
// DON'T do this (will fail):
const data = await response.json();

// DO this instead:
const response = await fetch(url);
const data = JSON.parse(await response.text()); // Manual parsing required
```

### 2. API CREDENTIALS
```javascript
const API_KEY = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W";
const USER_CODE = API_KEY.split('-')[0]; // "1073223"
const BASE_URL = "https://api.lessannoyingcrm.com";
```

### 3. PAGINATION LIMITATION (CRITICAL)
⚠️ **LACRM always returns maximum 25 records per page, regardless of MaxNumberOfResults parameter**

To get all 500+ contacts, you must loop through pages until you get 0 results:

```javascript
let page = 1;
let allContacts = [];

while (true) {
    const params = new URLSearchParams({
        'APIToken': API_KEY,
        'UserCode': USER_CODE,
        'Function': 'SearchContacts',
        'SearchTerm': '', // Empty = all contacts
        'MaxNumberOfResults': 10000, // Ignored, always returns 25 max
        'Page': page
    });
    
    const response = await fetch(`${BASE_URL}?${params}`);
    const result = JSON.parse(await response.text()); // Manual parsing!
    
    if (!result.Success || !result.Result || result.Result.length === 0) {
        break; // No more results
    }
    
    allContacts.push(...result.Result);
    page++;
}
```

### 4. UNIQUE DATA STRUCTURE
LACRM uses arrays for Email, Phone, and Address fields:

```javascript
// Example contact structure:
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

// Helper functions to extract data:
function getEmail(contact) {
    return contact.Email?.[0]?.Text?.split(' (')[0] || '';
}

function getPhone(contact) {
    return contact.Phone?.[0]?.Text?.split(' (')[0] || '';
}

function getAddress(contact) {
    const addr = contact.Address?.[0];
    if (!addr) return '';
    return [addr.Street, addr.City, addr.State, addr.Zip].filter(Boolean).join(', ');
}
```

### 5. COMPLETE WORKING EXAMPLE
Create a component that can:
- Fetch all contacts (handling pagination)
- Display them in a searchable list
- Create new contacts
- Handle the unique data format

```javascript
const LACRMIntegration = {
    apiKey: "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W",
    userCode: "1073223",
    baseUrl: "https://api.lessannoyingcrm.com",
    
    async apiCall(params) {
        const urlParams = new URLSearchParams({
            'APIToken': this.apiKey,
            'UserCode': this.userCode,
            ...params
        });
        
        const response = await fetch(`${this.baseUrl}?${urlParams}`);
        const result = JSON.parse(await response.text()); // CRITICAL: Manual parsing
        
        if (!result.Success) {
            throw new Error(`LACRM Error: ${result.Error}`);
        }
        
        return result.Result;
    },
    
    async getAllContacts() {
        let allContacts = [];
        let page = 1;
        
        while (true) {
            const contacts = await this.apiCall({
                'Function': 'SearchContacts',
                'SearchTerm': '',
                'Page': page
            });
            
            if (!contacts || contacts.length === 0) break;
            
            allContacts.push(...contacts);
            page++;
            
            if (page > 50) break; // Safety limit
        }
        
        return allContacts;
    },
    
    async createContact(data) {
        return await this.apiCall({
            'Function': 'CreateContact',
            'Name': data.name,
            'CompanyName': data.company,
            'Email': data.email,
            'Phone': data.phone,
            'Address': data.address,
            'Notes': data.notes
        });
    }
};
```

### 6. REQUIREMENTS FOR YOUR IMPLEMENTATION
Please create:

1. **Contact List Component**: Shows all contacts with proper data extraction
2. **Search Functionality**: Filters contacts locally (since API pagination makes server-side search complex)
3. **Contact Creation Form**: Allows adding new contacts with all fields
4. **Data Display**: Properly formats the Email/Phone/Address arrays
5. **Loading States**: Shows progress during the multi-page fetch process
6. **Error Handling**: Handles API failures gracefully

### 7. CRITICAL SUCCESS FACTORS
- Always use `JSON.parse(await response.text())` - never `response.json()`
- Always paginate through ALL pages to get complete contact list
- Always extract Email/Phone/Address from array structures
- Always handle the 25-record-per-page limitation
- Always check `result.Success` before using `result.Result`

### 8. TEST CASES
Your implementation should:
- Retrieve all 500+ contacts (not just 25)
- Display company names correctly (not "Unknown")
- Show clean email addresses (not "[object Object]")
- Handle contacts with missing fields gracefully
- Create new contacts successfully
- Search through contacts quickly

The biggest mistakes developers make with LACRM are:
1. Not manually parsing JSON (fails immediately)
2. Not implementing pagination (only gets 25 contacts)
3. Not handling the array structure for Email/Phone/Address (shows garbage data)

Follow these guidelines exactly and your integration will work perfectly. The API works great once you understand these quirks!

---

END OF PROMPT - Give this exact text to Bolt.net and it should be able to successfully integrate with LACRM API.