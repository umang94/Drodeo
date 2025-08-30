"""
LLM-Powered Video Analysis

Advanced video analysis using LLM for holistic content understanding,
story flow detection, and creative direction. Enhanced with unified
audio-visual analysis capabilities.
"""

import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import base64
from dataclasses import dataclass
from moviepy.editor import VideoFileClip
import openai
from openai import OpenAI
import librosa
import numpy as np

# Gemini API imports
try:
    import google.generativeai as genai
    from google.generativeai import types
    GEMINI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Gemini API library not available: {e}")
    GEMINI_AVAILABLE = False

# Import audio analyzer and logging
from src.audio.audio_analyzer import AudioFeatures, AudioAnalyzer
from src.utils.llm_logger import LLMResponseLogger

logger = logging.getLogger(__name__)

@dataclass
class AudioVisualSyncPlan:
    """LLM-generated synchronization blueprint for full-length videos"""
    music_duration: float          # Full music length (79s-206s)
    video_segments: List[Dict]     # Beat-aligned video segments
    transition_points: List[float] # Exact beat timestamps for cuts
    energy_mapping: Dict[str, str] # Music sections → visual styles
    sync_confidence: float         # LLM confidence (0-1)
    narrative_flow: str           # Overall story arc
    llm_reasoning: str            # LLM's reasoning for sync decisions
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'music_duration': self.music_duration,
            'video_segments': self.video_segments,
            'transition_points': self.transition_points,
            'energy_mapping': self.energy_mapping,
            'sync_confidence': self.sync_confidence,
            'narrative_flow': self.narrative_flow,
            'llm_reasoning': self.llm_reasoning
        }

@dataclass
class VideoAnalysis:
    """Container for comprehensive video analysis results."""
    file_path: str
    duration: float
    content_summary: str
    shot_types: List[str]  # wide, medium, close-up, etc.
    motion_characteristics: str
    visual_style: str
    mood_energy: str
    story_potential: str
    best_clips_for_themes: Dict[str, List[Dict]]  # theme -> list of clip suggestions
    transition_points: List[float]  # suggested cut points
    narrative_structure: str
    technical_quality: str

