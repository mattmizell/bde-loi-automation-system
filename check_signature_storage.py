#!/usr/bin/env python3
"""
Check if the signature was stored in PostgreSQL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def check_signature_storage():
    """Check PostgreSQL for stored signatures"""
    
    connection_string = "postgresql://mattmizell:training1@localhost/loi_automation"
    
    try:
        print("🔍 Checking PostgreSQL signature storage...")
        
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'electronic_signatures'
            )
        """)
        
        table_exists = cur.fetchone()[0]
        print(f"📊 Table exists: {'✅ Yes' if table_exists else '❌ No'}")
        
        if table_exists:
            # Get all signatures
            cur.execute("""
                SELECT verification_code, transaction_id, signer_name, 
                       company_name, signed_at, status, ip_address
                FROM electronic_signatures 
                ORDER BY signed_at DESC
            """)
            
            signatures = cur.fetchall()
            print(f"📝 Total signatures stored: {len(signatures)}")
            
            if signatures:
                print("\n🔍 Recent signatures:")
                for sig in signatures[-5:]:  # Show last 5
                    print(f"  📄 {sig['verification_code']} - {sig['signer_name']}")
                    print(f"     🏢 {sig['company_name']}")
                    print(f"     📅 {sig['signed_at']}")
                    print(f"     🌐 IP: {sig['ip_address']}")
                    print()
                
                # Check specific verification code
                verification_code = "LOI-A8308E02"
                cur.execute("""
                    SELECT * FROM electronic_signatures 
                    WHERE verification_code = %s
                """, (verification_code,))
                
                specific_sig = cur.fetchone()
                if specific_sig:
                    print(f"✅ Found signature {verification_code}:")
                    print(f"   📝 Signer: {specific_sig['signer_name']}")
                    print(f"   🏢 Company: {specific_sig['company_name']}")
                    print(f"   📅 Signed: {specific_sig['signed_at']}")
                    print(f"   ✅ Status: {specific_sig['status']}")
                    print(f"   🔐 Integrity: {specific_sig['integrity_hash'][:16]}...")
                    
                    # Check if signature image exists
                    if specific_sig['signature_image']:
                        print(f"   🖼️ Signature image: {len(specific_sig['signature_image'])} bytes")
                    else:
                        print("   ❌ No signature image found")
                else:
                    print(f"❌ Signature {verification_code} not found in database")
        
        cur.close()
        conn.close()
        return len(signatures) if table_exists else 0
        
    except Exception as e:
        print(f"❌ Error checking PostgreSQL: {e}")
        return 0

if __name__ == "__main__":
    print("🔍 PostgreSQL Signature Storage Check")
    print("=" * 50)
    
    signature_count = check_signature_storage()
    
    if signature_count > 0:
        print(f"\n✅ Found {signature_count} signatures in PostgreSQL")
        print("📄 Signature data is securely stored")
    else:
        print("\n❌ No signatures found in PostgreSQL")
        print("⚠️ The signature workflow may not have completed successfully")