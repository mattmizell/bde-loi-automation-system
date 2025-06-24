"""
AI Integration for LOI Automation System

Handles AI decision making using Grok API for transaction processing,
risk assessment, and workflow optimization.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

from ..core.loi_transaction_queue import LOITransaction

logger = logging.getLogger(__name__)

class GrokAIIntegration:
    """
    Grok AI integration for intelligent LOI processing decisions.
    
    Capabilities:
    - Transaction priority assessment
    - Risk factor analysis
    - Processing workflow optimization
    - Customer type classification
    - Document quality validation
    - Completion prediction
    """
    
    def __init__(self, api_key: str = None):
        # Use the same API key from the transaction coordinator
        self.api_key = api_key or "xai-730cElC0cSJcQ8KgbpaMZ32MrwhV1m563LNfxWr5zgc9UTkwBr2pYm36s86948sPHcJf8yH6rw9AgQUi"
        self.base_url = "https://api.x.ai/v1/chat/completions"
        
        # AI configuration
        self.ai_config = {
            'model': 'grok-3-latest',
            'temperature': 0.1,
            'max_tokens': 1000,
            'timeout': 30
        }
        
        # Decision caching
        self.decision_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Statistics
        self.ai_stats = {
            'decisions_made': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0,
            'average_response_time': 0.0,
            'last_decision': None
        }
        
        logger.info("🧠 Grok AI Integration initialized")
    
    async def make_loi_decision(self, transaction: LOITransaction, decision_type: str = "initial_assessment") -> Dict[str, Any]:
        """Make AI decision for LOI transaction"""
        
        start_time = datetime.now()
        
        try:
            # Create decision context
            decision_context = self._create_decision_context(transaction, decision_type)
            
            # Check cache first
            cache_key = self._generate_cache_key(decision_context)
            cached_decision = self._get_cached_decision(cache_key)
            
            if cached_decision:
                self.ai_stats['cache_hits'] += 1
                logger.info(f"🧠 Using cached AI decision for {transaction.id}")
                return cached_decision
            
            # Make AI API call
            ai_response = await self._call_grok_api(decision_context)
            
            # Process AI response
            decision = self._process_ai_response(ai_response, transaction, decision_type)
            
            # Cache decision
            self._cache_decision(cache_key, decision)
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_ai_stats(processing_time)
            
            logger.info(f"🧠 AI decision made for {transaction.id}: {decision['decision_type']}")
            return decision
            
        except Exception as e:
            self.ai_stats['errors'] += 1
            logger.error(f"❌ AI decision failed for {transaction.id}: {e}")
            
            # Return fallback decision
            return self._create_fallback_decision(transaction, decision_type, str(e))
    
    def _create_decision_context(self, transaction: LOITransaction, decision_type: str) -> Dict[str, Any]:
        """Create context for AI decision making"""
        
        customer_data = transaction.customer_data
        crm_data = transaction.crm_form_data
        
        # Calculate total fuel volume
        total_volume = crm_data.get('monthly_gasoline_volume', 0) + crm_data.get('monthly_diesel_volume', 0)
        
        # Calculate incentive ratio
        total_incentives = crm_data.get('total_estimated_incentives', 0)
        incentive_ratio = total_incentives / (total_volume * 12) if total_volume > 0 else 0
        
        context = {
            'transaction_id': transaction.id,
            'decision_type': decision_type,
            'customer_profile': {
                'company_name': customer_data.get('company_name', ''),
                'is_vip': customer_data.get('is_vip_customer', False),
                'customer_type': customer_data.get('customer_type', 'unknown'),
                'email_domain': customer_data.get('email', '').split('@')[-1] if customer_data.get('email') else '',
                'location': {
                    'state': customer_data.get('business_address', {}).get('state', ''),
                    'city': customer_data.get('business_address', {}).get('city', '')
                }
            },
            'fuel_requirements': {
                'monthly_gasoline_volume': crm_data.get('monthly_gasoline_volume', 0),
                'monthly_diesel_volume': crm_data.get('monthly_diesel_volume', 0),
                'total_monthly_volume': total_volume,
                'current_supplier': crm_data.get('current_fuel_supplier', ''),
                'conversion_timeline': crm_data.get('estimated_conversion_date')
            },
            'financial_profile': {
                'image_funding': crm_data.get('image_funding_amount', 0),
                'incentive_funding': crm_data.get('incentive_funding_amount', 0),
                'total_incentives': total_incentives,
                'incentive_per_gallon_ratio': incentive_ratio
            },
            'project_requirements': {
                'canopy_installation': crm_data.get('canopy_installation_required', False),
                'branding_removal': crm_data.get('current_branding_to_remove', ''),
                'special_requirements': crm_data.get('special_requirements_notes', '')
            },
            'transaction_metadata': {
                'created_at': transaction.created_at.isoformat(),
                'current_stage': transaction.workflow_stage,
                'processing_context': transaction.processing_context
            }
        }
        
        return context
    
    async def _call_grok_api(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call to Grok for AI decision"""
        
        self.ai_stats['api_calls'] += 1
        
        # Create system prompt based on decision type
        system_prompt = self._get_system_prompt(decision_context['decision_type'])
        
        # Create user prompt with context
        user_prompt = self._create_user_prompt(decision_context)
        
        # Prepare API request
        payload = {
            'model': self.ai_config['model'],
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': self.ai_config['temperature'],
            'max_tokens': self.ai_config['max_tokens'],
            'functions': self._get_function_definitions(),
            'function_call': 'auto'
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.ai_config['timeout'])
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Grok API error {response.status}: {error_text}")
    
    def _get_system_prompt(self, decision_type: str) -> str:
        """Get system prompt based on decision type"""
        
        prompts = {
            'initial_assessment': """
You are an expert fuel supply agreement analyst for Better Day Energy, specializing in VP Racing branded fuel supply agreements. Your role is to analyze Letter of Intent (LOI) requests and provide intelligent assessments for processing optimization.

Key responsibilities:
1. Assess transaction priority based on business value, customer profile, and urgency
2. Identify risk factors that may impact successful completion
3. Classify customer type and recommend processing approach
4. Estimate complexity and resource requirements
5. Provide routing recommendations for optimal workflow

Consider these business factors:
- VP Racing brand positioning and market strategy
- Fuel volume significance (high volume = high priority)
- Financial incentive levels and sustainability
- Customer relationship potential and lifetime value
- Geographic market opportunities
- Competitive displacement opportunities
- Implementation complexity and resource requirements

Provide structured analysis with confidence scores and clear reasoning.
""",
            
            'processing_guidance': """
You are providing processing guidance for an active LOI transaction in the Better Day Energy workflow system. 

Analyze the current transaction state and provide specific recommendations for:
1. Next steps in the workflow process
2. Potential risks or blockers to address
3. Resource allocation and timing recommendations
4. Customer communication strategies
5. Quality assurance checkpoints

Focus on practical, actionable guidance that helps ensure successful completion of the VP Racing fuel supply agreement.
""",
            
            'risk_assessment': """
You are a risk analyst for fuel supply agreements. Evaluate this LOI transaction for potential risks including:

1. Financial risks (incentive sustainability, payment capability)
2. Operational risks (volume commitments, delivery logistics)
3. Competitive risks (supplier switching likelihood)
4. Implementation risks (timeline, complexity, resource availability)
5. Regulatory/compliance risks
6. Customer relationship risks

Provide risk scoring and mitigation recommendations.
""",
            
            'completion_prediction': """
You are predicting the likelihood of successful completion for this LOI transaction.

Analyze factors that influence completion probability:
1. Customer engagement level and responsiveness
2. Financial commitment and incentive alignment
3. Timeline feasibility and market conditions
4. Implementation complexity and resource availability
5. Historical patterns for similar transactions

Provide completion probability with key success factors and potential failure points.
"""
        }
        
        return prompts.get(decision_type, prompts['initial_assessment'])
    
    def _create_user_prompt(self, context: Dict[str, Any]) -> str:
        """Create user prompt with transaction context"""
        
        return f"""
Analyze this VP Racing LOI transaction:

**Customer Profile:**
- Company: {context['customer_profile']['company_name']}
- Type: {context['customer_profile']['customer_type']}
- VIP Status: {context['customer_profile']['is_vip']}
- Location: {context['customer_profile']['location']['city']}, {context['customer_profile']['location']['state']}

**Fuel Requirements:**
- Monthly Gasoline: {context['fuel_requirements']['monthly_gasoline_volume']:,} gallons
- Monthly Diesel: {context['fuel_requirements']['monthly_diesel_volume']:,} gallons
- Total Monthly Volume: {context['fuel_requirements']['total_monthly_volume']:,} gallons
- Current Supplier: {context['fuel_requirements']['current_supplier']}
- Conversion Timeline: {context['fuel_requirements']['conversion_timeline']}

**Financial Profile:**
- Image Funding: ${context['financial_profile']['image_funding']:,}
- Incentive Funding: ${context['financial_profile']['incentive_funding']:,}
- Total Incentives: ${context['financial_profile']['total_incentives']:,}
- Incentive Ratio: ${context['financial_profile']['incentive_per_gallon_ratio']:.4f} per gallon

**Project Requirements:**
- Canopy Installation: {context['project_requirements']['canopy_installation']}
- Current Branding: {context['project_requirements']['branding_removal']}
- Special Requirements: {context['project_requirements']['special_requirements']}

**Decision Type:** {context['decision_type']}

Please provide your analysis using the available function calls.
"""
    
    def _get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions for Grok function calling"""
        
        return [
            {
                'name': 'provide_loi_assessment',
                'description': 'Provide comprehensive LOI transaction assessment',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'priority_score': {
                            'type': 'number',
                            'description': 'Priority score from 1-10 (10 = highest priority)',
                            'minimum': 1,
                            'maximum': 10
                        },
                        'complexity_score': {
                            'type': 'number',
                            'description': 'Complexity score from 1-10 (10 = most complex)',
                            'minimum': 1,
                            'maximum': 10
                        },
                        'risk_factors': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of identified risk factors'
                        },
                        'customer_classification': {
                            'type': 'string',
                            'enum': ['high_value', 'standard', 'strategic', 'competitive_displacement', 'new_market'],
                            'description': 'Customer classification for processing approach'
                        },
                        'processing_recommendation': {
                            'type': 'string',
                            'enum': ['expedite', 'standard', 'detailed_review', 'manual_approval'],
                            'description': 'Recommended processing approach'
                        },
                        'estimated_completion_days': {
                            'type': 'integer',
                            'description': 'Estimated days to complete the LOI process',
                            'minimum': 1,
                            'maximum': 30
                        },
                        'confidence_score': {
                            'type': 'number',
                            'description': 'Confidence in this assessment (0.0-1.0)',
                            'minimum': 0.0,
                            'maximum': 1.0
                        },
                        'key_insights': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'Key insights and observations'
                        },
                        'recommendations': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'Specific recommendations for this transaction'
                        },
                        'reasoning': {
                            'type': 'string',
                            'description': 'Detailed reasoning for the assessment'
                        }
                    },
                    'required': [
                        'priority_score', 'complexity_score', 'risk_factors',
                        'customer_classification', 'processing_recommendation',
                        'estimated_completion_days', 'confidence_score', 'reasoning'
                    ]
                }
            }
        ]
    
    def _process_ai_response(self, ai_response: Dict[str, Any], transaction: LOITransaction, decision_type: str) -> Dict[str, Any]:
        """Process AI response and create decision object"""
        
        try:
            # Extract function call result
            message = ai_response['choices'][0]['message']
            
            if 'function_call' in message:
                function_call = message['function_call']
                assessment = json.loads(function_call['arguments'])
                
                decision = {
                    'decision_id': f"grok_{int(datetime.now().timestamp())}_{transaction.id[:8]}",
                    'decision_type': decision_type,
                    'ai_provider': 'grok',
                    'model_name': self.ai_config['model'],
                    'confidence': assessment.get('confidence_score', 0.5),
                    'reasoning': assessment.get('reasoning', ''),
                    'expected_outcome': f"Priority: {assessment.get('priority_score', 5)}, Complexity: {assessment.get('complexity_score', 5)}",
                    'alternatives_considered': [],
                    'context': {
                        'priority_score': assessment.get('priority_score', 5),
                        'complexity': assessment.get('complexity_score', 5),
                        'risk_factors': assessment.get('risk_factors', []),
                        'customer_classification': assessment.get('customer_classification', 'standard'),
                        'processing_recommendation': assessment.get('processing_recommendation', 'standard'),
                        'estimated_completion_days': assessment.get('estimated_completion_days', 7),
                        'key_insights': assessment.get('key_insights', []),
                        'recommendations': assessment.get('recommendations', [])
                    },
                    'created_at': datetime.now().isoformat()
                }
                
            else:
                # Fallback if no function call
                content = message.get('content', '')
                decision = self._parse_text_response(content, transaction, decision_type)
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ Error processing AI response: {e}")
            return self._create_fallback_decision(transaction, decision_type, f"Response processing error: {e}")
    
    def _parse_text_response(self, content: str, transaction: LOITransaction, decision_type: str) -> Dict[str, Any]:
        """Parse text response when function calling fails"""
        
        # Simple text parsing fallback
        priority_score = 5.0
        complexity_score = 5.0
        
        # Look for key indicators in text
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['high priority', 'urgent', 'expedite']):
            priority_score = 8.0
        elif any(word in content_lower for word in ['low priority', 'background']):
            priority_score = 3.0
        
        if any(word in content_lower for word in ['complex', 'difficult', 'challenging']):
            complexity_score = 8.0
        elif any(word in content_lower for word in ['simple', 'straightforward', 'easy']):
            complexity_score = 3.0
        
        return {
            'decision_id': f"grok_text_{int(datetime.now().timestamp())}_{transaction.id[:8]}",
            'decision_type': decision_type,
            'ai_provider': 'grok',
            'model_name': self.ai_config['model'],
            'confidence': 0.6,
            'reasoning': content[:500],  # Truncate reasoning
            'expected_outcome': f"Text-parsed assessment",
            'alternatives_considered': [],
            'context': {
                'priority_score': priority_score,
                'complexity': complexity_score,
                'risk_factors': ['text_parsing_used'],
                'processing_recommendation': 'standard'
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _create_fallback_decision(self, transaction: LOITransaction, decision_type: str, error: str) -> Dict[str, Any]:
        """Create fallback decision when AI fails"""
        
        # Simple business rules fallback
        customer_data = transaction.customer_data
        crm_data = transaction.crm_form_data
        
        total_volume = crm_data.get('monthly_gasoline_volume', 0) + crm_data.get('monthly_diesel_volume', 0)
        total_incentives = crm_data.get('total_estimated_incentives', 0)
        
        # Basic priority assessment
        if customer_data.get('is_vip_customer') or total_volume > 50000 or total_incentives > 75000:
            priority_score = 8.0
            processing_recommendation = 'expedite'
        elif total_volume > 20000 or total_incentives > 25000:
            priority_score = 6.0
            processing_recommendation = 'standard'
        else:
            priority_score = 4.0
            processing_recommendation = 'standard'
        
        # Basic complexity assessment
        complexity_factors = []
        if crm_data.get('canopy_installation_required'):
            complexity_factors.append('canopy_installation')
        if crm_data.get('special_requirements_notes'):
            complexity_factors.append('special_requirements')
        if total_incentives > 50000:
            complexity_factors.append('high_financial_value')
        
        complexity_score = 5.0 + len(complexity_factors) * 1.5
        
        return {
            'decision_id': f"fallback_{int(datetime.now().timestamp())}_{transaction.id[:8]}",
            'decision_type': decision_type,
            'ai_provider': 'fallback_rules',
            'model_name': 'business_rules',
            'confidence': 0.3,
            'reasoning': f"AI unavailable, using fallback rules. Error: {error}",
            'expected_outcome': 'Fallback assessment',
            'alternatives_considered': [],
            'context': {
                'priority_score': priority_score,
                'complexity': min(complexity_score, 10.0),
                'risk_factors': ['ai_unavailable'] + complexity_factors,
                'processing_recommendation': processing_recommendation,
                'fallback_reason': error
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_cache_key(self, context: Dict[str, Any]) -> str:
        """Generate cache key for decision context"""
        
        # Create cache key from key context elements
        key_elements = [
            context['decision_type'],
            context['customer_profile']['company_name'],
            str(context['fuel_requirements']['total_monthly_volume']),
            str(context['financial_profile']['total_incentives']),
            context['customer_profile']['customer_type']
        ]
        
        return f"loi_decision_{'_'.join(key_elements)}"
    
    def _get_cached_decision(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached decision if available and not expired"""
        
        if cache_key in self.decision_cache:
            cached_item = self.decision_cache[cache_key]
            
            # Check if cache is still valid
            if (datetime.now() - cached_item['timestamp']).total_seconds() < self.cache_ttl:
                return cached_item['decision']
            else:
                # Remove expired cache
                del self.decision_cache[cache_key]
        
        return None
    
    def _cache_decision(self, cache_key: str, decision: Dict[str, Any]):
        """Cache decision for future use"""
        
        self.decision_cache[cache_key] = {
            'decision': decision,
            'timestamp': datetime.now()
        }
    
    def _update_ai_stats(self, processing_time: float):
        """Update AI integration statistics"""
        
        self.ai_stats['decisions_made'] += 1
        self.ai_stats['last_decision'] = datetime.now()
        
        # Update average response time
        current_avg = self.ai_stats['average_response_time']
        decision_count = self.ai_stats['decisions_made']
        
        self.ai_stats['average_response_time'] = (
            (current_avg * (decision_count - 1) + processing_time) / decision_count
        )
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Get AI integration statistics"""
        
        cache_hit_rate = 0.0
        if self.ai_stats['decisions_made'] > 0:
            cache_hit_rate = self.ai_stats['cache_hits'] / self.ai_stats['decisions_made']
        
        return {
            'integration_type': 'grok_ai',
            'stats': self.ai_stats,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.decision_cache),
            'api_config': {
                'model': self.ai_config['model'],
                'temperature': self.ai_config['temperature'],
                'timeout': self.ai_config['timeout']
            }
        }
    
    def clear_cache(self):
        """Clear decision cache"""
        
        self.decision_cache.clear()
        logger.info("🧠 AI decision cache cleared")

# Global AI integration instance
ai_integration = GrokAIIntegration()

def get_ai_integration() -> GrokAIIntegration:
    """Get the global AI integration instance"""
    return ai_integration

# Async wrapper function for coordinator integration
async def handle_ai_decision(transaction: LOITransaction, decision_type: str = "initial_assessment") -> Dict[str, Any]:
    """Handle AI decision - async wrapper for coordinator"""
    
    ai_client = get_ai_integration()
    return await ai_client.make_loi_decision(transaction, decision_type)