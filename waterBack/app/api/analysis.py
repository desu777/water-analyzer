from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
from datetime import datetime

from app.models.responses import AnalysisStatus, AnalysisResult, AnalysisPreview, ApiError
from app.utils.validation import validate_analysis_id
from app.utils.logger import log_debug, log_error, log_info
from app.services.workflow_manager import workflow_manager
from app.services.report_generator import report_generator
from app.services.report_cleanup import cleanup_service

router = APIRouter()

@router.get("/status/{analysis_id}", response_model=AnalysisStatus)
async def get_analysis_status(
    analysis_id: str = Path(..., description="Analysis ID")
):
    """
    Get current analysis status
    """
    try:
        # Validate analysis ID
        if not validate_analysis_id(analysis_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid analysis ID format"
            )
        
        # Get status from workflow manager
        status = workflow_manager.get_analysis_status(analysis_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        log_debug(f"Status requested for {analysis_id}: {status.status}", "ANALYSIS_API")
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get status failed for {analysis_id}: {str(e)}", "ANALYSIS_API")
        raise HTTPException(
            status_code=500,
            detail="Failed to get analysis status"
        )

@router.get("/result/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(
    analysis_id: str = Path(..., description="Analysis ID")
):
    """
    Get analysis results
    """
    try:
        # Validate analysis ID
        if not validate_analysis_id(analysis_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid analysis ID format"
            )
        
        # Get session
        session = workflow_manager.get_session(analysis_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        if session.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed. Current status: {session.status}"
            )
        
        # Check if report exists and is not expired
        report_status = cleanup_service.get_report_status(analysis_id)
        
        if not report_status["exists"]:
            raise HTTPException(
                status_code=404,
                detail="Analysis report not found or expired"
            )
        
        if report_status["expired"]:
            raise HTTPException(
                status_code=410,
                detail=f"Analysis report expired (available for 10 minutes only). Age: {report_status['age_minutes']:.1f} minutes"
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - session.startTime).total_seconds()
        
        result = AnalysisResult(
            id=analysis_id,
            originalFilename=session.context.originalFilename,
            analysisMarkdown=session.result,
            analysisDate=datetime.now(),
            processingTime=processing_time,
            pdfUrl=f"/api/download/{analysis_id}",
            previewUrl=f"/api/preview/{analysis_id}"
        )
        
        log_info(f"Analysis result retrieved for {analysis_id}", "ANALYSIS_API")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get result failed for {analysis_id}: {str(e)}", "ANALYSIS_API")
        raise HTTPException(
            status_code=500,
            detail="Failed to get analysis result"
        )

@router.get("/preview/{analysis_id}", response_model=AnalysisPreview)
async def get_analysis_preview(
    analysis_id: str = Path(..., description="Analysis ID")
):
    """
    Get analysis preview (markdown)
    """
    try:
        # Validate analysis ID
        if not validate_analysis_id(analysis_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid analysis ID format"
            )
        
        # Get session
        session = workflow_manager.get_session(analysis_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        if session.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed. Current status: {session.status}"
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - session.startTime).total_seconds()
        
        preview = AnalysisPreview(
            id=analysis_id,
            markdown=session.result,
            metadata={
                "originalFilename": session.context.originalFilename,
                "analysisDate": datetime.now().isoformat(),
                "processingTime": processing_time
            }
        )
        
        log_info(f"Analysis preview retrieved for {analysis_id}", "ANALYSIS_API")
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get preview failed for {analysis_id}: {str(e)}", "ANALYSIS_API")
        raise HTTPException(
            status_code=500,
            detail="Failed to get analysis preview"
        )

@router.get("/download/{analysis_id}")
async def download_analysis_pdf(
    analysis_id: str = Path(..., description="Analysis ID")
):
    """
    Download analysis PDF report
    """
    try:
        # Validate analysis ID
        if not validate_analysis_id(analysis_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid analysis ID format"
            )
        
        # Check if report exists and is not expired
        report_status = cleanup_service.get_report_status(analysis_id)
        
        if not report_status["exists"]:
            raise HTTPException(
                status_code=404,
                detail="Analysis report not found or expired"
            )
        
        if report_status["expired"]:
            raise HTTPException(
                status_code=410,
                detail=f"Analysis report expired (available for 10 minutes only). Age: {report_status['age_minutes']:.1f} minutes"
            )
        
        # Get report path
        report_path = report_generator.get_report_path(analysis_id)
        
        # Get original filename for download
        session = workflow_manager.get_session(analysis_id)
        original_filename = "water_analysis_report.pdf"
        
        if session and session.context:
            original_filename = f"analiza_{session.context.originalFilename.replace('.pdf', '')}.pdf"
        
        # Mark as downloaded for faster cleanup
        cleanup_service.mark_report_downloaded(analysis_id)
        
        log_info(f"PDF download started for {analysis_id} (marked as downloaded)", "ANALYSIS_API")
        
        return FileResponse(
            path=report_path,
            filename=original_filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={original_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Download failed for {analysis_id}: {str(e)}", "ANALYSIS_API")
        raise HTTPException(
            status_code=500,
            detail="Failed to download analysis report"
        )

@router.get("/report-status/{analysis_id}")
async def get_report_status(
    analysis_id: str = Path(..., description="Analysis ID")
):
    """
    Get report availability status
    """
    try:
        # Validate analysis ID
        if not validate_analysis_id(analysis_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid analysis ID format"
            )
        
        # Get report status
        report_status = cleanup_service.get_report_status(analysis_id)
        
        return {
            "analysisId": analysis_id,
            "exists": report_status["exists"],
            "expired": report_status["expired"],
            "ageMinutes": report_status.get("age_minutes", 0),
            "downloaded": report_status.get("downloaded", False),
            "expiresIn": max(0, 10 - report_status.get("age_minutes", 0)) if report_status["exists"] else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get report status failed for {analysis_id}: {str(e)}", "ANALYSIS_API")
        raise HTTPException(
            status_code=500,
            detail="Failed to get report status"
        ) 