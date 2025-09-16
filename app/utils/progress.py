#!/usr/bin/env python3

import threading
import time
from typing import Dict, Any
from datetime import datetime, timedelta

class ScanProgress:
    """Thread-safe progress tracking for concurrent scans"""
    
    def __init__(self, total_targets: int, max_workers: int = 8):
        self.total_targets = total_targets
        self.max_workers = max_workers
        self.completed_targets = 0
        self.active_workers = 0
        self.failed_targets = 0
        self.start_time = datetime.now()
        self.lock = threading.Lock()
        self.target_status: Dict[str, str] = {}  # target -> status
        self.display_thread = None
        self.stop_display = False
        
    def start_display(self):
        """Start the progress display thread"""
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
        
    def stop_display_thread(self):
        """Stop the progress display thread"""
        self.stop_display = True
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1)
            
    def _display_loop(self):
        """Main display loop that runs in background thread"""
        while not self.stop_display:
            self._print_progress()
            time.sleep(2)  # Update every 2 seconds
            
    def _print_progress(self):
        """Print current progress status"""
        with self.lock:
            elapsed = datetime.now() - self.start_time
            progress_percent = (self.completed_targets / self.total_targets * 100) if self.total_targets > 0 else 0
            
            # Create progress bar
            bar_length = 30
            filled_length = int(bar_length * progress_percent / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            # Calculate ETA
            if self.completed_targets > 0:
                avg_time_per_target = elapsed.total_seconds() / self.completed_targets
                remaining_targets = self.total_targets - self.completed_targets
                eta_seconds = remaining_targets * avg_time_per_target
                eta = str(timedelta(seconds=int(eta_seconds)))
            else:
                eta = "calculating..."
            
            # Clear line and print progress
            print(f"\r\033[K🔄 Progress: [{bar}] {progress_percent:5.1f}% | "
                  f"Completed: {self.completed_targets}/{self.total_targets} | "
                  f"Active Workers: {self.active_workers}/{self.max_workers} | "
                  f"Failed: {self.failed_targets} | "
                  f"ETA: {eta}", end="", flush=True)
    
    def target_started(self, target: str):
        """Mark a target as started"""
        with self.lock:
            self.active_workers += 1
            self.target_status[target] = "running"
            
    def target_completed(self, target: str):
        """Mark a target as completed"""
        with self.lock:
            self.completed_targets += 1
            self.active_workers -= 1
            self.target_status[target] = "completed"
            
    def target_failed(self, target: str):
        """Mark a target as failed"""
        with self.lock:
            self.completed_targets += 1
            self.active_workers -= 1
            self.failed_targets += 1
            self.target_status[target] = "failed"
            
    def get_summary(self) -> Dict[str, Any]:
        """Get final summary of scan progress"""
        with self.lock:
            total_time = datetime.now() - self.start_time
            return {
                "total_targets": self.total_targets,
                "completed": self.completed_targets,
                "failed": self.failed_targets,
                "success_rate": (self.completed_targets - self.failed_targets) / self.total_targets * 100 if self.total_targets > 0 else 0,
                "total_time": str(total_time),
                "avg_time_per_target": str(timedelta(seconds=total_time.total_seconds() / self.total_targets)) if self.total_targets > 0 else "0:00:00"
            }
    
    def print_final_summary(self):
        """Print final summary after scan completion"""
        self.stop_display_thread()
        print()  # New line after progress bar
        
        summary = self.get_summary()
        print(f"\n✅ Scan Complete!")
        print(f"   📊 Total Targets: {summary['total_targets']}")
        print(f"   ✅ Completed: {summary['completed'] - summary['failed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"   ⏱️  Total Time: {summary['total_time']}")
        print(f"   ⚡ Avg Time/Target: {summary['avg_time_per_target']}")
        print()

class ProgressManager:
    """Singleton manager for tracking multiple concurrent scans"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ProgressManager, cls).__new__(cls)
                    cls._instance.scans: Dict[str, ScanProgress] = {}
        return cls._instance
    
    def create_scan_progress(self, scan_id: str, total_targets: int, max_workers: int = 8) -> ScanProgress:
        """Create a new progress tracker for a scan"""
        progress = ScanProgress(total_targets, max_workers)
        progress.start_display()
        self.scans[scan_id] = progress
        return progress
    
    def get_scan_progress(self, scan_id: str) -> ScanProgress:
        """Get progress tracker for a scan"""
        return self.scans.get(scan_id)
    
    def remove_scan_progress(self, scan_id: str):
        """Remove progress tracker for completed scan"""
        if scan_id in self.scans:
            self.scans[scan_id].stop_display_thread()
            del self.scans[scan_id]

# Global progress manager instance
progress_manager = ProgressManager()
