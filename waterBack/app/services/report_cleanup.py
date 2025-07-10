import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Set
import time

from app.config import settings
from app.utils.logger import log_info, log_debug, log_error
from app.services.workflow_manager import workflow_manager

class ReportCleanupService:
    """Automatyczny cleanup raportów z optymalnym czasem przechowywania"""
    
    def __init__(self):
        self.reports_dir = Path(settings.REPORTS_FOLDER)
        self.cleanup_interval = settings.CLEANUP_INTERVAL_MINUTES * 60  # sekundy
        self.report_lifetime = settings.REPORT_LIFETIME_MINUTES * 60   # sekundy
        self.post_download_cleanup = settings.POST_DOWNLOAD_CLEANUP_MINUTES * 60  # sekundy
        self.download_tracking: Dict[str, float] = {}  # analysis_id -> timestamp pobrano
        self.cleanup_task = None
        
    async def start_cleanup_service(self):
        """Uruchom serwis cleanup w tle"""
        if self.cleanup_task:
            return
        
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        log_info("Started report cleanup service (10min retention)", "CLEANUP_SERVICE")
    
    async def stop_cleanup_service(self):
        """Zatrzymaj serwis cleanup"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None
            log_info("Stopped report cleanup service", "CLEANUP_SERVICE")
    
    async def _cleanup_loop(self):
        """Główna pętla cleanup"""
        while True:
            try:
                await self._cleanup_expired_reports()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error(f"Cleanup loop error: {str(e)}", "CLEANUP_SERVICE")
                await asyncio.sleep(60)  # Retry za minutę
    
    async def _cleanup_expired_reports(self):
        """Usuń wygasłe raporty"""
        current_time = time.time()
        deleted_count = 0
        
        if not self.reports_dir.exists():
            return
        
        for report_file in self.reports_dir.glob("*.pdf"):
            try:
                analysis_id = report_file.stem
                file_age = current_time - report_file.stat().st_mtime
                
                # Sprawdź czy raport został pobrany
                if analysis_id in self.download_tracking:
                    # Jeśli pobrano, usuń po krótkim czasie
                    download_time = self.download_tracking[analysis_id]
                    if current_time - download_time > self.post_download_cleanup:
                        report_file.unlink()
                        self.download_tracking.pop(analysis_id, None)
                        deleted_count += 1
                        log_debug(f"Deleted downloaded report: {analysis_id}", "CLEANUP_SERVICE")
                else:
                    # Jeśli nie pobrano, usuń po 10 minutach
                    if file_age > self.report_lifetime:
                        report_file.unlink()
                        deleted_count += 1
                        log_debug(f"Deleted expired report: {analysis_id}", "CLEANUP_SERVICE")
                
            except Exception as e:
                log_error(f"Error deleting report {report_file}: {str(e)}", "CLEANUP_SERVICE")
        
        # Cleanup starych sesji workflow
        await self._cleanup_old_sessions()
        
        if deleted_count > 0:
            log_info(f"Cleaned up {deleted_count} expired reports", "CLEANUP_SERVICE")
    
    async def _cleanup_old_sessions(self):
        """Usuń stare sesje workflow"""
        try:
            workflow_manager.cleanup_old_sessions(max_age_hours=1)  # 1 godzina
        except Exception as e:
            log_error(f"Session cleanup error: {str(e)}", "CLEANUP_SERVICE")
    
    def mark_report_downloaded(self, analysis_id: str):
        """Oznacz raport jako pobrany"""
        self.download_tracking[analysis_id] = time.time()
        log_debug(f"Marked report as downloaded: {analysis_id}", "CLEANUP_SERVICE")
    
    def get_report_status(self, analysis_id: str) -> Dict[str, any]:
        """Pobierz status raportu"""
        report_path = self.reports_dir / f"{analysis_id}.pdf"
        
        if not report_path.exists():
            return {"exists": False, "expired": True}
        
        current_time = time.time()
        file_age = current_time - report_path.stat().st_mtime
        
        return {
            "exists": True,
            "expired": file_age > self.report_lifetime,
            "age_minutes": file_age / 60,
            "downloaded": analysis_id in self.download_tracking
        }
    
    def cleanup_immediately(self, analysis_id: str):
        """Usuń raport natychmiast"""
        try:
            report_path = self.reports_dir / f"{analysis_id}.pdf"
            if report_path.exists():
                report_path.unlink()
                log_debug(f"Immediately cleaned up report: {analysis_id}", "CLEANUP_SERVICE")
            
            # Usuń z tracking
            self.download_tracking.pop(analysis_id, None)
            
        except Exception as e:
            log_error(f"Immediate cleanup failed for {analysis_id}: {str(e)}", "CLEANUP_SERVICE")

# Globalny serwis cleanup
cleanup_service = ReportCleanupService() 