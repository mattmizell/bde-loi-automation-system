# API Update for Adam - Better Day Energy CRM Integration

## Important Changes - Please Read

Hi Adam,

We've made significant improvements to the CRM integration. Here's what you need to know:

### 🚨 Key Changes

1. **Don't use LACRM API directly anymore** - We discovered several issues:
   - LACRM returns `text/html` content-type with JSON data (breaks most parsers)
   - Maximum 25 records per page (requires complex pagination)
   - Slow response times for large datasets

2. **Use our new CRM Bridge API instead** - Much faster and easier:
   - ✅ Instant response from PostgreSQL cache
   - ✅ All 500+ contacts in one request
   - ✅ Proper JSON responses
   - ✅ No pagination needed
   - ✅ Background sync keeps data fresh

### 📡 New API Endpoints

**Base URL**: `https://loi-automation-api.onrender.com`

#### 1. Get All Contacts
```
GET /api/contacts
Authorization: Bearer bde_adam_auth_2f93111a6ca5b0a443afbaed625d3268

Response:
{
  "success": true,
  "contacts": [
    {
      "id": "12345",
      "name": "John Smith",
      "email": "john@example.com",
      "company": "ABC Company",
      "phone": "555-123-4567"
    }
    // ... all contacts
  ],
  "total": 524
}
```

#### 2. Search Contacts
```
POST /api/search_contacts
Authorization: Bearer bde_adam_auth_2f93111a6ca5b0a443afbaed625d3268
Content-Type: application/json

{
  "query": "smith"
}

Response: Same format as above, filtered results
```

#### 3. Create Contact
```
POST /api/create_contact
Authorization: Bearer bde_adam_auth_2f93111a6ca5b0a443afbaed625d3268
Content-Type: application/json

{
  "name": "New Customer",
  "email": "new@example.com",
  "company": "New Company",
  "phone": "555-999-8888"
}
```

### 🔧 Integration with Bolt.new

For your Bolt.new AI application, here's a complete working example:

```javascript
// CRM Integration for Bolt.new
const CRM_API = {
  baseUrl: 'https://loi-automation-api.onrender.com',
  token: 'bde_adam_auth_2f93111a6ca5b0a443afbaed625d3268',
  
  // Fetch all contacts
  async getAllContacts() {
    try {
      const response = await fetch(`${this.baseUrl}/api/contacts`, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch contacts');
      
      const data = await response.json();
      return data.contacts;
    } catch (error) {
      console.error('Error fetching contacts:', error);
      return [];
    }
  },
  
  // Search contacts
  async searchContacts(query) {
    try {
      const response = await fetch(`${this.baseUrl}/api/search_contacts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      });
      
      if (!response.ok) throw new Error('Search failed');
      
      const data = await response.json();
      return data.contacts;
    } catch (error) {
      console.error('Error searching contacts:', error);
      return [];
    }
  },
  
  // Create new contact
  async createContact(contactData) {
    try {
      const response = await fetch(`${this.baseUrl}/api/create_contact`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(contactData)
      });
      
      if (!response.ok) throw new Error('Failed to create contact');
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error creating contact:', error);
      return { success: false, error: error.message };
    }
  }
};

// Example usage in your Bolt.new app:
async function loadContactsDropdown() {
  const contacts = await CRM_API.getAllContacts();
  
  const select = document.getElementById('contact-select');
  select.innerHTML = '<option value="">Select a contact...</option>';
  
  contacts.forEach(contact => {
    const option = document.createElement('option');
    option.value = contact.id;
    option.textContent = `${contact.name} - ${contact.company}`;
    select.appendChild(option);
  });
}

// Search as user types
async function handleContactSearch(searchTerm) {
  if (searchTerm.length < 2) return;
  
  const results = await CRM_API.searchContacts(searchTerm);
  // Update your UI with results
}
```

### 🎯 Benefits of Using Our API

1. **Speed**: Instant responses vs 5-10 seconds with LACRM
2. **Reliability**: No pagination issues or timeout errors
3. **Simplicity**: Standard JSON responses, no parsing issues
4. **Fresh Data**: Background sync every 5 minutes
5. **Better Search**: Fast local search across all fields

### ⚠️ Important Notes

- Your old LACRM integration will still work but is deprecated
- The new API requires the Bearer token in the Authorization header
- All endpoints return proper JSON with `application/json` content-type
- The cache is automatically refreshed every 5 minutes
- Creating a contact adds it to cache immediately, syncs to LACRM in background

### 🚀 Migration Steps

1. Update your API base URL to `https://loi-automation-api.onrender.com`
2. Add the Authorization header with your token
3. Remove any LACRM pagination logic (not needed anymore)
4. Remove any special JSON parsing for text/html responses
5. Test with the examples above

### 📞 Support

If you have any questions or issues:
- Test the API endpoints with Postman or curl first
- Check that you're using the correct Authorization header
- Contact me if you need help with the migration

The system is live and ready to use. You should see significant performance improvements, especially when loading contact lists or searching.

Let me know if you need any clarification or run into issues!

Best,
Matt

---

**Technical Details for Reference:**
- Cache refresh: Every 5 minutes
- Write sync: Every 30 seconds  
- Database: PostgreSQL with indexed search
- Hosting: Render.com with auto-scaling
- Auth: Bearer token (no expiration currently)