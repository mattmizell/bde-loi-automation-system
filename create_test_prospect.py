#!/usr/bin/env python3
"""
Create Test Prospect - Farely Barnhart

Create a detailed test record in the CRM for Farely Barnhart with comprehensive
notes about his interest in switching Farley's Gas and Go to Better Day Energy.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
import json
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_farely_barnhart_prospect():
    """Create Farely Barnhart prospect record in CRM"""
    
    try:
        logger.info("👤 Creating Farely Barnhart prospect record...")
        
        # CRM API configuration
        api_key = "1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W"
        base_url = "https://api.lessannoyingcrm.com/v2/"
        
        # Contact details for Farely Barnhart
        contact_data = {
            "Function": "CreateContact",
            "Parameters": {
                "AssignedTo": 1073223,  # User ID from CRM system
                "IsCompany": False,
                "Name": "Farely Barnhart",
                "CompanyName": "Farley's Gas and Go",
                "Email": [
                    {
                        "Text": "matt.mizell@gmail.com",
                        "Type": "Work"
                    }
                ],
                "Phone": [
                    {
                        "Text": "(618) 555-0123",
                        "Type": "Work"
                    }
                ],
                "Address": [
                    {
                        "Street": "1425 Main Street",
                        "City": "Mascoutah", 
                        "State": "IL",
                        "Zip": "62258",
                        "Type": "Work"
                    }
                ],
                "JobTitle": "Owner/Operator",
                "Industry": "Fuel Retail",
                "CustomFields": [
                    {
                        "Name": "Lead Source",
                        "Value": "Cold Outreach"
                    },
                    {
                        "Name": "Business Type", 
                        "Value": "Independent Gas Station"
                    },
                    {
                        "Name": "Current Supplier",
                        "Value": "Regional Distributor"
                    },
                    {
                        "Name": "Monthly Gasoline Volume (gallons)",
                        "Value": "85000"
                    },
                    {
                        "Name": "Monthly Diesel Volume (gallons)",
                        "Value": "25000"
                    },
                    {
                        "Name": "Lead Priority",
                        "Value": "High"
                    },
                    {
                        "Name": "Interest Level",
                        "Value": "Very Interested"
                    },
                    {
                        "Name": "Decision Timeline",
                        "Value": "60-90 Days"
                    },
                    {
                        "Name": "Annual Fuel Volume",
                        "Value": "1,320,000 gallons"
                    },
                    {
                        "Name": "Estimated Total Incentives",
                        "Value": "$125,000"
                    },
                    {
                        "Name": "Image Funding Amount",
                        "Value": "$75,000"
                    },
                    {
                        "Name": "Incentive Funding Amount", 
                        "Value": "$50,000"
                    },
                    {
                        "Name": "Conversion Priority",
                        "Value": "Q3 2025"
                    }
                ]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": api_key
            }
            
            # Create the contact
            async with session.post(base_url, headers=headers, json=contact_data) as response:
                response_text = await response.text()
                logger.info(f"CRM API Response Status: {response.status}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        
                        if 'ErrorCode' not in data:
                            contact_id = data.get('ContactId')
                            logger.info(f"✅ Created contact: Farely Barnhart")
                            logger.info(f"📧 Email: matt.mizell@gmail.com")
                            logger.info(f"🏢 Company: Farley's Gas and Go")
                            logger.info(f"🆔 Contact ID: {contact_id}")
                            
                            # Add detailed notes about his interest
                            await add_detailed_notes(session, headers, contact_id)
                            
                            return contact_id
                        else:
                            logger.error(f"❌ CRM API error: {data.get('ErrorCode')} - {data.get('ErrorDescription')}")
                            return None
                    except json.JSONDecodeError:
                        logger.error(f"❌ Invalid JSON response: {response_text[:200]}")
                        return None
                else:
                    logger.error(f"❌ HTTP error {response.status}: {response_text[:200]}")
                    return None
                    
    except Exception as e:
        logger.error(f"❌ Error creating prospect: {e}")
        return None

async def add_detailed_notes(session, headers, contact_id):
    """Add comprehensive notes about Farely's interest in BDE"""
    
    notes = [
        {
            "title": "Initial Contact - Cold Outreach Success",
            "content": """INITIAL CONTACT - COLD OUTREACH
Date: June 23, 2025
Contact Method: Phone Call
Duration: 45 minutes
Outcome: VERY POSITIVE RESPONSE

Farely Barnhart, owner of Farley's Gas and Go in Mascoutah, IL, responded extremely well to our cold outreach. He has been looking for alternatives to his current fuel supplier due to:

1. PRICING ISSUES:
   - Current supplier rates 3-5 cents above market
   - No volume discounts despite high monthly volume
   - Inconsistent pricing structure

2. SERVICE PROBLEMS:
   - Delivery delays affecting operations
   - Poor customer service response times
   - Limited account management support

3. GROWTH LIMITATIONS:
   - Current supplier cannot support expansion plans
   - No rebate/incentive programs available
   - Rigid contract terms

IMMEDIATE INTEREST:
Farely expressed strong interest in Better Day Energy's value proposition, particularly:
- Competitive pricing with transparent structure
- Reliable delivery scheduling
- Image program funding opportunities
- Dedicated account management

NEXT STEPS:
- Scheduled for detailed proposal presentation
- Requested LOI for volume commitments
- Timeline: Wants to switch by Q3 2025

STATUS: HOT PROSPECT - HIGH PRIORITY"""
        },
        {
            "title": "Business Analysis - Farley's Gas and Go",
            "content": """BUSINESS ANALYSIS - FARLEY'S GAS AND GO

LOCATION DETAILS:
Address: 1425 Main Street, Mascoutah, IL 62258
Type: Highway location with high traffic volume
Demographics: Serves local community + highway travelers
Competition: 2 other stations within 3 miles

CURRENT OPERATIONS:
Business Hours: 5:00 AM - 11:00 PM daily
Employees: 8 full-time, 4 part-time
Convenience Store: 2,400 sq ft with full deli
Car Wash: 2-bay automatic wash

FUEL VOLUME ANALYSIS:
Monthly Gasoline: 85,000 gallons
Monthly Diesel: 25,000 gallons
Annual Total: 1,320,000 gallons
Peak Months: May-August (summer travel)
Growth Trend: +12% year-over-year

FINANCIAL PROFILE:
Annual Revenue: ~$4.2 million
Fuel Margin: Currently 8-12 cents/gallon
Credit Rating: Excellent (750+ FICO)
Cash Flow: Strong and consistent

INFRASTRUCTURE:
Tanks: 4 gasoline (10K each), 2 diesel (8K each)
Age: Tanks installed 2018 (7 years old)
Condition: Excellent, all compliance current
Dispensers: 8 pumps, modern POS integration

EXPANSION PLANS:
- Adding EV charging stations (2026)
- Expanding convenience store
- Potential second location in nearby town

DECISION MAKERS:
Primary: Farely Barnhart (Owner, 100% decision authority)
Influences: His brother Tom (Operations Manager)
Accountant: Sarah Chen, CPA (financial review)

CONVERSION READINESS: EXCELLENT
- Infrastructure compatible
- Financial capacity confirmed
- Decision authority clear
- Timeline alignment good"""
        },
        {
            "title": "Competitive Analysis & Value Proposition",
            "content": """COMPETITIVE ANALYSIS & BDE VALUE PROPOSITION

CURRENT SUPPLIER ISSUES:
Supplier: Midwest Regional Fuel Distribution
Contract: Month-to-month (no long-term commitment)
Pricing: Cost+ model, 3-5¢ above rack
Delivery: Inconsistent, 2-3 day lead times
Service: Poor responsiveness, no dedicated rep

BDE COMPETITIVE ADVANTAGES:
1. PRICING BENEFITS:
   - Guaranteed savings of 2-4¢/gallon
   - Volume discounts at 75K+ gallons/month
   - Price protection during market volatility
   - Transparent, predictable pricing structure

2. SERVICE EXCELLENCE:
   - Dedicated account manager (region specialist)
   - 24/7 emergency support
   - Guaranteed delivery windows
   - Advanced logistics planning

3. FINANCIAL INCENTIVES:
   - Image Program: $75,000 funding available
   - Volume Incentives: $50,000 annual potential
   - Equipment financing: Competitive rates
   - Working capital support if needed

4. PARTNERSHIP APPROACH:
   - Business growth consulting
   - Market intelligence sharing
   - Technology integration support
   - Long-term relationship focus

ESTIMATED ANNUAL SAVINGS:
Direct Cost Savings: $39,600 (3¢/gal x 1.32M gal)
Volume Incentives: $50,000
Image Program Value: $75,000 (one-time)
TOTAL FIRST YEAR VALUE: $164,600

ROI ANALYSIS:
- Monthly savings: $3,300+ 
- Payback period: Immediate
- 3-year value: $215,000+

RISK MITIGATION:
- Performance guarantees in contract
- Service level agreements
- Price protection mechanisms
- Exit clauses if unsatisfied

CONVERSION TIMELINE:
Weeks 1-2: LOI execution and due diligence
Weeks 3-4: Contract finalization
Weeks 5-6: Logistics setup and testing
Week 7: Go-live with full BDE supply

FARELY'S RESPONSE:
"This is exactly what I've been looking for. My current supplier treats me like just another account number. BDE's approach feels like a real partnership."

STATUS: READY FOR LOI PRESENTATION"""
        },
        {
            "title": "LOI Preparation - Key Terms & Timeline",
            "content": """LOI PREPARATION - FARELY BARNHART
Farley's Gas and Go Conversion

PROPOSED LOI TERMS:
Volume Commitment: 110,000 gallons/month minimum
- Gasoline: 85,000 gallons/month
- Diesel: 25,000 gallons/month
Contract Duration: 36 months
Start Date: August 1, 2025 (target)

PRICING STRUCTURE:
- Base pricing: Rack + competitive margin
- Volume discount: 2¢/gallon at 100K+ monthly
- Additional discount: 1¢/gallon at 125K+ monthly
- Price review: Quarterly with market adjustments

INCENTIVE PACKAGE:
Image Program Funding: $75,000
- Canopy refresh/branding
- Signage updates
- POS integration
- Marketing materials

Performance Incentives: $50,000 annually
- Based on volume commitments
- Paid quarterly
- Growth bonuses available

DELIVERABLES FROM BDE:
- Dedicated account management
- Twice-weekly delivery schedule
- Emergency delivery capability
- 24/7 support hotline
- Monthly business reviews

CUSTOMER COMMITMENTS:
- Volume minimums as specified
- Exclusive fuel purchasing (no dual sourcing)
- BDE branding compliance
- Payment terms: Net 15 days

IMPLEMENTATION SUPPORT:
- Transition planning and coordination
- Staff training on new procedures
- Marketing launch support
- System integration assistance

SPECIAL CONSIDERATIONS:
- Current contract termination (30-day notice)
- Tank gauge system integration
- Existing brand removal and disposal
- Environmental compliance verification

APPROVAL PROCESS:
1. LOI review and execution (Farely)
2. Financial verification (Sarah Chen, CPA)
3. Site survey and compliance check (BDE team)
4. Final contract negotiation
5. Implementation planning

RISK FACTORS:
- Minimal - excellent credit, good infrastructure
- Current supplier non-compete: None
- Environmental issues: None identified
- Zoning/permits: All current and compliant

EXPECTED CLOSE TIMELINE:
LOI Signature Target: Within 5 business days
Contract Execution: 2-3 weeks post-LOI
Go-Live Date: August 1, 2025

INTERNAL APPROVALS NEEDED:
- Credit approval: Pre-qualified based on financials
- Operations approval: Site survey required
- Legal review: Standard terms, minimal risk

FARELY'S DECISION FACTORS:
1. Cost savings (PRIMARY - very price sensitive)
2. Service reliability (CRITICAL - past bad experience)
3. Growth support (IMPORTANT - expansion plans)
4. Partnership approach (VALUABLE - wants consultative relationship)

CLOSE PROBABILITY: 85% - Excellent prospect
URGENCY: High - wants summer implementation
COMPETITION: None identified currently

NEXT ACTION: Prepare and send LOI for signature
ASSIGNED TO: LOI Automation System
TARGET SEND DATE: Immediate"""
        }
    ]
    
    base_url = "https://api.lessannoyingcrm.com/v2/"
    
    for note in notes:
        try:
            note_data = {
                "Function": "CreateNote",
                "Parameters": {
                    "ContactId": contact_id,
                    "Note": f"{note['title']}\n\n{note['content']}\n\n---\nAdded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nBy: LOI Automation System"
                }
            }
            
            async with session.post(base_url, headers=headers, json=note_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'ErrorCode' not in data:
                        logger.info(f"📝 Added note: {note['title']}")
                    else:
                        logger.error(f"❌ Failed to add note: {data.get('ErrorDescription')}")
                else:
                    logger.error(f"❌ HTTP error adding note: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Error adding note '{note['title']}': {e}")

async def main():
    """Main function"""
    
    print("👤 Creating Farely Barnhart Test Prospect")
    print("🏢 Company: Farley's Gas and Go")
    print("📧 Email: matt.mizell@gmail.com")
    print("=" * 60)
    
    contact_id = await create_farely_barnhart_prospect()
    
    if contact_id:
        print(f"\n✅ Successfully created prospect record!")
        print(f"📋 Contact ID: {contact_id}")
        print(f"👤 Name: Farely Barnhart")
        print(f"🏢 Company: Farley's Gas and Go")
        print(f"📧 Email: matt.mizell@gmail.com")
        print(f"📍 Location: Mascoutah, IL")
        print(f"⛽ Monthly Volume: 110,000 gallons")
        print(f"💰 Estimated Value: $164,600 first year")
        print(f"📝 Status: Ready for LOI workflow testing")
        print(f"\n🔄 Ready to test complete LOI automation workflow!")
    else:
        print(f"\n❌ Failed to create prospect record")
        print(f"📋 Check logs for details")

if __name__ == "__main__":
    asyncio.run(main())