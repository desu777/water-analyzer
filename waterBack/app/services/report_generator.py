import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
import markdown
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.config import settings
from app.models.water_data import AnalysisContext
from app.utils.logger import log_debug, log_error, log_info, log_warning

class ReportGenerator:
    """Service for generating PDF reports from analysis results"""
    
    def __init__(self):
        self.reports_dir = Path(settings.REPORTS_FOLDER)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Register fonts and define styles
        self._register_fonts()
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _register_fonts(self):
        """Register custom TTF fonts for Polish characters."""
        try:
            # Try both absolute and relative paths
            fonts_path = Path("assets/fonts/ttf")
            if not fonts_path.exists():
                fonts_path = Path("waterBack/assets/fonts/ttf")
            
            log_info(f"Looking for fonts in: {fonts_path.absolute()}", "REPORT_GENERATOR")
            
            font_files = {
                'DejaVuSans': fonts_path / "DejaVuSans.ttf",
                'DejaVuSans-Bold': fonts_path / "DejaVuSans-Bold.ttf",
                'DejaVuSans-Italic': fonts_path / "DejaVuSans-Oblique.ttf",
                'DejaVuSans-BoldItalic': fonts_path / "DejaVuSans-BoldOblique.ttf"
            }

            # Check for font files existence
            for font_name, path in font_files.items():
                if not path.exists():
                    log_error(f"CRITICAL: Font file not found at {path.absolute()}", "REPORT_GENERATOR")
                    raise FileNotFoundError(f"Font file not found: {path}")
                else:
                    log_info(f"Found font: {font_name} at {path.absolute()}", "REPORT_GENERATOR")

            # Register each font
            for font_name, path in font_files.items():
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
                log_info(f"Registered font: {font_name}", "REPORT_GENERATOR")
            
            # Register the font family
            pdfmetrics.registerFontFamily(
                'DejaVuSans',
                normal='DejaVuSans',
                bold='DejaVuSans-Bold',
                italic='DejaVuSans-Italic',
                boldItalic='DejaVuSans-BoldItalic'
            )
            log_info("Successfully registered DejaVu font family.", "REPORT_GENERATOR")

        except Exception as e:
            log_error(f"Failed to register custom fonts: {str(e)}", "REPORT_GENERATOR")
            log_warning("Falling back to default fonts - Polish characters may not display correctly", "REPORT_GENERATOR")
            # Don't raise - fall back to default fonts

    def _add_custom_styles(self):
        """Add custom styles for water analysis reports using DejaVu font."""
        # Try to use DejaVu, fall back to Helvetica if not available
        try:
            # Test if our custom font is registered
            pdfmetrics.getFont('DejaVuSans')
            base_font = 'DejaVuSans'
            bold_font = 'DejaVuSans-Bold'
            italic_font = 'DejaVuSans-Italic'
            log_info("Using DejaVu fonts for PDF generation", "REPORT_GENERATOR")
        except:
            base_font = 'Helvetica'
            bold_font = 'Helvetica-Bold'
            italic_font = 'Helvetica-Oblique'
            log_warning("DejaVu fonts not available, using Helvetica fallback", "REPORT_GENERATOR")
        
        # Update base styles
        self.styles['Normal'].fontName = base_font
        self.styles['Italic'].fontName = italic_font
        
        # Main title style - improved
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontName=bold_font,
            fontSize=22,
            spaceAfter=30,
            spaceBefore=20,
            textColor=HexColor('#1e40af'),
            alignment=TA_CENTER,
            leading=26
        ))
        
        # Subtitle for company name
        self.styles.add(ParagraphStyle(
            name='CompanySubtitle',
            parent=self.styles['Normal'],
            fontName=italic_font,
            fontSize=14,
            spaceAfter=25,
            textColor=HexColor('#64748b'),
            alignment=TA_CENTER
        ))
        
        # Section headers (H1) - improved
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontName=bold_font,
            fontSize=16,
            spaceAfter=15,
            spaceBefore=25,
            textColor=HexColor('#1e40af'),
            leftIndent=0,
            leading=20
        ))
        
        # Subsection headers (H2) - improved
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontName=bold_font,
            fontSize=14,
            spaceAfter=12,
            spaceBefore=15,
            textColor=HexColor('#2563eb'),
            leftIndent=0,
            leading=18
        ))
        
        # Minor headers (H3) - improved
        self.styles.add(ParagraphStyle(
            name='MinorHeader',
            parent=self.styles['Heading3'],
            fontName=bold_font,
            fontSize=12,
            spaceAfter=8,
            spaceBefore=10,
            textColor=HexColor('#374151'),
            leftIndent=0,
            leading=16
        ))
        
        # Base body text - improved
        self.styles.add(ParagraphStyle(
            name='ReportBodyText',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=11,
            spaceAfter=10,
            spaceBefore=2,
            leading=14,
            alignment=TA_JUSTIFY
        ))
        
        # Parameter style (for lists) - improved
        self.styles.add(ParagraphStyle(
            name='ParameterText',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=10,
            spaceAfter=6,
            leftIndent=15,
            bulletIndent=5,
            leading=13
        ))
        
        # Warning style - improved
        self.styles.add(ParagraphStyle(
            name='WarningText',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor('#dc2626'),
            leftIndent=10,
            borderColor=HexColor('#fca5a5'),
            borderWidth=1,
            borderPadding=5,
            leading=14
        ))
        
        # Success style - improved
        self.styles.add(ParagraphStyle(
            name='SuccessText',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor('#16a34a'),
            leftIndent=10,
            borderColor=HexColor('#86efac'),
            borderWidth=1,
            borderPadding=5,
            leading=14
        ))
        
        # Separator style
        self.styles.add(ParagraphStyle(
            name='Separator',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=8,
            spaceAfter=15,
            spaceBefore=15,
            textColor=HexColor('#9ca3af'),
            alignment=TA_CENTER
        ))

    def _enhanced_markdown_to_reportlab(self, text: str) -> str:
        """Enhanced markdown to ReportLab conversion with better formatting."""
        if not text:
            return ""
        
        # Escape any existing XML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Convert **bold** to <b>bold</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Convert *italic* to <i>italic</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Convert bullet points with better formatting
        text = re.sub(r'^\s*[\*\-\+]\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        
        # Handle numbered lists
        text = re.sub(r'^\s*(\d+)\.\s+(.+)$', r'\1. \2', text, flags=re.MULTILINE)
        
        # Handle line breaks
        text = text.replace('\n', '<br/>')
        
        return text

    def _parse_and_format_content(self, content: str, story: list):
        """Parse markdown content and add properly formatted elements to story."""
        if not content.strip():
            return
            
        lines = content.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines but process accumulated paragraph
            if not line:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    formatted_text = self._enhanced_markdown_to_reportlab(paragraph_text)
                    story.append(Paragraph(formatted_text, self.styles['ReportBodyText']))
                    story.append(Spacer(1, 6))
                    current_paragraph = []
                continue
            
            # Handle separators
            if line.startswith('---') and len(line.strip('- ')) == 0:
                # Add accumulated paragraph first
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    formatted_text = self._enhanced_markdown_to_reportlab(paragraph_text)
                    story.append(Paragraph(formatted_text, self.styles['ReportBodyText']))
                    current_paragraph = []
                
                # Add separator
                story.append(Spacer(1, 10))
                story.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", self.styles['Separator']))
                story.append(Spacer(1, 10))
                continue
            
            # Handle headers
            if line.startswith('###'):
                # Process accumulated paragraph first
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    formatted_text = self._enhanced_markdown_to_reportlab(paragraph_text)
                    story.append(Paragraph(formatted_text, self.styles['ReportBodyText']))
                    current_paragraph = []
                
                header_text = line[3:].strip()
                formatted_header = self._enhanced_markdown_to_reportlab(header_text)
                story.append(Paragraph(formatted_header, self.styles['MinorHeader']))
                continue
                
            elif line.startswith('##'):
                # Process accumulated paragraph first
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    formatted_text = self._enhanced_markdown_to_reportlab(paragraph_text)
                    story.append(Paragraph(formatted_text, self.styles['ReportBodyText']))
                    current_paragraph = []
                
                header_text = line[2:].strip()
                formatted_header = self._enhanced_markdown_to_reportlab(header_text)
                story.append(Paragraph(formatted_header, self.styles['SubsectionHeader']))
                continue
                
            elif line.startswith('#'):
                # Process accumulated paragraph first
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    formatted_text = self._enhanced_markdown_to_reportlab(paragraph_text)
                    story.append(Paragraph(formatted_text, self.styles['ReportBodyText']))
                    current_paragraph = []
                
                header_text = line[1:].strip()
                formatted_header = self._enhanced_markdown_to_reportlab(header_text)
                story.append(Paragraph(formatted_header, self.styles['SectionHeader']))
                continue
            
            # Handle bullet points and lists
            if line.startswith(('• ', '- ', '* ')) or re.match(r'^\d+\.', line):
                # Process accumulated paragraph first
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    formatted_text = self._enhanced_markdown_to_reportlab(paragraph_text)
                    story.append(Paragraph(formatted_text, self.styles['ReportBodyText']))
                    current_paragraph = []
                
                formatted_line = self._enhanced_markdown_to_reportlab(line)
                
                # Check for special formatting (only text-based detection)
                if 'NIEBEZPIECZN' in line.upper() or 'BŁĄD' in line.upper() or 'NIEZGODNE' in line.upper() or 'PRZEKROCZENIE' in line.upper():
                    story.append(Paragraph(formatted_line, self.styles['WarningText']))
                elif 'DOBRA' in line.upper() or 'BEZPIECZN' in line.upper() or 'W NORMIE' in line.upper() or 'DOSKONAŁY' in line.upper():
                    story.append(Paragraph(formatted_line, self.styles['SuccessText']))
                else:
                    story.append(Paragraph(formatted_line, self.styles['ParameterText']))
                
                story.append(Spacer(1, 4))
                continue
            
            # Regular text - accumulate into paragraph
            current_paragraph.append(line)
        
        # Process any remaining paragraph
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            formatted_text = self._enhanced_markdown_to_reportlab(paragraph_text)
            story.append(Paragraph(formatted_text, self.styles['ReportBodyText']))
            story.append(Spacer(1, 6))

    async def generate_pdf_report(self, analysis_id: str, context: AnalysisContext, analysis_result: str) -> str:
        """Generate PDF report from analysis result"""
        try:
            log_info(f"Generating PDF report for {analysis_id}", "REPORT_GENERATOR")
            
            # Create PDF file path
            report_path = self.reports_dir / f"{analysis_id}.pdf"
            
            # Create PDF document with better margins
            doc = SimpleDocTemplate(
                str(report_path),
                pagesize=A4,
                rightMargin=60,
                leftMargin=60,
                topMargin=60,
                bottomMargin=60
            )
            
            # Build content
            story = []
            
            # Add header with improved styling
            self._add_enhanced_header(story, context)
            
            # Add analysis content with better parsing
            self._add_enhanced_analysis_content(story, analysis_result)
            
            # Add footer
            self._add_enhanced_footer(story)
            
            # Build PDF
            doc.build(story)
            
            log_info(f"PDF report generated: {report_path}", "REPORT_GENERATOR")
            return str(report_path)
            
        except Exception as e:
            log_error(f"PDF report generation failed: {str(e)}", "REPORT_GENERATOR")
            raise
    
    def _add_enhanced_header(self, story: list, context: AnalysisContext):
        """Add enhanced header section to PDF"""
        # Main title - updated as requested
        story.append(Paragraph("Personalizowana Analiza Jakości Wody", self.styles['MainTitle']))
        story.append(Paragraph("by Aquaforest Lab", self.styles['CompanySubtitle']))
        story.append(Spacer(1, 20))
        
        # Basic information table with better styling
        basic_info = [
            ['Informacje Podstawowe', ''],
            ['Data analizy:', datetime.now().strftime('%Y-%m-%d %H:%M')],
            ['Identyfikator analizy:', context.analysisId],
            ['Nazwa pliku:', context.originalFilename],
        ]
        
        # Add water data info if available
        if context.waterData:
            water_data = context.waterData
            if water_data.testDate:
                basic_info.append(['Data badania:', water_data.testDate])
            # Always add Laboratory, with a default value
            basic_info.append(['Laboratorium:', water_data.laboratory or 'Aquaforest Lab'])
        
        # Determine fonts to use
        try:
            pdfmetrics.getFont('DejaVuSans-Bold')
            header_font = 'DejaVuSans-Bold'
            body_font = 'DejaVuSans'
        except:
            header_font = 'Helvetica-Bold'
            body_font = 'Helvetica'
        
        # Create table with enhanced styling
        table = Table(basic_info, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), HexColor('#dbeafe')),
            ('TEXTCOLOR', (0, 0), (1, 0), HexColor('#1e40af')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), header_font),
            ('FONTNAME', (0, 1), (-1, -1), body_font),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f9fafb'), HexColor('#ffffff')]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 25))
    
    def _add_enhanced_analysis_content(self, story: list, analysis_result: str):
        """Add analysis content to PDF with enhanced markdown parsing"""
        try:
            # Use the enhanced content parser
            self._parse_and_format_content(analysis_result, story)
                
        except Exception as e:
            log_error(f"Error adding enhanced analysis content: {str(e)}", "REPORT_GENERATOR")
            # Fallback: add raw content with basic formatting
            formatted_content = self._enhanced_markdown_to_reportlab(analysis_result)
            story.append(Paragraph("Wyniki Analizy", self.styles['SectionHeader']))
            story.append(Paragraph(formatted_content, self.styles['ReportBodyText']))
    
    def _add_enhanced_footer(self, story: list):
        """Add enhanced footer section to PDF"""
        story.append(Spacer(1, 30))
        
        # Add separator line
        story.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", self.styles['Separator']))
        story.append(Spacer(1, 15))
        
        # Footer information with enhanced formatting
        footer_text = f"""
        <para align="center">
        <font size="9" color="#374151">
        <b>Raport wygenerowany automatycznie przez Aquaforest Lab</b><br/>
        Data utworzenia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/><br/>
        <font size="8" color="#6b7280">
        Uwaga: Ten raport służy wyłącznie celom informacyjnym.<br/>
        W przypadku wykrycia problemów skonsultuj się z ekspertem.<br/>
        Kontakt: info@aquaforest-lab.com
        </font>
        </font>
        </para>
        """
        
        story.append(Paragraph(footer_text, self.styles['ReportBodyText']))
    
    # Pozostałe metody pozostają bez zmian...
    def get_report_path(self, analysis_id: str) -> str:
        """Get report file path"""
        return str(self.reports_dir / f"{analysis_id}.pdf")
    
    def report_exists(self, analysis_id: str) -> bool:
        """Check if report exists"""
        report_path = self.reports_dir / f"{analysis_id}.pdf"
        return report_path.exists()
    
    def delete_report(self, analysis_id: str) -> bool:
        """Delete report file"""
        try:
            report_path = self.reports_dir / f"{analysis_id}.pdf"
            if report_path.exists():
                report_path.unlink()
                log_info(f"Deleted report: {report_path}", "REPORT_GENERATOR")
                return True
            return False
        except Exception as e:
            log_error(f"Failed to delete report: {str(e)}", "REPORT_GENERATOR")
            return False
    
    def cleanup_old_reports(self, max_age_hours: int = 24):
        """Clean up old report files"""
        try:
            current_time = datetime.now().timestamp()
            deleted_count = 0
            
            for report_file in self.reports_dir.glob("*.pdf"):
                file_age = current_time - report_file.stat().st_mtime
                if file_age > (max_age_hours * 3600):
                    report_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                log_info(f"Cleaned up {deleted_count} old reports", "REPORT_GENERATOR")
                
        except Exception as e:
            log_error(f"Report cleanup failed: {str(e)}", "REPORT_GENERATOR")

# Global report generator instance
report_generator = ReportGenerator()