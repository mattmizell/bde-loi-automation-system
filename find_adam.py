#!/usr/bin/env python3
"""
Find Adam Castelli in CRM

Search for Adam in the CRM to find his exact contact details.
"""

import asyncio
import aiohttp
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def search_for_adam():
    """Search for Adam in various ways"""
    
    api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
    base_url = "https://api.lessannoyingcrm.com/v2/"
    
    search_terms = [
        "adam@betterdayenergy.com",
        "adam",
        "castelli",
        "Adam Castelli"
    ]
    
    async with aiohttp.ClientSession() as session:
        
        for search_term in search_terms:
            logger.info(f"🔍 Searching for: '{search_term}'")
            
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": api_key
                }
                
                body = {
                    "Function": "SearchContacts",
                    "Parameters": {
                        "SearchTerm": search_term
                    }
                }
                
                async with session.post(base_url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'ErrorCode' not in data and data:
                            logger.info(f"✅ Found results for '{search_term}':")
                            
                            if isinstance(data, list):
                                for i, contact in enumerate(data[:3]):  # Show first 3 results
                                    logger.info(f"   {i+1}. ID: {contact.get('ContactId')} | Name: {contact.get('Name')} | Email: {contact.get('Email')} | Company: {contact.get('CompanyName')}")
                            else:
                                logger.info(f"   ID: {data.get('ContactId')} | Name: {data.get('Name')} | Email: {data.get('Email')} | Company: {data.get('CompanyName')}")
                        else:
                            logger.info(f"❌ No results for '{search_term}'")
                            
                    else:
                        logger.error(f"❌ API error {response.status} for '{search_term}'")
                        
            except Exception as e:
                logger.error(f"❌ Error searching for '{search_term}': {e}")
            
            print()  # Add spacing

if __name__ == "__main__":
    asyncio.run(search_for_adam())