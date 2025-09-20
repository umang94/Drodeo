#!/usr/bin/env python3
"""
Gemini Multimodal Analyzer (Audio-Free)

Complete video-only analysis using Gemini API for video content.
Focuses on creating the longest possible engaging video from available footage.
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json

# Gemini API imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Gemini API library not available: {e}")
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MultimodalAnalysisResult:
    """Results from analyzing multiple videos using Gemini (audio-free)"""
    video_paths: List[str]
    total_video_duration: float
    clip_selections: List[Dict]  # Selected clips from different videos
    sequencing_plan: List[Dict]  # Recommended sequence across videos
    cross_video_transitions: List[Dict]  # Transitions between different videos
    energy_matching: Dict[str, List[str]]  # Energy levels -> video recommendations
    sync_confidence: float
    gemini_reasoning: str
    processing_time: float
    udio_prompt: str  # Suggested UDIO audio prompt
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'video_paths': self.video_paths,
            'total_video_duration': self.total_video_duration,
            'clip_selections': self.clip_selections,
            'sequencing_plan': self.sequencing_plan,
            'cross_video_transitions': self.cross_video_transitions,
            'energy_matching': self.energy_matching,
            'sync_confidence': self.sync_confidence,
            'processing_time': self.processing_time,
            'gemini_reasoning': self.gemini_reasoning,
            'udio_prompt': self.udio_prompt
        }

class GeminiMultimodalAnalyzer:
    """Analyzes multiple videos using Gemini's multimodal capabilities (audio-free)"""
    
    def __init__(self):
        """Initialize Gemini multimodal analyzer with lazy initialization."""
        self.model = None
        self._initialized = False
        
        if not GEMINI_AVAILABLE:
            print("   ⚠️  Gemini API library not available")
            return
        
        # Lazy initialization - don't check API key until actually needed
        print("   ✅ Gemini multimodal analyzer initialized (lazy loading)")
    
    def is_available(self) -> bool:
        """Check if Gemini API is available and configured."""
        if not GEMINI_AVAILABLE:
            return False
        
        # Lazy initialization - configure Gemini only when needed
        if self.model is None:
            try:
                # Configure Gemini API
                api_key = os.getenv('GEMINI_API_KEY')
                if not api_key:
                    print("   ⚠️  GEMINI_API_KEY not found in environment variables")
                    return False
                
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("   ✅ Gemini API configured successfully")
                
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")
                print(f"   ❌ Gemini configuration failed: {e}")
                self.model = None
                return False
        
        return self.model is not None
    
    def analyze_batch(self, video_paths: List[str], 
                     test_name: str = "Video Content Generation") -> Optional[MultimodalAnalysisResult]:
        """
        Analyze multiple videos using Gemini multimodal capabilities (audio-free).
        Focuses on creating the longest possible engaging video from available footage.
        
        Args:
            video_paths: List of video file paths
            test_name: Name for this analysis (for logging)
            
        Returns:
            MultimodalAnalysisResult or None if analysis fails
        """
        if not self.is_available():
            print(f"   ❌ Cannot perform multimodal analysis - Gemini API not available")
            return None
        
        print(f"   🎬 Starting Gemini video-only analysis...")
        print(f"      Videos: {len(video_paths)} files")
        
        start_time = time.time()
        
        try:
            # Step 1: Upload all videos to Gemini
            print(f"      📤 Uploading {len(video_paths)} videos to Gemini...")
            uploaded_videos = []
            
            for video_path in video_paths:
                print(f"         Uploading {Path(video_path).name}...")
                uploaded_video = self._upload_video_to_gemini(video_path)
                if uploaded_video:
                    uploaded_videos.append({
                        'file': uploaded_video,
                        'path': video_path,
                        'name': Path(video_path).name
                    })
                    print(f"            ✅ Upload complete")
                else:
                    print(f"            ❌ Upload failed")
            
            if not uploaded_videos:
                print(f"      ❌ No videos uploaded successfully")
                return None
            
            print(f"      ✅ {len(uploaded_videos)} videos uploaded successfully")
            
            # Step 2: Perform video-only analysis
            print(f"      🤖 Performing video-only analysis...")
            analysis_result = self._analyze_video_only_with_gemini(
                uploaded_videos, test_name
            )
            
            processing_time = time.time() - start_time
            
            if analysis_result:
                analysis_result.processing_time = processing_time
                print(f"      ✅ Video-only analysis complete ({processing_time:.1f}s)")
                print(f"         Clip selections: {len(analysis_result.clip_selections)}")
                print(f"         Transitions: {len(analysis_result.cross_video_transitions)}")
                print(f"         Sync confidence: {analysis_result.sync_confidence:.2f}")
                if analysis_result.udio_prompt:
                    print(f"         UDIO prompt: {analysis_result.udio_prompt}")
                return analysis_result
            else:
                print(f"      ❌ Video-only analysis failed")
                return None
                
        except Exception as e:
            print(f"      ❌ Error in video-only analysis: {e}")
            logger.error(f"Video-only analysis failed: {e}")
            return None
    
    def _upload_video_to_gemini(self, video_path: str):
        """Upload single video to Gemini API with extended timeout for large files"""
        try:
            # Upload file
            uploaded_file = genai.upload_file(path=video_path)
            
            # Wait for processing with extended timeout for large files
            max_wait = 120  # 2 minutes for large concatenated videos
            elapsed = 0
            
            while uploaded_file.state.name == "PROCESSING" and elapsed < max_wait:
                time.sleep(2)  # Check less frequently
                elapsed += 2
                uploaded_file = genai.get_file(uploaded_file.name)
                if elapsed % 10 == 0:  # Print status every 10 seconds
                    print(f"            Still processing... ({elapsed}s elapsed)")
            
            if uploaded_file.state.name == "ACTIVE":
                print(f"            ✅ Upload complete after {elapsed}s")
                return uploaded_file
            else:
                print(f"            ❌ File processing failed: {uploaded_file.state.name} after {elapsed}s")
                return None
                
        except Exception as e:
            print(f"            ❌ Upload error: {e}")
            return None
    
    def _analyze_video_only_with_gemini(self, uploaded_videos: List[Dict], test_name: str) -> Optional[MultimodalAnalysisResult]:
        """Send only videos to Gemini for video-only analysis"""
        try:
            # Create video-only prompt with UDIO generation request
            prompt = self._create_video_only_prompt(uploaded_videos, test_name)
            
            print(f"      📝 Sending video-only prompt to Gemini:")
            print(f"         Videos: {[v['name'] for v in uploaded_videos]}")
            
            # Prepare content with only videos (no audio)
            content_parts = [prompt]
            
            # Add all uploaded videos
            for video_info in uploaded_videos:
                content_parts.append(video_info['file'])
            
            # Call Gemini API
            print(f"      🤖 Calling Gemini API with {len(content_parts)} content parts...")
            response = self.model.generate_content(content_parts)
            
            # LOG THE FULL GEMINI RESPONSE
            print(f"\n" + "="*80)
            print(f"🔍 FULL GEMINI RESPONSE:")
            print(f"="*80)
            print(response.text)
            print(f"="*80 + "\n")
            
            # Parse video-only response
            print(f"      📊 Parsing Gemini response...")
            result = self._parse_video_only_response(
                response.text, uploaded_videos
            )
            
            if result:
                print(f"      ✅ Parsing complete:")
                print(f"         Clip selections: {len(result.clip_selections)}")
                print(f"         Video sources in clips: {set(clip['video'] for clip in result.clip_selections)}")
                print(f"         Cross-video transitions: {len(result.cross_video_transitions)}")
                print(f"         Sequencing plan: {len(result.sequencing_plan)}")
                if result.udio_prompt:
                    print(f"         UDIO prompt: {result.udio_prompt}")
            
            return result
            
        except Exception as e:
            print(f"         ❌ Gemini video-only analysis error: {e}")
            logger.error(f"Gemini video-only analysis error: {e}")
            return None

    def _create_video_only_prompt(self, uploaded_videos: List[Dict], test_name: str) -> str:
        """Create video-only prompt for single concatenated video analysis"""
        
        video_names = [v['name'] for v in uploaded_videos]
        
        prompt = f"""
VIDEO-ONLY CONTENT ANALYSIS: {test_name}

**CRITICAL:** You have been provided with a SINGLE CONCATENATED VIDEO that contains multiple source videos seamlessly joined together. Please analyze this video to create an engaging compilation.

**IMPORTANT ARCHITECTURAL NOTE:** This is a single concatenated video file that contains multiple source videos. All timestamps you reference should be relative to this single concatenated video timeline.

**STEP 1 - VIDEO ANALYSIS:**
Analyze the concatenated video as a single continuous timeline:
- Visual content and scene changes throughout the video
- Energy level progression and pacing
- Natural transition points and visual flow
- Duration and overall structure

**STEP 2 - CONTENT SYNCHRONIZATION PLAN:**
Create a detailed timeline that maximizes the use of available footage:

1. **COMPELLING HOOK:**
   - Select the most engaging opening segment from the concatenated video
   - Specify exact timestamp within the concatenated video
   - Create visual intrigue to capture attention

2. **CONTENT FLOW ALIGNMENT:**
   For optimal viewing experience, analyze:
   - Which segments provide the best visual continuity
   - Exact timestamps for optimal clips within the concatenated video
   - Energy level progression throughout the video
   - Natural transition points based on visual flow

3. **CLIP SELECTION:**
   Identify specific clips with:
   - Exact timestamps (start-end in seconds) within the concatenated video
   - How each clip contributes to the overall narrative
   - Energy level and visual characteristics
   - Recommended placement in the overall sequence
   - Look for multiple engaging segments throughout the video

4. **CLIP SELECTION GUIDANCE:**
   - **Clips can start from ANY timestamp within the concatenated video, not just 0:00**
   - **Select the most visually engaging segments regardless of their position in the timeline**
   - **Always ensure start_time and end_time are within the actual video duration**
   - **Prefer content-rich segments over arbitrary beginning/end points**

5. **TRANSITION RECOMMENDATIONS:**
   - Specify transition points that maintain visual flow
   - Match visual movement and composition between clips
   - Create seamless flow between different segments

**STEP 3 - UDIO AUDIO PROMPT GENERATION:**
Based on the visual content and pacing, create a concise UDIO prompt for generating matching audio:
- Suggest appropriate music genre and atmosphere
- Recommend duration based on total video content
- Keep it concise and ready for UDIO input

**PREFERENCE:** When creating the timeline, prefer longer video durations when possible to make full use of the available footage, while maintaining engagement and visual coherence.

**OUTPUT FORMAT:**
Start your response with:
"VIDEO ANALYSIS COMPLETE"
"TOTAL_DURATION: [X] seconds"

Then provide the complete video analysis with precise timestamps.

Include your UDIO prompt suggestion at the end as:
"UDIO_PROMPT: [your concise audio prompt suggestion]"

**GOAL:** Create an engaging video compilation that makes optimal use of all available footage. It also provides a matching audio suggestion for manual generation.
"""
        
        return prompt

    def _parse_video_only_response(self, response_text: str, uploaded_videos: List[Dict]) -> Optional[MultimodalAnalysisResult]:
        """
        NO REGEX PARSING - Store raw response for self-translation
        
        ARCHITECTURAL TENET: This method no longer parses natural language with regex.
        Instead, it stores the complete response for Gemini's self-translation in Step 2.
        All parsing is deferred to the self-translator.
        """
        try:
            # Extract actual duration from Gemini response if available
            actual_duration = self._extract_duration_from_response(response_text)
            
            # NO REGEX PARSING - Return raw response for self-translation
            return MultimodalAnalysisResult(
                video_paths=[v['path'] for v in uploaded_videos],
                total_video_duration=actual_duration,  # Use actual duration or fallback
                clip_selections=[],  # Empty - will be filled by self-translator
                sequencing_plan=[],  # Empty - will be filled by self-translator
                cross_video_transitions=[],  # Empty - will be filled by self-translator
                energy_matching={},  # Empty - will be filled by self-translator
                sync_confidence=0.85,  # Default confidence
                gemini_reasoning=response_text,  # FULL response for self-translation
                processing_time=0.0,  # Will be set by caller
                udio_prompt="Epic cinematic music matching the video content"  # Default prompt
            )
            
        except Exception as e:
            print(f"         ❌ Error processing video-only response: {e}")
            logger.error(f"Error processing video-only response: {e}")
            return None
    
    def _extract_duration_from_response(self, response_text: str) -> float:
        """
        Extract the actual video duration from Gemini's response.
        This is the only parsing allowed to get the duration for the self-translator.
        """
        try:
            # Look for "TOTAL_DURATION: X seconds" pattern in the response
            lines = response_text.split('\n')
            for line in lines:
                if "TOTAL_DURATION:" in line:
                    # Extract the number from the line
                    parts = line.split(':')
                    if len(parts) > 1:
                        duration_part = parts[1].strip()
                        # Remove "seconds" and any other non-numeric characters
                        duration_str = ''.join(c for c in duration_part if c.isdigit() or c == '.')
                        if duration_str:
                            return float(duration_str)
            
            # If not found, return default duration
            return 120.0
            
        except (ValueError, IndexError):
            return 120.0  # Fallback to default duration
            
        except Exception as e:
            print(f"         ❌ Error processing video-only response: {e}")
            logger.error(f"Error processing video-only response: {e}")
            return None
    
    # REMOVED: All audio-related methods (_analyze_multimodal_with_gemini, _create_multimodal_prompt, 
    # _parse_multimodal_response, _extract_basic_audio_duration, _extract_basic_audio_tempo)
    # These methods were for audio-video multimodal analysis and are no longer needed
    
    def save_analysis_results(self, result: MultimodalAnalysisResult, output_file: str = None):
        """Save multimodal analysis results to JSON file"""
        try:
            if not output_file:
                timestamp = int(time.time())
                output_file = f"multimodal_analysis_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            print(f"      � Analysis results saved to: {output_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save analysis results: {e}")

def test_multimodal_analyzer():
    """Test the multimodal analyzer with sample content"""
    analyzer = GeminiMultimodalAnalyzer()
    
    if not analyzer.is_available():
        print("❌ Gemini multimodal analyzer not available")
        return
    
    # Test with sample video files (if they exist)
    video_paths = [
        "input_dev/DJI_0108_dev.MP4",
        "input_dev/IMG_7840_dev.mov"
    ]
    
    # Check if files exist
    existing_videos = [v for v in video_paths if os.path.exists(v)]
    if not existing_videos:
        print(f"❌ No test video files found")
        return
    
    print(f"🧪 Testing video-only multimodal analyzer...")
    result = analyzer.analyze_batch(existing_videos, "Test Video Analysis")
    
    if result:
        print(f"✅ Test successful!")
        print(f"   Clip selections: {len(result.clip_selections)}")
        print(f"   Sync confidence: {result.sync_confidence:.2f}")
        if result.udio_prompt:
            print(f"   UDIO prompt: {result.udio_prompt}")
        analyzer.save_analysis_results(result, "test_video_only_result.json")
    else:
        print(f"❌ Test failed")

if __name__ == "__main__":
    test_multimodal_analyzer()
