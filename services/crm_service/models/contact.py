"""
Contact Data Model
Standardized contact representation for the CRM service
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class Contact:
    """Standardized contact model"""
    id: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None
    source: str = "lacrm"  # Source system
    
    @property
    def full_name(self) -> str:
        """Get full name of contact"""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p)
    
    @property
    def display_name(self) -> str:
        """Get display name prioritizing company then full name"""
        if self.company_name:
            return f"{self.company_name} ({self.full_name})" if self.full_name else self.company_name
        return self.full_name or self.email or "Unknown Contact"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary"""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'updated_at', 'last_synced']:
            if data[field] and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        """Create contact from dictionary"""
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'updated_at', 'last_synced']:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except ValueError:
                    data[field] = None
        
        return cls(**data)
    
    @classmethod
    def from_lacrm(cls, lacrm_data: Dict[str, Any]) -> 'Contact':
        """Create contact from LACRM API response"""
        # Extract address from LACRM format
        address = None
        if lacrm_data.get('Address'):
            address = {
                'street': lacrm_data.get('Address', ''),
                'city': lacrm_data.get('City', ''),
                'state': lacrm_data.get('State', ''),
                'zip': lacrm_data.get('Zip', ''),
                'country': lacrm_data.get('Country', 'US')
            }
        
        # Extract custom fields
        custom_fields = {}
        for key, value in lacrm_data.items():
            if key not in ['ContactId', 'Name', 'Company Name', 'Email', 'Phone', 
                          'Address', 'City', 'State', 'Zip', 'Country', 'Created', 'Modified']:
                custom_fields[key] = value
        
        # Parse created/modified dates
        created_at = None
        updated_at = None
        if lacrm_data.get('Created'):
            try:
                created_at = datetime.fromisoformat(lacrm_data['Created'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        if lacrm_data.get('Modified'):
            try:
                updated_at = datetime.fromisoformat(lacrm_data['Modified'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # Split name if provided as single field
        first_name = ""
        last_name = ""
        if lacrm_data.get('Name'):
            name_parts = lacrm_data['Name'].split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        return cls(
            id=str(lacrm_data.get('ContactId', '')),
            first_name=first_name,
            last_name=last_name,
            company_name=lacrm_data.get('Company Name'),
            email=lacrm_data.get('Email'),
            phone=lacrm_data.get('Phone'),
            address=address,
            custom_fields=custom_fields,
            created_at=created_at,
            updated_at=updated_at,
            last_synced=datetime.now(),
            source="lacrm"
        )
    
    def to_lacrm_format(self) -> Dict[str, Any]:
        """Convert contact to LACRM API format"""
        lacrm_data = {
            'ContactId': self.id,
            'Name': self.full_name,
            'Company Name': self.company_name,
            'Email': self.email,
            'Phone': self.phone,
        }
        
        # Add address fields
        if self.address:
            lacrm_data.update({
                'Address': self.address.get('street', ''),
                'City': self.address.get('city', ''),
                'State': self.address.get('state', ''),
                'Zip': self.address.get('zip', ''),
                'Country': self.address.get('country', 'US'),
            })
        
        # Add custom fields
        if self.custom_fields:
            lacrm_data.update(self.custom_fields)
        
        # Remove None values
        return {k: v for k, v in lacrm_data.items() if v is not None}
    
    def matches_query(self, query: str) -> bool:
        """Check if contact matches search query"""
        query_lower = query.lower()
        search_fields = [
            self.first_name or "",
            self.last_name or "",
            self.company_name or "",
            self.email or "",
            self.phone or ""
        ]
        
        return any(query_lower in field.lower() for field in search_fields)
    
    def similarity_score(self, query: str) -> float:
        """Calculate similarity score for ranking search results"""
        query_lower = query.lower()
        score = 0.0
        
        # Exact matches get highest score
        if query_lower == (self.company_name or "").lower():
            score += 100
        if query_lower == self.full_name.lower():
            score += 90
        if query_lower == (self.email or "").lower():
            score += 85
        
        # Partial matches get lower scores
        if query_lower in (self.company_name or "").lower():
            score += 50
        if query_lower in self.full_name.lower():
            score += 40
        if query_lower in (self.email or "").lower():
            score += 30
        
        # Phone number matching (remove formatting)
        clean_phone = "".join(c for c in (self.phone or "") if c.isdigit())
        clean_query = "".join(c for c in query if c.isdigit())
        if clean_query and clean_query in clean_phone:
            score += 35
        
        return score

@dataclass
class ContactSearchResult:
    """Search result wrapper for contacts"""
    contact: Contact
    score: float
    match_fields: list
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'contact': self.contact.to_dict(),
            'score': self.score,
            'match_fields': self.match_fields
        }