import os
import uuid
import shutil
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.config import settings
from app.utils.logger import log_debug, log_error, log_info

class FileHandler:
    """Handler for file operations"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_FOLDER)
        self.temp_dir = Path(settings.TEMP_FOLDER)
        self.reports_dir = Path(settings.REPORTS_FOLDER)
        
        # Ensure directories exist
        for directory in [self.upload_dir, self.temp_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def read_file_async(self, file_path: str) -> str:
        """Asynchronously read a text file."""
        try:
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                content = await f.read()
            log_debug(f"Successfully read file async: {file_path}", "FILE_HANDLER")
            return content
        except Exception as e:
            log_error(f"Failed to read file async {file_path}: {str(e)}", "FILE_HANDLER")
            raise

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename with UUID"""
        file_extension = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"
    
    async def save_uploaded_file(self, file: UploadFile, analysis_id: str) -> str:
        """Save uploaded file to disk"""
        try:
            # Generate unique filename
            unique_filename = self.generate_unique_filename(file.filename)
            file_path = self.upload_dir / unique_filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            log_info(f"File saved: {unique_filename}", "FILE_HANDLER")
            return str(file_path)
            
        except Exception as e:
            log_error(f"Failed to save file: {str(e)}", "FILE_HANDLER")
            raise
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        return Path(file_path).stat().st_size
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from disk"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                log_info(f"File deleted: {file_path}", "FILE_HANDLER")
                return True
            return False
        except Exception as e:
            log_error(f"Failed to delete file: {str(e)}", "FILE_HANDLER")
            return False
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old files"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        for directory in [self.upload_dir, self.temp_dir, self.reports_dir]:
            for file_path in directory.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    self.delete_file(str(file_path))
    
    def get_report_path(self, analysis_id: str) -> str:
        """Get report file path"""
        return str(self.reports_dir / f"{analysis_id}.pdf")
    
    def get_temp_path(self, analysis_id: str, suffix: str = ".tmp") -> str:
        """Get temporary file path"""
        return str(self.temp_dir / f"{analysis_id}{suffix}")

# Global file handler instance
file_handler = FileHandler() 