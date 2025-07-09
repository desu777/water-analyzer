import uuid
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime

from app.models.responses import PDFUploadResponse, ApiError
from app.models.water_data import AnalysisContext
from app.utils.validation import validate_pdf_file, ValidationError
from app.utils.file_handler import file_handler
from app.utils.logger import log_debug, log_error, log_info
from app.services.workflow_manager import workflow_manager
from app.services.pdf_processor import pdf_processor
from app.services.ai_analyzer import ai_analyzer
from app.services.report_generator import report_generator

router = APIRouter()

@router.post("/upload-pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    pdf: UploadFile = File(...),
    userId: Optional[str] = Form(None)
):
    """
    Upload PDF file for water analysis
    """
    try:
        log_info(f"PDF upload started: {pdf.filename}", "UPLOAD_API")
        
        # Validate PDF file
        is_valid, error_message = validate_pdf_file(pdf)
        if not is_valid:
            raise ValidationError(error_message)
        
        # Generate analysis ID
        analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"
        
        # Save uploaded file
        file_path = await file_handler.save_uploaded_file(pdf, analysis_id)
        
        # Create analysis context
        context = AnalysisContext(
            analysisId=analysis_id,
            originalFilename=pdf.filename,
            extractedText="",  # Will be filled during processing
            metadata={
                'userId': userId,
                'uploadTime': str(datetime.now()),
                'filePath': file_path
            }
        )
        
        # Start workflow
        workflow_manager.start_analysis(analysis_id, context)
        
        # Start background processing
        background_tasks.add_task(process_pdf_analysis, analysis_id, file_path)
        
        log_info(f"PDF upload completed: {analysis_id}", "UPLOAD_API")
        
        return PDFUploadResponse(
            success=True,
            analysisId=analysis_id,
            message="PDF uploaded successfully. Analysis started."
        )
        
    except ValidationError as e:
        log_error(f"PDF validation failed: {str(e)}", "UPLOAD_API")
        return JSONResponse(
            status_code=400,
            content=ApiError(
                message=str(e),
                status=400,
                code="VALIDATION_ERROR"
            ).dict()
        )
    
    except Exception as e:
        log_error(f"PDF upload failed: {str(e)}", "UPLOAD_API")
        return JSONResponse(
            status_code=500,
            content=ApiError(
                message="Upload failed",
                status=500,
                code="UPLOAD_ERROR"
            ).dict()
        )

async def process_pdf_analysis(analysis_id: str, file_path: str):
    """
    Background task to process PDF analysis
    """
    try:
        log_info(f"Starting PDF analysis for {analysis_id}", "UPLOAD_API")
        
        # Step 1: Extract text from PDF
        workflow_manager.update_step(analysis_id, "parsing", "processing", "Wyodrębnianie tekstu z PDF...")
        
        extracted_text = await pdf_processor.extract_text_from_pdf(file_path)
        
        # Parse water data
        water_data = await pdf_processor.parse_water_data(extracted_text)
        
        workflow_manager.update_step(analysis_id, "parsing", "completed", "Tekst wyodrębniony pomyślnie")
        
        # Step 2: AI Analysis
        workflow_manager.update_step(analysis_id, "analysis", "processing", "Analiza wyników badań z wykorzystaniem AI...")
        
        # Update context with extracted data
        session = workflow_manager.get_session(analysis_id)
        if session and session.context:
            session.context.extractedText = extracted_text
            session.context.waterData = water_data
        
        # Perform AI analysis
        analysis_result = await ai_analyzer.analyze_water_data(session.context)
        
        workflow_manager.update_step(analysis_id, "analysis", "completed", "Analiza AI zakończona")
        
        # Step 3: Generate PDF report
        workflow_manager.update_step(analysis_id, "generation", "processing", "Generowanie raportu PDF...")
        
        report_path = await report_generator.generate_pdf_report(analysis_id, session.context, analysis_result)
        
        workflow_manager.update_step(analysis_id, "generation", "completed", "Raport PDF wygenerowany")
        
        # Step 4: Complete analysis
        workflow_manager.complete_analysis(analysis_id, analysis_result)
        
        # Cleanup uploaded file
        file_handler.delete_file(file_path)
        
        log_info(f"PDF analysis completed for {analysis_id}", "UPLOAD_API")
        
    except Exception as e:
        log_error(f"PDF analysis failed for {analysis_id}: {str(e)}", "UPLOAD_API")
        workflow_manager.error_analysis(analysis_id, str(e))
        
        # Cleanup on error
        file_handler.delete_file(file_path)
        report_generator.delete_report(analysis_id) 