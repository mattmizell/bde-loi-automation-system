#!/usr/bin/env python3
"""
Cache Manager - Centralized customer data caching for form rationalization
Handles syncing data from all forms to the unified customer cache
"""

import logging
import json
import os
import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CustomerCacheManager:
    """Manages customer data cache for cross-form data sharing"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        
    def sync_customer_setup_to_cache(self, customer_id: str, form_data: Dict[str, Any]) -> bool:
        """Sync Customer Setup form data to cache"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Get customer email for cache lookup
                    cur.execute("SELECT email, company_name FROM customers WHERE id = %s", (customer_id,))
                    customer_result = cur.fetchone()
                    
                    if not customer_result:
                        logger.error(f"Customer {customer_id} not found")
                        return False
                    
                    customer_email, customer_company = customer_result
                    
                    # Prepare cache data from Customer Setup form
                    cache_data = {
                        'company_name': form_data.get('legal_business_name', customer_company),
                        'email': form_data.get('primary_contact_email', customer_email),
                        'phone': form_data.get('primary_contact_phone', ''),
                        'address': {
                            'street_address': form_data.get('physical_address', ''),
                            'city': form_data.get('physical_city', ''),
                            'state': form_data.get('physical_state', ''),
                            'zip_code': form_data.get('physical_zip', '')
                        },
                        'custom_fields': {
                            'federal_tax_id': form_data.get('federal_tax_id', ''),
                            'state_tax_id': form_data.get('state_tax_id', ''),
                            'business_type': form_data.get('business_type', ''),
                            'years_in_business': form_data.get('years_in_business', ''),
                            'annual_fuel_volume': form_data.get('annual_fuel_volume', ''),
                            'number_of_locations': form_data.get('number_of_locations', ''),
                            'dba_name': form_data.get('dba_name', ''),
                            'dispenser_count': form_data.get('dispenser_count', ''),
                            'pos_system': form_data.get('pos_system', ''),
                            'current_fuel_brands': form_data.get('current_fuel_brands', ''),
                            'mailing_address': {
                                'address': form_data.get('mailing_address', ''),
                                'city': form_data.get('mailing_city', ''),
                                'state': form_data.get('mailing_state', ''),
                                'zip': form_data.get('mailing_zip', '')
                            },
                            'accounts_payable_contact': form_data.get('accounts_payable_contact', ''),
                            'accounts_payable_email': form_data.get('accounts_payable_email', ''),
                            'accounts_payable_phone': form_data.get('accounts_payable_phone', ''),
                            'source_form': 'customer_setup'
                        }
                    }
                    
                    self._upsert_cache_record(cur, customer_email, cache_data)
                    logger.info(f"✅ Synced Customer Setup data to cache for {cache_data['company_name']}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error syncing Customer Setup to cache: {e}")
            return False
    
    def sync_eft_to_cache(self, customer_id: str, form_data: Dict[str, Any]) -> bool:
        """Sync EFT form data to cache"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Get existing cache data and merge with EFT data
                    customer_email = form_data.get('contact_email', '')
                    
                    if not customer_email:
                        # Fallback to customer table email
                        cur.execute("SELECT email FROM customers WHERE id = %s", (customer_id,))
                        result = cur.fetchone()
                        customer_email = result[0] if result else ''
                    
                    # Get existing cache data
                    existing_data = self._get_cache_record(cur, customer_email)
                    
                    # Merge EFT data with existing cache data
                    cache_data = existing_data or {
                        'company_name': form_data.get('company_name', ''),
                        'email': customer_email,
                        'phone': form_data.get('contact_phone', ''),
                        'address': {},
                        'custom_fields': {}
                    }
                    
                    # Update with EFT-specific data
                    cache_data.update({
                        'company_name': form_data.get('company_name', cache_data.get('company_name', '')),
                        'email': form_data.get('contact_email', cache_data.get('email', '')),
                        'phone': form_data.get('contact_phone', cache_data.get('phone', ''))
                    })
                    
                    # Merge address data
                    if 'address' not in cache_data:
                        cache_data['address'] = {}
                    cache_data['address'].update({
                        'street_address': form_data.get('company_address', cache_data['address'].get('street_address', '')),
                        'city': form_data.get('company_city', cache_data['address'].get('city', '')),
                        'state': form_data.get('company_state', cache_data['address'].get('state', '')),
                        'zip_code': form_data.get('company_zip', cache_data['address'].get('zip_code', ''))
                    })
                    
                    # Merge custom fields
                    if 'custom_fields' not in cache_data:
                        cache_data['custom_fields'] = {}
                    cache_data['custom_fields'].update({
                        'federal_tax_id': form_data.get('federal_tax_id', cache_data['custom_fields'].get('federal_tax_id', '')),
                        'primary_contact_name': form_data.get('contact_name', cache_data['custom_fields'].get('primary_contact_name', '')),
                        'bank_name': form_data.get('bank_name', ''),
                        'account_holder_name': form_data.get('account_holder_name', ''),
                        'authorized_by_name': form_data.get('authorized_by_name', ''),
                        'authorization_date': form_data.get('authorization_date', ''),
                        'eft_completed': True,
                        'source_form': 'eft'
                    })
                    
                    self._upsert_cache_record(cur, customer_email, cache_data)
                    logger.info(f"✅ Synced EFT data to cache for {cache_data['company_name']}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error syncing EFT to cache: {e}")
            return False
    
    def sync_loi_to_cache(self, customer_id: str, form_data: Dict[str, Any], loi_type: str = 'general') -> bool:
        """Sync LOI form data to cache"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Get customer email
                    cur.execute("SELECT email, company_name FROM customers WHERE id = %s", (customer_id,))
                    customer_result = cur.fetchone()
                    
                    if not customer_result:
                        logger.error(f"Customer {customer_id} not found")
                        return False
                    
                    customer_email, customer_company = customer_result
                    
                    # Get existing cache data
                    existing_data = self._get_cache_record(cur, customer_email)
                    
                    # Merge LOI data with existing cache data
                    cache_data = existing_data or {
                        'company_name': customer_company,
                        'email': customer_email,
                        'phone': '',
                        'address': {},
                        'custom_fields': {}
                    }
                    
                    # Update with LOI-specific data
                    if 'custom_fields' not in cache_data:
                        cache_data['custom_fields'] = {}
                    
                    loi_data = {
                        'station_name': form_data.get('station_name', ''),
                        'station_address': form_data.get('station_address', ''),
                        'station_city': form_data.get('station_city', ''),
                        'station_state': form_data.get('station_state', ''),
                        'station_zip': form_data.get('station_zip', ''),
                        'monthly_gasoline_gallons': form_data.get('monthly_gasoline_gallons', 0),
                        'monthly_diesel_gallons': form_data.get('monthly_diesel_gallons', 0),
                        'total_monthly_gallons': form_data.get('total_monthly_gallons', 0),
                        'volume_incentive_requested': form_data.get('volume_incentive_requested', 0),
                        'image_funding_requested': form_data.get('image_funding_requested', 0),
                        'contract_start_date': form_data.get('contract_start_date', ''),
                        'contract_term_years': form_data.get('contract_term_years', ''),
                        'authorized_representative': form_data.get('authorized_representative', ''),
                        'representative_title': form_data.get('representative_title', ''),
                        f'{loi_type}_loi_completed': True,
                        'source_form': f'{loi_type}_loi'
                    }
                    
                    cache_data['custom_fields'].update(loi_data)
                    
                    # Update contact info if provided in LOI
                    if form_data.get('email'):
                        cache_data['email'] = form_data.get('email')
                    if form_data.get('phone'):
                        cache_data['phone'] = form_data.get('phone')
                    
                    self._upsert_cache_record(cur, customer_email, cache_data)
                    logger.info(f"✅ Synced {loi_type} LOI data to cache for {cache_data['company_name']}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error syncing LOI to cache: {e}")
            return False
    
    def get_cached_customer_data(self, customer_email: str = None, customer_id: str = None) -> Optional[Dict[str, Any]]:
        """Get cached customer data for form prefilling"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    if customer_email:
                        return self._get_cache_record(cur, customer_email)
                    elif customer_id:
                        # Get email from customer ID first
                        cur.execute("SELECT email FROM customers WHERE id = %s", (customer_id,))
                        result = cur.fetchone()
                        if result:
                            return self._get_cache_record(cur, result[0])
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error retrieving cached customer data: {e}")
            return None
    
    def _get_cache_record(self, cur, email: str) -> Optional[Dict[str, Any]]:
        """Get existing cache record"""
        cur.execute("""
            SELECT company_name, email, phone, address, custom_fields, 
                   first_name, last_name
            FROM crm_contacts_cache 
            WHERE email = %s
            ORDER BY last_synced DESC 
            LIMIT 1
        """, (email,))
        
        result = cur.fetchone()
        if result:
            company_name, email, phone, address, custom_fields, first_name, last_name = result
            return {
                'company_name': company_name,
                'email': email,
                'phone': phone,
                'address': address if isinstance(address, dict) else (json.loads(address) if address else {}),
                'custom_fields': custom_fields if isinstance(custom_fields, dict) else (json.loads(custom_fields) if custom_fields else {}),
                'first_name': first_name,
                'last_name': last_name
            }
        return None
    
    def _upsert_cache_record(self, cur, email: str, cache_data: Dict[str, Any]):
        """Insert or update cache record"""
        # Extract names from contact data
        contact_name = cache_data['custom_fields'].get('primary_contact_name', '')
        name_parts = contact_name.split(' ', 1) if contact_name else ['', '']
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate contact_id if needed
        contact_id = f"form_{email.replace('@', '_').replace('.', '_')}"
        
        cur.execute("""
            INSERT INTO crm_contacts_cache (
                contact_id, first_name, last_name, company_name, email, phone, 
                address, custom_fields, created_at, updated_at, last_synced, source
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (contact_id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                company_name = EXCLUDED.company_name,
                email = EXCLUDED.email,
                phone = EXCLUDED.phone,
                address = EXCLUDED.address,
                custom_fields = EXCLUDED.custom_fields,
                updated_at = EXCLUDED.updated_at,
                last_synced = EXCLUDED.last_synced
        """, (
            contact_id,
            first_name,
            last_name, 
            cache_data['company_name'],
            cache_data['email'],
            cache_data['phone'],
            json.dumps(cache_data['address']),
            json.dumps(cache_data['custom_fields']),
            datetime.utcnow(),
            datetime.utcnow(),
            datetime.utcnow(),
            'forms'
        ))