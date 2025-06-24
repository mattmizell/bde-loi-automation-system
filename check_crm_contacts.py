#!/usr/bin/env python3
"""
Check CRM Contacts

Use the same method that worked in our main app to get contacts from CRM.
"""

import asyncio
import aiohttp
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_crm_contacts():
    """Get contacts using the same method as our main app"""
    
    api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
    base_url = "https://api.lessannoyingcrm.com/v2/"
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": api_key
            }
            
            # Use the same request format that worked in simple_main.py
            data = {"Function": "GetContacts", "Parameters": {}}
            
            logger.info("📞 Calling CRM API to get contacts...")
            
            async with session.post(base_url, headers=headers, json=data) as response:
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                logger.info(f"Raw response (first 500 chars): {response_text[:500]}")
                
                # Parse the response like we do in simple_main.py
                contacts_list = []
                
                try:
                    # Try parsing as JSON first
                    data = json.loads(response_text)
                    if isinstance(data, dict) and 'Results' in data:
                        contacts_list = data['Results']
                    elif isinstance(data, list):
                        contacts_list = data
                    elif isinstance(data, dict) and 'ErrorCode' in data:
                        logger.error(f"CRM API Error: {data.get('ErrorCode')} - {data.get('ErrorDescription')}")
                        return
                except json.JSONDecodeError:
                    # Handle text/html response like in simple_main.py
                    logger.info("Response is not JSON, treating as text")
                    try:
                        # Look for JSON within the HTML response
                        import re
                        json_match = re.search(r'\[.*\]', response_text)
                        if json_match:
                            contacts_data = json.loads(json_match.group())
                            if isinstance(contacts_data, list):
                                contacts_list = contacts_data
                    except:
                        logger.error("Could not parse response as JSON or extract JSON from HTML")
                        return
                
                logger.info(f"✅ Found {len(contacts_list)} contacts")
                
                # Show first 10 contacts with details
                logger.info("📋 First 10 contacts:")
                for i, contact in enumerate(contacts_list[:10]):
                    contact_id = contact.get('ContactId', 'N/A')
                    name = contact.get('Name', 'N/A')
                    email = contact.get('Email', 'N/A')
                    company = contact.get('CompanyName', 'N/A')
                    
                    logger.info(f"  {i+1}. ID: {contact_id} | Name: {name} | Email: {email} | Company: {company}")
                
                # Look for any contact with 'adam' in name or email
                logger.info("\n🔍 Searching for 'adam' in contacts...")
                adam_found = False
                for contact in contacts_list:
                    name = str(contact.get('Name', '')).lower()
                    email = str(contact.get('Email', '')).lower()
                    company = str(contact.get('CompanyName', '')).lower()
                    
                    if 'adam' in name or 'adam' in email:
                        logger.info(f"🎯 FOUND ADAM: ID={contact.get('ContactId')} | Name={contact.get('Name')} | Email={contact.get('Email')} | Company={contact.get('CompanyName')}")
                        adam_found = True
                
                if not adam_found:
                    logger.info("❌ No contacts with 'adam' found")
                    
                    # Suggest a good test contact
                    if contacts_list:
                        test_contact = contacts_list[0]
                        logger.info(f"\n💡 Suggested test contact: ID={test_contact.get('ContactId')} | Name={test_contact.get('Name')} | Email={test_contact.get('Email')}")
                        return test_contact.get('ContactId')
                
    except Exception as e:
        logger.error(f"❌ Error getting CRM contacts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_crm_contacts())