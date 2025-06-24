"""
LOI Document Generator

Handles generation of LOI PDF documents from templates with CRM form data.
Provides template management, field mapping, and PDF creation capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import tempfile

# PDF generation libraries
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from jinja2 import Template, Environment, FileSystemLoader

from ..core.loi_transaction_queue import LOITransaction

logger = logging.getLogger(__name__)

class LOIDocumentGenerator:
    """
    Generate LOI PDF documents from templates with form data mapping.
    
    Capabilities:
    - Template-based document generation
    - Field mapping from CRM to document
    - PDF formatting with logos and branding
    - Dynamic content population
    - Multiple template support
    - Document validation and quality checks
    """
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Template configuration
        self.template_config = {
            'vp_racing_loi': {
                'name': 'VP Racing LOI Template',
                'file': 'vp_racing_loi_template.json',
                'version': '1.0',
                'fields': self._get_vp_racing_fields()
            }
        }
        
        # Document formatting settings
        self.format_settings = {
            'page_size': letter,
            'margins': {
                'top': 0.75 * inch,
                'bottom': 0.75 * inch,
                'left': 1.0 * inch,
                'right': 1.0 * inch
            },
            'font_sizes': {
                'title': 16,
                'heading': 14,
                'subheading': 12,
                'body': 11,
                'small': 9
            },
            'colors': {
                'primary': colors.HexColor('#1f4e79'),  # Better Day Energy blue
                'secondary': colors.HexColor('#f7931e'),  # VP Racing orange
                'text': colors.black,
                'light_gray': colors.HexColor('#f5f5f5')
            }
        }
        
        # Statistics
        self.generation_stats = {
            'documents_generated': 0,
            'templates_used': {},
            'generation_errors': 0,
            'average_generation_time': 0.0,
            'last_generation': None
        }
        
        # Initialize Jinja2 environment for text templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        logger.info("📄 LOI Document Generator initialized")
        self._create_default_templates()
    
    def _get_vp_racing_fields(self) -> Dict[str, Any]:
        """Define VP Racing LOI template field mappings"""
        
        return {
            # Header Section
            'customer_site_name': {
                'source': 'customer_data.company_name',
                'required': True,
                'default': '[CUSTOMER NAME]'
            },
            'dealer_address': {
                'source': 'customer_data.business_address',
                'required': True,
                'format': 'address_block'
            },
            
            # Contact Information
            'dealer_name': {
                'source': 'customer_data.contact_name',
                'required': True,
                'default': '[CONTACT NAME]'
            },
            'dealer_title': {
                'source': 'customer_data.contact_title',
                'required': False,
                'default': 'Owner/Manager'
            },
            'dealer_email': {
                'source': 'customer_data.email',
                'required': True,
                'format': 'email'
            },
            'dealer_phone': {
                'source': 'customer_data.phone',
                'required': True,
                'format': 'phone'
            },
            
            # Fuel Supply Details
            'monthly_gasoline_volume': {
                'source': 'crm_form_data.monthly_gasoline_volume',
                'required': True,
                'format': 'number_with_commas',
                'suffix': ' gallons'
            },
            'monthly_diesel_volume': {
                'source': 'crm_form_data.monthly_diesel_volume',
                'required': True,
                'format': 'number_with_commas',
                'suffix': ' gallons'
            },
            'current_supplier': {
                'source': 'crm_form_data.current_fuel_supplier',
                'required': False,
                'default': '[CURRENT SUPPLIER]'
            },
            'conversion_date': {
                'source': 'crm_form_data.estimated_conversion_date',
                'required': False,
                'format': 'date',
                'default': '[TO BE DETERMINED]'
            },
            
            # Agreement Terms
            'agreement_duration': {
                'source': 'static',
                'value': '10 years',
                'required': True
            },
            'fuel_brand': {
                'source': 'static',
                'value': 'VP Racing Fuels',
                'required': True
            },
            
            # Financial Incentives
            'image_funding_amount': {
                'source': 'crm_form_data.image_funding_amount',
                'required': False,
                'format': 'currency',
                'default': '$0'
            },
            'incentive_funding_amount': {
                'source': 'crm_form_data.incentive_funding_amount',
                'required': False,
                'format': 'currency',
                'default': '$0'
            },
            'total_estimated_incentives': {
                'source': 'crm_form_data.total_estimated_incentives',
                'required': True,
                'format': 'currency',
                'calculate': 'image_funding_amount + incentive_funding_amount'
            },
            
            # Project Details
            'canopy_installation': {
                'source': 'crm_form_data.canopy_installation_required',
                'required': False,
                'format': 'yes_no',
                'default': 'To be determined'
            },
            'current_branding': {
                'source': 'crm_form_data.current_branding_to_remove',
                'required': False,
                'default': '[CURRENT BRANDING]'
            },
            'special_requirements': {
                'source': 'crm_form_data.special_requirements_notes',
                'required': False,
                'default': 'None specified'
            },
            
            # Document Metadata
            'document_date': {
                'source': 'generated',
                'value': 'current_date',
                'format': 'date_long'
            },
            'document_id': {
                'source': 'transaction.id',
                'required': True
            }
        }
    
    async def generate_loi_document(self, transaction: LOITransaction, 
                                   template_name: str = 'vp_racing_loi') -> Dict[str, Any]:
        """Generate LOI document from template and transaction data"""
        
        start_time = datetime.now()
        
        try:
            # Get template configuration
            template_config = self.template_config.get(template_name)
            if not template_config:
                raise Exception(f"Template '{template_name}' not found")
            
            # Extract and validate data
            document_data = self._extract_document_data(transaction, template_config)
            validation_result = self._validate_document_data(document_data, template_config)
            
            if not validation_result['valid']:
                logger.warning(f"⚠️ Document validation issues: {validation_result['warnings']}")
            
            # Generate PDF document
            pdf_path = await self._generate_pdf_document(
                document_data, 
                template_config, 
                transaction.id
            )
            
            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Update statistics
            self._update_generation_stats(template_name, generation_time)
            
            result = {
                'success': True,
                'document_id': f"LOI_{transaction.id}",
                'file_path': pdf_path,
                'template_used': template_name,
                'generation_time': generation_time,
                'validation_score': validation_result['score'],
                'document_data': document_data,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"📄 Generated LOI document for {transaction.id} in {generation_time:.2f}s")
            return result
            
        except Exception as e:
            self.generation_stats['generation_errors'] += 1
            logger.error(f"❌ Failed to generate document for {transaction.id}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'template_name': template_name,
                'generation_time': (datetime.now() - start_time).total_seconds()
            }
    
    def _extract_document_data(self, transaction: LOITransaction, 
                              template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format data for document generation"""
        
        document_data = {}
        fields = template_config['fields']
        
        for field_name, field_config in fields.items():
            try:
                value = self._get_field_value(transaction, field_config)
                formatted_value = self._format_field_value(value, field_config)
                document_data[field_name] = formatted_value
                
            except Exception as e:
                logger.warning(f"⚠️ Error extracting field {field_name}: {e}")
                document_data[field_name] = field_config.get('default', '[DATA NOT AVAILABLE]')
        
        return document_data
    
    def _get_field_value(self, transaction: LOITransaction, field_config: Dict[str, Any]) -> Any:
        """Get field value from transaction data based on source configuration"""
        
        source = field_config['source']
        
        if source == 'static':
            return field_config['value']
        
        elif source == 'generated':
            if field_config['value'] == 'current_date':
                return datetime.now()
            else:
                return field_config['value']
        
        elif source.startswith('transaction.'):
            # Get value from transaction object
            field_path = source.replace('transaction.', '')
            return getattr(transaction, field_path, None)
        
        elif source.startswith('customer_data.'):
            # Get value from customer data
            field_path = source.replace('customer_data.', '')
            if field_path == 'business_address':
                # Special handling for address
                addr = transaction.customer_data.get('business_address', {})
                return addr
            else:
                return transaction.customer_data.get(field_path)
        
        elif source.startswith('crm_form_data.'):
            # Get value from CRM form data
            field_path = source.replace('crm_form_data.', '')
            return transaction.crm_form_data.get(field_path)
        
        else:
            return None
    
    def _format_field_value(self, value: Any, field_config: Dict[str, Any]) -> str:
        """Format field value according to configuration"""
        
        if value is None:
            return field_config.get('default', '')
        
        format_type = field_config.get('format', 'string')
        
        if format_type == 'currency':
            try:
                amount = float(value)
                return f"${amount:,.2f}"
            except:
                return field_config.get('default', '$0.00')
        
        elif format_type == 'number_with_commas':
            try:
                number = float(value)
                formatted = f"{number:,.0f}"
                suffix = field_config.get('suffix', '')
                return formatted + suffix
            except:
                return field_config.get('default', '0')
        
        elif format_type == 'date':
            try:
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    date_obj = value
                return date_obj.strftime('%m/%d/%Y')
            except:
                return field_config.get('default', 'TBD')
        
        elif format_type == 'date_long':
            try:
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    date_obj = value
                return date_obj.strftime('%B %d, %Y')
            except:
                return datetime.now().strftime('%B %d, %Y')
        
        elif format_type == 'yes_no':
            if isinstance(value, bool):
                return 'Yes' if value else 'No'
            elif isinstance(value, str):
                return 'Yes' if value.lower() in ['yes', 'true', '1'] else 'No'
            else:
                return field_config.get('default', 'No')
        
        elif format_type == 'phone':
            try:
                # Simple phone formatting
                digits = ''.join(filter(str.isdigit, str(value)))
                if len(digits) == 10:
                    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                else:
                    return str(value)
            except:
                return str(value)
        
        elif format_type == 'address_block':
            if isinstance(value, dict):
                parts = []
                if value.get('street'):
                    parts.append(value['street'])
                
                city_line = []
                if value.get('city'):
                    city_line.append(value['city'])
                if value.get('state'):
                    city_line.append(value['state'])
                if value.get('zip'):
                    city_line.append(value['zip'])
                
                if city_line:
                    parts.append(', '.join(city_line))
                
                return '\n'.join(parts) if parts else field_config.get('default', '')
            else:
                return str(value) if value else field_config.get('default', '')
        
        else:
            return str(value) if value is not None else field_config.get('default', '')
    
    def _validate_document_data(self, document_data: Dict[str, Any], 
                               template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document data completeness and quality"""
        
        errors = []
        warnings = []
        score = 100.0
        
        fields = template_config['fields']
        
        for field_name, field_config in fields.items():
            value = document_data.get(field_name, '')
            
            # Check required fields
            if field_config.get('required', False):
                if not value or value in ['[DATA NOT AVAILABLE]', '[CUSTOMER NAME]', '[CONTACT NAME]']:
                    errors.append(f"Missing required field: {field_name}")
                    score -= 15
            
            # Check for placeholder values
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                warnings.append(f"Placeholder value in field: {field_name}")
                score -= 5
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'score': max(score, 0)
        }
    
    async def _generate_pdf_document(self, document_data: Dict[str, Any], 
                                   template_config: Dict[str, Any], 
                                   transaction_id: str) -> str:
        """Generate PDF document using ReportLab"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=self.format_settings['page_size'],
            rightMargin=self.format_settings['margins']['right'],
            leftMargin=self.format_settings['margins']['left'],
            topMargin=self.format_settings['margins']['top'],
            bottomMargin=self.format_settings['margins']['bottom']
        )
        
        # Build document content
        story = []
        styles = getSampleStyleSheet()
        
        # Add custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=self.format_settings['font_sizes']['title'],
            textColor=self.format_settings['colors']['primary'],
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=self.format_settings['font_sizes']['heading'],
            textColor=self.format_settings['colors']['primary'],
            spaceBefore=20,
            spaceAfter=10
        )
        
        # Add document content
        story.append(Paragraph("LETTER OF INTENT", title_style))
        story.append(Paragraph("VP Racing Fuels Branded Supply Agreement", heading_style))
        story.append(Spacer(1, 20))
        
        # Add date and customer info
        story.append(Paragraph(f"Date: {document_data.get('document_date', '')}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Customer information section
        story.append(Paragraph("DEALER INFORMATION", heading_style))
        
        customer_info = [
            ['Business Name:', document_data.get('customer_site_name', '')],
            ['Contact Person:', document_data.get('dealer_name', '')],
            ['Title:', document_data.get('dealer_title', '')],
            ['Email:', document_data.get('dealer_email', '')],
            ['Phone:', document_data.get('dealer_phone', '')],
        ]
        
        # Add address
        address = document_data.get('dealer_address', '')
        if address:
            customer_info.append(['Address:', address])
        
        customer_table = Table(customer_info, colWidths=[1.5*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), self.format_settings['font_sizes']['body']),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(customer_table)
        story.append(Spacer(1, 20))
        
        # Fuel supply details
        story.append(Paragraph("FUEL SUPPLY DETAILS", heading_style))
        
        fuel_info = [
            ['Monthly Gasoline Volume:', document_data.get('monthly_gasoline_volume', '')],
            ['Monthly Diesel Volume:', document_data.get('monthly_diesel_volume', '')],
            ['Current Supplier:', document_data.get('current_supplier', '')],
            ['Estimated Conversion Date:', document_data.get('conversion_date', '')],
            ['Agreement Duration:', document_data.get('agreement_duration', '')],
        ]
        
        fuel_table = Table(fuel_info, colWidths=[2*inch, 3.5*inch])
        fuel_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), self.format_settings['font_sizes']['body']),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(fuel_table)
        story.append(Spacer(1, 20))
        
        # Financial incentives
        story.append(Paragraph("FINANCIAL INCENTIVES", heading_style))
        
        incentive_info = [
            ['Image Funding:', document_data.get('image_funding_amount', '$0.00')],
            ['Incentive Funding:', document_data.get('incentive_funding_amount', '$0.00')],
            ['Total Estimated Incentives:', document_data.get('total_estimated_incentives', '$0.00')],
        ]
        
        incentive_table = Table(incentive_info, colWidths=[2*inch, 3.5*inch])
        incentive_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), self.format_settings['font_sizes']['body']),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, -1), (-1, -1), self.format_settings['colors']['light_gray']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(incentive_table)
        story.append(Spacer(1, 20))
        
        # Project specifications
        story.append(Paragraph("PROJECT SPECIFICATIONS", heading_style))
        
        project_info = [
            ['Canopy Installation Required:', document_data.get('canopy_installation', 'TBD')],
            ['Current Branding to Remove:', document_data.get('current_branding', 'TBD')],
            ['Special Requirements:', document_data.get('special_requirements', 'None specified')],
        ]
        
        project_table = Table(project_info, colWidths=[2*inch, 3.5*inch])
        project_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), self.format_settings['font_sizes']['body']),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 30))
        
        # Signature section
        story.append(Paragraph("DEALER ACCEPTANCE", heading_style))
        story.append(Spacer(1, 20))
        
        signature_text = """By signing below, I acknowledge that I have read and agree to the terms outlined in this Letter of Intent for a VP Racing Fuels branded supply agreement. I understand that this is a preliminary agreement and that a formal contract will be executed upon mutual agreement of final terms."""
        
        story.append(Paragraph(signature_text, styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Signature lines
        signature_info = [
            ['Dealer Signature:', '_' * 40, 'Date:', '_' * 20],
            ['', '', '', ''],
            ['Print Name:', document_data.get('dealer_name', '_' * 30), 'Title:', document_data.get('dealer_title', '_' * 20)],
        ]
        
        signature_table = Table(signature_info, colWidths=[1.2*inch, 2.3*inch, 0.8*inch, 1.7*inch])
        signature_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), self.format_settings['font_sizes']['body']),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = f"Document ID: {document_data.get('document_id', transaction_id)} | Generated: {document_data.get('document_date', '')}"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=self.format_settings['font_sizes']['small'],
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
    
    def _update_generation_stats(self, template_name: str, generation_time: float):
        """Update document generation statistics"""
        
        self.generation_stats['documents_generated'] += 1
        self.generation_stats['last_generation'] = datetime.now()
        
        # Update template usage
        if template_name not in self.generation_stats['templates_used']:
            self.generation_stats['templates_used'][template_name] = 0
        self.generation_stats['templates_used'][template_name] += 1
        
        # Update average generation time
        total_docs = self.generation_stats['documents_generated']
        current_avg = self.generation_stats['average_generation_time']
        self.generation_stats['average_generation_time'] = (
            (current_avg * (total_docs - 1) + generation_time) / total_docs
        )
    
    def _create_default_templates(self):
        """Create default template files if they don't exist"""
        
        vp_racing_template = {
            "name": "VP Racing LOI Template",
            "version": "1.0",
            "description": "Standard Letter of Intent for VP Racing Fuel Supply Agreements",
            "created": datetime.now().isoformat(),
            "company_info": {
                "name": "Better Day Energy",
                "address": "123 Energy Blvd, St. Louis, MO 63101",
                "phone": "(314) 555-0123",
                "email": "info@betterdayenergy.com"
            },
            "brand_info": {
                "name": "VP Racing Fuels",
                "logo_path": "vp_racing_logo.png",
                "colors": {
                    "primary": "#f7931e",
                    "secondary": "#000000"
                }
            }
        }
        
        template_file = self.templates_dir / "vp_racing_loi_template.json"
        if not template_file.exists():
            with open(template_file, 'w') as f:
                json.dump(vp_racing_template, f, indent=2)
            logger.info("📄 Created default VP Racing LOI template")
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available document templates"""
        
        templates = []
        for template_id, config in self.template_config.items():
            templates.append({
                'id': template_id,
                'name': config['name'],
                'version': config['version'],
                'field_count': len(config['fields'])
            })
        
        return templates
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get document generation statistics"""
        
        return {
            'handler_type': 'document_generator',
            'stats': self.generation_stats,
            'available_templates': len(self.template_config),
            'format_settings': self.format_settings
        }

# Async wrapper function for coordinator integration
async def handle_document_generation(transaction: LOITransaction) -> Dict[str, Any]:
    """Handle document generation - async wrapper for coordinator"""
    
    # Note: In production, templates_dir would come from configuration
    templates_dir = "loi_automation_system/templates"
    
    generator = LOIDocumentGenerator(templates_dir)
    return await generator.generate_loi_document(transaction)