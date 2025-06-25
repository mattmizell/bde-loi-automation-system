"""
Search Service
Advanced contact search with fuzzy matching and ranking
"""

import logging
from typing import List, Dict, Any
from difflib import SequenceMatcher
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.crm_service.models.contact import Contact, ContactSearchResult
from services.crm_service.data.contact_repository import ContactRepository

logger = logging.getLogger(__name__)

class SearchService:
    """Advanced contact search service"""
    
    def __init__(self):
        self.repository = ContactRepository()
    
    def search_contacts(self, query: str, options: Dict[str, Any]) -> List[ContactSearchResult]:
        """Search contacts with advanced ranking and fuzzy matching"""
        try:
            # Get initial results from database
            db_results = self.repository.search_contacts(query, limit=options.get('limit', 20) * 2)
            
            # Apply fuzzy matching and scoring
            scored_results = []
            for contact in db_results:
                score = self._calculate_similarity_score(contact, query, options)
                
                if score >= options.get('fuzzy_threshold', 0.6):
                    match_fields = self._get_match_fields(contact, query)
                    result = ContactSearchResult(
                        contact=contact,
                        score=score,
                        match_fields=match_fields
                    )
                    scored_results.append(result)
            
            # Sort by score (highest first)
            scored_results.sort(key=lambda x: x.score, reverse=True)
            
            # Apply limit
            limit = options.get('limit', 20)
            return scored_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []
    
    def _calculate_similarity_score(self, contact: Contact, query: str, options: Dict[str, Any]) -> float:
        """Calculate similarity score for contact"""
        query_lower = query.lower()
        scores = []
        
        # Company name matching (highest weight)
        if contact.company_name:
            company_score = self._fuzzy_match(query_lower, contact.company_name.lower())
            scores.append(company_score * 3.0)  # 3x weight for company
        
        # Full name matching
        full_name = contact.full_name.lower()
        if full_name:
            name_score = self._fuzzy_match(query_lower, full_name)
            scores.append(name_score * 2.0)  # 2x weight for name
        
        # Email matching
        if contact.email:
            email_score = self._fuzzy_match(query_lower, contact.email.lower())
            scores.append(email_score * 1.5)  # 1.5x weight for email
        
        # Phone matching (exact digits only)
        if contact.phone:
            clean_phone = ''.join(c for c in contact.phone if c.isdigit())
            clean_query = ''.join(c for c in query if c.isdigit())
            if clean_query and len(clean_query) >= 4:
                phone_score = 1.0 if clean_query in clean_phone else 0.0
                scores.append(phone_score * 1.2)  # 1.2x weight for phone
        
        # Return weighted average
        return max(scores) if scores else 0.0
    
    def _fuzzy_match(self, query: str, text: str) -> float:
        """Calculate fuzzy match score between query and text"""
        if not query or not text:
            return 0.0
        
        # Exact match gets perfect score
        if query == text:
            return 1.0
        
        # Substring match gets high score
        if query in text:
            return 0.9
        
        # Use sequence matcher for fuzzy matching
        return SequenceMatcher(None, query, text).ratio()
    
    def _get_match_fields(self, contact: Contact, query: str) -> List[str]:
        """Get list of fields that matched the query"""
        query_lower = query.lower()
        match_fields = []
        
        if contact.company_name and query_lower in contact.company_name.lower():
            match_fields.append('company_name')
        
        if query_lower in contact.full_name.lower():
            match_fields.append('name')
        
        if contact.email and query_lower in contact.email.lower():
            match_fields.append('email')
        
        if contact.phone:
            clean_phone = ''.join(c for c in contact.phone if c.isdigit())
            clean_query = ''.join(c for c in query if c.isdigit())
            if clean_query and clean_query in clean_phone:
                match_fields.append('phone')
        
        return match_fields