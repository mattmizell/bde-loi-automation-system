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
        
        # LACRM API uses GET with URL parameters - correct function is GetContacts
        params = {
            'APIToken': api_key,
            'UserCode': user_code,
            'Function': 'GetContacts',
            'MaxNumberOfResults': 10000  # Get all contacts (max allowed)
        }
        
        print(f"🌐 API URL: {crm_url}")
        print(f"📋 Parameters: {params}")
        
        response = requests.get(crm_url, params=params, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Text (first 500 chars): {response.text[:500]}...")
        
        if response.status_code != 200:
            raise Exception(f"CRM API error: {response.status_code} - {response.text}")
        
        # LACRM returns JSON with text/html content-type, so parse manually
        try:
            result_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"📄 Raw response: {response.text}")
            raise Exception(f"Failed to parse CRM response as JSON: {e}")
        
        if not result_data.get('Success'):
            raise Exception(f"CRM API failed: {result_data.get('Error', 'Unknown error')}")
        
        customers_data = result_data.get('Result', [])
        
        if not isinstance(customers_data, list):
            customers_data = [customers_data] if customers_data else []
        
        print(f"✅ Retrieved {len(customers_data)} customers from CRM")
        
        # Insert customers into database cache
        print("💾 Inserting customers into database cache...")
        
        inserted_count = 0
        skipped_count = 0
        
        for customer in customers_data:
            try:
                # Extract customer data
                contact_id = str(customer.get('ContactId', ''))
                name = customer.get('Name', '').strip()
                email = customer.get('Email', '').strip()
                company_name = customer.get('CompanyName', '').strip()
                phone = customer.get('Phone', '').strip()
                address = customer.get('Address', '').strip()
                
                # Skip if no essential data
                if not contact_id or not name:
                    skipped_count += 1
                    continue
                
                # Combine additional fields into notes
                notes_parts = []
                if customer.get('Notes'):
                    notes_parts.append(f"Notes: {customer['Notes']}")
                if customer.get('Birthday'):
                    notes_parts.append(f"Birthday: {customer['Birthday']}")
                if customer.get('DateCreated'):
                    notes_parts.append(f"Created: {customer['DateCreated']}")
                if customer.get('DateModified'):
                    notes_parts.append(f"Modified: {customer['DateModified']}")
                
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