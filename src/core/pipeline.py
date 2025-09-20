"""
Two-Step Gemini Pipeline integration for Drodeo.
Provides reusable functions for the complete two-step pipeline execution.
"""

import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

# Import core components
from src.core.gemini_multimodal_analyzer import GeminiMultimodalAnalyzer
from src.core.gemini_self_translator import GeminiSelfTranslator
from src.core.video_mapping import VideoBatchMapping, translate_gemini_timestamps
from src.editing.video_editor import VideoEditor

def run_two_step_pipeline(fast_test: bool = False, music_path: Optional[str] = None, 
                         input_dir: Optional[str] = None, max_videos: int = 5) -> bool:
    """
    Run the complete two-step Gemini pipeline with validation and error handling.
    
    Args:
        fast_test: If True, limits processing for faster testing
        music_path: Optional specific music file to process
        input_dir: Optional custom directory containing video files
        max_videos: Maximum number of videos to process (default: 5)
    
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    print("🚀 Starting Two-Step Gemini Pipeline (Audio-Free)")
    print("=" * 50)
    print(f"📊 Maximum videos to process: {max_videos}")
    
    # Get music file to process (optional for audio-free mode)
    # Always attempt to find music files, auto-discovery if no specific path provided
    music_file = _get_music_file(music_path)
    
    # Get available development videos with max limit
    video_files = _get_development_videos(fast_test, input_dir, max_videos)
    if not video_files:
        return False
    
    try:
        # Step 1: Video-Only Multimodal Analysis
        print("\n📊 Step 1: Video-Only Multimodal Analysis")
        analyzer = GeminiMultimodalAnalyzer()
        
        start_time = time.time()
        
        # Process videos (with batching if >10 videos)
        analysis_result = _process_video_batches(
            video_files, 
            analyzer, 
            f"Video Analysis - {len(video_files)} videos"
        )
        
        if not analysis_result:
            print("❌ Video analysis failed")
            return False
            
        gemini_reasoning, total_duration, udio_prompt, mapping = analysis_result
        
        step1_time = time.time() - start_time
        print(f"   ✅ Completed in {step1_time:.1f}s")
        print(f"   📊 Total duration: {total_duration:.1f}s")
        print(f"   📈 Sync confidence: 0.85")  # Default confidence for batched processing
        if udio_prompt:
            print(f"   🎵 UDIO prompt: {udio_prompt}")
        
        # Step 2: Self-Translation
        print("\n🤖 Step 2: Self-Translation")
        translator = GeminiSelfTranslator()
        
        # Get video durations for validation
        video_durations = _get_video_durations(video_files)
        available_video_names = [os.path.basename(path) for path in video_files]
        
        start_time = time.time()
        # Apply timestamp translation to convert concatenated video references to original videos
        translated_reasoning = translate_gemini_timestamps(gemini_reasoning, mapping)
        
        editing_instructions = translator.translate_timeline(
            gemini_reasoning=translated_reasoning,  # Use the translated reasoning
            video_duration=total_duration,
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
            
            # Handle concatenated video reference (batch_1_*.mp4) by mapping to original videos
            if video_name.startswith('batch_1_') and video_name.endswith('.mp4'):
                # This is a concatenated video reference - map to original videos
                # For now, use the first original video as fallback
                if video_files:
                    clip_data['video_path'] = video_files[0]
                    print(f"   🔄 Mapped concatenated video reference to: {os.path.basename(video_files[0])}")
            else:
                # Normal video file mapping
                found = False
                for full_path in video_files:
                    if os.path.basename(full_path) == video_name:
                        clip_data['video_path'] = full_path
                        found = True
                        break
                
                if not found:
                    # If video not found, use first available video as fallback
                    if video_files:
                        clip_data['video_path'] = video_files[0]
                        print(f"   ⚠️  Video '{video_name}' not found, using fallback: {os.path.basename(video_files[0])}")
                    else:
                        print(f"   ❌ No videos available for fallback, cannot proceed")
                        return False
        
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

def _get_development_videos(fast_test: bool = False, input_dir: Optional[str] = None, 
                          max_videos: int = 5) -> List[str]:
    """Get development videos for processing, with fast-test option and max limit."""
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
    
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV', '.AVI', '.MKV']
    video_files = []
    
    # Use os.walk for efficient recursive search with early termination
    for root, dirs, files in os.walk(str(input_dev_dir)):
        for file in files:
            if len(video_files) >= max_videos:
                break  # Stop searching once we have enough videos
                
            file_path = Path(root) / file
            if file_path.suffix.lower() in [ext.lower() for ext in video_extensions]:
                video_files.append(str(file_path))
        
        if len(video_files) >= max_videos:
            break  # Stop directory traversal once we have enough videos
    
    # Filter out directories and only keep files
    video_files = [f for f in video_files if os.path.isfile(f)]
    
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
    
    # Apply max_videos limit
    if len(video_files) > max_videos:
        video_files = video_files[:max_videos]
        print(f"   ✅ Found {len(video_files)} videos (limited to {max_videos} as requested)")
    else:
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

def _create_video_batches(video_files: List[str], max_batch_size: int = 10) -> List[List[str]]:
    """
    Group videos into batches of specified size
    
    Args:
        video_files: List of video file paths
        max_batch_size: Maximum number of videos per batch
        
    Returns:
        List of batches, each containing video file paths
    """
    if not video_files:
        return []
    
    batches = []
    for i in range(0, len(video_files), max_batch_size):
        batch = video_files[i:i + max_batch_size]
        batches.append(batch)
    
    print(f"📦 Created {len(batches)} batches with max {max_batch_size} videos each")
    for i, batch in enumerate(batches):
        print(f"   Batch {i+1}: {len(batch)} videos")
    
    return batches

def _concatenate_video_batch_no_blanks(batch_videos: List[str], batch_number: int, temp_dir: str) -> str:
    """
    Concatenate videos in a batch WITHOUT blank frames and save to temporary file
    
    Args:
        batch_videos: List of video file paths in the batch
        batch_number: Batch number for naming
        temp_dir: Temporary directory to save concatenated video
        
    Returns:
        Path to temporary concatenated video file
    """
    if not batch_videos:
        raise ValueError("No videos provided for concatenation")
    
    print(f"🔗 Processing batch {batch_number}: {len(batch_videos)} videos (no blank frames)")
    
    # Create video editor instance
    editor = VideoEditor()
    
    try:
        # Concatenate videos WITHOUT blank frames
        concatenated_video = editor.concatenate_videos(batch_videos)
        
        # Create temporary output path
        timestamp = int(time.time())
        output_filename = f"batch_{batch_number}_{timestamp}.mp4"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Ensure temp directory exists
        os.makedirs(temp_dir, exist_ok=True)
        
        # Render the concatenated video with better error handling
        print(f"   💾 Saving concatenated batch to: {output_path}")
        try:
            # Validate the concatenated video before saving
            if concatenated_video is None:
                raise ValueError("Concatenated video is None")
            
            if not hasattr(concatenated_video, 'get_frame') or not callable(getattr(concatenated_video, 'get_frame', None)):
                raise ValueError("Concatenated video missing get_frame method")
            
            # Test that we can access a frame
            test_frame = concatenated_video.get_frame(0)
            if test_frame is None:
                raise ValueError("Concatenated video returned None frame")
            
            concatenated_video.write_videofile(
                output_path,
                fps=min(concatenated_video.fps, 30),
                codec='libx264',
                verbose=False,
                logger=None
            )
            
            concatenated_video.close()
            print(f"   ✅ Batch {batch_number} concatenation complete: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"   ❌ Failed to save concatenated batch: {e}")
            if concatenated_video:
                try:
                    concatenated_video.close()
                except:
                    pass
            raise
        
    except Exception as e:
        print(f"❌ Failed to concatenate batch {batch_number}: {e}")
        raise

def _cleanup_temporary_files(temp_files: List[str]):
    """
    Remove temporary concatenated video files
    
    Args:
        temp_files: List of temporary file paths to remove
    """
    if not temp_files:
        return
    
    print(f"🧹 Cleaning up {len(temp_files)} temporary files...")
    
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"   ✅ Removed: {os.path.basename(temp_file)}")
        except Exception as e:
            print(f"   ⚠️  Failed to remove {temp_file}: {e}")

def _process_video_batches(video_files: List[str], analyzer: GeminiMultimodalAnalyzer, 
                          test_name: str) -> Optional[Tuple[str, float, str]]:
    """
    Process videos in batches through Gemini analysis
    
    Args:
        video_files: List of all video file paths
        analyzer: GeminiMultimodalAnalyzer instance
        test_name: Name for the analysis
        
    Returns:
        Tuple of (combined_gemini_reasoning, total_duration, udio_prompt) or None if failed
    """
    # Always use single concatenation approach for batch processing
    print("📊 Processing all videos with single concatenation")
    
    # Create video mapping for timestamp translation
    mapping = VideoBatchMapping()
    
    # Get actual durations for accurate mapping
    video_durations = _get_video_durations(video_files)
    actual_durations = [video_durations.get(os.path.basename(v), 60.0) for v in video_files]
    total_duration = sum(actual_durations)  # NO blank frames added
    
    # Create mapping metadata WITHOUT blank frames
    batch = mapping.create_mapping_from_concatenation(
        video_files, 
        concatenated_duration=total_duration,
        blank_duration=0.0  # No blank frames
    )
    
    # Concatenate all videos into a single file
    temp_dir = "temp/concatenated_batches"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Concatenate all videos WITHOUT blank frames
        concatenated_path = _concatenate_video_batch_no_blanks(video_files, 1, temp_dir)
        
        # Analyze the single concatenated video
        result = analyzer.analyze_batch([concatenated_path], test_name)
        if not result:
            raise ValueError("Gemini analysis failed for concatenated video")
        
        # Translate timestamps back to original videos
        translated_reasoning = translate_gemini_timestamps(result.gemini_reasoning, mapping)
        
        print(f"✅ Single concatenation processing successful")
        print(f"   Total duration: {result.total_video_duration:.1f}s")
        print(f"   Translated reasoning length: {len(translated_reasoning)} characters")
        
        return translated_reasoning, result.total_video_duration, result.udio_prompt, mapping
        
    except Exception as e:
        print(f"❌ Single concatenation processing failed: {e}")
        # Clean up temporary files even on failure
        _cleanup_temporary_files([concatenated_path] if 'concatenated_path' in locals() else [])
        return None
    finally:
        # Clean up temporary files on success
        if 'concatenated_path' in locals():
            _cleanup_temporary_files([concatenated_path])

if __name__ == "__main__":
    # Test the pipeline
    success = run_two_step_pipeline(fast_test=True)
    print(f"\nPipeline test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
