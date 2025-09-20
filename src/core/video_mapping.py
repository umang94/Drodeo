"""
Video Reference Mapping System for Drodeo Batch Processing

Handles mapping between concatenated video timestamps and original video segments
to enable single API call processing while maintaining editing precision.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import os
from pathlib import Path

@dataclass
class VideoSegment:
    """Represents a segment of an original video within a concatenated video"""
    original_path: str
    start_in_batch: float  # Start time in concatenated video (seconds)
    end_in_batch: float    # End time in concatenated video (seconds)
    duration: float        # Duration of this segment (seconds)
    
    def __post_init__(self):
        """Calculate duration automatically"""
        self.duration = self.end_in_batch - self.start_in_batch

@dataclass
class Batch:
    """Represents a batch of concatenated videos with mapping metadata"""
    batch_id: int
    concatenated_path: str
    original_videos: List[VideoSegment]  # Videos in this batch
    total_duration: float
    blank_frame_duration: float = 1.0  # Duration of blank frames between videos
    
    def find_original_video(self, timestamp: float) -> Optional[VideoSegment]:
        """
        Find which original video corresponds to a timestamp in the concatenated video
        
        Args:
            timestamp: Time in seconds within the concatenated video
            
        Returns:
            VideoSegment if found, None otherwise
        """
        for segment in self.original_videos:
            if segment.start_in_batch <= timestamp <= segment.end_in_batch:
                return segment
        return None
    
    def translate_timestamp(self, timestamp: float) -> Optional[Dict]:
        """
        Translate a concatenated video timestamp back to original video reference
        
        Args:
            timestamp: Time in seconds within the concatenated video
            
        Returns:
            Dictionary with original video path and local timestamp, or None if not found
        """
        segment = self.find_original_video(timestamp)
        if segment:
            local_timestamp = timestamp - segment.start_in_batch
            return {
                'original_path': segment.original_path,
                'local_timestamp': local_timestamp,
                'segment_start': segment.start_in_batch,
                'segment_end': segment.end_in_batch
            }
        return None

class VideoBatchMapping:
    """Manages mapping between concatenated videos and original video segments"""
    
    def __init__(self):
        self.batches: List[Batch] = []
    
    def add_batch(self, batch: Batch):
        """Add a batch to the mapping"""
        self.batches.append(batch)
    
    def find_original_video(self, timestamp: float, batch_id: int = 0) -> Optional[VideoSegment]:
        """
        Find which original video corresponds to a timestamp in a specific batch
        
        Args:
            timestamp: Time in seconds within the concatenated video
            batch_id: ID of the batch to search in (default: 0 for single batch)
            
        Returns:
            VideoSegment if found, None otherwise
        """
        if 0 <= batch_id < len(self.batches):
            return self.batches[batch_id].find_original_video(timestamp)
        return None
    
    def translate_timestamp(self, timestamp: float, batch_id: int = 0) -> Optional[Dict]:
        """
        Translate a concatenated video timestamp back to original video reference
        
        Args:
            timestamp: Time in seconds within the concatenated video
            batch_id: ID of the batch to search in (default: 0 for single batch)
            
        Returns:
            Dictionary with original video path and local timestamp, or None if not found
        """
        if 0 <= batch_id < len(self.batches):
            return self.batches[batch_id].translate_timestamp(timestamp)
        return None
    
    def create_mapping_from_concatenation(self, video_paths: List[str], 
                                        concatenated_duration: float,
                                        blank_duration: float = 0.0) -> Batch:
        """
        Create mapping metadata from a list of concatenated videos
        
        Args:
            video_paths: List of original video file paths in concatenation order
            concatenated_duration: Total duration of the concatenated video
            blank_duration: Duration of blank frames between videos (0.0 for no blanks)
            
        Returns:
            Batch object with complete mapping metadata
        """
        from moviepy.editor import VideoFileClip
        
        segments = []
        current_time = 0.0
        
        for i, video_path in enumerate(video_paths):
            if not os.path.exists(video_path):
                continue
                
            try:
                # Get original video duration
                clip = VideoFileClip(video_path)
                video_duration = clip.duration
                clip.close()
                
                # Create segment mapping
                segment = VideoSegment(
                    original_path=video_path,
                    start_in_batch=current_time,
                    end_in_batch=current_time + video_duration,
                    duration=video_duration
                )
                segments.append(segment)
                
                # Move to next segment position (video only, no blank frames)
                current_time += video_duration
                
                # Add blank frame duration after each video except the last one (if enabled)
                if blank_duration > 0 and i < len(video_paths) - 1:
                    current_time += blank_duration
                    
            except Exception as e:
                print(f"Warning: Failed to process video {video_path}: {e}")
                continue
        
        # Create batch with mapping
        batch = Batch(
            batch_id=0,
            concatenated_path="",  # Will be set by caller
            original_videos=segments,
            total_duration=concatenated_duration,
            blank_frame_duration=blank_duration
        )
        
        self.add_batch(batch)
        return batch
    
    def validate_mapping(self) -> bool:
        """Validate that the mapping is consistent and complete"""
        if not self.batches:
            return False
            
        for batch in self.batches:
            # Check for overlapping segments
            segments = sorted(batch.original_videos, key=lambda x: x.start_in_batch)
            for i in range(len(segments) - 1):
                if segments[i].end_in_batch > segments[i + 1].start_in_batch:
                    return False
                    
            # Check total duration consistency
            total_mapped_duration = sum(seg.duration for seg in segments)
            total_blank_time = (len(segments) - 1) * batch.blank_frame_duration
            expected_total = total_mapped_duration + total_blank_time
            
            if abs(expected_total - batch.total_duration) > 1.0:  # Allow 1 second tolerance
                return False
                
        return True

# Utility functions for timestamp translation in Gemini responses
def translate_gemini_timestamps(gemini_reasoning: str, mapping: VideoBatchMapping) -> str:
    """
    Translate timestamps in Gemini's response from concatenated video to original videos
    
    Args:
        gemini_reasoning: Raw Gemini response text
        mapping: VideoBatchMapping instance with translation data
        
    Returns:
        Modified reasoning with original video references
    """
    if not mapping.batches:
        return gemini_reasoning
    
    # Get the first batch (assuming single batch processing)
    batch = mapping.batches[0]
    
    # Extract all timestamps from the reasoning
    timestamps = extract_timestamps_from_reasoning(gemini_reasoning)
    
    # Create a mapping of concatenated timestamps to original video info
    timestamp_mapping = {}
    for timestamp in timestamps:
        translation = batch.translate_timestamp(timestamp)
        if translation:
            timestamp_mapping[timestamp] = translation
    
    # Replace timestamps in the reasoning text
    translated_reasoning = gemini_reasoning
    
    # Replace timestamps with original video references
    for concat_timestamp, video_info in sorted(timestamp_mapping.items(), key=lambda x: x[0], reverse=True):
        original_video = os.path.basename(video_info['original_path'])
        local_timestamp = video_info['local_timestamp']
        
        # Format the replacement text
        replacement = f"{original_video} at {local_timestamp:.1f}s"
        
        # Replace the timestamp in various formats
        timestamp_patterns = [
            f"{concat_timestamp:.1f}s",
            f"{int(concat_timestamp)}s",
            f"{int(concat_timestamp//60)}:{int(concat_timestamp%60):02d}",
            f"{concat_timestamp:.1f}",
        ]
        
        for pattern in timestamp_patterns:
            translated_reasoning = translated_reasoning.replace(
                pattern, 
                replacement
            )
    
    # Add header to indicate translation was applied
    if timestamp_mapping:
        translated_reasoning = f"TIMESTAMP TRANSLATION APPLIED (Concatenated → Original Videos):\n{translated_reasoning}"
    
    return translated_reasoning

def extract_timestamps_from_reasoning(reasoning: str) -> List[float]:
    """
    Extract timestamps from Gemini's reasoning text
    
    Args:
        reasoning: Gemini response text
        
    Returns:
        List of timestamps found in the text
    """
    import re
    
    # Simple pattern to find timestamps (e.g., "1:23", "45.6s", "1m30s")
    patterns = [
        r'(\d+):(\d+)',  # MM:SS format
        r'(\d+\.?\d*)\s*s',  # 45.6s format
        r'(\d+)m\s*(\d+)s',  # 1m30s format
    ]
    
    timestamps = []
    
    for pattern in patterns:
        matches = re.findall(pattern, reasoning)
        for match in matches:
            if isinstance(match, tuple):
                # Handle MM:SS format
                if len(match) == 2:
                    minutes = int(match[0])
                    seconds = int(match[1])
                    total_seconds = minutes * 60 + seconds
                    timestamps.append(total_seconds)
                # Handle 1m30s format
                elif len(match) == 2 and 'm' in reasoning:
                    minutes = int(match[0])
                    seconds = int(match[1])
                    total_seconds = minutes * 60 + seconds
                    timestamps.append(total_seconds)
            else:
                # Handle single number format
                try:
                    seconds = float(match)
                    timestamps.append(seconds)
                except ValueError:
                    continue
    
    return sorted(set(timestamps))

if __name__ == "__main__":
    # Test the mapping system
    mapping = VideoBatchMapping()
    
    # Create test video paths using actual files from input_dev if they exist
    input_dev_path = Path("input_dev")
    test_videos = []
    
    if input_dev_path.exists():
        for ext in ['.mp4', '.mov', '.avi', '.mkv']:
            test_videos.extend([str(p) for p in input_dev_path.glob(f"*{ext}")])
    
    # Use first 3 videos if available, otherwise use mock data
    if len(test_videos) >= 3:
        test_videos = test_videos[:3]
        print(f"Using real videos: {[Path(v).name for v in test_videos]}")
        
        # Get actual durations for realistic testing
        from moviepy.editor import VideoFileClip
        actual_durations = []
        for video_path in test_videos:
            try:
                clip = VideoFileClip(video_path)
                actual_durations.append(clip.duration)
                clip.close()
            except:
                actual_durations.append(10.0)  # Fallback
        
        total_duration = sum(actual_durations) + (len(test_videos) - 1) * 1.0
        batch = mapping.create_mapping_from_concatenation(
            test_videos, 
            concatenated_duration=total_duration,
            blank_duration=1.0
        )
    else:
        # Fallback to direct mock data creation without file operations
        print("Using direct mock data for testing")
        mock_videos = ["mock_video1.mp4", "mock_video2.mp4", "mock_video3.mp4"]
        mock_durations = [15.0, 20.0, 25.0]
        
        # Create segments directly without file operations
        segments = []
        current_time = 0.0
        
        for i, (video_path, duration) in enumerate(zip(mock_videos, mock_durations)):
            segment = VideoSegment(
                original_path=video_path,
                start_in_batch=current_time,
                end_in_batch=current_time + duration,
                duration=duration
            )
            segments.append(segment)
            current_time += duration
            
            # Add blank frame after each video except the last one
            if i < len(mock_videos) - 1:
                current_time += 1.0  # blank duration
        
        total_duration = current_time
        batch = Batch(
            batch_id=0,
            concatenated_path="mock_concatenated.mp4",
            original_videos=segments,
            total_duration=total_duration,
            blank_frame_duration=1.0
        )
        mapping.add_batch(batch)
    
    print("✅ Video mapping system test completed")
    print(f"   Batch contains {len(batch.original_videos)} video segments")
    print(f"   Total duration: {batch.total_duration:.1f}s")
    print(f"   Mapping validation: {mapping.validate_mapping()}")
