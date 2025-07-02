/**
 * CRM Search Component for Better Day Energy Forms
 * Reusable JavaScript for CRM integration across all forms
 */

class CRMSearchComponent {
    constructor(config = {}) {
        this.searchInputId = config.searchInputId || 'crm-search';
        this.searchResultsId = config.searchResultsId || 'search-results';
        this.statusId = config.statusId || 'crm-status';
        this.fieldMappings = config.fieldMappings || this.getDefaultFieldMappings();
        
        this.searchTimeout = null;
        this.selectedContact = null;
        
        this.init();
    }
    
    getDefaultFieldMappings() {
        return {
            company_name: 'company-name',
            email: 'customer-email',
            phone: 'customer-phone',
            // Address fields
            bank_address: 'bank-address',
            bank_city: 'bank-city', 
            bank_state: 'bank-state',
            bank_zip: 'bank-zip',
            // Additional fields
            account_holder_name: 'account-holder'
        };
    }
    
    init() {
        this.searchInput = document.getElementById(this.searchInputId);
        this.searchResults = document.getElementById(this.searchResultsId);
        this.statusElement = document.getElementById(this.statusId);
        
        if (!this.searchInput) {
            console.warn('CRM Search: Search input not found');
            return;
        }
        
        this.bindEvents();
        this.makeGlobal();
    }
    
