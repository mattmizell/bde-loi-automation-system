#!/usr/bin/env python3
"""
Debug signature endpoints and transaction storage
Check if our test transactions actually exist in the database
"""

import psycopg2
import requests
from datetime import datetime

# Test transaction IDs from comprehensive testing
TEST_TRANSACTION_IDS = [
    "55071680-be2f-40dc-88b9-6e3e9c439b2e",  # Customer Setup
    "10e884f9-c69f-4d2a-a865-84985dcefdc1"   # EFT Sales
]

def check_database_for_transactions():
    """Check if transactions exist in database"""
    print("🔍 Checking database for test transactions...")
    
    try:
        # Try production database first
        conn = psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
        print("✅ Connected to production database")
    except Exception as e:
        print(f"❌ Production DB failed: {e}")
        return
    
    cur = conn.cursor()
    
    # Check different possible tables where transactions might be stored
    tables_to_check = [
        "loi_transactions",
        "customers", 
        "p66_loi_form_data",
        "eft_form_data",
        "customer_setup_data"
    ]
    
    print(f"\n📊 Checking {len(tables_to_check)} tables for our transaction IDs...")
    
    for table in tables_to_check:
        try:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                print(f"\n✅ Table '{table}' exists")
                
                # Get table schema
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cur.fetchall()
                print(f"   Columns: {', '.join([col[0] for col in columns[:5]])}...")
                
                # Check for our transaction IDs
                for transaction_id in TEST_TRANSACTION_IDS:
                    # Try different possible ID column names
                    id_columns = ['id', 'transaction_id', 'loi_id', 'customer_id']
                    
                    for id_col in id_columns:
                        # Check if column exists
                        if any(col[0] == id_col for col in columns):
                            try:
                                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {id_col} = %s", (transaction_id,))
                                count = cur.fetchone()[0]
                                if count > 0:
                                    print(f"   🎯 FOUND: {transaction_id[:8]}... in {table}.{id_col}")
                                    
                                    # Get the full record
                                    cur.execute(f"SELECT * FROM {table} WHERE {id_col} = %s LIMIT 1", (transaction_id,))
                                    record = cur.fetchone()
                                    if record:
                                        print(f"   📋 Record: {str(record)[:100]}...")
                                        
                            except Exception as e:
                                pass  # Column doesn't exist or query failed
                                
            else:
                print(f"❌ Table '{table}' does not exist")
                
        except Exception as e:
            print(f"❌ Error checking table '{table}': {e}")
    
    conn.close()

def test_signature_endpoint_directly():
    """Test signature endpoint with debug info"""
    print("\n🔗 Testing signature endpoints directly...")
    
    for transaction_id in TEST_TRANSACTION_IDS:
        print(f"\n--- Testing: {transaction_id[:8]}... ---")
        
        url = f"https://loi-automation-api.onrender.com/api/v1/loi/sign/{transaction_id}"
        
        try:
            response = requests.get(url, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                print(f"✅ Success! Content length: {len(content)}")
                
                # Check for key elements
                if "signature" in content.lower():
                    print("✅ Contains signature elements")
                if "canvas" in content.lower():
                    print("✅ Contains canvas element")
                if "esign" in content.lower():
                    print("✅ Contains ESIGN compliance")
                    
            elif response.status_code == 500:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"❌ Server error: {error_detail}")
                
            else:
                print(f"❌ Unexpected status: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

def main():
    print("🚀 Debug Signature Endpoints")
    print(f"⏰ {datetime.now()}")
    print("="*50)
    
    # Check database first
    check_database_for_transactions()
    
    # Test endpoints
    test_signature_endpoint_directly()
    
    print("\n🎯 Summary:")
    print("- If transactions not found in DB, they weren't saved during testing")
    print("- If endpoints return 500 errors, there's a backend bug")
    print("- We may need to create fresh transactions for signature testing")

if __name__ == "__main__":
    main()