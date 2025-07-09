import magic
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException

from app.config import settings
from app.utils.logger import log_debug, log_error, log_warning

def validate_pdf_file(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded PDF file
    Returns: (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not file:
            return False, "No file provided"
        
        # Check filename
        if not file.filename:
            return False, "Filename is missing"
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension != '.pdf':
            return False, f"Invalid file extension: {file_extension}. Only PDF files are allowed."
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)     # Reset to beginning
        
        max_size = settings.MAX_PDF_SIZE_MB * 1024 * 1024  # Convert to bytes
        if file_size > max_size:
            return False, f"File too large: {file_size} bytes. Maximum allowed: {max_size} bytes ({settings.MAX_PDF_SIZE_MB}MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Check MIME type using python-magic
        try:
            file_content = file.file.read(1024)  # Read first 1KB
            file.file.seek(0)  # Reset
            
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type != 'application/pdf':
                return False, f"Invalid file type: {mime_type}. Expected: application/pdf"
        except Exception as e:
            log_warning(f"MIME type check failed: {str(e)}", "VALIDATION")
            # Continue without MIME check if magic fails
        
        # Additional PDF header check
        pdf_header = file_content[:5]
        if pdf_header != b'%PDF-':
            return False, "File does not appear to be a valid PDF (missing PDF header)"
        
        log_debug(f"PDF validation passed: {file.filename} ({file_size} bytes)", "VALIDATION")
        return True, None
        
    except Exception as e:
        log_error(f"PDF validation error: {str(e)}", "VALIDATION")
        return False, f"Validation error: {str(e)}"

def validate_analysis_id(analysis_id: str) -> bool:
    """Validate analysis ID format"""
    if not analysis_id:
        return False
    
    # Check if it's a valid UUID-like string or custom format
    if len(analysis_id) < 10 or len(analysis_id) > 100:
        return False
    
    # Check for invalid characters
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not set(analysis_id).issubset(allowed_chars):
        return False
    
    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove path components
    filename = Path(filename).name
    
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name_part = filename[:200]
        ext_part = filename[-50:]
        filename = name_part + ext_part
    
    return filename

class ValidationError(HTTPException):
    """Custom validation error"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=message) 