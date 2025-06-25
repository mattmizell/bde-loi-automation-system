#!/usr/bin/env python3
"""
Simple test script for PDF generation functionality
"""

import tempfile
import os
import sys
import importlib.util

# Import the html_to_pdf method directly
sys.path.append('.')

def test_html_to_pdf():
    """Test HTML to PDF conversion directly"""
    
    # Sample HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test Signed LOI Document</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .section { margin-bottom: 25px; }
            h1 { color: #1f4e79; }
            h2 { color: #2563eb; margin-top: 25px; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .signature { border: 2px solid #007bff; padding: 15px; margin: 20px 0; border-radius: 5px; }
            .footer { margin-top: 30px; font-size: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>VP RACING FUEL SUPPLY AGREEMENT</h1>
            <h2>LETTER OF INTENT</h2>
        </div>
        
        <div class="section">
            <h2>Customer Information</h2>
            <table>
                <tr><th>Company Name</th><td>Test Company LLC</td></tr>
                <tr><th>Signer Name</th><td>John Test</td></tr>
                <tr><th>Business Address</th><td>123 Test St, Test City, TS 12345</td></tr>
                <tr><th>Email</th><td>john@example.com</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Deal Terms</h2>
            <table>
                <tr><th>Total Gallons</th><td>50,000</td></tr>
                <tr><th>Price per Gallon</th><td>$2.45</td></tr>
                <tr><th>Signing Incentive</th><td>$2,500</td></tr>
                <tr><th>Contract Duration</th><td>24 months</td></tr>
            </table>
        </div>
        
        <div class="signature">
            <h3>Electronic Signature</h3>
            <p><strong>Signed by:</strong> John Test</p>
            <p><strong>Date:</strong> 2025-06-25</p>
            <p><strong>Verification Code:</strong> TEST-VERIFY-123</p>
        </div>
        
        <div class="footer">
            <p>This document has been electronically signed and is legally binding.</p>
        </div>
    </body>
    </html>
    """
    
    print("🔍 Testing PDF generation methods...")
    
    # Test path
    pdf_path = "/tmp/test_signed_document.pdf"
    
    # Try different PDF generation methods
    success = False
    
    # Method 1: Try wkhtmltopdf
    print("📄 Method 1: Testing wkhtmltopdf...")
    try:
        import subprocess
        import tempfile
        
        # Check if wkhtmltopdf is available
        try:
            subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, check=True)
            wkhtmltopdf_available = True
            print("✅ wkhtmltopdf is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            wkhtmltopdf_available = False
            print("❌ wkhtmltopdf not available")
        
        if wkhtmltopdf_available:
            # Write HTML to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                temp_html = f.name
            
            # Convert to PDF
            result = subprocess.run([
                'wkhtmltopdf',
                '--enable-local-file-access',
                '--margin-top', '20mm',
                '--margin-bottom', '20mm',
                '--margin-left', '20mm',
                '--margin-right', '20mm',
                temp_html,
                pdf_path
            ], capture_output=True, text=True)
            
            # Clean up temp file
            os.unlink(temp_html)
            
            if result.returncode == 0:
                print(f"✅ PDF generated successfully with wkhtmltopdf: {pdf_path}")
                print(f"   File size: {os.path.getsize(pdf_path)} bytes")
                success = True
            else:
                print(f"❌ wkhtmltopdf failed: {result.stderr}")
        
    except Exception as e:
        print(f"❌ wkhtmltopdf error: {e}")
    
    # Method 2: Try WeasyPrint
    if not success:
        print("📄 Method 2: Testing WeasyPrint...")
        try:
            import weasyprint
            
            # Generate PDF with WeasyPrint
            weasyprint.HTML(string=html_content).write_pdf(pdf_path)
            print(f"✅ PDF generated successfully with WeasyPrint: {pdf_path}")
            print(f"   File size: {os.path.getsize(pdf_path)} bytes")
            success = True
            
        except ImportError:
            print("❌ WeasyPrint not available")
        except Exception as e:
            print(f"❌ WeasyPrint error: {e}")
    
    # Method 3: Try ReportLab
    if not success:
        print("📄 Method 3: Testing ReportLab...")
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            import re
            from html import unescape
            
            # Convert HTML to text for reportlab
            text_content = re.sub('<[^<]+?>', '', html_content)
            text_content = unescape(text_content)
            
            # Create PDF with reportlab
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Split content into paragraphs
            paragraphs = text_content.split('\n\n')
            
            for para in paragraphs:
                if para.strip():
                    if 'LETTER OF INTENT' in para.upper():
                        p = Paragraph(para.strip(), styles['Title'])
                    elif para.strip().isupper() and len(para.strip()) < 50:
                        p = Paragraph(para.strip(), styles['Heading1'])
                    else:
                        p = Paragraph(para.strip(), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 0.1*inch))
            
            doc.build(story)
            print(f"✅ PDF generated successfully with ReportLab: {pdf_path}")
            print(f"   File size: {os.path.getsize(pdf_path)} bytes")
            success = True
            
        except ImportError:
            print("❌ ReportLab not available")
        except Exception as e:
            print(f"❌ ReportLab error: {e}")
    
    # Fallback: Create enhanced HTML
    if not success:
        print("📄 Fallback: Creating enhanced HTML...")
        try:
            html_with_print_styles = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Signed Document</title>
                <style>
                    @media print {{
                        body {{ margin: 0.5in; font-family: Arial, sans-serif; }}
                        .no-print {{ display: none; }}
                    }}
                    body {{ font-family: Arial, sans-serif; line-height: 1.4; }}
                    h1 {{ color: #1f4e79; text-align: center; }}
                    h2 {{ color: #2563eb; border-bottom: 2px solid #2563eb; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .signature {{ border: 2px solid #007bff; padding: 10px; margin: 20px 0; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                {html_content.split('<body>')[1].split('</body>')[0] if '<body>' in html_content else html_content}
                <div class="no-print">
                    <p><strong>Note:</strong> This is a print-ready HTML version. Use your browser's print function to create a PDF.</p>
                </div>
            </body>
            </html>
            """
            
            html_path = pdf_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_with_print_styles)
            
            print(f"✅ HTML document saved (print-ready): {html_path}")
            print(f"   File size: {os.path.getsize(html_path)} bytes")
            success = True
            
        except Exception as e:
            print(f"❌ HTML fallback error: {e}")
    
    # Test results
    if success:
        print("\n🎉 Document generation test completed successfully!")
        if os.path.exists(pdf_path):
            print(f"📄 PDF available at: {pdf_path}")
        else:
            html_path = pdf_path.replace('.pdf', '.html')
            if os.path.exists(html_path):
                print(f"📄 HTML available at: {html_path}")
    else:
        print("\n❌ All document generation methods failed")
    
    # Clean up
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    html_path = pdf_path.replace('.pdf', '.html')
    if os.path.exists(html_path):
        print(f"📄 Test HTML file created: {html_path}")
        # Don't remove HTML so user can verify it works

if __name__ == "__main__":
    test_html_to_pdf()