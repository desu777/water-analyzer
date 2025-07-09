import pypdf
import pdfplumber
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.water_data import WaterTestData, WaterParameter
from app.utils.logger import log_debug, log_error, log_info

class PDFProcessor:
    """Service for processing PDF files and extracting water test data"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            log_info(f"Extracting text from PDF: {file_path}", "PDF_PROCESSOR")
            
            # Try pdfplumber first (better for tables)
            try:
                text = self._extract_with_pdfplumber(file_path)
                if text and len(text.strip()) > 100:  # Reasonable amount of text
                    return text
            except Exception as e:
                log_debug(f"pdfplumber extraction failed: {str(e)}", "PDF_PROCESSOR")
            
            # Fallback to pypdf
            try:
                text = self._extract_with_pypdf(file_path)
                if text and len(text.strip()) > 50:
                    return text
            except Exception as e:
                log_debug(f"pypdf extraction failed: {str(e)}", "PDF_PROCESSOR")
            
            raise Exception("Failed to extract text with both PDF libraries")
            
        except Exception as e:
            log_error(f"PDF text extraction failed: {str(e)}", "PDF_PROCESSOR")
            raise
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber (better for tables)"""
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[PAGE {page_num + 1}]\n{page_text}")
                
                # Extract tables
                tables = page.extract_tables()
                for table_num, table in enumerate(tables):
                    if table:
                        table_text = self._format_table_as_text(table)
                        text_parts.append(f"[TABLE {table_num + 1}]\n{table_text}")
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pypdf(self, file_path: str) -> str:
        """Extract text using pypdf (fallback)"""
        text_parts = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[PAGE {page_num + 1}]\n{page_text}")
        
        return "\n\n".join(text_parts)
    
    def _format_table_as_text(self, table: List[List[str]]) -> str:
        """Format table data as readable text"""
        if not table:
            return ""
        
        formatted_rows = []
        for row in table:
            if row:
                # Clean and join row cells
                cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                formatted_rows.append(" | ".join(cleaned_row))
        
        return "\n".join(formatted_rows)
    
    async def parse_water_data(self, extracted_text: str) -> WaterTestData:
        """Parse extracted text to structured water data"""
        try:
            log_info("Parsing water data from extracted text", "PDF_PROCESSOR")
            
            # Extract basic information
            test_date = self._extract_test_date(extracted_text)
            laboratory = self._extract_laboratory(extracted_text)
            sample_location = self._extract_sample_location(extracted_text)
            
            # Extract parameters
            parameters = self._extract_parameters(extracted_text)
            
            water_data = WaterTestData(
                testDate=test_date,
                laboratory=laboratory,
                sampleLocation=sample_location,
                parameters=parameters
            )
            
            log_info(f"Parsed {len(parameters)} water parameters", "PDF_PROCESSOR")
            return water_data
            
        except Exception as e:
            log_error(f"Water data parsing failed: {str(e)}", "PDF_PROCESSOR")
            # Return empty structure if parsing fails
            return WaterTestData(parameters=[])
    
    def _extract_test_date(self, text: str) -> Optional[str]:
        """Extract test date from text"""
        # Common date patterns
        date_patterns = [
            r'data\s+badania[:\s]+(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})',
            r'data[:\s]+(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})',
            r'(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})',
            r'(\d{2,4}[.\-/]\d{1,2}[.\-/]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_laboratory(self, text: str) -> Optional[str]:
        """Extract laboratory name from text"""
        lab_patterns = [
            r'laboratorium[:\s]+([^\n]+)',
            r'lab[:\s]+([^\n]+)',
            r'wykonawca[:\s]+([^\n]+)',
            r'akredytowane\s+laboratorium[:\s]+([^\n]+)'
        ]
        
        for pattern in lab_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_sample_location(self, text: str) -> Optional[str]:
        """Extract sample location from text"""
        location_patterns = [
            r'miejsce\s+poboru[:\s]+([^\n]+)',
            r'lokalizacja[:\s]+([^\n]+)',
            r'adres[:\s]+([^\n]+)',
            r'poboru\s+próbki[:\s]+([^\n]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_parameters(self, text: str) -> List[WaterParameter]:
        """Extract water parameters from text"""
        parameters = []
        
        # Common parameter patterns
        parameter_patterns = {
            'pH': r'pH[:\s]+(\d+[,.]?\d*)',
            'przewodność': r'przewodność[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'mętność': r'mętność[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'chlorki': r'chlorki[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'siarczany': r'siarczany[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'azotany': r'azotany[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'azotyny': r'azotyny[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'żelazo': r'żelazo[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'mangan': r'mangan[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'twardość': r'twardość[:\s]+(\d+[,.]?\d*)\s*(\w+)',
            'fluor': r'fluor[:\s]+(\d+[,.]?\d*)\s*(\w+)'
        }
        
        for param_name, pattern in parameter_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).replace(',', '.')
                    value = float(value_str)
                    unit = match.group(2) if len(match.groups()) > 1 else None
                    
                    parameter = WaterParameter(
                        name=param_name,
                        value=value,
                        unit=unit
                    )
                    parameters.append(parameter)
                except (ValueError, AttributeError):
                    continue
        
        # Try to extract from tables
        table_parameters = self._extract_from_table_format(text)
        parameters.extend(table_parameters)
        
        return parameters
    
    def _extract_from_table_format(self, text: str) -> List[WaterParameter]:
        """Extract parameters from table format"""
        parameters = []
        
        # Look for table-like structures
        lines = text.split('\n')
        for line in lines:
            # Simple table pattern: Parameter | Value | Unit
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    param_name = parts[0]
                    value_str = parts[1]
                    unit = parts[2]
                    
                    # Try to convert value to float
                    try:
                        value = float(value_str.replace(',', '.'))
                        parameter = WaterParameter(
                            name=param_name,
                            value=value,
                            unit=unit
                        )
                        parameters.append(parameter)
                    except ValueError:
                        continue
        
        return parameters
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get PDF file metadata"""
        try:
            file_stat = Path(file_path).stat()
            metadata = {
                'file_size': file_stat.st_size,
                'created_time': datetime.fromtimestamp(file_stat.st_ctime),
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime),
                'page_count': 0
            }
            
            # Get page count
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    metadata['page_count'] = len(pdf_reader.pages)
            except Exception:
                pass
            
            return metadata
            
        except Exception as e:
            log_error(f"Failed to get file metadata: {str(e)}", "PDF_PROCESSOR")
            return {}

# Global PDF processor instance
pdf_processor = PDFProcessor() 