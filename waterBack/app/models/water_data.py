from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

class WaterParameter(BaseModel):
    """Single water parameter model"""
    name: str = Field(..., description="Parameter name")
    value: Any = Field(..., description="Parameter value (number or string)")
    unit: Optional[str] = Field(None, description="Parameter unit")
    acceptable: Optional[bool] = Field(None, description="Is parameter within acceptable range")
    range: Optional[Dict[str, float]] = Field(None, description="Acceptable range (min, max)")
    description: Optional[str] = Field(None, description="Parameter description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "pH",
                "value": 7.2,
                "unit": "pH",
                "acceptable": True,
                "range": {"min": 6.5, "max": 8.5},
                "description": "Water acidity/alkalinity level"
            }
        }

class WaterTestData(BaseModel):
    """Complete water test data model"""
    testDate: Optional[str] = Field(None, description="Test date from PDF")
    laboratory: Optional[str] = Field(None, description="Laboratory name")
    sampleLocation: Optional[str] = Field(None, description="Sample location")
    parameters: List[WaterParameter] = Field([], description="List of water parameters")
    summary: Optional[str] = Field(None, description="Test summary")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "testDate": "2024-01-15",
                "laboratory": "Water Quality Lab",
                "sampleLocation": "Home tap water",
                "parameters": [
                    {
                        "name": "pH",
                        "value": 7.2,
                        "unit": "pH",
                        "acceptable": True,
                        "range": {"min": 6.5, "max": 8.5}
                    }
                ],
                "summary": "Water quality is within acceptable parameters",
                "recommendations": ["Regular testing recommended"]
            }
        }

class AnalysisContext(BaseModel):
    """Context for AI analysis"""
    analysisId: str = Field(..., description="Analysis ID")
    originalFilename: str = Field(..., description="Original PDF filename")
    extractedText: str = Field(..., description="Extracted text from PDF")
    waterData: Optional[WaterTestData] = Field(None, description="Structured water data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysisId": "analysis_123456",
                "originalFilename": "water_test_results.pdf",
                "extractedText": "WATER QUALITY ANALYSIS REPORT\nDate: 2024-01-15\npH: 7.2...",
                "waterData": {
                    "testDate": "2024-01-15",
                    "parameters": []
                },
                "metadata": {
                    "fileSize": 245760,
                    "pageCount": 2,
                    "processingTime": 1.2
                }
            }
        }

class AnalysisSession(BaseModel):
    """Analysis session tracking"""
    id: str = Field(..., description="Session ID")
    status: str = Field(..., description="Current status")
    startTime: datetime = Field(..., description="Session start time")
    currentStep: str = Field(..., description="Current processing step")
    progress: int = Field(0, description="Progress percentage")
    context: Optional[AnalysisContext] = Field(None, description="Analysis context")
    result: Optional[str] = Field(None, description="Analysis result")
    error: Optional[str] = Field(None, description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "analysis_123456",
                "status": "processing",
                "startTime": "2024-01-15T10:30:00Z",
                "currentStep": "analysis",
                "progress": 65,
                "context": None,
                "result": None,
                "error": None
            }
        } 