"""
LLM-Powered Video Analysis

Advanced video analysis using LLM for holistic content understanding,
story flow detection, and creative direction.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import base64
from dataclasses import dataclass
from moviepy.editor import VideoFileClip
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

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
    
    def __init__(self):
        """Initialize LLM video analyzer."""
        try:
            self.client = OpenAI()
            print("   ✅ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
            print(f"   ❌ OpenAI client initialization failed: {e}")
    
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
