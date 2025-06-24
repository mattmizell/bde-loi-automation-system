#!/usr/bin/env python3
"""
Test CRM API diagnostics to understand why we're only getting ~25 contacts when expecting 500+
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from integrated_pdf_signature_server import crm_bidirectional_sync
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run CRM API diagnostics"""
    print("🔬 Starting CRM API Diagnostics")
    print("=" * 60)
    print("Purpose: Understand why we're only getting ~25 contacts when expecting 500+")
    print()
    
    # Run the diagnostics
    crm_bidirectional_sync.diagnose_crm_access()
    
    print()
    print("🔬 Diagnostics complete!")
    print()
    print("Next steps based on results:")
    print("1. If all approaches return ~25 contacts:")
    print("   - API key may have data visibility restrictions")
    print("   - User role in LACRM may limit contact access")
    print("   - Account settings may filter available contacts")
    print()
    print("2. If alternative functions work:")
    print("   - Update sync process to use the working function")
    print("   - Implement proper parameters for full data access")
    print()
    print("3. If some approaches return more contacts:")
    print("   - Identify the optimal search parameters")
    print("   - Update the sync process accordingly")

if __name__ == "__main__":
    main()