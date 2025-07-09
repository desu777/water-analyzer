import asyncio
import json
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse
from typing import Optional

from app.utils.validation import validate_analysis_id
from app.utils.logger import log_debug, log_error, log_info
from app.services.workflow_manager import workflow_manager
from app.models.responses import AnalysisWorkflow

router = APIRouter()

@router.get("/stream/{analysis_id}")
async def stream_analysis_progress(
    analysis_id: str = Path(..., description="Analysis ID")
):
    """
    Stream analysis progress using Server-Sent Events (SSE)
    """
    try:
        # Validate analysis ID
        if not validate_analysis_id(analysis_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid analysis ID format"
            )
        
        # Check if analysis exists
        session = workflow_manager.get_session(analysis_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found"
            )
        
        log_info(f"SSE stream started for {analysis_id}", "STREAMING_API")
        
        # Create SSE generator
        async def event_generator():
            """Generate SSE events for analysis progress"""
            
            # Buffer to store events for this client
            event_buffer = []
            
            # Callback function to receive workflow updates
            def workflow_callback(update: AnalysisWorkflow):
                event_data = {
                    "step": update.step,
                    "status": update.status,
                    "message": update.message,
                    "progress": update.progress,
                    "elapsedTime": update.elapsedTime
                }
                event_buffer.append(event_data)
            
            # Register callback
            workflow_manager.register_sse_callback(analysis_id, workflow_callback)
            
            try:
                # Send initial status
                current_status = workflow_manager.get_analysis_status(analysis_id)
                if current_status:
                    initial_data = {
                        "step": "status",
                        "status": current_status.status,
                        "message": f"Aktualny status: {current_status.status}",
                        "progress": current_status.progress,
                        "elapsedTime": 0
                    }
                    
                    yield f"data: {json.dumps(initial_data)}\n\n"
                
                # Stream updates
                while True:
                    # Send buffered events
                    while event_buffer:
                        event_data = event_buffer.pop(0)
                        yield f"data: {json.dumps(event_data)}\n\n"
                    
                    # Check if analysis is complete or error
                    session = workflow_manager.get_session(analysis_id)
                    if session and session.status in ['completed', 'error']:
                        # Send final event and break
                        final_data = {
                            "step": "complete" if session.status == "completed" else "error",
                            "status": session.status,
                            "message": "Analiza zakończona" if session.status == "completed" else session.error,
                            "progress": 100 if session.status == "completed" else session.progress,
                            "elapsedTime": 0
                        }
                        
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                    
                    # Wait before next check
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                log_debug(f"SSE stream cancelled for {analysis_id}", "STREAMING_API")
            except Exception as e:
                log_error(f"SSE stream error for {analysis_id}: {str(e)}", "STREAMING_API")
                # Send error event
                error_data = {
                    "step": "error",
                    "status": "error",
                    "message": f"Błąd streamingu: {str(e)}",
                    "progress": 0,
                    "elapsedTime": 0
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            finally:
                # Unregister callback
                workflow_manager.unregister_sse_callback(analysis_id)
                log_debug(f"SSE stream ended for {analysis_id}", "STREAMING_API")
        
        # Return SSE response
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"SSE stream setup failed for {analysis_id}: {str(e)}", "STREAMING_API")
        raise HTTPException(
            status_code=500,
            detail="Failed to setup progress stream"
        ) 