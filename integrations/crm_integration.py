"""
Less Annoying CRM Integration

Handles retrieval of LOI form submissions from Less Annoying CRM API.
Provides data validation and standardization for LOI processing.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from ..core.loi_transaction_queue import LOITransaction

logger = logging.getLogger(__name__)

class LessAnnoyingCRMIntegration:
    """
    Integration with Less Annoying CRM for LOI form data retrieval.
    
    Capabilities:
    - Retrieve form submissions via API
    - Validate and standardize form data
    - Handle API errors and retries
    - Map CRM fields to LOI processing format
    """
    
    def __init__(self, api_key: str = None, base_url: str = None):
        # Use CRM Bridge instead of direct LACRM API
        self.crm_bridge_url = "https://loi-automation-api.onrender.com/api/v1/crm-bridge"
        self.crm_bridge_token = "bde_loi_auth_e6db5173a4393421ffadae85f9a3513e"
        
        # Legacy parameters (deprecated)
        self.api_key = api_key
        self.base_url = base_url
        
        # CRM field mapping for LOI forms
        self.field_mapping = {
            # Customer Information
            'Company/Business Name': 'company_business_name',
            'Contact Person Name': 'contact_person_name', 
            'Contact Person Title': 'contact_person_title',
            'Business Address Street': 'business_address_street',
            'Business Address City': 'business_address_city',
            'Business Address State': 'business_address_state',
            'Business Address ZIP': 'business_address_zip',
            'Email Address': 'email_address',
            'Phone Number': 'phone_number',
            
            # Fuel Supply Details
            'Monthly Gasoline Volume (gallons)': 'monthly_gasoline_volume',
            'Monthly Diesel Volume (gallons)': 'monthly_diesel_volume',
            'Current Fuel Supplier': 'current_fuel_supplier',
            'Estimated Conversion Date': 'estimated_conversion_date',
            
            # Financial Information
            'Image Funding Amount': 'image_funding_amount',
            'Incentive Funding Amount': 'incentive_funding_amount',
            'Total Estimated Incentives': 'total_estimated_incentives',
            
            # Project Specifications
            'Canopy Installation Required': 'canopy_installation_required',
            'Current Branding to Remove': 'current_branding_to_remove',
            'Special Requirements/Notes': 'special_requirements_notes'
        }
        
        self.integration_stats = {
            'forms_retrieved': 0,
            'api_calls_made': 0,
            'errors_encountered': 0,
            'last_sync': None
        }
        
        logger.info("🔗 Less Annoying CRM Integration initialized")
    
    async def retrieve_loi_form_data(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Retrieve LOI form data for a transaction"""
        
        try:
            # Check if we already have CRM data
            if transaction.crm_form_data and transaction.crm_form_data.get('crm_retrieved'):
                logger.info(f"📋 CRM data already retrieved for {transaction.id}")
                return {
                    'success': True,
                    'form_data': transaction.crm_form_data,
                    'source': 'cached'
                }
            
            # Get form submission ID from transaction context
            form_submission_id = transaction.processing_context.get('crm_form_id')
            if not form_submission_id:
                # Try to find form by customer email
                customer_email = transaction.customer_data.get('email')
                if customer_email:
                    form_submission_id = await self._find_form_by_email(customer_email)
            
            if not form_submission_id:
                raise Exception("No CRM form submission ID found for transaction")
            
            # Retrieve form data from CRM
            form_data = await self._get_form_submission(form_submission_id)
            
            # Validate and standardize data
            standardized_data = self._standardize_form_data(form_data)
            
            # Validate required fields
            validation_result = self._validate_form_data(standardized_data)
            if not validation_result['valid']:
                raise Exception(f"Form data validation failed: {validation_result['errors']}")
            
            # Update stats
            self.integration_stats['forms_retrieved'] += 1
            self.integration_stats['last_sync'] = datetime.now()
            
            logger.info(f"📋 Successfully retrieved CRM data for {transaction.id}")
            
            return {
                'success': True,
                'form_data': standardized_data,
                'source': 'crm_api',
                'form_submission_id': form_submission_id,
                'retrieved_at': datetime.now().isoformat(),
                'validation_score': validation_result['score']
            }
            
        except Exception as e:
            self.integration_stats['errors_encountered'] += 1
            logger.error(f"❌ Failed to retrieve CRM data for {transaction.id}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'fallback_data': self._create_fallback_data(transaction)
            }
    
    async def _get_form_submission(self, submission_id: str) -> Dict[str, Any]:
        """Get form submission from Less Annoying CRM API"""
        
        self.integration_stats['api_calls_made'] += 1
        
        async with aiohttp.ClientSession() as session:
            
            # Use CRM Bridge instead of direct LACRM API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.crm_bridge_token}"
            }
            
            # Search for contact by ID using CRM bridge
            search_body = {
                "query": submission_id,
                "limit": 1
            }
            
            async with session.post(f"{self.crm_bridge_url}/contacts/search", headers=headers, json=search_body) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success') and data.get('contacts'):
                        # Return first contact in LACRM format for compatibility
                        contact = data['contacts'][0]
                        return {
                            'ContactId': contact['contact_id'],
                            'Name': contact['name'],
                            'CompanyName': contact['company_name'],
                            'Email': contact['email'],
                            'Phone': contact['phone']
                        }
                    else:
                        return None
                else:
                    raise Exception(f"CRM Bridge returned status {response.status}")
    
    async def _find_form_by_email(self, email: str) -> Optional[str]:
        """Find form submission by customer email"""
        
        try:
            self.integration_stats['api_calls_made'] += 1
            
            async with aiohttp.ClientSession() as session:
                
                # Search for contact by email using CRM Bridge
                headers = {
                    "Content-Type": "application/json", 
                    "Authorization": f"Bearer {self.crm_bridge_token}"
                }
                
                body = {
                    "query": email,
                    "limit": 1
                }
                
                async with session.post(f"{self.crm_bridge_url}/contacts/search", headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('success') and data.get('contacts'):
                            # Return first matching contact ID
                            contacts = data['contacts']
                            if contacts:
                                return contacts[0]['contact_id']
                    
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error searching for contact by email {email}: {e}")
            return None
    
    def _standardize_form_data(self, raw_form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize CRM form data to LOI processing format"""
        
        standardized = {
            'crm_retrieved': True,
            'crm_contact_id': raw_form_data.get('ContactId'),
            'crm_last_modified': raw_form_data.get('LastModified')
        }
        
        # Map custom fields
        custom_fields = raw_form_data.get('CustomFields', [])
        
        for field in custom_fields:
            field_name = field.get('Name', '')
            field_value = field.get('Value', '')
            
            # Map to standardized field name
            if field_name in self.field_mapping:
                standardized_name = self.field_mapping[field_name]
                standardized[standardized_name] = self._convert_field_value(standardized_name, field_value)
        
        # Also map standard contact fields
        standardized.update({
            'company_business_name': raw_form_data.get('CompanyName', ''),
            'contact_person_name': raw_form_data.get('Name', ''),
            'email_address': raw_form_data.get('Email', ''),
            'phone_number': raw_form_data.get('Phone', '')
        })
        
        return standardized
    
    def _convert_field_value(self, field_name: str, field_value: str) -> Any:
        """Convert field value to appropriate type"""
        
        if not field_value or field_value.strip() == '':
            return None
        
        # Numeric fields
        numeric_fields = [
            'monthly_gasoline_volume',
            'monthly_diesel_volume', 
            'image_funding_amount',
            'incentive_funding_amount',
            'total_estimated_incentives'
        ]
        
        if field_name in numeric_fields:
            try:
                # Remove commas and dollar signs
                cleaned_value = field_value.replace(',', '').replace('$', '').strip()
                return float(cleaned_value)
            except ValueError:
                return 0.0
        
        # Boolean fields
        boolean_fields = ['canopy_installation_required']
        
        if field_name in boolean_fields:
            return field_value.lower() in ['yes', 'true', '1', 'on']
        
        # Date fields
        date_fields = ['estimated_conversion_date']
        
        if field_name in date_fields:
            try:
                # Try to parse common date formats
                for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                    try:
                        parsed_date = datetime.strptime(field_value, date_format)
                        return parsed_date.isoformat()
                    except ValueError:
                        continue
                return field_value  # Return as string if parsing fails
            except:
                return field_value
        
        # Default: return as string
        return field_value.strip()
    
    def _validate_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate form data completeness and accuracy"""
        
        errors = []
        warnings = []
        score = 100.0
        
        # Required fields validation
        required_fields = [
            'company_business_name',
            'contact_person_name',
            'email_address',
            'monthly_gasoline_volume',
            'monthly_diesel_volume'
        ]
        
        for field in required_fields:
            if not form_data.get(field):
                errors.append(f"Missing required field: {field}")
                score -= 20
        
        # Data quality checks
        if form_data.get('email_address'):
            email = form_data['email_address']
            if '@' not in email or '.' not in email:
                errors.append("Invalid email address format")
                score -= 10
        
        # Volume validation
        gas_volume = form_data.get('monthly_gasoline_volume', 0)
        diesel_volume = form_data.get('monthly_diesel_volume', 0)
        
        if gas_volume <= 0 and diesel_volume <= 0:
            errors.append("At least one fuel volume must be greater than 0")
            score -= 15
        
        if gas_volume > 1000000 or diesel_volume > 1000000:
            warnings.append("Very high fuel volumes detected - please verify")
            score -= 5
        
        # Financial validation
        total_incentives = form_data.get('total_estimated_incentives', 0)
        image_funding = form_data.get('image_funding_amount', 0)
        incentive_funding = form_data.get('incentive_funding_amount', 0)
        
        calculated_total = image_funding + incentive_funding
        if total_incentives > 0 and abs(total_incentives - calculated_total) > 1000:
            warnings.append("Total incentives doesn't match sum of components")
            score -= 5
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'score': max(score, 0)
        }
    
    def _create_fallback_data(self, transaction: LOITransaction) -> Dict[str, Any]:
        """Create fallback data when CRM retrieval fails"""
        
        customer_data = transaction.customer_data
        
        return {
            'company_business_name': customer_data.get('company_name', ''),
            'contact_person_name': customer_data.get('contact_name', ''),
            'email_address': customer_data.get('email', ''),
            'phone_number': customer_data.get('phone', ''),
            'fallback_mode': True,
            'manual_review_required': True
        }
    
    async def get_recent_submissions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent LOI form submissions from CRM"""
        
        try:
            self.integration_stats['api_calls_made'] += 1
            
            async with aiohttp.ClientSession() as session:
                
                # Get recent contacts (Less Annoying CRM doesn't have direct form submission endpoint)
                url = f"{self.base_url}/GetContacts"
                params = {
                    'UserCode': self.api_user,
                    'APIToken': self.api_token,
                    'ModifiedSince': (datetime.now() - timedelta(hours=hours)).isoformat()
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('Success'):
                            contacts = data.get('Result', [])
                            
                            # Filter for contacts that appear to be LOI submissions
                            loi_submissions = []
                            for contact in contacts:
                                if self._is_loi_submission(contact):
                                    loi_submissions.append(contact)
                            
                            return loi_submissions
                    
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error retrieving recent submissions: {e}")
            return []
    
    def _is_loi_submission(self, contact: Dict[str, Any]) -> bool:
        """Determine if a contact is an LOI form submission"""
        
        # Check for LOI-specific custom fields
        custom_fields = contact.get('CustomFields', [])
        field_names = [field.get('Name', '') for field in custom_fields]
        
        # Look for LOI-specific fields
        loi_indicators = [
            'Monthly Gasoline Volume',
            'Monthly Diesel Volume',
            'Total Estimated Incentives',
            'Canopy Installation Required'
        ]
        
        return any(indicator in field_name for field_name in field_names for indicator in loi_indicators)
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration performance statistics"""
        
        return {
            'integration_type': 'less_annoying_crm',
            'stats': self.integration_stats,
            'field_mappings': len(self.field_mapping),
            'api_endpoint': self.base_url
        }

# Async wrapper function for coordinator integration
async def handle_crm_integration(transaction: LOITransaction) -> Dict[str, Any]:
    """Handle CRM integration - async wrapper for coordinator"""
    
    # Get API key from environment configuration
    import os
    api_key = os.getenv('CRM_API_KEY', '1073223-4036284360051868673733029852600-hzOnMMgwOvTV86XHs9c4H3gF5I7aTwO33PJSRXk9yQT957IY1W')
    
    crm_integration = LessAnnoyingCRMIntegration(api_key)
    return await crm_integration.retrieve_loi_form_data(transaction)