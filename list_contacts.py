#!/usr/bin/env python3
"""
List CRM contacts to find Adam

Get a list of contacts from the CRM to find Adam Castelli.
"""

import asyncio
import aiohttp
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def list_contacts():
    """List contacts from CRM"""
    
    api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
    base_url = "https://api.lessannoyingcrm.com/v2/"
    
    async with aiohttp.ClientSession() as session:
        
        logger.info("📋 Getting list of CRM contacts...")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": api_key
            }
            
            body = {
                "Function": "GetContactList",
                "Parameters": {}
            }
            
            async with session.post(base_url, headers=headers, json=body) as response:
                if response.status == 200:
                    response_text = await response.text()
                    logger.info(f"Raw response: {response_text[:500]}...")
                    
                    try:
                        data = json.loads(response_text)
                    except:
                        # Handle text/html response
                        data = response_text
                    
                    if isinstance(data, dict):
                        if 'ErrorCode' in data:
                            logger.error(f"❌ CRM API error: {data.get('ErrorCode')} - {data.get('ErrorDescription')}")
                        elif 'Results' in data:
                            contacts = data['Results']
                            logger.info(f"✅ Found {len(contacts)} contacts")
                            
                            # Look for Adam in the contacts
                            for contact in contacts:
                                name = contact.get('Name', '').lower()
                                email = contact.get('Email', '').lower()
                                company = contact.get('CompanyName', '').lower()
                                
                                if 'adam' in name or 'adam' in email or 'castelli' in name:
                                    logger.info(f"🎯 FOUND ADAM: ID={contact.get('ContactId')} | Name={contact.get('Name')} | Email={contact.get('Email')} | Company={contact.get('CompanyName')}")
                    
                    elif isinstance(data, list):
                        contacts = data
                        logger.info(f"✅ Found {len(contacts)} contacts")
                        
                        # Look for Adam in the contacts
                        for contact in contacts:
                            name = contact.get('Name', '').lower()
                            email = contact.get('Email', '').lower() 
                            company = contact.get('CompanyName', '').lower()
                            
                            if 'adam' in name or 'adam' in email or 'castelli' in name:
                                logger.info(f"🎯 FOUND ADAM: ID={contact.get('ContactId')} | Name={contact.get('Name')} | Email={contact.get('Email')} | Company={contact.get('CompanyName')}")
                    
                else:
                    logger.error(f"❌ HTTP error {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Error listing contacts: {e}")

if __name__ == "__main__":
    asyncio.run(list_contacts())