"""
Two-Step Gemini Pipeline integration for Drodeo.
Provides reusable functions for the complete two-step pipeline execution.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Optional

# Import core components
from src.core.gemini_multimodal_analyzer import GeminiMultimodalAnalyzer
from src.core.gemini_self_translator import GeminiSelfTranslator
from src.editing.video_editor import VideoEditor

def run_two_step_pipeline(fast_test: bool = False, music_path: Optional[str] = None, input_dir: Optional[str] = None) -> bool:
    """
    Run the complete two-step Gemini pipeline with validation and error handling.
    
    Args:
        fast_test: If True, limits processing for faster testing
        music_path: Optional specific music file to process
        input_dir: Optional custom directory containing video files
    
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    print("🚀 Starting Two-Step Gemini Pipeline (Audio-Free)")
    print("=" * 50)
    
    # Get music file to process (optional for audio-free mode)
    # Always attempt to find music files, auto-discover if no specific path provided
    music_file = _get_music_file(music_path)
    
    # Get available development videos
    video_files = _get_development_videos(fast_test, input_dir)
    if not video_files:
        return False
    
    try:
        # Step 1: Video-Only Multimodal Analysis
        print("\n📊 Step 1: Video-Only Multimodal Analysis")
        analyzer = GeminiMultimodalAnalyzer()
        
        start_time = time.time()
        multimodal_result = analyzer.analyze_batch(
            video_paths=video_files,
            test_name=f"Video Analysis - {len(video_files)} videos"
        )
        
        step1_time = time.time() - start_time
        print(f"   ✅ Completed in {step1_time:.1f}s")
        print(f"   📊 Total duration: {multimodal_result.total_video_duration:.1f}s")
        print(f"   📈 Sync confidence: {multimodal_result.sync_confidence:.2f}")
        if multimodal_result.udio_prompt:
            print(f"   🎵 UDIO prompt: {multimodal_result.udio_prompt}")
        
        # Step 2: Self-Translation
        print("\n🤖 Step 2: Self-Translation")
        translator = GeminiSelfTranslator()
        
        # Get video durations for validation
        video_durations = _get_video_durations(video_files)
        available_video_names = [os.path.basename(path) for path in video_files]
        
        start_time = time.time()
        editing_instructions = translator.translate_timeline(
            gemini_reasoning=multimodal_result.gemini_reasoning,
            video_duration=multimodal_result.total_video_duration,
            available_videos=available_video_names,
            video_durations=video_durations
        )
        
        step2_time = time.time() - start_time
        print(f"   ✅ Completed in {step2_time:.1f}s")
        print(f"   📊 Clips: {len(editing_instructions.clips)}")
        print(f"   🔀 Transitions: {len(editing_instructions.transitions)}")
        print(f"   📈 Confidence: {editing_instructions.metadata.get('confidence', 'N/A')}")
        
        # Validate instructions
        if not translator.validate_instructions(editing_instructions, available_video_names):
            print("❌ Editing instructions validation failed")
            return False
        print("   ✅ Instructions validation passed")
        
        # Step 3: Video Creation
        print("\n🎬 Step 3: Video Creation")
        editor = VideoEditor()
        
        # Update video paths in instructions to full paths
        for clip_data in editing_instructions.clips:
            video_name = clip_data['video_path']
            for full_path in video_files:
                if os.path.basename(full_path) == video_name:
                    clip_data['video_path'] = full_path
                    break
        
        start_time = time.time()
        
        # Handle audio-free mode (music_file might be None)
        if music_file:
            output_path = editor.create_from_instructions(
                instructions=editing_instructions,
                music_name=Path(music_file).stem,
                music_path=music_file
            )
        else:
            # Create video without music (silent video)
            output_path = editor.create_from_instructions(
                instructions=editing_instructions,
                music_name="silent_video",
                music_path=None
            )
            print("   🎵 No music file provided - creating silent video")
        
        step3_time = time.time() - start_time
        print(f"   ✅ Completed in {step3_time:.1f}s")
        
        # Verify output
        if not os.path.exists(output_path):
            print(f"❌ Output file not found: {output_path}")
            return False
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   📁 Output: {os.path.basename(output_path)} ({file_size:.1f} MB)")
        
        # Summary
        total_time = step1_time + step2_time + step3_time
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"   ⏱️  Total time: {total_time:.1f}s")
        print(f"   📊 Analysis: {step1_time:.1f}s")
        print(f"   🤖 Translation: {step2_time:.1f}s")
        print(f"   🎬 Creation: {step3_time:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def _get_music_file(specific_music_path: Optional[str] = None) -> Optional[str]:
    """Get music file to process, with fallback to auto-discovery."""
    if specific_music_path and os.path.exists(specific_music_path):
        return specific_music_path
    
    # Auto-discover music files
    music_dir = Path("music")
    if not music_dir.exists():
        print("❌ music/ directory not found")
        return None
    
    music_extensions = ['.mp3', '.m4a', '.wav', '.flac', '.ogg', '.MP3', '.M4A', '.WAV']
    music_files = []
    
    for file_path in music_dir.iterdir():
        if file_path.is_file() and file_path.suffix in music_extensions:
            music_files.append(str(file_path))
    
    if not music_files:
        print("❌ No music files found in music/ directory")
        return None
    
    # Use the first available music file
    return music_files[0]

def _get_development_videos(fast_test: bool = False, input_dir: Optional[str] = None) -> List[str]:
    """Get development videos for processing, with fast-test option."""
    if input_dir and input_dir != "input":
        # For custom directories, look in input_dev/{dirname}/
        source_path = Path(input_dir)
        source_dir_name = source_path.name
        input_dev_dir = Path("input_dev") / source_dir_name
    else:
        # For default "input" directory, use input_dev directly
        input_dev_dir = Path("input_dev")
    
    if not input_dev_dir.exists():
        print(f"❌ Development video directory not found: {input_dev_dir}")
        return []
    
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(input_dev_dir.glob(f"*{ext}"))
    
    video_files = [str(f) for f in video_files if f.is_file()]
    
    if not video_files:
        print("❌ No development videos found in input_dev/")
        return []
    
    # Sort for consistent ordering
    video_files.sort()
    
    if fast_test:
        # Limit to 3 videos for fast testing
        limited_videos = video_files[:3]
        print(f"   🚀 Fast test mode: Using {len(limited_videos)} videos")
        return limited_videos
    
    # Limit to Gemini's maximum (10 videos) for normal operation
    if len(video_files) > 10:
        print(f"   ⚠️  Found {len(video_files)} videos, limiting to 10")
        return video_files[:10]
    
    print(f"   ✅ Found {len(video_files)} development videos")
    return video_files

def _get_video_durations(video_paths: List[str]) -> dict:
    """Get durations for all video files."""
    durations = {}
    
    for video_path in video_paths:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            durations[os.path.basename(video_path)] = clip.duration
            clip.close()
        except Exception:
            # Fallback duration if we can't get the actual duration
            durations[os.path.basename(video_path)] = 60.0
    
    return durations

if __name__ == "__main__":
    # Test the pipeline
    success = run_two_step_pipeline(fast_test=True)
    print(f"\nPipeline test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
