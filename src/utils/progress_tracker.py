#!/usr/bin/env python3
"""
Progress Tracker Module for Drone Video Generator

This module provides enhanced progress tracking and error handling:
- Real-time progress updates during video processing
- Detailed error reporting with recovery suggestions
- Performance metrics and timing information
- User-friendly status messages
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import traceback
import sys

@dataclass
class ProcessingStep:
    """Represents a single processing step with timing and status."""
    name: str
    description: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    error_message: Optional[str] = None
    progress_percent: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

class ProgressTracker:
    """Enhanced progress tracking and error handling for video processing."""
    
    def __init__(self, total_videos: int = 0, target_themes: List[str] = None):
        """
        Initialize progress tracker
        
        Args:
            total_videos: Total number of videos to process
            target_themes: List of target themes to generate
        """
        self.total_videos = total_videos
        self.target_themes = target_themes or []
        self.start_time = datetime.now()
        self.steps: Dict[str, ProcessingStep] = {}
        self.current_step: Optional[str] = None
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        
        # Initialize processing steps
        self._initialize_steps()
        
        # Configure logging
        self._setup_logging()
    
    def _initialize_steps(self):
        """Initialize all processing steps."""
        steps_config = [
            ("validation", "Validating input files"),
            ("video_analysis", "Analyzing video content"),
            ("ai_processing", "AI-powered scene analysis"),
            ("clip_selection", "Selecting best clips"),
            ("theme_assignment", "Assigning clips to themes"),
            ("music_preparation", "Preparing background music"),
            ("video_rendering", "Rendering themed videos"),
            ("finalization", "Finalizing output")
        ]
        
        for step_id, description in steps_config:
            self.steps[step_id] = ProcessingStep(
                name=step_id,
                description=description
            )
    
    def _setup_logging(self):
        """Setup enhanced logging for progress tracking."""
        # Create a custom logger for progress tracking
        self.logger = logging.getLogger('progress_tracker')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler with custom formatting
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def start_step(self, step_id: str, details: Dict[str, Any] = None):
        """Start a processing step."""
        if step_id not in self.steps:
            self.steps[step_id] = ProcessingStep(
                name=step_id,
                description=step_id.replace('_', ' ').title()
            )
        
        step = self.steps[step_id]
        step.start_time = datetime.now()
        step.status = "running"
        step.progress_percent = 0.0
        if details:
            step.details.update(details)
        
        self.current_step = step_id
        
        # Log step start
        self.logger.info(f"🚀 {step.description}...")
        if details:
            for key, value in details.items():
                self.logger.info(f"   {key}: {value}")
    
    def update_step_progress(self, step_id: str, progress_percent: float, 
                           message: str = None, details: Dict[str, Any] = None):
        """Update progress for a specific step."""
        if step_id not in self.steps:
            return
        
        step = self.steps[step_id]
        step.progress_percent = min(100.0, max(0.0, progress_percent))
        
        if details:
            step.details.update(details)
        
        # Log progress update
        if message:
            self.logger.info(f"   📊 {message} ({progress_percent:.1f}%)")
        elif progress_percent % 25 == 0:  # Log every 25%
            self.logger.info(f"   📊 {step.description}: {progress_percent:.1f}%")
    
    def complete_step(self, step_id: str, success: bool = True, 
                     message: str = None, details: Dict[str, Any] = None):
        """Complete a processing step."""
        if step_id not in self.steps:
            return
        
        step = self.steps[step_id]
        step.end_time = datetime.now()
        step.status = "completed" if success else "failed"
        step.progress_percent = 100.0 if success else step.progress_percent
        
        if details:
            step.details.update(details)
        
        # Calculate duration
        if step.start_time:
            duration = step.end_time - step.start_time
            step.details['duration'] = duration.total_seconds()
        
        # Log completion
        duration_str = f" ({duration.total_seconds():.1f}s)" if step.start_time else ""
        if success:
            self.logger.info(f"   ✅ {step.description} completed{duration_str}")
            if message:
                self.logger.info(f"      {message}")
        else:
            self.logger.error(f"   ❌ {step.description} failed{duration_str}")
            if message:
                self.logger.error(f"      {message}")
        
        # Clear current step if this was it
        if self.current_step == step_id:
            self.current_step = None
    
    def add_error(self, error: Exception, context: str = None, 
                  recovery_suggestion: str = None):
        """Add an error with context and recovery suggestions."""
        error_info = {
            'timestamp': datetime.now(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context or "Unknown context",
            'recovery_suggestion': recovery_suggestion,
            'traceback': traceback.format_exc()
        }
        
        self.errors.append(error_info)
        
        # Log error
        self.logger.error(f"❌ Error in {context or 'processing'}: {error}")
        if recovery_suggestion:
            self.logger.info(f"💡 Suggestion: {recovery_suggestion}")
    
    def add_warning(self, message: str, context: str = None):
        """Add a warning message."""
        warning_info = {
            'timestamp': datetime.now(),
            'message': message,
            'context': context or "Unknown context"
        }
        
        self.warnings.append(warning_info)
        
        # Log warning
        self.logger.warning(f"⚠️  {message}")
    
    def get_overall_progress(self) -> float:
        """Calculate overall progress percentage."""
        if not self.steps:
            return 0.0
        
        total_progress = sum(step.progress_percent for step in self.steps.values())
        return total_progress / len(self.steps)
    
    def get_elapsed_time(self) -> timedelta:
        """Get total elapsed time since start."""
        return datetime.now() - self.start_time
    
    def estimate_remaining_time(self) -> Optional[timedelta]:
        """Estimate remaining processing time."""
        progress = self.get_overall_progress()
        if progress <= 0:
            return None
        
        elapsed = self.get_elapsed_time()
        total_estimated = elapsed / (progress / 100.0)
        remaining = total_estimated - elapsed
        
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def print_summary(self):
        """Print a comprehensive summary of the processing session."""
        elapsed = self.get_elapsed_time()
        overall_progress = self.get_overall_progress()
        
        print("\n" + "=" * 60)
        print("📊 PROCESSING SUMMARY")
        print("=" * 60)
        
        # Overall stats
        print(f"⏱️  Total time: {elapsed}")
        print(f"📈 Overall progress: {overall_progress:.1f}%")
        print(f"🎯 Target themes: {len(self.target_themes)}")
        print(f"📹 Videos processed: {self.total_videos}")
        
        # Step details
        print(f"\n📋 Step Details:")
        for step_id, step in self.steps.items():
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(step.status, "❓")
            
            duration_str = ""
            if step.start_time and step.end_time:
                duration = step.end_time - step.start_time
                duration_str = f" ({duration.total_seconds():.1f}s)"
            
            print(f"   {status_icon} {step.description}: {step.progress_percent:.1f}%{duration_str}")
        
        # Errors and warnings
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors[-3:], 1):  # Show last 3 errors
                print(f"   {i}. {error['context']}: {error['message']}")
                if error['recovery_suggestion']:
                    print(f"      💡 {error['recovery_suggestion']}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings[-3:], 1):  # Show last 3 warnings
                print(f"   {i}. {warning['context']}: {warning['message']}")
        
        # Performance metrics
        completed_steps = [s for s in self.steps.values() if s.status == "completed"]
        if completed_steps:
            avg_step_time = sum(s.details.get('duration', 0) for s in completed_steps) / len(completed_steps)
            print(f"\n⚡ Performance:")
            print(f"   Average step time: {avg_step_time:.1f}s")
            print(f"   Steps completed: {len(completed_steps)}/{len(self.steps)}")
        
        print("=" * 60)
    
    def get_status_dict(self) -> Dict[str, Any]:
        """Get current status as a dictionary for API/JSON export."""
        return {
            'start_time': self.start_time.isoformat(),
            'elapsed_time': self.get_elapsed_time().total_seconds(),
            'overall_progress': self.get_overall_progress(),
            'current_step': self.current_step,
            'total_videos': self.total_videos,
            'target_themes': self.target_themes,
            'steps': {
                step_id: {
                    'name': step.name,
                    'description': step.description,
                    'status': step.status,
                    'progress_percent': step.progress_percent,
                    'start_time': step.start_time.isoformat() if step.start_time else None,
                    'end_time': step.end_time.isoformat() if step.end_time else None,
                    'details': step.details
                }
                for step_id, step in self.steps.items()
            },
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'estimated_remaining': self.estimate_remaining_time().total_seconds() if self.estimate_remaining_time() else None
        }

def create_progress_tracker(total_videos: int, target_themes: List[str]) -> ProgressTracker:
    """Factory function to create a progress tracker."""
    return ProgressTracker(total_videos=total_videos, target_themes=target_themes)

# Example usage and testing
if __name__ == "__main__":
    # Test the progress tracker
    tracker = ProgressTracker(total_videos=2, target_themes=['happy', 'peaceful'])
    
    # Simulate processing steps
    tracker.start_step('validation', {'files_found': 2})
    time.sleep(0.5)
    tracker.update_step_progress('validation', 50.0, "Checking file formats")
    time.sleep(0.5)
    tracker.complete_step('validation', success=True, message="All files valid")
    
    tracker.start_step('video_analysis')
    time.sleep(0.3)
    tracker.update_step_progress('video_analysis', 75.0, "Analyzing motion patterns")
    time.sleep(0.3)
    tracker.complete_step('video_analysis', success=True)
    
    # Simulate an error
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        tracker.add_error(e, "video_rendering", "Check available disk space and try again")
    
    # Add a warning
    tracker.add_warning("Low motion detected in some clips", "clip_selection")
    
    # Print summary
    tracker.print_summary()
