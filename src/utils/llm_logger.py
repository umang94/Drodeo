"""
OpenAI API Response Logger

Comprehensive logging system for OpenAI API interactions in the enhanced
audio-visual analysis system. Tracks requests, responses, sync plans,
and generates analysis reports.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import time

logger = logging.getLogger(__name__)

@dataclass
class RequestMetadata:
    """Metadata for OpenAI API requests"""
    timestamp: str
    session_id: str
    request_id: str
    audio_file: str
    video_file: str
    audio_duration: float
    audio_size_mb: float
    keyframe_count: int
    keyframe_timestamps: List[float]
    model: str
    prompt_tokens: Optional[int] = None
    max_tokens: int = 1500
    processing_time_seconds: Optional[float] = None

@dataclass
class ResponseMetadata:
    """Metadata for OpenAI API responses"""
    response_id: str
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    response_time_seconds: float
    success: bool
    error_message: Optional[str] = None

class LLMResponseLogger:
    """Comprehensive logging for OpenAI API interactions"""
    
    def __init__(self, base_log_dir: str = "logs/openai_responses"):
        """
        Initialize the LLM response logger
        
        Args:
            base_log_dir: Base directory for storing logs
        """
        self.base_log_dir = Path(base_log_dir)
        self.current_session_id = None
        self.current_session_dir = None
        self.request_counter = 0
        
        # Ensure log directory exists
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup file logging for the session"""
        log_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler for this logger
        log_file = self.base_log_dir / "llm_logger.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)
        
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    
    def start_session(self, session_id: str) -> str:
        """
        Start a new logging session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path to session directory
        """
        self.current_session_id = session_id
        self.request_counter = 0
        
        # Create session directory
        today = datetime.now().strftime('%Y-%m-%d')
        daily_dir = self.base_log_dir / today
        daily_dir.mkdir(exist_ok=True)
        
        self.current_session_dir = daily_dir / session_id
        self.current_session_dir.mkdir(exist_ok=True)
        
        # Create session metadata
        session_metadata = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'session_dir': str(self.current_session_dir),
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost_estimate': 0.0
        }
        
        session_file = self.current_session_dir / "session_metadata.json"
        with open(session_file, 'w') as f:
            json.dump(session_metadata, f, indent=2)
        
        logger.info(f"Started logging session: {session_id}")
        logger.info(f"Session directory: {self.current_session_dir}")
        
        return str(self.current_session_dir)
    
    def log_audio_visual_analysis(self, request_data: Dict, response: Any, 
                                 audio_path: str, video_path: str, 
                                 keyframe_timestamps: List[float],
                                 processing_time: float) -> str:
        """
        Log complete audio-visual analysis interaction
        
        Args:
            request_data: Request metadata
            response: OpenAI API response
            audio_path: Path to audio file
            video_path: Path to video file
            keyframe_timestamps: List of keyframe timestamps
            processing_time: Total processing time in seconds
            
        Returns:
            Request ID for this interaction
        """
        if not self.current_session_dir:
            raise ValueError("No active session. Call start_session() first.")
        
        self.request_counter += 1
        request_id = f"request_{self.request_counter:03d}"
        
        # Create request metadata
        audio_size_mb = os.path.getsize(audio_path) / (1024 * 1024) if os.path.exists(audio_path) else 0
        
        request_metadata = RequestMetadata(
            timestamp=datetime.now().isoformat(),
            session_id=self.current_session_id,
            request_id=request_id,
            audio_file=Path(audio_path).name,
            video_file=Path(video_path).name,
            audio_duration=request_data.get('audio_duration', 0),
            audio_size_mb=audio_size_mb,
            keyframe_count=len(keyframe_timestamps),
            keyframe_timestamps=keyframe_timestamps,
            model=request_data.get('model', 'gpt-4o'),
            processing_time_seconds=processing_time
        )
        
        # Save request metadata
        request_file = self.current_session_dir / f"{request_id}_metadata.json"
        with open(request_file, 'w') as f:
            json.dump(asdict(request_metadata), f, indent=2)
        
        # Save complete API response
        response_data = {
            'id': getattr(response, 'id', 'unknown'),
            'object': getattr(response, 'object', 'chat.completion'),
            'created': getattr(response, 'created', int(time.time())),
            'model': getattr(response, 'model', 'gpt-4o'),
            'choices': [],
            'usage': {}
        }
        
        # Extract choices
        if hasattr(response, 'choices') and response.choices:
            for choice in response.choices:
                choice_data = {
                    'index': getattr(choice, 'index', 0),
                    'message': {
                        'role': getattr(choice.message, 'role', 'assistant'),
                        'content': getattr(choice.message, 'content', '')
                    },
                    'finish_reason': getattr(choice, 'finish_reason', 'stop')
                }
                response_data['choices'].append(choice_data)
        
        # Extract usage information
        if hasattr(response, 'usage'):
            response_data['usage'] = {
                'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                'total_tokens': getattr(response.usage, 'total_tokens', 0)
            }
        
        # Save API response
        response_file = self.current_session_dir / f"{request_id}_response.json"
        with open(response_file, 'w') as f:
            json.dump(response_data, f, indent=2)
        
        # Log summary
        total_tokens = response_data['usage'].get('total_tokens', 0)
        logger.info(f"Logged API interaction {request_id}")
        logger.info(f"  Audio: {Path(audio_path).name} ({audio_size_mb:.2f}MB)")
        logger.info(f"  Video: {Path(video_path).name} ({len(keyframe_timestamps)} keyframes)")
        logger.info(f"  Tokens: {total_tokens}, Time: {processing_time:.2f}s")
        
        return request_id
    
    def log_sync_plan_generation(self, request_id: str, sync_plan: Any, 
                                confidence: float, llm_reasoning: str = "") -> None:
        """
        Log generated sync plans with metadata
        
        Args:
            request_id: Associated request ID
            sync_plan: Generated AudioVisualSyncPlan
            confidence: LLM confidence score (0-1)
            llm_reasoning: LLM's reasoning for the sync plan
        """
        if not self.current_session_dir:
            raise ValueError("No active session. Call start_session() first.")
        
        # Convert sync plan to dictionary
        if hasattr(sync_plan, '__dict__'):
            sync_plan_data = sync_plan.__dict__.copy()
        else:
            sync_plan_data = sync_plan
        
        # Add metadata
        sync_plan_data.update({
            'request_id': request_id,
            'generation_timestamp': datetime.now().isoformat(),
            'sync_confidence': confidence,
            'llm_reasoning': llm_reasoning,
            'plan_quality_metrics': self._calculate_plan_quality_metrics(sync_plan_data)
        })
        
        # Save sync plan
        sync_plan_file = self.current_session_dir / f"{request_id}_sync_plan.json"
        with open(sync_plan_file, 'w') as f:
            json.dump(sync_plan_data, f, indent=2)
        
        logger.info(f"Logged sync plan for {request_id}")
        logger.info(f"  Duration: {sync_plan_data.get('music_duration', 0):.1f}s")
        logger.info(f"  Transitions: {len(sync_plan_data.get('transition_points', []))}")
        logger.info(f"  Confidence: {confidence:.2f}")
    
    def _calculate_plan_quality_metrics(self, sync_plan_data: Dict) -> Dict[str, float]:
        """Calculate quality metrics for a sync plan"""
        metrics = {}
        
        # Transition density (transitions per minute)
        duration = sync_plan_data.get('music_duration', 1)
        transitions = len(sync_plan_data.get('transition_points', []))
        metrics['transition_density'] = (transitions / duration) * 60
        
        # Energy mapping completeness
        energy_mapping = sync_plan_data.get('energy_mapping', {})
        metrics['energy_mapping_completeness'] = len(energy_mapping) / max(1, len(energy_mapping))
        
        # Video segment coverage
        video_segments = sync_plan_data.get('video_segments', [])
        if video_segments:
            total_segment_duration = sum(
                seg.get('end_time', 0) - seg.get('start_time', 0) 
                for seg in video_segments
            )
            metrics['segment_coverage'] = min(1.0, total_segment_duration / duration)
        else:
            metrics['segment_coverage'] = 0.0
        
        return metrics
    
    def log_video_generation_result(self, music_filename: str, output_path: str, 
                                   sync_plan: Any, success: bool = True, 
                                   error_message: str = "") -> None:
        """
        Log video generation results
        
        Args:
            music_filename: Name of music file
            output_path: Path to generated video
            sync_plan: Sync plan used for generation
            success: Whether generation was successful
            error_message: Error message if generation failed
        """
        if not self.current_session_dir:
            return
        
        result_data = {
            'timestamp': datetime.now().isoformat(),
            'music_filename': music_filename,
            'output_path': output_path,
            'success': success,
            'error_message': error_message,
            'file_exists': os.path.exists(output_path) if output_path else False,
            'file_size_mb': 0
        }
        
        # Get file size if exists
        if result_data['file_exists']:
            result_data['file_size_mb'] = os.path.getsize(output_path) / (1024 * 1024)
        
        # Add sync plan summary
        if hasattr(sync_plan, '__dict__'):
            result_data['sync_plan_summary'] = {
                'music_duration': getattr(sync_plan, 'music_duration', 0),
                'transition_count': len(getattr(sync_plan, 'transition_points', [])),
                'sync_confidence': getattr(sync_plan, 'sync_confidence', 0)
            }
        
        # Save result
        result_file = self.current_session_dir / f"video_result_{music_filename}.json"
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        logger.info(f"Logged video generation result for {music_filename}")
        if success:
            logger.info(f"  Output: {Path(output_path).name} ({result_data['file_size_mb']:.1f}MB)")
        else:
            logger.error(f"  Failed: {error_message}")
    
    def create_analysis_report(self, session_id: str) -> str:
        """
        Generate comprehensive analysis report for session
        
        Args:
            session_id: Session ID to generate report for
            
        Returns:
            Path to generated HTML report
        """
        if not self.current_session_dir:
            raise ValueError("No active session")
        
        # Collect all session data
        session_data = self._collect_session_data()
        
        # Generate HTML report
        report_html = self._generate_html_report(session_data)
        
        # Save report
        report_dir = self.base_log_dir / "analysis_reports"
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f"{session_id}_report.html"
        with open(report_file, 'w') as f:
            f.write(report_html)
        
        logger.info(f"Generated analysis report: {report_file}")
        return str(report_file)
    
    def _collect_session_data(self) -> Dict:
        """Collect all data from current session"""
        session_data = {
            'requests': [],
            'sync_plans': [],
            'video_results': [],
            'summary': {}
        }
        
        if not self.current_session_dir.exists():
            return session_data
        
        # Collect request data
        for file in self.current_session_dir.glob("request_*_metadata.json"):
            with open(file) as f:
                session_data['requests'].append(json.load(f))
        
        # Collect sync plans
        for file in self.current_session_dir.glob("request_*_sync_plan.json"):
            with open(file) as f:
                session_data['sync_plans'].append(json.load(f))
        
        # Collect video results
        for file in self.current_session_dir.glob("video_result_*.json"):
            with open(file) as f:
                session_data['video_results'].append(json.load(f))
        
        # Calculate summary statistics
        session_data['summary'] = self._calculate_session_summary(session_data)
        
        return session_data
    
    def _calculate_session_summary(self, session_data: Dict) -> Dict:
        """Calculate summary statistics for session"""
        summary = {
            'total_requests': len(session_data['requests']),
            'total_videos_generated': len(session_data['video_results']),
            'successful_generations': sum(1 for r in session_data['video_results'] if r['success']),
            'total_tokens': 0,
            'average_processing_time': 0,
            'average_confidence': 0,
            'total_video_duration': 0
        }
        
        # Calculate token usage
        for request in session_data['requests']:
            # This would need to be matched with response data
            pass
        
        # Calculate average confidence
        confidences = [sp.get('sync_confidence', 0) for sp in session_data['sync_plans']]
        if confidences:
            summary['average_confidence'] = sum(confidences) / len(confidences)
        
        # Calculate total video duration
        for sync_plan in session_data['sync_plans']:
            summary['total_video_duration'] += sync_plan.get('music_duration', 0)
        
        return summary
    
    def _generate_html_report(self, session_data: Dict) -> str:
        """Generate HTML report from session data"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LLM Analysis Report - {self.current_session_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>LLM Audio-Visual Analysis Report</h1>
                <p><strong>Session:</strong> {self.current_session_id}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Session Summary</h2>
                <div class="metric">Total Requests: {session_data['summary']['total_requests']}</div>
                <div class="metric">Videos Generated: {session_data['summary']['total_videos_generated']}</div>
                <div class="metric">Success Rate: {session_data['summary']['successful_generations']}/{session_data['summary']['total_videos_generated']}</div>
                <div class="metric">Avg Confidence: {session_data['summary']['average_confidence']:.2f}</div>
                <div class="metric">Total Duration: {session_data['summary']['total_video_duration']:.1f}s</div>
            </div>
            
            <div class="section">
                <h2>Request Details</h2>
                <table>
                    <tr>
                        <th>Request ID</th>
                        <th>Audio File</th>
                        <th>Duration</th>
                        <th>Keyframes</th>
                        <th>Processing Time</th>
                    </tr>
        """
        
        for request in session_data['requests']:
            html += f"""
                    <tr>
                        <td>{request['request_id']}</td>
                        <td>{request['audio_file']}</td>
                        <td>{request['audio_duration']:.1f}s</td>
                        <td>{request['keyframe_count']}</td>
                        <td>{request.get('processing_time_seconds', 0):.2f}s</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Sync Plan Analysis</h2>
                <table>
                    <tr>
                        <th>Request ID</th>
                        <th>Music Duration</th>
                        <th>Transitions</th>
                        <th>Confidence</th>
                        <th>Transition Density</th>
                    </tr>
        """
        
        for sync_plan in session_data['sync_plans']:
            metrics = sync_plan.get('plan_quality_metrics', {})
            html += f"""
                    <tr>
                        <td>{sync_plan['request_id']}</td>
                        <td>{sync_plan.get('music_duration', 0):.1f}s</td>
                        <td>{len(sync_plan.get('transition_points', []))}</td>
                        <td>{sync_plan.get('sync_confidence', 0):.2f}</td>
                        <td>{metrics.get('transition_density', 0):.1f}/min</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html

def create_session_logger(session_id: str = None) -> LLMResponseLogger:
    """
    Convenience function to create a session logger
    
    Args:
        session_id: Optional session ID, auto-generated if not provided
        
    Returns:
        Configured LLMResponseLogger instance
    """
    if not session_id:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger_instance = LLMResponseLogger()
    logger_instance.start_session(session_id)
    
    return logger_instance

if __name__ == "__main__":
    # Test the logging system
    test_logger = create_session_logger("test_session")
    print(f"Test session created: {test_logger.current_session_dir}")
    
    # Test logging a mock request
    mock_response = type('MockResponse', (), {
        'id': 'test-123',
        'choices': [type('Choice', (), {
            'message': type('Message', (), {'content': 'Test response'}),
            'finish_reason': 'stop'
        })],
        'usage': type('Usage', (), {
            'prompt_tokens': 100,
            'completion_tokens': 50,
            'total_tokens': 150
        })
    })
    
    request_id = test_logger.log_audio_visual_analysis(
        request_data={'model': 'gpt-4o', 'audio_duration': 60.0},
        response=mock_response,
        audio_path="test_audio.wav",
        video_path="test_video.mp4",
        keyframe_timestamps=[0, 10, 20, 30],
        processing_time=5.2
    )
    
    print(f"Test request logged: {request_id}")
