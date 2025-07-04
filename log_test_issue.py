#!/usr/bin/env python3
"""
Test Issue Logging Utility
Logs issues found during testing to database for batch fixing
"""

import psycopg2
from datetime import datetime

def log_test_issue(test_run_id, form_type, issue_category, issue_description, 
                   error_message="", reproduction_steps="", severity="MEDIUM"):
    """Log a test issue to the database"""
    
    try:
        conn = psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO test_issue_log 
            (test_run_id, form_type, issue_category, issue_description, 
             error_message, reproduction_steps, severity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (test_run_id, form_type, issue_category, issue_description,
              error_message, reproduction_steps, severity))
        
        conn.commit()
        conn.close()
        print(f"✅ Logged {severity} issue: {issue_description}")
        
    except Exception as e:
        print(f"❌ Failed to log issue: {e}")

def get_open_issues(test_run_id=None):
    """Get all open issues, optionally filtered by test run"""
    
    try:
        conn = psycopg2.connect("postgresql://loi_user:2laNcRN0ATESCFQg1mGhknBielnDJfiS@dpg-d1dd5nadbo4c73cmub8g-a.oregon-postgres.render.com/loi_automation")
        cur = conn.cursor()
        
        if test_run_id:
            cur.execute("""
                SELECT test_run_id, form_type, issue_category, issue_description, 
                       error_message, severity, found_at
                FROM test_issue_log 
                WHERE status = 'OPEN' AND test_run_id = %s
                ORDER BY severity, found_at
            """, (test_run_id,))
        else:
            cur.execute("""
                SELECT test_run_id, form_type, issue_category, issue_description, 
                       error_message, severity, found_at
                FROM test_issue_log 
                WHERE status = 'OPEN'
                ORDER BY severity, found_at
            """)
        
        issues = cur.fetchall()
        conn.close()
        
        return issues
        
    except Exception as e:
        print(f"❌ Failed to get issues: {e}")
        return []

if __name__ == "__main__":
    # Test the logging system
    test_run = f"TEST_RUN_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Example usage
    log_test_issue(
        test_run_id=test_run,
        form_type="P66_LOI", 
        issue_category="Database",
        issue_description="Transaction status enum mismatch",
        error_message="invalid input value for enum transactionstatus: 'pending_signature'",
        reproduction_steps="1. Submit P66 LOI form 2. Check database insert",
        severity="CRITICAL"
    )
    
    print("\nOpen issues:")
    issues = get_open_issues(test_run)
    for issue in issues:
        print(f"- {issue[1]}: {issue[3]} [{issue[5]}]")