#!/usr/bin/env python3
"""
Generate a new LOI signature request for Farley Barnhart
"""

import json
import uuid
from datetime import datetime, timedelta

# Generate new signature request
new_request = {
    "transaction_id": f"TXN-{str(uuid.uuid4())[:8].upper()}",
    "signature_token": str(uuid.uuid4()),
    "signer_name": "Farely Barnhart",
    "signer_email": "matt.mizell@gmail.com",
    "company_name": "Farley's Gas and Go",
    "document_name": "VP Racing Fuel Supply Agreement - Letter of Intent",
    "status": "pending",
    "created_at": datetime.now().isoformat(),
    "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
}

# Save to signature request data file
signature_data = {
    "request_001": new_request
}

with open("signature_request_data.json", "w") as f:
    json.dump(signature_data, f, indent=2)

print("🆕 New LOI Generated for Farley Barnhart!")
print(f"📧 Transaction ID: {new_request['transaction_id']}")
print(f"🔗 Signature Token: {new_request['signature_token']}")
print(f"📅 Expires: {datetime.fromisoformat(new_request['expires_at']).strftime('%B %d, %Y')}")
print(f"\n🖊️  Signature URL: http://localhost:8001/sign/{new_request['signature_token']}")
print(f"📧 Email would be sent to: {new_request['signer_email']}")
print("\n✅ Ready for Farley to sign his new LOI!")