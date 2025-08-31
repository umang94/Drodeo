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
        """Parse Gemini's multimodal response into structured results"""
        try:
            # Extract basic audio information (estimated from response)
            audio_duration = self._extract_audio_duration(response_text)
            audio_tempo = self._extract_audio_tempo(response_text)
            
            # Extract clip selections
            clip_selections = self._extract_clip_selections(response_text, uploaded_videos)
            
            # Extract sequencing plan
            sequencing_plan = self._extract_sequencing_plan(response_text, uploaded_videos)
            
            # Extract cross-video transitions
            cross_video_transitions = self._extract_cross_video_transitions(response_text)
            
            # Extract energy matching
            energy_matching = self._extract_energy_matching(response_text, uploaded_videos)
            
            # Extract sync confidence
            sync_confidence = self._extract_sync_confidence(response_text)
            
            return MultimodalAnalysisResult(
                audio_path=audio_path,
                video_paths=[v['path'] for v in uploaded_videos],
                audio_duration=audio_duration,
                audio_tempo=audio_tempo,
                clip_selections=clip_selections,
                sequencing_plan=sequencing_plan,
                cross_video_transitions=cross_video_transitions,
                energy_matching=energy_matching,
                sync_confidence=sync_confidence,
                gemini_reasoning=response_text[:2000],  # Store first 2000 chars
                processing_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            print(f"         ❌ Error parsing multimodal response: {e}")
            logger.error(f"Error parsing multimodal response: {e}")
            return None
    
    def _extract_audio_duration(self, text: str) -> float:
        """Extract audio duration from response (estimated)"""
        import re
        
        # Look for duration patterns
        patterns = [
            r'duration[:\s]+(\d+\.?\d*)\s*(?:seconds?|s)',
            r'(\d+\.?\d*)\s*(?:seconds?|s)\s*(?:long|duration)',
            r'track.*?(\d+\.?\d*)\s*(?:seconds?|s)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    return float(matches[0])
                except:
                    continue
        
        return 120.0  # Default duration
    
    def _extract_audio_tempo(self, text: str) -> float:
        """Extract audio tempo from response"""
        import re
        
        # Look for BPM patterns
        patterns = [
            r'(\d+\.?\d*)\s*bpm',
            r'tempo[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*beats?\s*per\s*minute'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    return float(matches[0])
                except:
                    continue
        
        return 120.0  # Default tempo
    
    def _extract_clip_selections(self, text: str, uploaded_videos: List[Dict]) -> List[Dict]:
        """Extract clip selections from response with improved parsing for all video sources"""
        import re
        
        clip_selections = []
        
        print(f"         🔍 Parsing clips from {len(uploaded_videos)} video sources...")
        
        # Create mapping of video names for easier matching
        video_name_map = {}
        for video_info in uploaded_videos:
            full_name = video_info['name']
            base_name = full_name.replace('.MP4', '').replace('.mov', '').replace('.mp4', '').replace('_dev', '')
            video_name_map[full_name] = video_info
            video_name_map[base_name] = video_info
            print(f"            📹 Looking for clips from: {full_name}")
        
        # Enhanced patterns to match Gemini's response format
        # Pattern 1: "**Video Source:** VideoName.ext" followed by "**Timestamp:** X:XX-X:XX"
        video_timestamp_pattern = r'\*\*Video\s+Source:\*\*\s*([^\n\*]+).*?\*\*Timestamp:\*\*\s*(\d+):(\d+)-(\d+):(\d+)'
        matches = re.findall(video_timestamp_pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            video_ref, start_min, start_sec, end_min, end_sec = match
            video_ref = video_ref.strip()
            
            # Find matching video
            matched_video = None
            for name_key, video_info in video_name_map.items():
                if name_key.lower() in video_ref.lower() or video_ref.lower() in name_key.lower():
                    matched_video = video_info
                    break
            
            if matched_video:
                try:
                    start_time = int(start_min) * 60 + int(start_sec)
                    end_time = int(end_min) * 60 + int(end_sec)
                    
                    if start_time < end_time and end_time - start_time >= 1:
                        clip_selections.append({
                            'video': matched_video['name'],
                            'video_path': matched_video['path'],
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': end_time - start_time,
                            'energy_level': 'high'
                        })
                        print(f"            ✅ Found clip: {matched_video['name']} ({start_time}s-{end_time}s)")
                except (ValueError, IndexError):
                    continue
        
        # Pattern 2: Look for video names followed by timestamps in bullet points
        # Example: "DJI_0110_dev.MP4: 0:01-0:15" or "IMG_7840_dev.mov: 0:25-0:49"
        for video_info in uploaded_videos:
            video_name = video_info['name']
            base_name = video_name.replace('.MP4', '').replace('.mov', '').replace('.mp4', '')
            
            # Multiple patterns for this video
            patterns = [
                # Pattern: VideoName: timestamp-timestamp
                rf'{re.escape(video_name)}[:\s]*(\d+):(\d+)-(\d+):(\d+)',
                rf'{re.escape(base_name)}[:\s]*(\d+):(\d+)-(\d+):(\d+)',
                # Pattern: VideoName followed by timestamp on next line
                rf'{re.escape(video_name)}.*?(\d+):(\d+)-(\d+):(\d+)',
                rf'{re.escape(base_name)}.*?(\d+):(\d+)-(\d+):(\d+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    try:
                        start_min, start_sec, end_min, end_sec = match
                        start_time = int(start_min) * 60 + int(start_sec)
                        end_time = int(end_min) * 60 + int(end_sec)
                        
                        if start_time < end_time and end_time - start_time >= 1:
                            # Clamp to reasonable bounds
                            max_duration = 60.0
                            start_time = max(0, min(start_time, max_duration - 2))
                            end_time = max(start_time + 1, min(end_time, max_duration))
                            
                            clip_selections.append({
                                'video': video_name,
                                'video_path': video_info['path'],
                                'start_time': start_time,
                                'end_time': end_time,
                                'duration': end_time - start_time,
                                'energy_level': self._extract_energy_for_clip(text, video_name, start_time)
                            })
                            print(f"            ✅ Found clip: {video_name} ({start_time}s-{end_time}s)")
                            
                    except (ValueError, IndexError):
                        continue
        
        # Pattern 3: Look for structured sections like "DJI_0108_dev.MP4:" followed by bullet points
        for video_info in uploaded_videos:
            video_name = video_info['name']
            base_name = video_name.replace('.MP4', '').replace('.mov', '').replace('.mp4', '')
            
            # Find sections for this video
            section_pattern = rf'\*\s*\*\*{re.escape(base_name)}[^:]*:\*\*(.*?)(?=\*\s*\*\*\w+|$)'
            sections = re.findall(section_pattern, text, re.IGNORECASE | re.DOTALL)
            
            for section in sections:
                # Look for timestamps in this section
                timestamp_matches = re.findall(r'(\d+):(\d+)-(\d+):(\d+)', section)
                
                for match in timestamp_matches:
                    try:
                        start_min, start_sec, end_min, end_sec = match
                        start_time = int(start_min) * 60 + int(start_sec)
                        end_time = int(end_min) * 60 + int(end_sec)
                        
                        if start_time < end_time and end_time - start_time >= 1:
                            max_duration = 60.0
                            start_time = max(0, min(start_time, max_duration - 2))
                            end_time = max(start_time + 1, min(end_time, max_duration))
                            
                            clip_selections.append({
                                'video': video_name,
                                'video_path': video_info['path'],
                                'start_time': start_time,
                                'end_time': end_time,
                                'duration': end_time - start_time,
                                'energy_level': self._extract_energy_for_clip(section, video_name, start_time)
                            })
                            print(f"            ✅ Found clip: {video_name} ({start_time}s-{end_time}s)")
                            
                    except (ValueError, IndexError):
                        continue
        
        # Remove duplicates
        seen = set()
        unique_clips = []
        for clip in clip_selections:
            clip_key = (clip['video'], clip['start_time'], clip['end_time'])
            if clip_key not in seen:
                seen.add(clip_key)
                unique_clips.append(clip)
        
        print(f"         📊 Extracted {len(unique_clips)} unique clips from {len(set(clip['video'] for clip in unique_clips))} videos")
        
        return unique_clips[:20]  # Allow more clips for better variety
    
    def _extract_sequencing_plan(self, text: str, uploaded_videos: List[Dict]) -> List[Dict]:
        """Extract sequencing recommendations"""
        # Simple sequencing extraction - look for order indicators
        sequencing = []
        
        order_patterns = [
            r'(?:first|start|begin|intro).*?(\w+\.(?:mp4|mov))',
            r'(?:second|then|next).*?(\w+\.(?:mp4|mov))',
            r'(?:third|after|follow).*?(\w+\.(?:mp4|mov))',
            r'(?:final|end|last|outro).*?(\w+\.(?:mp4|mov))'
        ]
        
        for i, pattern in enumerate(order_patterns):
            import re
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                video_name = matches[0]
                sequencing.append({
                    'sequence_order': i + 1,
                    'video': video_name,
                    'timing': f'position_{i+1}',
                    'reason': f'Recommended for sequence position {i+1}'
                })
        
        return sequencing
    
    def _extract_cross_video_transitions(self, text: str) -> List[Dict]:
        """Extract cross-video transition recommendations"""
        transitions = []
        
        # Look for transition keywords with timestamps
        import re
        transition_pattern = r'transition.*?(\d+\.?\d*)[:\s]*(?:second|s)'
        matches = re.findall(transition_pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                timestamp = float(match)
                transitions.append({
                    'timestamp': timestamp,
                    'type': 'cross_video_cut',
                    'description': 'Beat-aligned transition between videos'
                })
            except:
                continue
        
        return transitions[:10]  # Limit transitions
    
    def _extract_energy_matching(self, text: str, uploaded_videos: List[Dict]) -> Dict[str, List[str]]:
        """Extract energy level to video mappings"""
        energy_mapping = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        for video_info in uploaded_videos:
            video_name = video_info['name']
            
            # Check energy associations
            if 'high energy' in text.lower() and video_name.lower() in text.lower():
                energy_mapping['high'].append(video_name)
            elif 'medium energy' in text.lower() and video_name.lower() in text.lower():
                energy_mapping['medium'].append(video_name)
            elif 'low energy' in text.lower() and video_name.lower() in text.lower():
                energy_mapping['low'].append(video_name)
            else:
                energy_mapping['medium'].append(video_name)  # Default
        
        return energy_mapping
    
    def _extract_energy_for_clip(self, text: str, video_name: str, timestamp: float) -> str:
        """Extract energy level for specific clip"""
        # Simple energy detection around timestamp context
        if 'high' in text.lower():
            return 'high'
        elif 'low' in text.lower():
            return 'low'
        else:
            return 'medium'
    
    def _extract_sync_confidence(self, text: str) -> float:
        """Extract synchronization confidence score"""
        import re
        
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
                    if score > 1:
                        score = score / 100 if score <= 100 else score / 10
                    return min(1.0, max(0.0, score))
                except:
                    continue
        
        return 0.75  # Default confidence
    
    def save_analysis_results(self, result: MultimodalAnalysisResult, output_file: str = None):
        """Save multimodal analysis results to JSON file"""
        try:
            if not output_file:
                timestamp = int(time.time())
                output_file = f"multimodal_analysis_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            print(f"      💾 Analysis results saved to: {output_file}")
            
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
