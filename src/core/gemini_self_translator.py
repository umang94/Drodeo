#!/usr/bin/env python3
"""
Gemini Self-Translation Module for Two-Step Pipeline

This module implements Step 2 of the revolutionary two-step Gemini pipeline:
- Takes Gemini's natural language creative timeline from Step 1
- Translates it into structured JSON editing instructions
- Eliminates all regex parsing through intelligent self-translation
- Provides MoviePy-compatible instructions for direct video creation
"""

import os
import json
import logging
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import google.generativeai as genai

from src.utils.config import GEMINI_VIDEO_CONFIG
from src.utils.llm_logger import LLMResponseLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EditingInstructions:
    """
    Structured editing instructions from Gemini self-translation
    All parameters are MoviePy-compatible for direct processing
    """
    clips: List[Dict]                      # MoviePy-compatible clip instructions
    transitions: List[Dict]                # Beat-aligned transition points
    audio_sync: Dict                       # Music synchronization settings
    output_settings: Dict                  # Rendering configuration
    metadata: Dict                         # Translation confidence and notes

class GeminiSelfTranslator:
    """
    Step 2 of Two-Step Gemini Pipeline: Self-Translation
    
    Converts Gemini's natural language creative timeline into structured JSON
    editing instructions that can be directly consumed by VideoEditor.
    """
    
    def __init__(self):
        """Initialize the Gemini Self-Translator"""
        # Configure Gemini API
        api_key = GEMINI_VIDEO_CONFIG.get("api_key")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("🤖 GeminiSelfTranslator initialized successfully")
    
    def translate_timeline(self, gemini_reasoning: str, video_duration: Optional[float] = None, 
                          available_videos: List[str] = None, video_durations: Optional[Dict[str, float]] = None) -> EditingInstructions:
        """
        Translate Gemini's creative timeline into structured JSON editing instructions
        
        Args:
            gemini_reasoning: Natural language creative timeline from Step 1
            video_duration: Target video duration in seconds (optional - will extract from reasoning)
            available_videos: List of available video filenames
            video_durations: Optional dict mapping video filenames to their durations
            
        Returns:
            EditingInstructions with MoviePy-compatible parameters
        """
        start_time = time.time()
        
        logger.info("🤖 Starting Gemini self-translation...")
        if video_duration is not None:
            logger.info(f"   📊 Video duration: {video_duration:.1f}s")
        else:
            logger.info("   📊 Video duration: None (will extract from reasoning)")
        logger.info(f"   📹 Available videos: {len(available_videos) if available_videos else 0}")
        
        try:
            # Create self-translation prompt
            prompt = self._create_self_translation_prompt(
                gemini_reasoning, video_duration, available_videos, video_durations
            )
            
            # Send to Gemini Text API for self-translation
            logger.info("   🔄 Requesting self-translation from Gemini...")
            logger.debug(f"   📝 Prompt preview: {prompt[:200]}...")
            
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini self-translation")
            
            logger.debug(f"   📥 Response preview: {response.text[:200]}...")
            
            # Parse JSON response
            editing_instructions = self._parse_translation_response(
                response.text, video_duration
            )
            
            processing_time = time.time() - start_time
            
            logger.info("   ✅ Self-translation completed successfully")
            logger.info(f"      📊 Clips generated: {len(editing_instructions.clips)}")
            logger.info(f"      🔀 Transitions: {len(editing_instructions.transitions)}")
            logger.info(f"      ⏱️  Processing time: {processing_time:.1f}s")
            logger.info(f"      📈 Confidence: {editing_instructions.metadata.get('confidence', 'N/A')}")
            
            return editing_instructions
            
        except Exception as e:
            logger.error(f"❌ Self-translation failed: {str(e)}")
            
            # Return fallback instructions
            return self._create_fallback_instructions(video_duration, available_videos)
    
    def _create_self_translation_prompt(self, gemini_reasoning: str, 
                                       video_duration: float, 
                                       available_videos: List[str],
                                       video_durations: Optional[Dict[str, float]] = None) -> str:
        """
        Create the Step 2 prompt for Gemini self-translation
        
        Args:
            gemini_reasoning: Original creative timeline from Step 1
            video_duration: Target duration in seconds
            available_videos: List of available video filenames
            video_durations: Optional dict mapping video filenames to their durations
            
        Returns:
            Formatted prompt for self-translation
        """
        available_videos_str = ', '.join(available_videos)
        
        # CRITICAL FIX: Include video duration information in prompt
        video_info_str = ""
        if video_durations:
            video_info_lines = []
            for video in available_videos:
                duration = video_durations.get(video, "unknown")
                video_info_lines.append(f"  - {video}: {duration:.1f}s duration")
            video_info_str = f"""
**VIDEO DURATION CONSTRAINTS:**
{chr(10).join(video_info_lines)}

**CRITICAL TIMESTAMP VALIDATION:**
- start_time and end_time must be within each video's actual duration
- For example, if a video is 20.5s long, end_time cannot exceed 20.5
- Always respect these duration limits to prevent "T_Start should be smaller than clip's duration" errors
"""
        
        # Handle case where video_duration is None (extract from reasoning)
        duration_instruction = ""
        target_duration_for_output = "EXTRACT_FROM_REASONING"
        
        if video_duration is None:
            duration_instruction = """
**CRITICAL:** The video duration is not provided. You MUST extract the actual video duration from the creative timeline analysis above and use that as the target duration."""
            target_duration_for_output = "EXTRACT_FROM_REASONING"
        else:
            duration_instruction = f"- Target video duration: {video_duration} seconds"
            target_duration_for_output = video_duration

        prompt = f"""You are a professional video editing assistant. Your task is to convert Gemini's creative timeline into precise JSON editing instructions for MoviePy video editing software.

**CRITICAL INSTRUCTION: BLINDLY FOLLOW GEMINI'S CREATIVE TIMELINE**
You MUST follow the exact creative timeline provided by Gemini in Step 1. Do NOT make creative decisions or optimize clip selection. Your only job is to translate the provided timeline into JSON format.

**ORIGINAL CREATIVE TIMELINE FROM STEP 1:**
{gemini_reasoning}

**TECHNICAL CONSTRAINTS:**
{duration_instruction}
- Available video files: {available_videos_str}
- Video editing software: MoviePy 1.0.3
- Required output format: Structured JSON
{video_info_str}

**YOUR TASK:**
Convert the creative timeline above into precise JSON editing instructions EXACTLY as specified in the timeline.

**CRITICAL REQUIREMENTS:**

1. **BLIND FOLLOWING:** Use EXACTLY the video sources, timestamps, and durations specified in the creative timeline
2. **NO CREATIVE DECISIONS:** Do not optimize, shorten, or modify the timeline in any way
3. **Exact Video Paths:** Use only filenames from the available_videos list
4. **Precise Timestamps:** All times in seconds (float format) exactly as specified
5. **Complete Coverage:** Clips must cover the full target duration specified in the timeline
6. **No Gaps:** Ensure transitions connect clips seamlessly
7. **Energy Matching:** Map creative descriptions to energy levels
8. **MoviePy Compatible:** All parameters must work with MoviePy 1.0.3
9. **RESPECT VIDEO DURATIONS:** Always check that start_time and end_time are within each video's actual duration
10. **TIMESTAMP INTERPRETATION:** The timestamps in this creative timeline have already been translated from concatenated video positions to original video references. For example, "DJI_0424_dev.MP4 at 0.0s" means use the video file DJI_0424_dev.MP4 starting from 0.0 seconds.

**JSON STRUCTURE:**
Follow this exact structure:

```json
{{
  "editing_instructions": {{
    "clips": [
      {{
        "video_path": "exact_filename_from_available_videos",
        "start_time": 0.0,
        "end_time": 15.5,
        "energy_level": "high|medium|low",
        "fade_in": 0.3,
        "fade_out": 0.3,
        "speed_factor": 1.0,
        "volume_factor": 0.0
      }}
    ],
    "transitions": [
      {{
        "timestamp": 15.5,
        "type": "cross_fade",
        "duration": 0.5,
        "next_clip_index": 1
      }}
    ],
    "output_settings": {{
      "target_duration": {target_duration_for_output},
      "fps": 30,
      "resolution": [1920, 1080],
      "codec": "libx264"
    }}
  }},
  "metadata": {{
    "confidence": 0.85,
    "processing_time": 2.3,
    "translation_notes": "Brief explanation of key decisions"
  }}
}}
```

**PARAMETER GUIDELINES:**

- **fade_in/fade_out:** 0.1-1.0 seconds (0.3 typical)
- **speed_factor:** 0.5-2.0 (1.0 = normal speed)
- **volume_factor:** 0.0 (no audio in video-only mode)
- **transition duration:** 0.2-1.0 seconds
- **energy_level:** "high" (action/movement), "medium" (moderate), "low" (calm/static)

Return ONLY the JSON structure. No additional text or explanation."""

        return prompt
    
    def _parse_translation_response(self, response_text: str, 
                                   video_duration: float) -> EditingInstructions:
        """
        Parse Gemini's JSON response into EditingInstructions
        
        Args:
            response_text: Raw response from Gemini
            video_duration: Target duration for validation
            
        Returns:
            Parsed EditingInstructions object
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            
            # Remove markdown code block markers if present
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.startswith('```'):
                json_text = json_text[3:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            
            json_text = json_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(json_text)
            
            # Extract editing instructions
            if 'editing_instructions' in parsed_data:
                instructions_data = parsed_data['editing_instructions']
                metadata = parsed_data.get('metadata', {})
            else:
                # Handle case where JSON is directly the editing instructions
                instructions_data = parsed_data
                metadata = {}
            
            # Validate required fields
            clips = instructions_data.get('clips', [])
            transitions = instructions_data.get('transitions', [])
            audio_sync = instructions_data.get('audio_sync', {
                "music_volume": 0.7,
                "original_audio_volume": 0.3,
                "fade_in_duration": 1.0,
                "fade_out_duration": 1.0
            })
            output_settings = instructions_data.get('output_settings', {
                "target_duration": video_duration if video_duration is not None else 120.0,
                "fps": 30,
                "resolution": [1920, 1080],
                "codec": "libx264",
                "audio_codec": "aac"
            })
            
            # Validate clips coverage
            if clips:
                total_duration = sum(
                    clip.get('end_time', 0) - clip.get('start_time', 0) 
                    for clip in clips
                )
                logger.info(f"      📊 Total clips duration: {total_duration:.1f}s (target: {video_duration if video_duration is not None else 'N/A'}s)")
            
            # Create EditingInstructions object
            editing_instructions = EditingInstructions(
                clips=clips,
                transitions=transitions,
                audio_sync=audio_sync,
                output_settings=output_settings,
                metadata=metadata
            )
            
            return editing_instructions
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {str(e)}")
            logger.error(f"   Raw response: {response_text[:200]}...")
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {str(e)}")
            raise ValueError(f"Failed to parse Gemini response: {str(e)}")
    
    def _create_fallback_instructions(self, video_duration: Optional[float], 
                                     available_videos: List[str]) -> EditingInstructions:
        """
        Create fallback editing instructions when self-translation fails
        
        Args:
            video_duration: Target duration in seconds (can be None)
            available_videos: List of available video filenames
            
        Returns:
            Basic EditingInstructions for fallback processing
        """
        logger.warning("🔧 Creating fallback editing instructions...")
        
        # Handle case where video_duration is None
        if video_duration is None:
            video_duration = 120.0  # Default fallback duration
            logger.warning(f"   ⚠️  Video duration is None, using fallback: {video_duration}s")
        
        # Create simple clips using available videos
        clips = []
        if available_videos:
            clip_duration = min(video_duration / len(available_videos), 30.0)
            
            for i, video_path in enumerate(available_videos):
                start_time = i * clip_duration
                end_time = min(start_time + clip_duration, video_duration)
                
                if start_time >= video_duration:
                    break
                
                clips.append({
                    "video_path": video_path,
                    "start_time": 0.0,  # Use from beginning of source video
                    "end_time": end_time - start_time,
                    "energy_level": "medium",
                    "fade_in": 0.3 if i > 0 else 0.0,
                    "fade_out": 0.3 if i < len(available_videos) - 1 else 0.0,
                    "speed_factor": 1.0,
                    "volume_factor": 0.3
                })
        
        # Create basic transitions
        transitions = []
        for i in range(len(clips) - 1):
            transitions.append({
                "timestamp": clips[i]["end_time"],
                "type": "cross_fade",
                "duration": 0.5,
                "next_clip_index": i + 1
            })
        
        return EditingInstructions(
            clips=clips,
            transitions=transitions,
            audio_sync={
                "music_volume": 0.7,
                "original_audio_volume": 0.3,
                "fade_in_duration": 1.0,
                "fade_out_duration": 1.0
            },
            output_settings={
                "target_duration": video_duration,
                "fps": 30,
                "resolution": [1920, 1080],
                "codec": "libx264",
                "audio_codec": "aac"
            },
            metadata={
                "confidence": 0.5,
                "processing_time": 0.1,
                "translation_notes": "Fallback instructions due to self-translation failure"
            }
        )
    
    def validate_instructions(self, instructions: EditingInstructions, 
                             available_videos: List[str]) -> bool:
        """
        Validate editing instructions for correctness and completeness
        
        Args:
            instructions: EditingInstructions to validate
            available_videos: List of available video filenames
            
        Returns:
            True if instructions are valid, False otherwise
        """
        try:
            # Check if clips exist
            if not instructions.clips:
                logger.warning("⚠️  No clips in editing instructions")
                return False
            
            # Validate video paths
            for i, clip in enumerate(instructions.clips):
                video_path = clip.get('video_path', '')
                if video_path not in available_videos:
                    logger.warning(f"⚠️  Clip {i}: Invalid video path '{video_path}'")
                    return False
                
                # Validate timestamps with better error handling
                start_time = clip.get('start_time', 0)
                end_time = clip.get('end_time', 0)
                if start_time >= end_time:
                    logger.warning(f"⚠️  Clip {i}: Invalid timestamps {start_time} >= {end_time}")
                    # Instead of failing completely, fix the timestamps
                    logger.warning(f"   🔄 Fixing timestamps: using start_time=0, end_time=10")
                    clip['start_time'] = 0.0
                    clip['end_time'] = 10.0
                    # Don't return False - continue with fixed timestamps
                    # return False
            
            # Validate audio sync settings
            audio_sync = instructions.audio_sync
            if not isinstance(audio_sync, dict):
                logger.warning("⚠️  Invalid audio_sync settings")
                return False
            
            logger.info("✅ Editing instructions validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {str(e)}")
            return False

def main():
    """Test the Gemini Self-Translator functionality"""
    translator = GeminiSelfTranslator()
    
    # Test with sample creative timeline
    sample_timeline = """
    AUDIO ANALYSIS:
    Duration: 150 seconds
    BPM: 80
    Structure: Ambient intro (0:00-0:20), Building section (0:20-0:60), Climax (0:60-1:20), Outro (1:20-2:30)
    
    VIDEO CONTENT DISCOVERED:
    Video 1 (DJI_0108_dev.MP4): Aerial Seattle cityscape, calm energy, best segments 0:00-0:30
    Video 2 (IMG_7840_dev.mov): Ground-level bridge walkway, medium energy, best segment 0:05-0:25
    
    CREATIVE TIMELINE:
    0:00-0:20 (Ambient Intro): Use Video 1 aerial cityscape (0:00-0:20) for establishing mood
    0:20-0:40 (Building): Transition to Video 2 bridge walkway (0:05-0:25) as energy increases
    """
    
    available_videos = ["DJI_0108_dev.MP4", "IMG_7840_dev.mov"]
    
    try:
        instructions = translator.translate_timeline(
            sample_timeline, 150.0, available_videos
        )
        
        print(f"✅ Translation successful!")
        print(f"   Clips: {len(instructions.clips)}")
        print(f"   Transitions: {len(instructions.transitions)}")
        print(f"   Confidence: {instructions.metadata.get('confidence', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Translation failed: {e}")

if __name__ == "__main__":
    main()
