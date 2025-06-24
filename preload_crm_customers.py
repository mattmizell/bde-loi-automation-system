#!/usr/bin/env python3
"""
Preload all CRM customers into PostgreSQL database cache
This will populate the crm_contacts_cache table with all customers from Less Annoying CRM
"""

import os
import requests
import json
import psycopg2
from datetime import datetime

def preload_crm_customers():
    """Load all customers from CRM into database cache"""
    
    # Database connection
    database_url = "postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation"
    
    # CRM API configuration
    api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
    api_parts = api_key.split('-', 1)
    user_code = api_parts[0]
    crm_url = "https://api.lessannoyingcrm.com"
    
    print("🔄 Preloading CRM Customers into Database Cache")
    print("=" * 60)
    
    try:
        # Connect to database
        print("🗄️ Connecting to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Clear existing cache
        print("🧹 Clearing existing customer cache...")
        cur.execute("DELETE FROM crm_contacts_cache")
        conn.commit()
        
        # Get all contacts from CRM using the specific LACRM format we know works
        print("📞 Fetching all customers from Less Annoying CRM...")
        print("🔧 Using LACRM-specific API format...")
        
        # Use proper LACRM API pagination to get ALL contacts
        all_customers = []
        customers_by_id = {}  # Use dict to deduplicate by ContactId
        
        print("🔍 Using SearchContacts with proper pagination...")
        print("📚 LACRM API investigative approach to understand data limits")
        
        page = 1
        max_results_per_page = 10000  # LACRM API maximum
        total_retrieved = 0
        
        while True:
            print(f"\n📄 Fetching page {page} (requesting up to {max_results_per_page} records)...")
            
            params = {
                'APIToken': api_key,
                'UserCode': user_code,
                'Function': 'SearchContacts',
                'SearchTerm': '',  # Empty to get all contacts
                'MaxNumberOfResults': max_results_per_page,
                'Page': page
            }
            
            print(f"📋 Parameters: Function=SearchContacts, SearchTerm='', MaxNumberOfResults={max_results_per_page}, Page={page}")
            
            try:
                response = requests.get(crm_url, params=params, timeout=30)
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ API error: {response.status_code} - {response.text[:200]}...")
                    break
                
                # LACRM returns JSON with text/html content-type, so parse manually
                try:
                    result_data = json.loads(response.text)
                    print(f"🔧 API Response keys: {list(result_data.keys())}")
                    if 'HasMoreResults' in result_data:
                        print(f"📄 HasMoreResults: {result_data.get('HasMoreResults')}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"📄 Raw response text: {response.text[:1000]}")
                    break
                
                if not result_data.get('Success'):
                    print(f"❌ CRM API failed: {result_data.get('Error', 'Unknown error')}")
                    break
                
                customers_data = result_data.get('Result', [])
                
                if not isinstance(customers_data, list):
                    customers_data = [customers_data] if customers_data else []
                
                print(f"✅ Retrieved {len(customers_data)} customers from page {page}")
                
                # If we got no results, we've reached the end
                if len(customers_data) == 0:
                    print("📋 No more customers found - reached end of data")
                    break
                
                # Add to our deduplicated collection
                new_customers = 0
                for customer in customers_data:
                    contact_id = str(customer.get('ContactId', ''))
                    if contact_id and contact_id not in customers_by_id:
                        customers_by_id[contact_id] = customer
                        new_customers += 1
                
                total_retrieved += new_customers
                print(f"📊 Added {new_customers} new unique customers")
                print(f"📊 Total unique customers so far: {len(customers_by_id)}")
                
                # Show a sample customer from this page
                if len(customers_data) > 0:
                    sample_customer = customers_data[0]
                    name = sample_customer.get('Name', 'No name')
                    company = sample_customer.get('CompanyName', 'No company')
                    contact_id = sample_customer.get('ContactId', 'No ID')
                    print(f"📋 Sample from page {page}: {name} / {company} - ID: {contact_id}")
                
                # LACRM appears to limit to 25 results per page regardless of MaxNumberOfResults
                # Continue until we get 0 results (indicating end of data)
                # Don't stop just because we got fewer than max_results_per_page
                
                # Move to next page
                page += 1
                
                # Safety check to prevent infinite loops
                if page > 50:  # 50 pages * 25 contacts = 1250 contacts max (should be plenty)
                    print("⚠️ Safety limit reached - stopping pagination")
                    break
                
            except Exception as e:
                print(f"❌ Page {page} fetch failed: {e}")
                break
        
        # Convert back to list
        customers_data = list(customers_by_id.values())
        print(f"\n🎉 Pagination complete!")
        print(f"📊 Total pages fetched: {page}")
        print(f"📊 Final result: {len(customers_data)} unique customers found")
        
        # Insert customers into database cache
        print("💾 Inserting customers into database cache...")
        
        inserted_count = 0
        skipped_count = 0
        
        for customer in customers_data:
            try:
                # Extract customer data using actual LACRM format, handling different data types
                contact_id = str(customer.get('ContactId', ''))
                name = str(customer.get('CompanyName', '') or 'Unknown Contact')
                
                # Extract email (LACRM format: list of dicts with 'Text' field)
                email_raw = customer.get('Email', '')
                if isinstance(email_raw, list) and len(email_raw) > 0:
                    # Extract Text field from first email entry, handle both formats
                    first_email = email_raw[0]
                    if isinstance(first_email, dict):
                        email_text = first_email.get('Text', '')
                        # Remove "(Work)" suffix if present
                        email = email_text.split(' (')[0] if email_text else ''
                    else:
                        email = str(first_email)
                elif isinstance(email_raw, dict):
                    email = str(email_raw.get('Text', '') or email_raw.get('Value', '') or '')
                else:
                    email = str(email_raw or '')
                
                # Company name
                company_name = str(customer.get('CompanyName', '') or '')
                
                # Extract phone (LACRM format: list of dicts with 'Text' field)
                phone_raw = customer.get('Phone', '')
                if isinstance(phone_raw, list) and len(phone_raw) > 0:
                    # Extract Text field from first phone entry, handle both formats
                    first_phone = phone_raw[0]
                    if isinstance(first_phone, dict):
                        phone_text = first_phone.get('Text', '')
                        # Remove "(Work)" suffix if present
                        phone = phone_text.split(' (')[0] if phone_text else ''
                    else:
                        phone = str(first_phone)
                elif isinstance(phone_raw, dict):
                    phone = str(phone_raw.get('Text', '') or phone_raw.get('Value', '') or '')
                else:
                    phone = str(phone_raw or '')
                
                # Extract address (LACRM format: list of dicts with structured address)
                address_raw = customer.get('Address', '')
                if isinstance(address_raw, list) and len(address_raw) > 0:
                    # Extract address from first address entry
                    first_address = address_raw[0]
                    if isinstance(first_address, dict):
                        # LACRM address structure: Street, City, State, Zip
                        street = first_address.get('Street', '')
                        city = first_address.get('City', '')
                        state = first_address.get('State', '')
                        zip_code = first_address.get('Zip', '')
                        address_parts = [p for p in [street, city, state, zip_code] if p]
                        address = ', '.join(address_parts)
                    else:
                        address = str(first_address)
                elif isinstance(address_raw, dict):
                    address = str(address_raw.get('Street', '') or address_raw.get('Text', '') or address_raw.get('Value', '') or '')
                else:
                    address = str(address_raw or '')
                
                # Skip if no essential data
                if not contact_id or not name:
                    skipped_count += 1
                    continue
                
                # Combine additional fields into notes using actual LACRM field names
                notes_parts = []
                if customer.get('BackgroundInfo'):
                    notes_parts.append(f"Background: {customer['BackgroundInfo']}")
                if customer.get('Birthday'):
                    notes_parts.append(f"Birthday: {customer['Birthday']}")
                if customer.get('Industry'):
                    notes_parts.append(f"Industry: {customer['Industry']}")
                if customer.get('NumEmployees'):
                    notes_parts.append(f"Employees: {customer['NumEmployees']}")
                if customer.get('Website'):
                    notes_parts.append(f"Website: {customer['Website']}")
                if customer.get('CreationDate'):
                    notes_parts.append(f"Created: {customer['CreationDate']}")
                if customer.get('EditedDate'):
                    notes_parts.append(f"Modified: {customer['EditedDate']}")
                if customer.get('AssignedTo'):
                    notes_parts.append(f"Assigned: {customer['AssignedTo']}")
                
                notes = " | ".join(notes_parts)
                
                # Insert into database
                cur.execute("""
                    INSERT INTO crm_contacts_cache 
                    (contact_id, name, email, company_name, phone, address, notes, sync_status, last_sync)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (contact_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        company_name = EXCLUDED.company_name,
                        phone = EXCLUDED.phone,
                        address = EXCLUDED.address,
                        notes = EXCLUDED.notes,
                        sync_status = EXCLUDED.sync_status,
                        last_sync = EXCLUDED.last_sync,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    contact_id,
                    name,
                    email,
                    company_name,
                    phone,
                    address,
                    notes,
                    'synced',
                    datetime.now()
                ))
                
                inserted_count += 1
                
                # Show progress every 50 records
                if inserted_count % 50 == 0:
                    print(f"  📋 Processed {inserted_count} customers...")
                
            except Exception as e:
                print(f"⚠️ Error processing customer {customer.get('ContactId', 'unknown')}: {e}")
                print(f"   Customer data types: Email={type(customer.get('Email'))}, Phone={type(customer.get('Phone'))}, Address={type(customer.get('Address'))}")
                if customer.get('Email'):
                    print(f"   Email value: {customer['Email']}")
                skipped_count += 1
                continue
        
        # Commit all changes
        conn.commit()
        
        # Update sync log
        cur.execute("""
            INSERT INTO crm_sync_log (sync_type, records_updated, last_sync_time)
            VALUES (%s, %s, %s)
        """, ('full_preload', inserted_count, datetime.now()))
        
        conn.commit()
        
        # Get final counts
        cur.execute("SELECT COUNT(*) FROM crm_contacts_cache")
        total_cached = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"\n🎉 CRM Customer Preload Complete!")
        print(f"✅ Successfully cached: {inserted_count} customers")
        print(f"⚠️ Skipped (incomplete data): {skipped_count} records")
        print(f"📊 Total in database cache: {total_cached} customers")
        print(f"🗄️ Database ready for fast LOI customer lookups")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Preload failed: {e}")
        return False

def test_cache_search():
    """Test the cached customer search functionality"""
    
    database_url = "postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation"
    
    print("\n🔍 Testing Customer Cache Search...")
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Test search for common terms
        test_searches = ['gas', 'station', 'energy', 'smith', 'john']
        
        for search_term in test_searches:
            cur.execute("""
                SELECT contact_id, name, company_name, email 
                FROM crm_contacts_cache 
                WHERE LOWER(name) LIKE %s 
                   OR LOWER(company_name) LIKE %s 
                   OR LOWER(email) LIKE %s
                LIMIT 3
            """, (f'%{search_term.lower()}%', f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
            
            results = cur.fetchall()
            
            if results:
                print(f"  🔍 '{search_term}' found {len(results)} matches:")
                for contact_id, name, company, email in results:
                    print(f"    • {name} ({company}) - {email}")
            else:
                print(f"  🔍 '{search_term}' - no matches")
        
        cur.close()
        conn.close()
        
        print("✅ Cache search test completed")
        
    except Exception as e:
        print(f"❌ Cache search test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting CRM Customer Preload Process")
    
    success = preload_crm_customers()
    
    if success:
        test_cache_search()
        print("\n🎯 System is now ready for fast customer lookups!")
        print("   • Admin dashboard will search local cache first")
        print("   • No delays waiting for CRM API calls")
        print("   • Duplicate prevention works instantly")
    else:
        print("\n❌ Preload failed - check error messages above")
    
    exit(0 if success else 1)