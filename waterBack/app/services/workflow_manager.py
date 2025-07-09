import asyncio
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field

from app.models.water_data import AnalysisSession, AnalysisContext
from app.models.responses import AnalysisWorkflow, AnalysisStatus
from app.utils.logger import log_debug, log_error, log_info

@dataclass
class WorkflowStep:
    """Workflow step definition"""
    step_id: str
    name: str
    description: str
    progress_start: int
    progress_end: int
    estimated_duration: float = 10.0  # seconds

class WorkflowManager:
    """Manager for analysis workflow and progress tracking"""
    
    def __init__(self):
        self.active_sessions: Dict[str, AnalysisSession] = {}
        self.workflow_steps = self._initialize_workflow_steps()
        self.sse_callbacks: Dict[str, List[Callable]] = {}
    
    def _initialize_workflow_steps(self) -> List[WorkflowStep]:
        """Initialize workflow steps"""
        return [
            WorkflowStep(
                step_id="upload",
                name="Przesyłanie pliku",
                description="Wysyłanie pliku na serwer",
                progress_start=0,
                progress_end=10,
                estimated_duration=2.0
            ),
            WorkflowStep(
                step_id="parsing",
                name="Analiza treści",
                description="Odczytywanie danych z PDF",
                progress_start=10,
                progress_end=30,
                estimated_duration=8.0
            ),
            WorkflowStep(
                step_id="analysis",
                name="Analiza AI",
                description="Analiza wyników badań",
                progress_start=30,
                progress_end=80,
                estimated_duration=25.0
            ),
            WorkflowStep(
                step_id="generation",
                name="Generowanie raportu",
                description="Tworzenie końcowego raportu",
                progress_start=80,
                progress_end=95,
                estimated_duration=8.0
            ),
            WorkflowStep(
                step_id="complete",
                name="Zakończone",
                description="Analiza gotowa do pobrania",
                progress_start=95,
                progress_end=100,
                estimated_duration=1.0
            )
        ]
    
    def start_analysis(self, analysis_id: str, context: AnalysisContext) -> AnalysisSession:
        """Start new analysis workflow"""
        session = AnalysisSession(
            id=analysis_id,
            status="processing",
            startTime=datetime.now(),
            currentStep="upload",
            progress=0,
            context=context
        )
        
        self.active_sessions[analysis_id] = session
        log_info(f"Started analysis workflow for {analysis_id}", "WORKFLOW_MANAGER")
        
        # Send initial update
        self._send_workflow_update(analysis_id, "upload", "processing", "Rozpoczynanie analizy...", 0)
        
        return session
    
    def update_step(self, analysis_id: str, step_id: str, status: str, message: str, progress: Optional[int] = None):
        """Update workflow step"""
        if analysis_id not in self.active_sessions:
            log_error(f"Analysis session not found: {analysis_id}", "WORKFLOW_MANAGER")
            return
        
        session = self.active_sessions[analysis_id]
        session.currentStep = step_id
        
        # Calculate progress if not provided
        if progress is None:
            step = self._get_workflow_step(step_id)
            if step:
                if status == "completed":
                    progress = step.progress_end
                elif status == "processing":
                    progress = step.progress_start + (step.progress_end - step.progress_start) // 2
                else:
                    progress = step.progress_start
        
        session.progress = progress
        
        # Update session status
        if status == "error":
            session.status = "error"
            session.error = message
        elif step_id == "complete" and status == "completed":
            session.status = "completed"
        
        log_debug(f"Updated step {step_id} for {analysis_id}: {status} ({progress}%)", "WORKFLOW_MANAGER")
        
        # Send SSE update
        self._send_workflow_update(analysis_id, step_id, status, message, progress)
    
    def complete_analysis(self, analysis_id: str, result: str):
        """Complete analysis workflow"""
        if analysis_id not in self.active_sessions:
            return
        
        session = self.active_sessions[analysis_id]
        session.status = "completed"
        session.result = result
        session.progress = 100
        
        log_info(f"Completed analysis workflow for {analysis_id}", "WORKFLOW_MANAGER")
        
        # Send final update
        self._send_workflow_update(analysis_id, "complete", "completed", "Analiza zakończona pomyślnie", 100)
    
    def error_analysis(self, analysis_id: str, error_message: str):
        """Mark analysis as error"""
        if analysis_id not in self.active_sessions:
            return
        
        session = self.active_sessions[analysis_id]
        session.status = "error"
        session.error = error_message
        
        log_error(f"Analysis failed for {analysis_id}: {error_message}", "WORKFLOW_MANAGER")
        
        # Send error update
        self._send_workflow_update(analysis_id, session.currentStep, "error", error_message, session.progress)
    
    def get_analysis_status(self, analysis_id: str) -> Optional[AnalysisStatus]:
        """Get current analysis status"""
        if analysis_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[analysis_id]
        
        return AnalysisStatus(
            id=analysis_id,
            status=session.status,
            progress=session.progress,
            message=f"Krok: {session.currentStep}",
            startTime=session.startTime,
            completedTime=datetime.now() if session.status == "completed" else None,
            error=session.error
        )
    
    def get_session(self, analysis_id: str) -> Optional[AnalysisSession]:
        """Get analysis session"""
        return self.active_sessions.get(analysis_id)
    
    def cleanup_session(self, analysis_id: str):
        """Clean up completed session"""
        if analysis_id in self.active_sessions:
            del self.active_sessions[analysis_id]
            log_debug(f"Cleaned up session {analysis_id}", "WORKFLOW_MANAGER")
    
    def register_sse_callback(self, analysis_id: str, callback: Callable):
        """Register SSE callback for workflow updates"""
        if analysis_id not in self.sse_callbacks:
            self.sse_callbacks[analysis_id] = []
        
        self.sse_callbacks[analysis_id].append(callback)
        log_debug(f"Registered SSE callback for {analysis_id}", "WORKFLOW_MANAGER")
    
    def unregister_sse_callback(self, analysis_id: str):
        """Unregister SSE callbacks"""
        if analysis_id in self.sse_callbacks:
            del self.sse_callbacks[analysis_id]
            log_debug(f"Unregistered SSE callbacks for {analysis_id}", "WORKFLOW_MANAGER")
    
    def _send_workflow_update(self, analysis_id: str, step: str, status: str, message: str, progress: int):
        """Send workflow update to SSE callbacks"""
        if analysis_id not in self.sse_callbacks:
            return
        
        # Calculate elapsed time
        session = self.active_sessions.get(analysis_id)
        elapsed_time = 0
        if session:
            elapsed_time = (datetime.now() - session.startTime).total_seconds()
        
        update = AnalysisWorkflow(
            step=step,
            status=status,
            message=message,
            progress=progress,
            elapsedTime=elapsed_time
        )
        
        # Send to all registered callbacks
        for callback in self.sse_callbacks[analysis_id]:
            try:
                callback(update)
            except Exception as e:
                log_error(f"SSE callback error: {str(e)}", "WORKFLOW_MANAGER")
    
    def _get_workflow_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get workflow step by ID"""
        for step in self.workflow_steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        current_time = datetime.now()
        to_remove = []
        
        for analysis_id, session in self.active_sessions.items():
            age = (current_time - session.startTime).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(analysis_id)
        
        for analysis_id in to_remove:
            self.cleanup_session(analysis_id)
            self.unregister_sse_callback(analysis_id)
        
        if to_remove:
            log_info(f"Cleaned up {len(to_remove)} old sessions", "WORKFLOW_MANAGER")

# Global workflow manager instance
workflow_manager = WorkflowManager() 