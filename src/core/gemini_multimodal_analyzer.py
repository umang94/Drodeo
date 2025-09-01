#!/usr/bin/env python3
"""
Gemini Multimodal Analyzer

Complete multimodal analysis using Gemini API for audio + video content.
Replaces separate audio and video analysis with unified multimodal approach.
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
    """Results from analyzing multiple videos with single audio track using Gemini"""
    audio_path: str
    video_paths: List[str]
    audio_duration: float
    audio_tempo: float
    clip_selections: List[Dict]  # Selected clips from different videos
    sequencing_plan: List[Dict]  # Recommended sequence across videos
    cross_video_transitions: List[Dict]  # Transitions between different videos
    energy_matching: Dict[str, List[str]]  # Energy levels -> video recommendations
    sync_confidence: float
    gemini_reasoning: str
    processing_time: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'audio_path': self.audio_path,
            'video_paths': self.video_paths,
            'audio_duration': self.audio_duration,
            'audio_tempo': self.audio_tempo,
            'clip_selections': self.clip_selections,
            'sequencing_plan': self.sequencing_plan,
            'cross_video_transitions': self.cross_video_transitions,
            'energy_matching': self.energy_matching,
            'sync_confidence': self.sync_confidence,
            'processing_time': self.processing_time,
            'gemini_reasoning': self.gemini_reasoning
        }

class GeminiMultimodalAnalyzer:
    """Analyzes audio + multiple videos simultaneously using Gemini's multimodal capabilities"""
    
    def __init__(self):
        """Initialize Gemini multimodal analyzer."""
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
            
            print("   ✅ Gemini multimodal analyzer initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            print(f"   ❌ Gemini initialization failed: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available and configured."""
        return GEMINI_AVAILABLE and self.model is not None
    
    def analyze_batch(self, audio_path: str, video_paths: List[str], 
                     test_name: str = "Music Video Generation") -> Optional[MultimodalAnalysisResult]:
        """
        Analyze multiple videos with single audio track using Gemini multimodal capabilities.
        This is the core method that replaces separate audio and video analysis.
        
        Args:
            audio_path: Path to music file
            video_paths: List of video file paths
            test_name: Name for this analysis (for logging)
            
        Returns:
            MultimodalAnalysisResult or None if analysis fails
        """
        if not self.is_available():
            print(f"   ❌ Cannot perform multimodal analysis - Gemini API not available")
            return None
        
        print(f"   🎵🎬 Starting Gemini multimodal analysis...")
        print(f"      Audio: {Path(audio_path).name}")
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
            
            # Step 2: Upload audio to Gemini
            print(f"      📤 Uploading audio to Gemini...")
            uploaded_audio = self._upload_audio_to_gemini(audio_path)
            if not uploaded_audio:
                print(f"      ❌ Audio upload failed")
                return None
            
            print(f"      ✅ Audio uploaded successfully")
            
            # Step 3: Perform multimodal analysis
            print(f"      🤖 Performing multimodal analysis...")
            analysis_result = self._analyze_multimodal_with_gemini(
                audio_path, uploaded_audio, uploaded_videos, test_name
            )
            
            processing_time = time.time() - start_time
            
            if analysis_result:
                analysis_result.processing_time = processing_time
                print(f"      ✅ Multimodal analysis complete ({processing_time:.1f}s)")
                print(f"         Clip selections: {len(analysis_result.clip_selections)}")
                print(f"         Transitions: {len(analysis_result.cross_video_transitions)}")
                print(f"         Sync confidence: {analysis_result.sync_confidence:.2f}")
                return analysis_result
            else:
                print(f"      ❌ Multimodal analysis failed")
                return None
                
        except Exception as e:
            print(f"      ❌ Error in multimodal analysis: {e}")
            logger.error(f"Multimodal analysis failed: {e}")
            return None
    
    def _upload_video_to_gemini(self, video_path: str):
        """Upload single video to Gemini API"""
        try:
            # Upload file
            uploaded_file = genai.upload_file(path=video_path)
            
            # Wait for processing
            max_wait = 30
            elapsed = 0
            
            while uploaded_file.state.name == "PROCESSING" and elapsed < max_wait:
                time.sleep(1)
                elapsed += 1
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "ACTIVE":
                return uploaded_file
            else:
                print(f"            File processing failed: {uploaded_file.state.name}")
                return None
                
        except Exception as e:
            print(f"            Upload error: {e}")
            return None
    
    def _upload_audio_to_gemini(self, audio_path: str):
        """Upload audio file to Gemini API"""
        try:
            # Upload file
            uploaded_file = genai.upload_file(path=audio_path)
            
            # Wait for processing
            max_wait = 30
            elapsed = 0
            
            while uploaded_file.state.name == "PROCESSING" and elapsed < max_wait:
                time.sleep(1)
                elapsed += 1
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "ACTIVE":
                return uploaded_file
            else:
                print(f"         Audio processing failed: {uploaded_file.state.name}")
                return None
                
        except Exception as e:
            print(f"         Audio upload error: {e}")
            return None
    
    def _analyze_multimodal_with_gemini(self, audio_path: str, uploaded_audio, 
                                       uploaded_videos: List[Dict], test_name: str) -> Optional[MultimodalAnalysisResult]:
        """Send audio + multiple videos to Gemini for unified analysis"""
        try:
            # Create comprehensive multimodal prompt
            prompt = self._create_multimodal_prompt(audio_path, uploaded_videos, test_name)
            
            print(f"      📝 Sending prompt to Gemini:")
            print(f"         Audio: {Path(audio_path).name}")
            print(f"         Videos: {[v['name'] for v in uploaded_videos]}")
            
            # Prepare content with audio and all videos
            content_parts = [prompt, uploaded_audio]
            
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
            
            # Parse multimodal response
            print(f"      📊 Parsing Gemini response...")
            result = self._parse_multimodal_response(
                response.text, audio_path, uploaded_videos
            )
            
            if result:
                print(f"      ✅ Parsing complete:")
                print(f"         Clip selections: {len(result.clip_selections)}")
                print(f"         Video sources in clips: {set(clip['video'] for clip in result.clip_selections)}")
                print(f"         Cross-video transitions: {len(result.cross_video_transitions)}")
                print(f"         Sequencing plan: {len(result.sequencing_plan)}")
            
            return result
            
        except Exception as e:
            print(f"         ❌ Gemini multimodal analysis error: {e}")
            logger.error(f"Gemini multimodal analysis error: {e}")
            return None
    
    def _create_multimodal_prompt(self, audio_path: str, uploaded_videos: List[Dict], test_name: str) -> str:
        """Create comprehensive prompt for multimodal analysis with explicit audio analysis request"""
        
        video_names = [v['name'] for v in uploaded_videos]
        
        prompt = f"""
MULTIMODAL MUSIC-VIDEO ANALYSIS: {test_name}

**CRITICAL:** You have been provided with both an audio track and {len(uploaded_videos)} video files. Please confirm you can access both by analyzing them together.

**STEP 1 - AUDIO ANALYSIS (REQUIRED FIRST):**
Analyze the audio track "{Path(audio_path).name}" and provide:
- Exact duration in seconds (listen to the full track)
- BPM/Tempo (detect actual beats)
- Musical structure with precise timestamps (intro, verse, chorus, bridge, outro)
- Energy profile throughout the song (high/medium/low energy sections)
- Genre and instrumentation
- Key musical moments and transitions

**STEP 2 - VIDEO ANALYSIS (REQUIRED):**
Analyze each video source:
{chr(10).join([f'- {i+1}. {name}: Visual content, duration, scene changes, energy level' for i, name in enumerate(video_names)])}

**STEP 3 - MULTIMODAL SYNCHRONIZATION PLAN:**
Create a detailed timeline that combines the audio analysis with video recommendations:

1. **COMPELLING HOOK (0-15 seconds):**
   - Based on actual audio intro, select matching video clip
   - Specify exact video source and timestamp
   - Match visual energy to musical opening

2. **SONG STRUCTURE ALIGNMENT:**
   For each musical section identified in Step 1, specify:
   - Which video source provides the best visual match
   - Exact timestamps for optimal clips from EACH video
   - Energy level matching between audio and video
   - Beat-aligned cut points based on actual audio analysis

3. **CROSS-VIDEO CLIP SELECTION:**
   For EACH video source, identify 3-5 specific clips with:
   - Video name and exact timestamps (start-end in seconds)
   - How each clip matches specific audio moments
   - Energy level alignment with music
   - Recommended placement in song structure

4. **TRANSITION RECOMMENDATIONS:**
   - Specify exact transition points based on musical beats
   - Match visual movement to audio rhythm
   - Create seamless flow between different video sources

**OUTPUT FORMAT:**
Start your response with:
"AUDIO ACCESS: [CONFIRMED/FAILED]"
"AUDIO DURATION: [X] seconds"
"AUDIO BPM: [X] BPM"

Then provide the complete multimodal analysis with precise timestamps based on your actual audio analysis.

**GOAL:** Create a music video plan that uses REAL audio analysis (not assumptions) to perfectly synchronize visual content with the actual musical structure, rhythm, and energy progression.
"""
        
        return prompt
    
    def _parse_multimodal_response(self, response_text: str, audio_path: str, 
                                  uploaded_videos: List[Dict]) -> Optional[MultimodalAnalysisResult]:
        """
        NO REGEX PARSING - Store raw response for self-translation
        
        ARCHITECTURAL TENET: This method no longer parses natural language with regex.
        Instead, it extracts only basic metadata and stores the complete response
        for Gemini's self-translation in Step 2.
        """
        try:
            # Extract only basic audio information using simple patterns (not complex parsing)
            audio_duration = self._extract_basic_audio_duration(response_text)
            audio_tempo = self._extract_basic_audio_tempo(response_text)
            
            # NO REGEX PARSING - Return raw response for self-translation
            return MultimodalAnalysisResult(
                audio_path=audio_path,
                video_paths=[v['path'] for v in uploaded_videos],
                audio_duration=audio_duration,
                audio_tempo=audio_tempo,
                clip_selections=[],  # Empty - will be filled by self-translator
                sequencing_plan=[],  # Empty - will be filled by self-translator
                cross_video_transitions=[],  # Empty - will be filled by self-translator
                energy_matching={},  # Empty - will be filled by self-translator
                sync_confidence=0.85,  # Default confidence
                gemini_reasoning=response_text,  # FULL response for self-translation
                processing_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            print(f"         ❌ Error processing multimodal response: {e}")
            logger.error(f"Error processing multimodal response: {e}")
            return None
    
    def _extract_basic_audio_duration(self, text: str) -> float:
        """
        NO REGEX EXTRACTION - Return default for self-translation
        
        ARCHITECTURAL TENET: No regex parsing of natural language responses.
        The self-translator will extract all structured data in Step 2.
        """
        return 120.0  # Default duration - actual value extracted by self-translator
    
    def _extract_basic_audio_tempo(self, text: str) -> float:
        """
        NO REGEX EXTRACTION - Return default for self-translation
        
        ARCHITECTURAL TENET: No regex parsing of natural language responses.
        The self-translator will extract all structured data in Step 2.
        """
        return 120.0  # Default tempo - actual value extracted by self-translator
    
    # REMOVED: All complex regex parsing methods
    # These methods violated the "NO REGEX PARSING" architectural tenet
    # Self-translation in Step 2 handles all structured data extraction
    
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
    
    # Test with sample files (if they exist)
    audio_path = "music_input/Fractite - Quicky-qPBvJ6E7RXY.mp3"
    video_paths = [
        "input_dev/DJI_0108_dev.MP4",
        "input_dev/IMG_7840_dev.mov"
    ]
    
    # Check if files exist
    if not os.path.exists(audio_path):
        print(f"❌ Test audio file not found: {audio_path}")
        return
    
    existing_videos = [v for v in video_paths if os.path.exists(v)]
    if not existing_videos:
        print(f"❌ No test video files found")
        return
    
    print(f"🧪 Testing multimodal analyzer...")
    result = analyzer.analyze_batch(audio_path, existing_videos, "Test Analysis")
    
    if result:
        print(f"✅ Test successful!")
        print(f"   Clip selections: {len(result.clip_selections)}")
        print(f"   Sync confidence: {result.sync_confidence:.2f}")
        analyzer.save_analysis_results(result, "test_multimodal_result.json")
    else:
        print(f"❌ Test failed")

if __name__ == "__main__":
    test_multimodal_analyzer()