class LLMVideoAnalyzer:
    """Analyzes videos using LLM for comprehensive content understanding."""
    
    def __init__(self, llm_logger: Optional[LLMResponseLogger] = None):
        """Initialize LLM video analyzer."""
        try:
            self.client = OpenAI()
            print("   ✅ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
            print(f"   ❌ OpenAI client initialization failed: {e}")
        
        # Initialize audio analyzer and logger
        self.audio_analyzer = AudioAnalyzer()
        self.llm_logger = llm_logger
        
        print("   🎵 Audio analyzer initialized")
        if self.llm_logger:
            print("   📝 LLM logging enabled")
    
    def analyze_video(self, video_path: str, use_dev_version: bool = True) -> Optional[VideoAnalysis]:
        """
        Analyze a video file using LLM for comprehensive understanding.
        
        Args:
            video_path: Path to video file
            use_dev_version: Use development version for faster processing
            
        Returns:
            VideoAnalysis object or None if analysis fails
        """
        if not self.client:
            print(f"   ❌ Cannot analyze {Path(video_path).name} - OpenAI client not available")
            return None
        
        # Determine which video file to analyze
        if use_dev_version:
            dev_path = self._get_dev_version_path(video_path)
            analysis_path = dev_path if os.path.exists(dev_path) else video_path
        else:
            analysis_path = video_path
        
        print(f"   🎬 Analyzing video: {Path(analysis_path).name}")
        
        try:
            # Extract video information
            video_info = self._get_video_info(analysis_path)
            if not video_info:
                return None
            
            # Create video frames for analysis
            frames_data = self._extract_analysis_frames(analysis_path, num_frames=8)
            if not frames_data:
                return None
            
            # Send to LLM for analysis
            analysis_result = self._analyze_with_llm(analysis_path, video_info, frames_data)
            
            if analysis_result:
                print(f"      ✅ Analysis complete for {Path(video_path).name}")
                return analysis_result
            else:
                print(f"      ❌ Analysis failed for {Path(video_path).name}")
                return None
                
        except Exception as e:
            logger.error(f"Video analysis failed for {video_path}: {e}")
            print(f"      ❌ Error analyzing {Path(video_path).name}: {e}")
            return None
    
    def _get_dev_version_path(self, original_path: str) -> str:
        """Get the development version path for a video."""
        path = Path(original_path)
        dev_filename = f"{path.stem}_dev{path.suffix}"
        return str(Path("input_dev") / dev_filename)
    
    def _get_video_info(self, video_path: str) -> Optional[Dict]:
        """Extract basic video information."""
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': (clip.w, clip.h),
                'file_size_mb': os.path.getsize(video_path) / (1024 * 1024)
            }
            clip.close()
            return info
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {e}")
            return None
    
    def _extract_analysis_frames(self, video_path: str, num_frames: int = 8) -> Optional[List[str]]:
        """Extract frames from video for LLM analysis."""
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            # Extract frames at evenly spaced intervals
            frame_times = [i * duration / (num_frames - 1) for i in range(num_frames)]
            frame_data = []
            
            for i, time_point in enumerate(frame_times):
                try:
                    # Extract frame
                    frame = clip.get_frame(time_point)
                    
                    # Convert to base64 for LLM
                    import cv2
                    import numpy as np
                    
                    # Convert RGB to BGR for OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Encode as JPEG
                    _, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    frame_data.append(frame_base64)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract frame at {time_point}s: {e}")
                    continue
            
            clip.close()
            
            if len(frame_data) >= 4:  # Need at least 4 frames for analysis
                print(f"      📸 Extracted {len(frame_data)} frames for analysis")
                return frame_data
            else:
                print(f"      ⚠️  Only extracted {len(frame_data)} frames, need at least 4")
                return None
                
        except Exception as e:
            logger.error(f"Frame extraction failed for {video_path}: {e}")
            return None
    
    def _analyze_with_llm(self, video_path: str, video_info: Dict, frames_data: List[str]) -> Optional[VideoAnalysis]:
        """Send video data to LLM for comprehensive analysis."""
        try:
            # Prepare the prompt
            prompt = self._create_analysis_prompt(video_path, video_info)
            
            # Prepare messages with frames
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert video editor and cinematographer. Analyze videos for content, style, mood, and editing potential. Provide detailed, actionable insights for video editing."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Add frames to the message
            for i, frame_data in enumerate(frames_data):
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame_data}",
                        "detail": "low"  # Use low detail for faster processing
                    }
                })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4 with vision
                messages=messages,
                max_tokens=1500,
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            # Convert to structured analysis
            return self._parse_llm_response(video_path, video_info, analysis_text)
            
        except Exception as e:
            logger.error(f"LLM analysis failed for {video_path}: {e}")
            return None
    
    def _create_analysis_prompt(self, video_path: str, video_info: Dict) -> str:
        """Create comprehensive analysis prompt for LLM."""
        filename = Path(video_path).name
        duration = video_info.get('duration', 0)
        size = video_info.get('size', (0, 0))
        
        prompt = f"""
Analyze this video comprehensively for video editing purposes:

**Video Details:**
- File: {filename}
- Duration: {duration:.1f} seconds
- Resolution: {size[0]}x{size[1]}

**Analysis Required:**

1. **Content Summary**: What happens in this video? What's the main subject/action?

2. **Shot Types**: Identify the types of shots (wide establishing, medium, close-up, aerial, handheld, etc.)

3. **Motion Characteristics**: Describe camera movement and subject motion (static, smooth pan, dynamic movement, etc.)

4. **Visual Style**: Describe the visual aesthetic (cinematic, documentary, casual, professional, etc.)

5. **Mood & Energy**: What's the emotional tone? (peaceful, exciting, dramatic, happy, contemplative, etc.)

6. **Story Potential**: How could this video work in a narrative? What story does it tell?

7. **Best Clips for Themes**: For each theme below, suggest 2-3 specific time segments (start-end seconds) that would work best:
   - Mellow/Calm
   - Exciting/Dynamic
   - Cinematic/Dramatic

8. **Transition Points**: Suggest 3-5 optimal cut points (timestamps) where transitions would work naturally

9. **Narrative Structure**: Does this video have a beginning/middle/end? How should it be used in editing?

10. **Technical Quality**: Comment on image quality, stability, lighting, composition

Please provide specific timestamps and actionable editing insights. Focus on how this video can be used effectively in music-synchronized editing.
"""
        return prompt
    
    def _parse_llm_response(self, video_path: str, video_info: Dict, analysis_text: str) -> VideoAnalysis:
        """Parse LLM response into structured VideoAnalysis object."""
        try:
            # For now, create a basic structure from the text response
            # In a more sophisticated version, we could ask the LLM to return JSON
            
            analysis = VideoAnalysis(
                file_path=video_path,
                duration=video_info.get('duration', 0),
                content_summary=self._extract_section(analysis_text, "Content Summary", "Shot Types"),
                shot_types=self._extract_list_section(analysis_text, "Shot Types"),
                motion_characteristics=self._extract_section(analysis_text, "Motion Characteristics", "Visual Style"),
                visual_style=self._extract_section(analysis_text, "Visual Style", "Mood & Energy"),
                mood_energy=self._extract_section(analysis_text, "Mood & Energy", "Story Potential"),
                story_potential=self._extract_section(analysis_text, "Story Potential", "Best Clips"),
                best_clips_for_themes=self._extract_clips_section(analysis_text),
                transition_points=self._extract_timestamps(analysis_text, "Transition Points"),
                narrative_structure=self._extract_section(analysis_text, "Narrative Structure", "Technical Quality"),
                technical_quality=self._extract_section(analysis_text, "Technical Quality", "")
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            # Return basic analysis if parsing fails
            return VideoAnalysis(
                file_path=video_path,
                duration=video_info.get('duration', 0),
                content_summary=analysis_text[:200] + "...",
                shot_types=["unknown"],
                motion_characteristics="Analysis parsing failed",
                visual_style="Unknown",
                mood_energy="Unknown",
                story_potential="Unknown",
                best_clips_for_themes={},
                transition_points=[],
                narrative_structure="Unknown",
                technical_quality="Unknown"
            )
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract a section of text between markers."""
        try:
            start_idx = text.find(start_marker)
            if start_idx == -1:
                return "Not found"
            
            start_idx = text.find(":", start_idx) + 1
            
            if end_marker:
                end_idx = text.find(end_marker, start_idx)
                if end_idx == -1:
                    end_idx = len(text)
            else:
                end_idx = len(text)
            
            section = text[start_idx:end_idx].strip()
            return section[:500]  # Limit length
            
        except Exception:
            return "Extraction failed"
    
    def _extract_list_section(self, text: str, marker: str) -> List[str]:
        """Extract a list from a section."""
        section = self._extract_section(text, marker, "Motion Characteristics")
        # Simple extraction - look for common shot type keywords
        shot_types = []
        keywords = ["wide", "medium", "close-up", "aerial", "handheld", "static", "pan", "tilt", "zoom"]
        
        for keyword in keywords:
            if keyword.lower() in section.lower():
                shot_types.append(keyword)
        
        return shot_types if shot_types else ["unknown"]
    
    def _extract_clips_section(self, text: str) -> Dict[str, List[Dict]]:
        """Extract clip suggestions for themes."""
        # This is a simplified extraction - in practice, we'd want more sophisticated parsing
        clips = {
            "mellow": [],
            "exciting": [],
            "cinematic": []
        }
        
        # Look for timestamp patterns like "0:15-0:30" or "15-30 seconds"
        import re
        timestamp_pattern = r'(\d+):(\d+)-(\d+):(\d+)|(\d+)-(\d+)\s*seconds?'
        matches = re.findall(timestamp_pattern, text.lower())
        
        for match in matches:
            if match[0] and match[1]:  # Format: mm:ss-mm:ss
                start = int(match[0]) * 60 + int(match[1])
                end = int(match[2]) * 60 + int(match[3])
            elif match[4] and match[5]:  # Format: ss-ss seconds
                start = int(match[4])
                end = int(match[5])
            else:
                continue
            
            clip_info = {"start": start, "end": end, "reason": "LLM suggested"}
            
            # Simple theme assignment based on context
            context = text[max(0, text.find(str(match)) - 100):text.find(str(match)) + 100].lower()
            if "mellow" in context or "calm" in context:
                clips["mellow"].append(clip_info)
            elif "exciting" in context or "dynamic" in context:
                clips["exciting"].append(clip_info)
            else:
                clips["cinematic"].append(clip_info)
        
        return clips
    
    def _extract_timestamps(self, text: str, marker: str) -> List[float]:
        """Extract timestamp list from text."""
        section = self._extract_section(text, marker, "Narrative Structure")
        
        # Extract timestamps using regex
        import re
        timestamp_pattern = r'(\d+):(\d+)|(\d+)\s*seconds?'
        matches = re.findall(timestamp_pattern, section)
        
        timestamps = []
        for match in matches:
            if match[0] and match[1]:  # Format: mm:ss
                timestamp = int(match[0]) * 60 + int(match[1])
            elif match[2]:  # Format: ss seconds
                timestamp = int(match[2])
            else:
                continue
            
            timestamps.append(float(timestamp))
        
        return sorted(timestamps)
    
    def analyze_audio_visual_unified(self, audio_path: str, video_paths: List[str], 
                                   use_dev_versions: bool = True, use_cache: bool = True) -> Optional[AudioVisualSyncPlan]:
        """
        Enhanced unified audio-visual analysis using GPT-4o with full audio + strategic keyframes
        
        Args:
            audio_path: Path to music file
            video_paths: List of video file paths
            use_dev_versions: Use development versions for faster processing
            use_cache: Whether to use keyframe caching
            
        Returns:
            AudioVisualSyncPlan object or None if analysis fails
        """
        if not self.client:
            print(f"   ❌ Cannot perform audio-visual analysis - OpenAI client not available")
            return None
        
        print(f"🎵🎬 Starting unified audio-visual analysis...")
        print(f"   Audio: {Path(audio_path).name}")
        print(f"   Videos: {len(video_paths)} files")
        
        start_time = time.time()
        
        try:
            # Step 1: Analyze audio for beats and features
            print(f"   🎵 Analyzing audio features...")
            audio_features = self.audio_analyzer.analyze_audio_file(audio_path)
            if not audio_features:
                print(f"   ❌ Audio analysis failed")
                return None
            
            # Step 2: Downsample audio for LLM input
            print(f"   🔄 Downsampling audio for LLM...")
            compressed_audio_path = self._downsample_audio_for_llm(audio_path)
            if not compressed_audio_path:
                print(f"   ❌ Audio downsampling failed")
                return None
            
            # Step 3: Extract strategic keyframes from videos
            print(f"   📸 Extracting strategic keyframes...")
            keyframes_data, keyframe_timestamps = self._extract_strategic_keyframes(
                video_paths, audio_features, use_dev_versions, use_cache=use_cache
            )
            if not keyframes_data:
                print(f"   ❌ Keyframe extraction failed")
                return None
            
            # Step 4: Send to GPT-4o for unified analysis
            print(f"   🤖 Performing unified LLM analysis...")
            sync_plan = self._analyze_audio_visual_with_llm(
                compressed_audio_path, keyframes_data, keyframe_timestamps, 
                audio_features, video_paths
            )
            
            processing_time = time.time() - start_time
            
            if sync_plan:
                print(f"   ✅ Audio-visual analysis complete ({processing_time:.2f}s)")
                print(f"      Duration: {sync_plan.music_duration:.1f}s")
                print(f"      Transitions: {len(sync_plan.transition_points)}")
                print(f"      Confidence: {sync_plan.sync_confidence:.2f}")
                
                # Log the analysis if logger is available
                if self.llm_logger:
                    self._log_analysis_results(
                        audio_path, video_paths, keyframe_timestamps, 
                        processing_time, sync_plan
                    )
                
                return sync_plan
            else:
                print(f"   ❌ Unified analysis failed")
                return None
                
        except Exception as e:
            logger.error(f"Audio-visual analysis failed: {e}")
            print(f"   ❌ Error in unified analysis: {e}")
            return None
        finally:
            # Cleanup compressed audio file
            if 'compressed_audio_path' in locals() and os.path.exists(compressed_audio_path):
                try:
                    os.remove(compressed_audio_path)
                except:
                    pass
    
    def _downsample_audio_for_llm(self, audio_path: str, target_size_mb: float = 1.0) -> Optional[str]:
        """
        Downsample audio for LLM input (~1MB target)
        
        Args:
            audio_path: Original audio file path
            target_size_mb: Target file size in MB
            
        Returns:
            Path to compressed audio file or None if failed
        """
        try:
            # Load audio with librosa
            y, sr = librosa.load(audio_path, sr=22050)  # Downsample to 22kHz
            
            # Convert to mono if stereo
            if len(y.shape) > 1:
                y = librosa.to_mono(y)
            
            # Create temporary compressed file
            compressed_path = f"temp_compressed_audio_{int(time.time())}.wav"
            
            # Save compressed audio
            import soundfile as sf
            sf.write(compressed_path, y, sr)
            
            # Check file size
            file_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
            
            print(f"      Compressed: {file_size_mb:.2f}MB (target: {target_size_mb}MB)")
            
            if file_size_mb <= target_size_mb * 1.5:  # Allow 50% tolerance
                return compressed_path
            else:
                # Further compression needed - reduce sample rate more
                y_reduced, sr_reduced = librosa.load(audio_path, sr=16000)
                if len(y_reduced.shape) > 1:
                    y_reduced = librosa.to_mono(y_reduced)
                
                sf.write(compressed_path, y_reduced, sr_reduced)
                file_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
                print(f"      Further compressed: {file_size_mb:.2f}MB")
                
                return compressed_path
                
        except Exception as e:
            logger.error(f"Audio downsampling failed: {e}")
            return None
    
    def _extract_strategic_keyframes(self, video_paths: List[str], audio_features: AudioFeatures,
                                   use_dev_versions: bool = True, target_frames: int = None, 
                                   use_cache: bool = True) -> tuple:
        """
        Extract strategic keyframes aligned with beats and energy peaks
        Dynamic keyframe count: 1 frame every 2 seconds of video duration
        
        Args:
            video_paths: List of video file paths
            audio_features: Audio analysis results
            use_dev_versions: Use development versions
            target_frames: Ignored - calculated dynamically based on video duration
            use_cache: Whether to use keyframe caching
            
        Returns:
            Tuple of (keyframes_data, keyframe_timestamps)
        """
        try:
            from src.utils.cache_manager import CacheManager
            import cv2
            
            all_keyframes = []
            all_timestamps = []
            cache_manager = CacheManager() if use_cache else None
            
            print(f"      Using dynamic keyframe calculation (1 frame per 2 seconds)")
            
            for video_path in video_paths:
                # Determine which video file to use
                if use_dev_versions:
                    dev_path = self._get_dev_version_path(video_path)
                    analysis_path = dev_path if os.path.exists(dev_path) else video_path
                else:
                    analysis_path = video_path
                
                # Get video duration to calculate dynamic keyframe count
                try:
                    clip = VideoFileClip(analysis_path)
                    video_duration = clip.duration
                    clip.close()
                except Exception as e:
                    logger.warning(f"Failed to get duration for {Path(analysis_path).name}: {e}")
                    continue
                
                # Calculate dynamic keyframe count: 1 frame every 2 seconds
                frames_per_video = max(1, int(video_duration / 2))
                print(f"      {Path(analysis_path).name}: {video_duration:.1f}s → {frames_per_video} frames")
                
                # Try to load keyframes from cache first
                cached_keyframes = None
                if cache_manager and use_cache:
                    if cache_manager.has_keyframes_cache(analysis_path, frames_per_video):
                        cached_keyframes = cache_manager.get_cached_keyframes(analysis_path, frames_per_video)
                        print(f"      ✅ Using cached keyframes for {Path(analysis_path).name}")
                
                if cached_keyframes:
                    # Use cached keyframes - convert to base64
                    for i, frame in enumerate(cached_keyframes):
                        try:
                            # Convert cached frame to base64
                            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            frame_base64 = base64.b64encode(buffer).decode('utf-8')
                            
                            all_keyframes.append(frame_base64)
                            # Use evenly distributed timestamps for cached frames
                            timestamp = i * (audio_features.duration / len(cached_keyframes))
                            all_timestamps.append(timestamp)
                            
                        except Exception as e:
                            logger.warning(f"Failed to process cached frame {i} from {Path(analysis_path).name}: {e}")
                            continue
                else:
                    # Extract keyframes fresh and cache them
                    print(f"      🔄 Extracting fresh keyframes for {Path(analysis_path).name}")
                    try:
                        clip = VideoFileClip(analysis_path)
                        video_duration = clip.duration
                        
                        # Calculate evenly distributed timestamps for this video
                        frame_times = [i * video_duration / frames_per_video for i in range(frames_per_video)]
                        
                        # Store frames for caching
                        frames_to_cache = []
                        
                        for time_point in frame_times:
                            try:
                                # Extract frame
                                frame = clip.get_frame(time_point)
                                
                                # Convert to base64 for LLM
                                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                                _, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                                
                                all_keyframes.append(frame_base64)
                                all_timestamps.append(time_point)
                                
                                # Store frame for caching (BGR format for cv2.imwrite)
                                frames_to_cache.append(frame_bgr)
                                
                            except Exception as e:
                                logger.warning(f"Failed to extract frame at {time_point}s from {Path(analysis_path).name}: {e}")
                                continue
                        
                        clip.close()
                        
                        # Cache the extracted keyframes
                        if cache_manager and frames_to_cache:
                            cache_manager.cache_keyframes(analysis_path, frames_to_cache, len(frames_to_cache))
                            print(f"      💾 Cached {len(frames_to_cache)} keyframes for {Path(analysis_path).name}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to process video {Path(video_path).name}: {e}")
                        continue
            
            print(f"      Extracted {len(all_keyframes)} strategic keyframes")
            
            if len(all_keyframes) >= 10:  # Need minimum keyframes for analysis
                return all_keyframes, all_timestamps
            else:
                print(f"      ⚠️  Only extracted {len(all_keyframes)} keyframes, need at least 10")
                return None, None
                
        except Exception as e:
            logger.error(f"Strategic keyframe extraction failed: {e}")
            return None, None
    
    def _calculate_strategic_timestamps(self, audio_features: AudioFeatures, 
                                      target_count: int) -> List[float]:
        """
        Calculate strategic timestamps based on audio analysis
        
        Args:
            audio_features: Audio analysis results
            target_count: Target number of timestamps
            
        Returns:
            List of strategic timestamps
        """
        strategic_times = []
        
        # Add beat-aligned timestamps
        beat_times = audio_features.beats[:target_count // 2]  # Use half for beats
        strategic_times.extend(beat_times)
        
        # Add energy peak timestamps
        energy_profile = audio_features.energy_profile
        if energy_profile:
            # Find energy peaks
            energy_array = np.array(energy_profile)
            peak_indices = []
            
            # Simple peak detection
            for i in range(1, len(energy_array) - 1):
                if energy_array[i] > energy_array[i-1] and energy_array[i] > energy_array[i+1]:
                    peak_indices.append(i)
            
            # Convert peak indices to timestamps
            window_size = audio_features.duration / len(energy_profile)
            energy_peak_times = [i * window_size for i in peak_indices]
            
            # Add top energy peaks
            energy_peaks_sorted = sorted(energy_peak_times, 
                                       key=lambda t: energy_profile[min(int(t / window_size), len(energy_profile) - 1)], 
                                       reverse=True)
            
            strategic_times.extend(energy_peaks_sorted[:target_count // 4])
        
        # Add evenly distributed timestamps to ensure coverage
        even_times = [i * audio_features.duration / (target_count // 4) 
                     for i in range(target_count // 4)]
        strategic_times.extend(even_times)
        
        # Remove duplicates and sort
        strategic_times = sorted(list(set(strategic_times)))
        
        # Limit to target count
        return strategic_times[:target_count]
    
    def _analyze_audio_visual_with_llm(self, compressed_audio_path: str, keyframes_data: List[str],
                                     keyframe_timestamps: List[float], audio_features: AudioFeatures,
                                     video_paths: List[str]) -> Optional[AudioVisualSyncPlan]:
        """
        Send audio + keyframes to GPT-4o for unified analysis
        
        Args:
            compressed_audio_path: Path to compressed audio file
            keyframes_data: List of base64-encoded keyframes
            keyframe_timestamps: Corresponding timestamps
            audio_features: Audio analysis results
            video_paths: Original video paths
            
        Returns:
            AudioVisualSyncPlan or None if failed
        """
        try:
            # Create comprehensive prompt
            prompt = self._create_audio_visual_prompt(
                compressed_audio_path, keyframe_timestamps, audio_features, video_paths
            )
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert video editor and music producer. Analyze audio and video together to create perfect synchronization plans for music-driven video editing. Focus on beat alignment, energy matching, and narrative flow."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Add audio analysis as structured text (OpenAI API doesn't support direct audio in chat completions)
            audio_description = f"""
**AUDIO ANALYSIS:**
- Duration: {audio_features.duration:.1f} seconds
- Tempo: {audio_features.tempo:.1f} BPM
- Beat timestamps (first 20): {[f'{b:.1f}s' for b in audio_features.beats[:20]]}
- Energy profile (first 10 windows): {[f'{e:.3f}' for e in audio_features.energy_profile[:10]]}
- Total beats detected: {len(audio_features.beats)}
- Average beat interval: {audio_features.average_beat_interval:.2f}s

**BEAT SYNCHRONIZATION POINTS:**
Key beats for video transitions: {[f'{b:.1f}s' for b in audio_features.beats[::4][:12]]}
"""
            
            messages[1]["content"].append({
                "type": "text",
                "text": audio_description
            })
            
            # Add keyframes with timestamps
            for i, (frame_data, timestamp) in enumerate(zip(keyframes_data, keyframe_timestamps)):
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame_data}",
                        "detail": "low"
                    }
                })
                # Add timestamp context
                if i == 0 or i % 5 == 0:  # Add timestamp info every 5 frames
                    messages[1]["content"].append({
                        "type": "text",
                        "text": f"[Frame at {timestamp:.1f}s]"
                    })
            
            # Call GPT-4o API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=2000,
                temperature=0.2
            )
            
            # Parse response into sync plan
            response_text = response.choices[0].message.content
            sync_plan = self._parse_audio_visual_response(response_text, audio_features)
            
            return sync_plan
            
        except Exception as e:
            logger.error(f"Audio-visual LLM analysis failed: {e}")
            return None
    
    def _create_audio_visual_prompt(self, audio_path: str, keyframe_timestamps: List[float],
                                  audio_features: AudioFeatures, video_paths: List[str]) -> str:
        """Create comprehensive prompt for audio-visual analysis"""
        
        video_names = [Path(p).name for p in video_paths]
        
        prompt = f"""
Analyze this music track and video keyframes together to create a perfect synchronization plan:

**MUSIC ANALYSIS:**
- Duration: {audio_features.duration:.1f} seconds
- Tempo: {audio_features.tempo:.1f} BPM
- Beats detected: {len(audio_features.beats)}
- Energy profile: {len(audio_features.energy_profile)} energy points

**VIDEO CONTENT:**
- Source videos: {', '.join(video_names)}
- Keyframes: {len(keyframe_timestamps)} strategic frames
- Timestamps: {', '.join([f'{t:.1f}s' for t in keyframe_timestamps[:10]])}...

**TASK: Create a comprehensive synchronization plan**

Please analyze the audio and video content together and provide:

1. **Music Duration**: Use the FULL music duration ({audio_features.duration:.1f}s) - no artificial limits
2. **Video Segments**: Divide the music into 4-6 segments based on energy/mood changes
3. **Transition Points**: Specify exact timestamps for video cuts aligned with musical beats
4. **Energy Mapping**: Map music sections to appropriate visual styles from the keyframes
5. **Narrative Flow**: Describe the overall story arc that connects audio and visual elements
6. **Sync Confidence**: Rate your confidence in this sync plan (0.0-1.0)

Focus on creating beat-precise transitions that match the music's energy and rhythm.
Ensure the video plan covers the COMPLETE music duration, not just a portion.

Return your analysis in a structured format with specific timestamps and clear reasoning.
"""
        
        return prompt
    
    def _parse_audio_visual_response(self, response_text: str, audio_features: AudioFeatures) -> Optional[AudioVisualSyncPlan]:
        """Parse LLM response into AudioVisualSyncPlan"""
        try:
            # Extract key information from response
            music_duration = audio_features.duration
            
            # Extract transition points from response
            transition_points = self._extract_timestamps_from_response(response_text)
            
            # If no transitions found, use beat-based transitions
            if not transition_points:
                # Use every 4th beat for transitions
                beat_transitions = audio_features.beats[::4]
                transition_points = beat_transitions[:8]  # Limit to 8 transitions
            
            # Extract video segments
            video_segments = self._extract_video_segments(response_text, music_duration)
            
            # Extract energy mapping
            energy_mapping = self._extract_energy_mapping(response_text)
            
            # Extract confidence score
            sync_confidence = self._extract_confidence_score(response_text)
            
            # Extract narrative flow
            narrative_flow = self._extract_narrative_flow(response_text)
            
            # Create sync plan
            sync_plan = AudioVisualSyncPlan(
                music_duration=music_duration,
                video_segments=video_segments,
                transition_points=transition_points,
                energy_mapping=energy_mapping,
                sync_confidence=sync_confidence,
                narrative_flow=narrative_flow,
                llm_reasoning=response_text[:1000]  # Store first 1000 chars of reasoning
            )
            
            return sync_plan
            
        except Exception as e:
            logger.error(f"Error parsing audio-visual response: {e}")
            
            # Create fallback sync plan
            return AudioVisualSyncPlan(
                music_duration=audio_features.duration,
                video_segments=[{
                    'start_time': 0,
                    'end_time': audio_features.duration,
                    'energy_level': 'medium',
                    'visual_style': 'mixed'
                }],
                transition_points=audio_features.beats[::4][:8],
                energy_mapping={'full_track': 'dynamic_mixed'},
                sync_confidence=0.5,
                narrative_flow="Fallback sync plan due to parsing error",
                llm_reasoning="LLM response parsing failed, using algorithmic fallback"
            )
    
    def _extract_timestamps_from_response(self, text: str) -> List[float]:
        """Extract transition timestamps from LLM response"""
        import re
        
        # Look for various timestamp formats
        patterns = [
            r'(\d+):(\d+)',  # mm:ss format
            r'(\d+\.?\d*)\s*seconds?',  # X.X seconds format
            r'at\s+(\d+\.?\d*)',  # "at X" format
            r'(\d+\.?\d*)s',  # Xs format
        ]
        
        timestamps = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) == 2:
                        # mm:ss format
                        minutes, seconds = match
                        timestamp = int(minutes) * 60 + int(seconds)
                    else:
                        # Single number format
                        timestamp = float(match)
                    
                    if 0 <= timestamp <= 300:  # Reasonable range
                        timestamps.append(timestamp)
                except:
                    continue
        
        # Remove duplicates and sort
        timestamps = sorted(list(set(timestamps)))
        return timestamps[:12]  # Limit to 12 transitions
    
    def _extract_video_segments(self, text: str, duration: float) -> List[Dict]:
        """Extract video segments from LLM response"""
        # Simple segment extraction - divide into 4-6 segments
        num_segments = min(6, max(4, int(duration / 15)))  # 15s per segment average
        segment_duration = duration / num_segments
        
        segments = []
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, duration)
            
            # Try to extract energy level from text for this segment
            energy_level = "medium"  # Default
            if "high energy" in text.lower() or "intense" in text.lower():
                energy_level = "high"
            elif "calm" in text.lower() or "peaceful" in text.lower():
                energy_level = "low"
            
            segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'energy_level': energy_level,
                'visual_style': 'dynamic' if energy_level == 'high' else 'smooth'
            })
        
        return segments
    
    def _extract_energy_mapping(self, text: str) -> Dict[str, str]:
        """Extract energy mapping from LLM response"""
        # Simple energy mapping extraction
        mapping = {}
        
        if "intro" in text.lower():
            mapping["intro"] = "establishing_shots"
        if "buildup" in text.lower() or "build" in text.lower():
            mapping["buildup"] = "dynamic_movement"
        if "climax" in text.lower() or "peak" in text.lower():
            mapping["climax"] = "fast_cuts"
        if "outro" in text.lower() or "ending" in text.lower():
            mapping["outro"] = "wide_shots"
        
        # Default mapping if nothing found
        if not mapping:
            mapping = {
                "full_track": "mixed_dynamic"
            }
        
        return mapping
    
    def _extract_confidence_score(self, text: str) -> float:
        """Extract confidence score from LLM response"""
        import re
        
        # Look for confidence patterns
        patterns = [
            r'confidence[:\s]+(\d+\.?\d*)%',
            r'confidence[:\s]+(\d+\.?\d*)/10',
            r'confidence[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)%\s+confidence',
            r'rate[:\s]+(\d+\.?\d*)/10',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    score = float(matches[0])
                    # Normalize to 0-1 range
                    if score > 1:
                        score = score / 100 if score <= 100 else score / 10
                    return min(1.0, max(0.0, score))
                except:
                    continue
        
        # Default confidence
        return 0.75
    
    def _extract_narrative_flow(self, text: str) -> str:
        """Extract narrative flow description from LLM response"""
        # Look for narrative/story sections
        markers = ["narrative", "story", "flow", "arc", "structure"]
        
        for marker in markers:
            start_idx = text.lower().find(marker)
            if start_idx != -1:
                # Extract next 200 characters
                end_idx = min(start_idx + 300, len(text))
                section = text[start_idx:end_idx].strip()
                
                # Clean up the section
                sentences = section.split('.')
                if len(sentences) > 1:
                    return '. '.join(sentences[:2]) + '.'
                else:
                    return section
        
        # Default narrative flow
        return "Progressive energy build with beat-synchronized transitions"
    
    def _log_analysis_results(self, audio_path: str, video_paths: List[str], 
                            keyframe_timestamps: List[float], processing_time: float,
                            sync_plan: AudioVisualSyncPlan) -> None:
        """Log analysis results using LLM logger"""
        if not self.llm_logger:
            return
        
        try:
            # Create mock response for logging (since we don't have the actual response object)
            mock_response = type('MockResponse', (), {
                'id': f'audio_visual_{int(time.time())}',
                'choices': [type('Choice', (), {
                    'message': type('Message', (), {'content': sync_plan.llm_reasoning}),
                    'finish_reason': 'stop'
                })],
                'usage': type('Usage', (), {
                    'prompt_tokens': len(keyframe_timestamps) * 100,  # Estimate
                    'completion_tokens': len(sync_plan.llm_reasoning.split()),
                    'total_tokens': len(keyframe_timestamps) * 100 + len(sync_plan.llm_reasoning.split())
                })
            })
            
            # Log the analysis
            request_id = self.llm_logger.log_audio_visual_analysis(
                request_data={
                    'model': 'gpt-4o',
                    'audio_duration': sync_plan.music_duration
                },
                response=mock_response,
                audio_path=audio_path,
                video_path=video_paths[0] if video_paths else "multiple_videos",
                keyframe_timestamps=keyframe_timestamps,
                processing_time=processing_time
            )
            
            # Log the sync plan
            self.llm_logger.log_sync_plan_generation(
                request_id=request_id,
                sync_plan=sync_plan,
                confidence=sync_plan.sync_confidence,
                llm_reasoning=sync_plan.llm_reasoning
            )
            
        except Exception as e:
            logger.warning(f"Failed to log analysis results: {e}")
    
    def analyze_multiple_videos(self, video_paths: List[str], use_dev_versions: bool = True) -> Dict[str, VideoAnalysis]:
        """Analyze multiple videos and return results."""
        print(f"🎬 Analyzing {len(video_paths)} videos with LLM...")
        
        results = {}
        
        for i, video_path in enumerate(video_paths, 1):
            print(f"\n[{i}/{len(video_paths)}] Processing {Path(video_path).name}")
            
            analysis = self.analyze_video(video_path, use_dev_versions)
            if analysis:
                results[video_path] = analysis
            else:
                print(f"   ⚠️  Skipping {Path(video_path).name} due to analysis failure")
        
        print(f"\n✅ Completed analysis of {len(results)}/{len(video_paths)} videos")
        return results
    
    def save_analysis_cache(self, analyses: Dict[str, VideoAnalysis], cache_file: str = "video_analyses.json"):
        """Save analysis results to cache file."""
        try:
            cache_data = {}
            for video_path, analysis in analyses.items():
                cache_data[video_path] = {
                    'file_path': analysis.file_path,
                    'duration': analysis.duration,
                    'content_summary': analysis.content_summary,
                    'shot_types': analysis.shot_types,
                    'motion_characteristics': analysis.motion_characteristics,
                    'visual_style': analysis.visual_style,
                    'mood_energy': analysis.mood_energy,
                    'story_potential': analysis.story_potential,
                    'best_clips_for_themes': analysis.best_clips_for_themes,
                    'transition_points': analysis.transition_points,
                    'narrative_structure': analysis.narrative_structure,
                    'technical_quality': analysis.technical_quality
                }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"   💾 Analysis cache saved to {cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to save analysis cache: {e}")


# Gemini Video Intelligence data structures
@dataclass
class MusicSyncSegment:
    """Video segment optimized for music synchronization"""
    start_time: float
    end_time: float
    energy_level: str        # "high", "medium", "low"
    music_compatibility: str # "buildup", "drop", "calm", "climax"
    visual_rhythm: str       # "fast", "moderate", "slow"
    recommended_bpm: float   # Optimal BPM for this segment
    confidence: float        # Analysis confidence

@dataclass
class GeminiVideoAnalysis:
    """Comprehensive video analysis from Gemini API optimized for music synchronization"""
    file_path: str
    duration: float
    music_sync_segments: List[MusicSyncSegment]  # Segments optimized for music
    beat_aligned_cuts: List[float]               # Optimal cut points for beats
    energy_profile: Dict[str, List[float]]       # High/medium/low energy timestamps
    narrative_flow: str                          # Story arc description
    sync_confidence: float                       # Confidence in music matching
    gemini_reasoning: str                        # Natural language analysis
    processing_time: float = 0.0
    api_cost: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'file_path': self.file_path,
            'duration': self.duration,
            'music_sync_segments': [{'start': s.start_time, 'end': s.end_time, 
                                   'energy': s.energy_level, 'compatibility': s.music_compatibility,
                                   'rhythm': s.visual_rhythm, 'bpm': s.recommended_bpm,
                                   'confidence': s.confidence} for s in self.music_sync_segments],
            'beat_aligned_cuts': self.beat_aligned_cuts,
            'energy_profile': self.energy_profile,
            'narrative_flow': self.narrative_flow,
            'sync_confidence': self.sync_confidence,
            'gemini_reasoning': self.gemini_reasoning,
            'processing_time': self.processing_time,
            'api_cost': self.api_cost
        }


class GeminiVideoAnalyzer:
    """Analyzes videos using Gemini API for music-driven video generation."""
    
    def __init__(self):
        """Initialize Gemini video analyzer."""
        self.model = None
        
        if not GEMINI_AVAILABLE:
            print("   ⚠️  Gemini API library not available")
            return
        
        try:
            # Configure Gemini API
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("   ⚠️  GEMINI_API_KEY not found in environment variables")
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            print("   ✅ Gemini API initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            print(f"   ❌ Gemini initialization failed: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available and configured."""
        return GEMINI_AVAILABLE and self.model is not None
    
    def analyze_video_comprehensive(self, video_path: str, use_cache: bool = True) -> Optional[GeminiVideoAnalysis]:
        """
        Analyze a video file using Gemini API for comprehensive understanding.
        
        Args:
            video_path: Path to video file
            use_cache: Whether to use cached results
            
        Returns:
            GeminiVideoAnalysis object or None if analysis fails
        """
        if not self.is_available():
            print(f"   ❌ Cannot analyze {Path(video_path).name} - Gemini API not available")
            return None
        
        print(f"   🌟 Analyzing video with Gemini API: {Path(video_path).name}")
        
        start_time = time.time()
        
        try:
            # Step 1: Check cache first
            if use_cache:
                cached_analysis = self._load_cached_analysis(video_path)
                if cached_analysis:
                    print(f"      ✅ Using cached Gemini analysis")
                    return cached_analysis
            
            # Step 2: Upload video to Gemini
            print(f"      📤 Uploading video to Gemini...")
            video_file = self._upload_video_to_gemini(video_path)
            if not video_file:
                print(f"      ❌ Failed to upload video to Gemini")
                return None
            
            # Step 3: Request comprehensive analysis
            print(f"      🔍 Requesting Gemini video analysis...")
            analysis_result = self._request_video_analysis(video_file, video_path)
            
            processing_time = time.time() - start_time
            
            if analysis_result:
                analysis_result.processing_time = processing_time
                print(f"      ✅ Gemini analysis complete ({processing_time:.2f}s)")
                print(f"         Music sync segments: {len(analysis_result.music_sync_segments)}")
                print(f"         Beat aligned cuts: {len(analysis_result.beat_aligned_cuts)}")
                print(f"         Sync confidence: {analysis_result.sync_confidence:.2f}")
                
                # Cache the results
                if use_cache:
                    self._cache_analysis(video_path, analysis_result)
                
                return analysis_result
            else:
                print(f"      ❌ Gemini analysis failed")
                return None
                
        except Exception as e:
            logger.error(f"Gemini analysis failed for {video_path}: {e}")
            print(f"      ❌ Error in Gemini analysis: {e}")
            return None
    
    def analyze_for_music_sync(self, video_path: str, audio_features: AudioFeatures, use_cache: bool = True) -> Optional[GeminiVideoAnalysis]:
        """
        Analyze a video specifically for music synchronization using Gemini API.
        
        Args:
            video_path: Path to video file
            audio_features: Audio analysis results for music-aware prompting
            use_cache: Whether to use cached results
            
        Returns:
            GeminiVideoAnalysis object optimized for music sync or None if analysis fails
        """
        if not self.is_available():
            print(f"   ❌ Cannot analyze {Path(video_path).name} - Gemini API not available")
            return None
        
        print(f"   🎵 Analyzing video for music sync with Gemini API: {Path(video_path).name}")
        print(f"      Music: {audio_features.tempo:.1f} BPM, {audio_features.duration:.1f}s")
        
        start_time = time.time()
        
        try:
            # Step 1: Check cache first (music-specific cache)
            if use_cache:
                cached_analysis = self._load_cached_music_analysis(video_path, audio_features)
                if cached_analysis:
                    print(f"      ✅ Using cached music-sync analysis")
                    return cached_analysis
            
            # Step 2: Upload video to Gemini
            print(f"      📤 Uploading video to Gemini...")
            video_file = self._upload_video_to_gemini(video_path)
            if not video_file:
                print(f"      ❌ Failed to upload video to Gemini")
                return None
            
            # Step 3: Request music-aware analysis
            print(f"      🎵 Requesting music-aware analysis...")
            analysis_result = self._request_music_sync_analysis(video_file, video_path, audio_features)
            
            processing_time = time.time() - start_time
            
            if analysis_result:
                analysis_result.processing_time = processing_time
                print(f"      ✅ Music-sync analysis complete ({processing_time:.2f}s)")
                print(f"         Recommended BPM matches: {len([s for s in analysis_result.music_sync_segments if abs(s.recommended_bpm - audio_features.tempo) < 20])}")
                print(f"         Beat alignment confidence: {analysis_result.sync_confidence:.2f}")
                
                # Cache the results
                if use_cache:
                    self._cache_music_analysis(video_path, audio_features, analysis_result)
                
                return analysis_result
            else:
                print(f"      ❌ Music-sync analysis failed")
                return None
                
        except Exception as e:
            logger.error(f"Gemini music-sync analysis failed for {video_path}: {e}")
            print(f"      ❌ Error in music-sync analysis: {e}")
            return None
    
    def _upload_video_to_gemini(self, video_path: str) -> Optional[Any]:
        """Upload video file to Gemini API."""
        try:
            # Check file size
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            
            if file_size_mb <= 20:  # Use inline upload for small files
                print(f"         Using inline upload for {file_size_mb:.1f}MB file")
                return self._upload_inline(video_path)
            else:
                print(f"         Using File API for {file_size_mb:.1f}MB file")
                return self._upload_with_file_api(video_path)
                
        except Exception as e:
            logger.error(f"Failed to upload video to Gemini: {e}")
            return None
    
    def _upload_inline(self, video_path: str) -> Optional[Any]:
        """Upload video inline for small files."""
        try:
            # Upload file using the File API
            print(f"         Uploading {Path(video_path).name} to Gemini...")
            uploaded_file = genai.upload_file(path=video_path)
            
            print(f"         Upload complete: {uploaded_file.name}")
            
            # Wait for file to be processed
            print(f"         Waiting for file to be processed...")
            import time
            max_wait_time = 60  # Maximum wait time in seconds
            wait_interval = 2   # Check every 2 seconds
            elapsed_time = 0
            
            while uploaded_file.state.name == "PROCESSING" and elapsed_time < max_wait_time:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                uploaded_file = genai.get_file(uploaded_file.name)
                print(f"         File state: {uploaded_file.state.name} ({elapsed_time}s)")
            
            if uploaded_file.state.name == "ACTIVE":
                print(f"         File ready for analysis: {uploaded_file.state.name}")
                return uploaded_file
            else:
                print(f"         File processing failed or timed out: {uploaded_file.state.name}")
                return None
            
        except Exception as e:
            print(f"Failed to upload video inline: {e}")
            logger.error(f"Failed to upload video inline: {e}")
            return None
    
    def _upload_with_file_api(self, video_path: str) -> Optional[Any]:
        """Upload video using Gemini File API for larger files."""
        try:
            # Upload using File API
            uploaded_file = self.client.files.upload(file=video_path)
            
            # Create file data part
            video_part = types.Part(
                file_data=types.FileData(
                    file_uri=uploaded_file.uri,
                    mime_type=uploaded_file.mime_type
                )
            )
            
            return video_part
            
        except Exception as e:
            logger.error(f"Failed to upload video with File API: {e}")
            return None
    
    def _request_video_analysis(self, video_file: Any, video_path: str) -> Optional[GeminiVideoAnalysis]:
        """Request comprehensive video analysis from Gemini API."""
        try:
            # Create analysis prompt
            prompt = self._create_comprehensive_analysis_prompt(video_path)
            
            print(f"         Sending analysis request to Gemini...")
            
            # Request analysis using the model's generate_content method
            response = self.model.generate_content([video_file, prompt])
            
            print(f"         Received response from Gemini")
            
            # Parse response
            return self._parse_comprehensive_response(response.text, video_path)
            
        except Exception as e:
            print(f"Failed to request video analysis: {e}")
            logger.error(f"Failed to request video analysis: {e}")
            return None
    
    def _request_music_sync_analysis(self, video_part: Any, video_path: str, audio_features: AudioFeatures) -> Optional[GeminiVideoAnalysis]:
        """Request music-aware video analysis from Gemini API."""
        try:
            # Create music-aware analysis prompt
            prompt = self._create_music_sync_prompt(video_path, audio_features)
            
            # Create content with video and prompt
            content = types.Content(
                parts=[
                    video_part,
                    types.Part(text=prompt)
                ]
            )
            
            # Request analysis
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[content]
            )
            
            # Parse response
            return self._parse_music_sync_response(response.text, video_path, audio_features)
            
        except Exception as e:
            logger.error(f"Failed to request music-sync analysis: {e}")
            return None
    
    def _create_comprehensive_analysis_prompt(self, video_path: str) -> str:
        """Create comprehensive analysis prompt for Gemini."""
        filename = Path(video_path).name
        
        prompt = f"""
Analyze this video comprehensively for music-driven video editing:

**Video File:** {filename}

**Analysis Required:**

1. **Video Segments**: Divide the video into 4-8 segments based on visual content, energy, and natural transitions. For each segment provide:
   - Start and end timestamps (in seconds)
   - Energy level (high/medium/low)
   - Visual rhythm (fast/moderate/slow)
   - Music compatibility (buildup/drop/calm/climax)
   - Recommended BPM range for this segment

2. **Beat-Aligned Cut Points**: Identify 8-12 optimal timestamps where video cuts would work naturally with musical beats. Consider:
   - Natural scene transitions
   - Movement changes
   - Visual rhythm shifts
   - Action peaks or pauses

3. **Energy Profile**: Analyze the video's energy throughout its duration:
   - High energy timestamps (action, fast movement, dynamic scenes)
   - Medium energy timestamps (moderate activity, transitions)
   - Low energy timestamps (calm, peaceful, establishing shots)

4. **Narrative Flow**: Describe the overall story arc and how it could complement music structure:
   - Beginning/intro potential
   - Build-up sections
   - Climax moments
   - Resolution/outro potential

5. **Music Synchronization Confidence**: Rate how well this video would synchronize with music (0.0-1.0) and explain why.

**Output Format:**
Please structure your response clearly with specific timestamps and actionable insights for music-video synchronization.

Focus on creating precise, beat-aligned recommendations that will eliminate repetition and create smooth, music-driven video flow.
"""
        return prompt
    
    def _create_music_sync_prompt(self, video_path: str, audio_features: AudioFeatures) -> str:
        """Create music-aware analysis prompt for Gemini."""
        filename = Path(video_path).name
        
        prompt = f"""
Analyze this video specifically for synchronization with the provided music:

**Video File:** {filename}
**Music Details:**
- Duration: {audio_features.duration:.1f} seconds
- Tempo: {audio_features.tempo:.1f} BPM
- Beat count: {len(audio_features.beats)} beats
- Average beat interval: {audio_features.average_beat_interval:.2f}s

**Key Beat Timestamps:** {[f'{b:.1f}s' for b in audio_features.beats[:20]]}

**Music-Aware Analysis Required:**

1. **Music Sync Segments**: Divide the video into segments that match the music's {audio_features.tempo:.1f} BPM tempo:
   - Segments with fast visual rhythm matching high BPM
   - Segments with slow visual rhythm for melodic parts
   - Energy levels that complement the music's energy profile

2. **Beat-Aligned Cuts**: Identify cut points that align with the provided beat timestamps:
   - Natural transitions at beat markers
   - Visual rhythm changes that match musical beats
   - Action peaks that coincide with strong beats

3. **Energy Matching**: Match video energy to music energy:
   - High energy video segments for intense musical parts
   - Calm video segments for softer musical sections
   - Dynamic segments for build-ups and drops

4. **Visual Rhythm Analysis**: Analyze how the video's visual pace complements {audio_features.tempo:.1f} BPM:
   - Fast cuts and movement for uptempo sections
   - Slower, flowing shots for melodic parts
   - Rhythmic patterns that enhance musical rhythm

5. **BPM Recommendations**: For each video segment, recommend optimal BPM ranges that would work best.

**Goal:** Create perfect synchronization between this video and the {audio_features.tempo:.1f} BPM music track.

Provide specific timestamps, energy levels, and synchronization confidence scores.
"""
        return prompt
    
    def _parse_comprehensive_response(self, response_text: str, video_path: str) -> Optional[GeminiVideoAnalysis]:
        """Parse Gemini comprehensive analysis response."""
        try:
            # Get video duration
            try:
                clip = VideoFileClip(video_path)
                duration = clip.duration
                clip.close()
            except:
                duration = 60.0  # Default fallback
            
            # Extract music sync segments
            music_sync_segments = self._extract_music_sync_segments(response_text)
            
            # Extract beat-aligned cuts
            beat_aligned_cuts = self._extract_beat_cuts(response_text)
            
            # Extract energy profile
            energy_profile = self._extract_energy_profile(response_text, duration)
            
            # Extract narrative flow
            narrative_flow = self._extract_narrative_flow(response_text)
            
            # Extract sync confidence
            sync_confidence = self._extract_confidence_score(response_text)
            
            return GeminiVideoAnalysis(
                file_path=video_path,
                duration=duration,
                music_sync_segments=music_sync_segments,
                beat_aligned_cuts=beat_aligned_cuts,
                energy_profile=energy_profile,
                narrative_flow=narrative_flow,
                sync_confidence=sync_confidence,
                gemini_reasoning=response_text[:1000]
            )
            
        except Exception as e:
            logger.error(f"Error parsing comprehensive response: {e}")
            return None
    
    def _parse_music_sync_response(self, response_text: str, video_path: str, audio_features: AudioFeatures) -> Optional[GeminiVideoAnalysis]:
        """Parse Gemini music-sync analysis response."""
        try:
            # Get video duration
            try:
                clip = VideoFileClip(video_path)
                duration = clip.duration
                clip.close()
            except:
                duration = audio_features.duration  # Use music duration as fallback
            
            # Extract music sync segments with BPM awareness
            music_sync_segments = self._extract_music_sync_segments_with_bpm(response_text, audio_features.tempo)
            
            # Extract beat-aligned cuts using provided beats
            beat_aligned_cuts = self._extract_beat_cuts_with_beats(response_text, audio_features.beats)
            
            # Extract energy profile
            energy_profile = self._extract_energy_profile(response_text, duration)
            
            # Extract narrative flow
            narrative_flow = self._extract_narrative_flow(response_text)
            
            # Extract sync confidence
            sync_confidence = self._extract_confidence_score(response_text)
            
            return GeminiVideoAnalysis(
                file_path=video_path,
                duration=duration,
                music_sync_segments=music_sync_segments,
                beat_aligned_cuts=beat_aligned_cuts,
                energy_profile=energy_profile,
                narrative_flow=narrative_flow,
                sync_confidence=sync_confidence,
                gemini_reasoning=response_text[:1000]
            )
            
        except Exception as e:
            logger.error(f"Error parsing music-sync response: {e}")
            return None
    
    def _extract_music_sync_segments(self, text: str) -> List[MusicSyncSegment]:
        """Extract music sync segments from response text."""
        segments = []
        
        # Simple extraction - create default segments
        # In a real implementation, this would parse the actual response
        import re
        
        # Look for timestamp patterns
        timestamp_pattern = r'(\d+\.?\d*)-(\d+\.?\d*)\s*(?:seconds?|s)'
        matches = re.findall(timestamp_pattern, text.lower())
        
        for i, match in enumerate(matches[:8]):  # Limit to 8 segments
            try:
                start_time = float(match[0])
                end_time = float(match[1])
                
                # Extract energy level from context
                energy_level = "medium"
                if "high energy" in text.lower() or "intense" in text.lower():
                    energy_level = "high"
                elif "calm" in text.lower() or "low energy" in text.lower():
                    energy_level = "low"
                
                # Extract music compatibility
                compatibility = "calm"
                if "buildup" in text.lower():
                    compatibility = "buildup"
                elif "drop" in text.lower() or "climax" in text.lower():
                    compatibility = "drop"
                elif "climax" in text.lower():
                    compatibility = "climax"
                
                # Extract visual rhythm
                visual_rhythm = "moderate"
                if "fast" in text.lower():
                    visual_rhythm = "fast"
                elif "slow" in text.lower():
                    visual_rhythm = "slow"
                
                segments.append(MusicSyncSegment(
                    start_time=start_time,
                    end_time=end_time,
                    energy_level=energy_level,
                    music_compatibility=compatibility,
                    visual_rhythm=visual_rhythm,
                    recommended_bpm=120.0,  # Default BPM
                    confidence=0.8
                ))
                
            except:
                continue
        
        # If no segments found, create default segments
        if not segments:
            segments = [
                MusicSyncSegment(
                    start_time=0.0,
                    end_time=30.0,
                    energy_level="medium",
                    music_compatibility="calm",
                    visual_rhythm="moderate",
                    recommended_bpm=120.0,
                    confidence=0.7
                )
            ]
        
        return segments
    
    def _extract_music_sync_segments_with_bpm(self, text: str, target_bpm: float) -> List[MusicSyncSegment]:
        """Extract music sync segments with BPM awareness."""
        segments = self._extract_music_sync_segments(text)
        
        # Update BPM recommendations based on target BPM
        for segment in segments:
            if segment.visual_rhythm == "fast":
                segment.recommended_bpm = target_bpm * 1.2  # 20% faster
            elif segment.visual_rhythm == "slow":
                segment.recommended_bpm = target_bpm * 0.8  # 20% slower
            else:
                segment.recommended_bpm = target_bpm
        
        return segments
    
    def _extract_beat_cuts(self, text: str) -> List[float]:
        """Extract beat-aligned cut points from response text."""
        import re
        
        # Look for various timestamp formats
        patterns = [
            r'(\d+\.?\d*)\s*seconds?',
            r'(\d+):(\d+)',  # mm:ss format
            r'at\s+(\d+\.?\d*)',
        ]
        
        timestamps = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) == 2:
                        # mm:ss format
                        timestamp = int(match[0]) * 60 + int(match[1])
                    else:
                        timestamp = float(match)
                    
                    if 0 <= timestamp <= 300:  # Reasonable range
                        timestamps.append(timestamp)
                except:
                    continue
        
        # Remove duplicates and sort
        timestamps = sorted(list(set(timestamps)))
        return timestamps[:12]  # Limit to 12 cuts
    
    def _extract_beat_cuts_with_beats(self, text: str, beats: List[float]) -> List[float]:
        """Extract beat cuts aligned with provided beats."""
        extracted_cuts = self._extract_beat_cuts(text)
        
        if not extracted_cuts:
            # Use every 4th beat as fallback
            return beats[::4][:12]
        
        # Align extracted cuts with nearest beats
        aligned_cuts = []
        for cut in extracted_cuts:
            # Find nearest beat
            nearest_beat = min(beats, key=lambda b: abs(b - cut))
            if abs(nearest_beat - cut) < 2.0:  # Within 2 seconds
                aligned_cuts.append(nearest_beat)
            else:
                aligned_cuts.append(cut)
        
        return aligned_cuts[:12]
    
    def _extract_energy_profile(self, text: str, duration: float) -> Dict[str, List[float]]:
        """Extract energy profile from response text."""
        # Create default energy profile
        num_windows = int(duration / 5)  # 5-second windows
        
        energy_profile = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        # Simple extraction based on keywords
        if "high energy" in text.lower():
            energy_profile["high"] = [i * 5 for i in range(0, num_windows, 3)]
        if "medium energy" in text.lower() or "moderate" in text.lower():
            energy_profile["medium"] = [i * 5 for i in range(1, num_windows, 3)]
        if "low energy" in text.lower() or "calm" in text.lower():
            energy_profile["low"] = [i * 5 for i in range(2, num_windows, 3)]
        
        return energy_profile
    
    def _extract_narrative_flow(self, text: str) -> str:
        """Extract narrative flow description from LLM response"""
        # Look for narrative/story sections
        markers = ["narrative", "story", "flow", "arc", "structure"]
        
        for marker in markers:
            start_idx = text.lower().find(marker)
            if start_idx != -1:
                # Extract next 200 characters
                end_idx = min(start_idx + 300, len(text))
                section = text[start_idx:end_idx].strip()
                
                # Clean up the section
                sentences = section.split('.')
                if len(sentences) > 1:
                    return '. '.join(sentences[:2]) + '.'
                else:
                    return section
        
        # Default narrative flow
        return "Progressive energy build with beat-synchronized transitions"
    
    def _extract_confidence_score(self, text: str) -> float:
        """Extract confidence score from LLM response"""
        import re
        
        # Look for confidence patterns
        patterns = [
            r'confidence[:\s]+(\d+\.?\d*)%',
            r'confidence[:\s]+(\d+\.?\d*)/10',
            r'confidence[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)%\s+confidence',
            r'rate[:\s]+(\d+\.?\d*)/10',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    score = float(matches[0])
                    # Normalize to 0-1 range
                    if score > 1:
                        score = score / 100 if score <= 100 else score / 10
                    return min(1.0, max(0.0, score))
                except:
                    continue
        
        # Default confidence
        return 0.75
    
    def _load_cached_analysis(self, video_path: str) -> Optional[GeminiVideoAnalysis]:
        """Load cached Gemini analysis if available."""
        # Simple cache implementation - in practice, use proper cache manager
        cache_file = f"cache/gemini_{Path(video_path).stem}.json"
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct GeminiVideoAnalysis object
                segments = [MusicSyncSegment(**seg) for seg in data.get('music_sync_segments', [])]
                
                return GeminiVideoAnalysis(
                    file_path=data['file_path'],
                    duration=data['duration'],
                    music_sync_segments=segments,
                    beat_aligned_cuts=data['beat_aligned_cuts'],
                    energy_profile=data['energy_profile'],
                    narrative_flow=data['narrative_flow'],
                    sync_confidence=data['sync_confidence'],
                    gemini_reasoning=data['gemini_reasoning'],
                    processing_time=data.get('processing_time', 0.0),
                    api_cost=data.get('api_cost', 0.0)
                )
        except:
            pass
        
        return None
    
    def _load_cached_music_analysis(self, video_path: str, audio_features: AudioFeatures) -> Optional[GeminiVideoAnalysis]:
        """Load cached music-specific analysis if available."""
        # Music-specific cache with BPM in filename
        cache_file = f"cache/gemini_music_{Path(video_path).stem}_{int(audio_features.tempo)}bpm.json"
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct GeminiVideoAnalysis object
                segments = [MusicSyncSegment(**seg) for seg in data.get('music_sync_segments', [])]
                
                return GeminiVideoAnalysis(
                    file_path=data['file_path'],
                    duration=data['duration'],
                    music_sync_segments=segments,
                    beat_aligned_cuts=data['beat_aligned_cuts'],
                    energy_profile=data['energy_profile'],
                    narrative_flow=data['narrative_flow'],
                    sync_confidence=data['sync_confidence'],
                    gemini_reasoning=data['gemini_reasoning'],
                    processing_time=data.get('processing_time', 0.0),
                    api_cost=data.get('api_cost', 0.0)
                )
        except:
            pass
        
        return None
    
    def _cache_analysis(self, video_path: str, analysis: GeminiVideoAnalysis) -> None:
        """Cache Gemini analysis results."""
        try:
            os.makedirs("cache", exist_ok=True)
            cache_file = f"cache/gemini_{Path(video_path).stem}.json"
            
            with open(cache_file, 'w') as f:
                json.dump(analysis.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to cache analysis: {e}")
    
    def _cache_music_analysis(self, video_path: str, audio_features: AudioFeatures, analysis: GeminiVideoAnalysis) -> None:
        """Cache music-specific analysis results."""
        try:
            os.makedirs("cache", exist_ok=True)
            cache_file = f"cache/gemini_music_{Path(video_path).stem}_{int(audio_features.tempo)}bpm.json"
            
            with open(cache_file, 'w') as f:
                json.dump(analysis.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to cache music analysis: {e}")


def test_video_analysis():
    """Test the LLM video analyzer with a sample video."""
    analyzer = LLMVideoAnalyzer()
    
    # Test with one development video
    test_videos = ["input_dev/DJI_0108_dev.MP4", "input_dev/IMG_7840_dev.mov"]
    
    for video in test_videos:
        if os.path.exists(video):
            print(f"\n🧪 Testing analysis on {video}")
            analysis = analyzer.analyze_video(video, use_dev_version=False)
            
            if analysis:
                print(f"✅ Analysis successful!")
                print(f"   Content: {analysis.content_summary[:100]}...")
                print(f"   Shot types: {analysis.shot_types}")
                print(f"   Mood: {analysis.mood_energy}")
                print(f"   Transition points: {analysis.transition_points}")
            else:
                print(f"❌ Analysis failed")
            break
    else:
        print("❌ No test videos found")

if __name__ == "__main__":
    test_video_analysis()