    bindEvents() {
        // Search input with debouncing
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value.trim());
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-box')) {
                this.hideResults();
            }
        });
    }
    
    handleSearchInput(query) {
        clearTimeout(this.searchTimeout);
        
        if (query.length < 2) {
            this.hideResults();
            return;
        }
        
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }
    
    async performSearch(query) {
        try {
            this.showStatus('loading', 'Searching CRM...');
            
            const response = await fetch('/api/v1/crm-bridge/contacts/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer bde_loi_auth_e6db5173a4393421ffadae85f9a3513e'
                },
                body: JSON.stringify({
                    query: query,
                    limit: 10
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.contacts) {
                this.displayResults(data.contacts);
                this.hideStatus();
            } else {
                this.hideResults();
                this.showStatus('error', 'Search failed. Please try again.');
            }
        } catch (error) {
            console.error('CRM search error:', error);
            this.hideResults();
            this.showStatus('error', 'Search error. Please try again.');
        }
    }
    
    displayResults(contacts) {
        if (!this.searchResults) return;
        
        if (contacts.length === 0) {
            this.searchResults.innerHTML = '<div class="search-result">No results found</div>';
            this.searchResults.style.display = 'block';
            return;
        }
        
        const resultsHtml = contacts.map(contact => `
            <div class="search-result" onclick="window.crmSearch.selectContact(${this.escapeJson(contact)})">
                <div class="search-result-name">${contact.name || 'No name'}</div>
                <div class="search-result-company">${contact.company_name || 'No company'}</div>
                <div class="search-result-email">${contact.email || 'No email'}</div>
            </div>
        `).join('');
        
        this.searchResults.innerHTML = resultsHtml;
        this.searchResults.style.display = 'block';
    }
    
    selectContact(contact) {
        this.selectedContact = contact;
        this.populateForm(contact);
        this.hideResults();
        
        // Update search input to show selected contact
        this.searchInput.value = `${contact.company_name || 'Unknown'} - ${contact.name || 'No name'}`;
        
        // Show success status
        this.showStatus('found', 
            `✅ Found: ${contact.company_name} - ${contact.name} 
             <button type="button" class="clear-crm-btn" onclick="window.crmSearch.clearData()">Clear</button>`
        );
    }
    
    populateForm(contact) {
        // Populate basic fields
        this.setFieldValue(this.fieldMappings.company_name, contact.company_name);
        this.setFieldValue(this.fieldMappings.email, contact.email);
        this.setFieldValue(this.fieldMappings.phone, contact.phone);
        
        // Parse and populate address
        if (contact.address) {
            const addressParts = this.parseAddress(contact.address);
            
            this.setFieldValue(this.fieldMappings.bank_address, addressParts.street);
            this.setFieldValue(this.fieldMappings.bank_city, addressParts.city);
            this.setFieldValue(this.fieldMappings.bank_state, addressParts.state);
            this.setFieldValue(this.fieldMappings.bank_zip, addressParts.zip);
        }
        
        // Set account holder to company name
        this.setFieldValue(this.fieldMappings.account_holder_name, contact.company_name);
        
        // Custom field population hook
        if (this.onContactSelected) {
            this.onContactSelected(contact);
        }
    }
    
    parseAddress(addressString) {
        if (!addressString) return {};
        
        // Handle multi-line addresses
        const cleanAddress = addressString.replace(/\n/g, ', ').replace(/\s+/g, ' ');
        const parts = cleanAddress.split(',').map(part => part.trim());
        
        if (parts.length >= 3) {
            const street = parts[0];
            const city = parts[1];
            
            // Last part might be "State Zip" or "State, Zip"
            const lastPart = parts[parts.length - 1];
            const stateZipMatch = lastPart.match(/^([A-Z]{2})\s*,?\s*(\d{5}(-\d{4})?)$/i);
            
            if (stateZipMatch) {
                return {
                    street: street,
                    city: city,
                    state: stateZipMatch[1],
                    zip: stateZipMatch[2]
                };
            } else {
                // Try to extract zip from end
                const zipMatch = lastPart.match(/(\d{5}(-\d{4})?)$/);
                if (zipMatch) {
                    const zip = zipMatch[1];
                    const state = lastPart.replace(zipMatch[0], '').trim().replace(/,$/, '');
                    return {
                        street: street,
                        city: city,
                        state: state,
                        zip: zip
                    };
                }
            }
        }
        
        return { street: addressString };
    }
    
    setFieldValue(fieldId, value) {
        if (!fieldId || !value) return;
        
        const element = document.getElementById(fieldId);
        if (element) {
            element.value = value;
        }
    }
    
    clearData() {
        this.selectedContact = null;
        this.searchInput.value = '';
        this.hideStatus();
        
        // Clear only CRM-populated fields, keep manual entries
        const fieldsToKeep = ['initiated-by', 'notes', 'authorized-by-name', 'authorized-by-title'];
        const formElements = document.querySelectorAll('input, select, textarea');
        
        formElements.forEach(element => {
            if (element.id && !fieldsToKeep.includes(element.id)) {
                element.value = '';
            }
        });
        
        // Custom clear hook
        if (this.onDataCleared) {
            this.onDataCleared();
        }
    }
    
    showStatus(type, message) {
        if (!this.statusElement) return;
        
        this.statusElement.className = `crm-status ${type}`;
        this.statusElement.innerHTML = message;
        this.statusElement.style.display = 'block';
    }
    
    hideStatus() {
        if (this.statusElement) {
            this.statusElement.style.display = 'none';
        }
    }
    
    hideResults() {
        if (this.searchResults) {
            this.searchResults.style.display = 'none';
        }
    }
    
    escapeJson(obj) {
        return JSON.stringify(obj).replace(/"/g, '&quot;');
    }
    
    makeGlobal() {
        // Make instance globally accessible for onclick handlers
        window.crmSearch = this;
    }
}

// CSS for CRM search component
const CRM_SEARCH_CSS = `
    .crm-search-section {
        background: #f8f9fa;
        padding: 25px;
        border-radius: 8px;
        margin-bottom: 25px;
        border: 2px solid #28a745;
    }
    
    .search-box {
        position: relative;
        margin-bottom: 15px;
    }
    
    .search-results {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ced4da;
        border-top: none;
        max-height: 300px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
    }
    
    .search-result {
        padding: 12px;
        border-bottom: 1px solid #e9ecef;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .search-result:hover {
        background: #f8f9fa;
    }
    
    .search-result:last-child {
        border-bottom: none;
    }
    
    .search-result-name {
        font-weight: 600;
        color: #1f4e79;
    }
    
    .search-result-company {
        color: #495057;
        font-size: 14px;
    }
    
    .search-result-email {
        color: #6c757d;
        font-size: 13px;
    }
    
    .crm-status {
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        margin-top: 10px;
        display: none;
    }
    
    .crm-status.found {
        background: #d1e7dd;
        color: #0f5132;
        border: 1px solid #badbcc;
        display: block;
    }
    
    .crm-status.loading {
        background: #fff3cd;
        color: #664d03;
        border: 1px solid #ffecb5;
        display: block;
    }
    
    .crm-status.error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
        display: block;
    }
    
    .clear-crm-btn {
        background: #6c757d;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        margin-left: 10px;
    }
    
    .clear-crm-btn:hover {
        background: #5a6268;
    }
`;

// Function to inject CSS
function injectCRMSearchCSS() {
    if (!document.getElementById('crm-search-css')) {
        const style = document.createElement('style');
        style.id = 'crm-search-css';
        style.textContent = CRM_SEARCH_CSS;
        document.head.appendChild(style);
    }
}

// Function to create CRM search HTML
function createCRMSearchHTML() {
    return `
        <div class="crm-search-section">
            <h3>🔍 Search CRM Database</h3>
            <p style="margin-bottom: 15px; color: #495057;">Search our 2,500+ customer database to auto-populate form fields</p>
            
            <div class="search-box">
                <label for="crm-search">Search by Company Name, Contact Name, or Email</label>
                <input type="text" id="crm-search" placeholder="Type to search CRM..." autocomplete="off">
                <div class="search-results" id="search-results"></div>
            </div>
            
            <div class="crm-status" id="crm-status"></div>
        </div>
    `;
}

// Auto-initialize if DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        injectCRMSearchCSS();
    });
} else {
    injectCRMSearchCSS();
}