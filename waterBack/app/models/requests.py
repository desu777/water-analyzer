from pydantic import BaseModel, Field
from typing import Optional
from fastapi import UploadFile

class PDFUploadRequest(BaseModel):
    """Request model for PDF upload"""
    userId: Optional[str] = Field(None, description="Optional user identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "userId": "user123"
            }
        }

class AnalysisRequest(BaseModel):
    """Request model for analysis operations"""
    analysisId: str = Field(..., description="Analysis ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysisId": "analysis_123456"
            }
        } 