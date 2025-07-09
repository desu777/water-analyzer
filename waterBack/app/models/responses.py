from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class PDFUploadResponse(BaseModel):
    """Response model for PDF upload"""
    success: bool = Field(..., description="Upload success status")
    analysisId: str = Field(..., description="Unique analysis identifier")
    message: str = Field(..., description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "analysisId": "analysis_123456",
                "message": "PDF uploaded successfully",
                "error": None
            }
        }

class AnalysisStatus(BaseModel):
    """Analysis status response"""
    id: str = Field(..., description="Analysis ID")
    status: Literal['uploading', 'processing', 'completed', 'error'] = Field(..., description="Current status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Current status message")
    startTime: datetime = Field(..., description="Analysis start time")
    completedTime: Optional[datetime] = Field(None, description="Analysis completion time")
    error: Optional[str] = Field(None, description="Error message if status is error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "analysis_123456",
                "status": "processing",
                "progress": 65,
                "message": "Analyzing water parameters...",
                "startTime": "2024-01-15T10:30:00Z",
                "completedTime": None,
                "error": None
            }
        }

class AnalysisResult(BaseModel):
    """Analysis result response"""
    id: str = Field(..., description="Analysis ID")
    originalFilename: str = Field(..., description="Original PDF filename")
    analysisMarkdown: str = Field(..., description="Analysis results in markdown format")
    analysisDate: datetime = Field(..., description="Analysis completion date")
    processingTime: float = Field(..., description="Processing time in seconds")
    pdfUrl: Optional[str] = Field(None, description="URL to download PDF report")
    previewUrl: Optional[str] = Field(None, description="URL to preview results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "analysis_123456",
                "originalFilename": "water_test_results.pdf",
                "analysisMarkdown": "# Water Analysis Results\n\n## Summary\nYour water quality is...",
                "analysisDate": "2024-01-15T10:35:00Z",
                "processingTime": 45.2,
                "pdfUrl": "/api/download/analysis_123456",
                "previewUrl": "/api/preview/analysis_123456"
            }
        }

class AnalysisPreview(BaseModel):
    """Analysis preview response"""
    id: str = Field(..., description="Analysis ID")
    markdown: str = Field(..., description="Analysis results in markdown format")
    metadata: dict = Field(..., description="Analysis metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "analysis_123456",
                "markdown": "# Water Analysis Results\n\n## Summary\nYour water quality is...",
                "metadata": {
                    "originalFilename": "water_test_results.pdf",
                    "analysisDate": "2024-01-15T10:35:00Z",
                    "processingTime": 45.2
                }
            }
        }

class AnalysisWorkflow(BaseModel):
    """Workflow update for SSE streaming"""
    step: Literal['upload', 'parsing', 'analysis', 'generation', 'complete'] = Field(..., description="Current workflow step")
    status: Literal['processing', 'completed', 'error'] = Field(..., description="Step status")
    message: str = Field(..., description="Step message")
    progress: int = Field(..., description="Overall progress (0-100)")
    elapsedTime: float = Field(..., description="Elapsed time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": "analysis",
                "status": "processing",
                "message": "Analyzing water parameters with AI...",
                "progress": 65,
                "elapsedTime": 23.5
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: int = Field(..., description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": 1705312800
            }
        }

class ApiError(BaseModel):
    """Standard API error response"""
    message: str = Field(..., description="Error message")
    status: Optional[int] = Field(None, description="HTTP status code")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "File too large. Maximum size is 10MB",
                "status": 413,
                "code": "FILE_TOO_LARGE"
            }
        } 