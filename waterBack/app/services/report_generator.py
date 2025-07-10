import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
    
    def _markdown_to_reportlab(self, text: str) -> str:
        """Convert simple markdown formatting to ReportLab XML tags."""
        if not text:
            return ""
        
        # Escape any existing XML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Convert **bold** to <b>bold</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Convert *italic* to <i>italic</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Convert bullet points
        text = re.sub(r'^\s*[\*\-\+]\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        
        # Handle line breaks
        text = text.replace('\n', '<br/>')
        
        return text

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
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='WaterTitle',
            parent=self.styles['Title'],
            fontName=bold_font,
            fontSize=20,
            spaceAfter=20,
            textColor=HexColor('#2563eb'),
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='WaterSubtitle',
            parent=self.styles['Heading2'],
            fontName=bold_font,
            fontSize=14,
            spaceAfter=12,
            textColor=HexColor('#1d4ed8'),
            leftIndent=0
        ))
        
        # Base body text
        self.styles.add(ParagraphStyle(
            name='WaterBodyText',
            parent=self.styles['Normal'],
            fontName=base_font,
            spaceAfter=8
        ))
        
        # Parameter style (for lists)
        self.styles.add(ParagraphStyle(
            name='WaterParameter',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=10,
            spaceAfter=6,
            leftIndent=20
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='WaterWarning',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor('#dc2626'),
            leftIndent=10
        ))
        
        # Success style
        self.styles.add(ParagraphStyle(
            name='WaterSuccess',
            parent=self.styles['Normal'],
            fontName=base_font,
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor('#16a34a'),
            leftIndent=10
        ))
    
    async def generate_pdf_report(self, analysis_id: str, context: AnalysisContext, analysis_result: str) -> str:
        """Generate PDF report from analysis result"""
        try:
            log_info(f"Generating PDF report for {analysis_id}", "REPORT_GENERATOR")
            
            # Create PDF file path
            report_path = self.reports_dir / f"{analysis_id}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(report_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Add header
            self._add_header(story, context)
            
            # Add analysis content
            self._add_analysis_content(story, analysis_result)
            
            # Add footer
            self._add_footer(story)
            
            # Build PDF
            doc.build(story)
            
            log_info(f"PDF report generated: {report_path}", "REPORT_GENERATOR")
            return str(report_path)
            
        except Exception as e:
            log_error(f"PDF report generation failed: {str(e)}", "REPORT_GENERATOR")
            raise
    
    def _add_header(self, story: list, context: AnalysisContext):
        """Add header section to PDF"""
        # Main title
        story.append(Paragraph("🔬 Analiza Jakości Wody", self.styles['WaterTitle']))
        story.append(Spacer(1, 12))
        
        # Basic information table
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
            if water_data.laboratory:
                basic_info.append(['Laboratorium:', water_data.laboratory])
            if water_data.sampleLocation:
                basic_info.append(['Lokalizacja próbki:', water_data.sampleLocation])
        
        # Determine fonts to use
        try:
            pdfmetrics.getFont('DejaVuSans-Bold')
            header_font = 'DejaVuSans-Bold'
            body_font = 'DejaVuSans'
        except:
            header_font = 'Helvetica-Bold'
            body_font = 'Helvetica'
        
        # Create table
        table = Table(basic_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), HexColor('#dbeafe')),
            ('TEXTCOLOR', (0, 0), (1, 0), HexColor('#1e40af')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), header_font),
            ('FONTNAME', (0, 1), (-1, -1), body_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
    
    def _add_analysis_content(self, story: list, analysis_result: str):
        """Add analysis content to PDF with proper markdown parsing"""
        try:
            # Parse markdown content
            sections = self._parse_markdown_sections(analysis_result)
            
            for section_title, section_content in sections.items():
                # Add section title (convert any markdown in title)
                title_text = self._markdown_to_reportlab(section_title)
                story.append(Paragraph(title_text, self.styles['WaterSubtitle']))
                story.append(Spacer(1, 6))
                
                # Add section content
                paragraphs = section_content.split('\n\n')
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # Convert markdown to ReportLab format
                        formatted_paragraph = self._markdown_to_reportlab(paragraph.strip())
                        
                        # Process different types of content
                        if paragraph.startswith('- ') or paragraph.startswith('*'):
                            # List item
                            story.append(Paragraph(formatted_paragraph, self.styles['WaterParameter']))
                        elif '❌' in paragraph or 'NIEBEZPIECZN' in paragraph.upper():
                            # Warning content
                            story.append(Paragraph(formatted_paragraph, self.styles['WaterWarning']))
                        elif '✅' in paragraph or 'DOBRA' in paragraph.upper():
                            # Success content
                            story.append(Paragraph(formatted_paragraph, self.styles['WaterSuccess']))
                        else:
                            # Regular paragraph
                            story.append(Paragraph(formatted_paragraph, self.styles['WaterBodyText']))
                        
                        story.append(Spacer(1, 6))
                
                story.append(Spacer(1, 12))
                
        except Exception as e:
            log_error(f"Error adding analysis content: {str(e)}", "REPORT_GENERATOR")
            # Fallback: add raw content with basic formatting
            formatted_content = self._markdown_to_reportlab(analysis_result)
            story.append(Paragraph("Wyniki Analizy", self.styles['WaterSubtitle']))
            story.append(Paragraph(formatted_content, self.styles['WaterBodyText']))
    
    def _parse_markdown_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# ') or line.startswith('## '):
                # New section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = line.lstrip('# ')
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _add_footer(self, story: list):
        """Add footer section to PDF"""
        story.append(Spacer(1, 20))
        
        # Footer information with proper encoding
        footer_text = """
        <para align="center">
        <font size="8" color="#666666">
        Raport wygenerowany automatycznie przez Water Test Analyzer<br/>
        Data utworzenia: {}<br/>
        Uwaga: Ten raport służy wyłącznie celom informacyjnym. 
        W przypadku wykrycia problemów skonsultuj się z ekspertem.
        </font>
        </para>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        story.append(Paragraph(footer_text, self.styles['WaterBodyText']))
    
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