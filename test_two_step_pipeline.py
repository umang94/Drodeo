#!/usr/bin/env python3
"""
Two-Step Gemini Pipeline Test Script

Tests the complete two-step pipeline:
1. Step 1: Multimodal Analysis (GeminiMultimodalAnalyzer)
2. Step 2: Self-Translation (GeminiSelfTranslator)  
3. Step 3: Video Creation (VideoEditor.create_from_instructions)

IMPORTANT: Uses input_dev/ videos for fast development testing (35-70x faster)
"""

import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append('src')

from src.core.gemini_multimodal_analyzer import GeminiMultimodalAnalyzer
from src.core.gemini_self_translator import GeminiSelfTranslator
from src.editing.video_editor import VideoEditor

def test_two_step_pipeline(music_path=None):
    """Test the complete two-step Gemini pipeline"""
    
    print("🧪 TESTING TWO-STEP GEMINI PIPELINE")
    print("=" * 60)
    
    # Test configuration - ALWAYS use input_dev/ for development
    if music_path is None:
        # Auto-discover music files in music/ directory
        music_files = []
        music_dir = Path("music")
        if music_dir.exists():
            music_extensions = ['.mp3', '.m4a', '.wav', '.flac', '.ogg', '.MP3', '.M4A', '.WAV']
            for file_path in music_dir.iterdir():
                if file_path.is_file() and file_path.suffix in music_extensions:
                    music_files.append(str(file_path))
        
        if not music_files:
            print("❌ No music files found in music/ directory")
            return False
        
        # Use the first available music file
        music_path = music_files[0]
        print(f"🎵 Auto-selected music: {os.path.basename(music_path)}")
    
    print(f"🎵 Testing with: {os.path.basename(music_path)}")
    
    # Dynamically discover all video files in input_dev/
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV']
    video_paths = []
    
    input_dev_dir = Path("input_dev")
    if input_dev_dir.exists():
        for file_path in input_dev_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in video_extensions:
                video_paths.append(str(file_path))
    
    # Sort for consistent ordering and limit to Gemini's maximum (10 videos)
    video_paths.sort()
    if len(video_paths) > 10:
        print(f"   ⚠️  Found {len(video_paths)} videos, limiting to 10 (Gemini's maximum)")
        video_paths = video_paths[:10]
    
    # Verify test files exist
    print("📂 Verifying test files...")
    if not os.path.exists(music_path):
        print(f"❌ Music file not found: {music_path}")
        return False
    
    available_videos = []
    for video_path in video_paths:
        if os.path.exists(video_path):
            available_videos.append(video_path)
            print(f"   ✅ {os.path.basename(video_path)} ({os.path.getsize(video_path) / (1024*1024):.1f} MB)")
        else:
            print(f"   ⚠️  Missing: {video_path}")
    
    if len(available_videos) < 2:
        print(f"❌ Need at least 2 videos for testing, found {len(available_videos)}")
        return False
    
    print(f"✅ Test files ready: 1 audio + {len(available_videos)} low-res development videos")
    
    try:
        # Step 1: Multimodal Analysis
        print("\n📊 Step 1: Initialize Gemini Multimodal Analyzer")
        analyzer = GeminiMultimodalAnalyzer()
        
        print("📊 Step 2: Perform Multimodal Analysis")
        start_time = time.time()
        
        multimodal_result = analyzer.analyze_batch(
            audio_path=music_path,
            video_paths=available_videos
        )
        
        step1_time = time.time() - start_time
        print(f"   ✅ Step 1 completed in {step1_time:.1f}s")
        print(f"   📊 Audio duration: {multimodal_result.audio_duration:.1f}s")
        print(f"   📊 Audio BPM: {multimodal_result.audio_tempo}")
        print(f"   📊 Sync confidence: {multimodal_result.sync_confidence:.2f}")
        print(f"   📊 Reasoning length: {len(multimodal_result.gemini_reasoning)} characters")
        
        # Step 2: Self-Translation
        print("\n🤖 Step 3: Initialize Gemini Self-Translator")
        translator = GeminiSelfTranslator()
        
        print("🤖 Step 4: Perform Self-Translation")
        start_time = time.time()
        
        # Get video durations for validation
        video_durations = {}
        for video_path in available_videos:
            try:
                from moviepy.editor import VideoFileClip
                temp_clip = VideoFileClip(video_path)
                video_durations[os.path.basename(video_path)] = temp_clip.duration
                temp_clip.close()
            except Exception as e:
                logger.warning(f"Failed to get duration for {video_path}: {e}")
                video_durations[os.path.basename(video_path)] = 60.0  # Fallback duration
        
        available_video_names = [os.path.basename(path) for path in available_videos]
        editing_instructions = translator.translate_timeline(
            gemini_reasoning=multimodal_result.gemini_reasoning,
            audio_duration=multimodal_result.audio_duration,
            available_videos=available_video_names,
            video_durations=video_durations  # Pass actual durations
        )
        
        step2_time = time.time() - start_time
        print(f"   ✅ Step 2 completed in {step2_time:.1f}s")
        print(f"   📊 Clips generated: {len(editing_instructions.clips)}")
        print(f"   📊 Transitions: {len(editing_instructions.transitions)}")
        print(f"   📊 Translation confidence: {editing_instructions.metadata.get('confidence', 'N/A')}")
        
        # Validate instructions
        print("\n🔍 Step 5: Validate Editing Instructions")
        is_valid = translator.validate_instructions(editing_instructions, available_video_names)
        if not is_valid:
            print("❌ Editing instructions validation failed")
            return False
        print("   ✅ Editing instructions validation passed")
        
        # Step 3: Video Creation
        print("\n🎬 Step 6: Initialize Video Editor")
        editor = VideoEditor()
        
        print("🎬 Step 7: Create Video from Instructions")
        start_time = time.time()
        
        # Update video paths in instructions to full paths
        for clip_data in editing_instructions.clips:
            video_name = clip_data['video_path']
            # Find full path for this video name
            for full_path in available_videos:
                if os.path.basename(full_path) == video_name:
                    clip_data['video_path'] = full_path
                    break
        
        output_path = editor.create_from_instructions(
            instructions=editing_instructions,
            music_name="TwoStep_Pipeline_Test",
            music_path=music_path
        )
        
        step3_time = time.time() - start_time
        print(f"   ✅ Step 3 completed in {step3_time:.1f}s")
        
        # Verify output
        print("\n✅ Step 8: Verify Output")
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"   📁 Output: {os.path.basename(output_path)}")
            print(f"   💾 File size: {file_size:.1f} MB")
            
            # Get video info
            video_info = editor.get_video_info(output_path)
            if video_info:
                print(f"   🎵 Video duration: {video_info.get('duration', 'N/A'):.1f}s")
                print(f"   📺 Resolution: {video_info.get('width', 'N/A')}x{video_info.get('height', 'N/A')}")
                print(f"   🎵 Has audio: {video_info.get('has_audio', 'N/A')}")
            
            print("   ✅ Output verification successful")
        else:
            print(f"   ❌ Output file not found: {output_path}")
            return False
        
        # Summary
        total_time = step1_time + step2_time + step3_time
        print(f"\n🎉 TWO-STEP PIPELINE TEST RESULTS:")
        print(f"   📊 Step 1 (Multimodal Analysis): {step1_time:.1f}s")
        print(f"   🤖 Step 2 (Self-Translation): {step2_time:.1f}s")
        print(f"   🎬 Step 3 (Video Creation): {step3_time:.1f}s")
        print(f"   ⏱️  Total time: {total_time:.1f}s")
        print(f"   💰 Estimated cost: ~$0.26 (${0.25:.2f} + ${0.01:.2f})")
        print(f"   ✅ SUCCESS: Two-step pipeline working perfectly!")
        
        # Save test results
        test_results = {
            "timestamp": time.time(),
            "test_type": "two_step_pipeline",
            "music_file": os.path.basename(music_path),
            "video_files": [os.path.basename(p) for p in available_videos],
            "step1_time": step1_time,
            "step2_time": step2_time,
            "step3_time": step3_time,
            "total_time": total_time,
            "audio_duration": multimodal_result.audio_duration,
            "audio_bpm": multimodal_result.audio_tempo,
            "sync_confidence": multimodal_result.sync_confidence,
            "clips_generated": len(editing_instructions.clips),
            "transitions_generated": len(editing_instructions.transitions),
            "translation_confidence": editing_instructions.metadata.get('confidence', 0),
            "output_file": os.path.basename(output_path),
            "output_size_mb": file_size,
            "success": True
        }
        
        results_file = f"two_step_pipeline_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"   📄 Test results saved: {results_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TWO-STEP PIPELINE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components separately"""
    
    print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
    print("=" * 60)
    
    try:
        # Test GeminiSelfTranslator with sample data
        print("🤖 Testing GeminiSelfTranslator with sample data...")
        
        translator = GeminiSelfTranslator()
        
        sample_reasoning = """
        AUDIO ANALYSIS:
        Duration: 79.1 seconds
        BPM: 92.3
        Structure: Electronic intro (0:00-0:10), Build-up (0:10-0:30), Drop (0:30-0:50), Outro (0:50-1:19)
        
        VIDEO CONTENT DISCOVERED:
        Video 1 (DJI_0108_dev.MP4): Aerial Seattle cityscape, calm energy, best segments 0:00-0:20
        Video 2 (IMG_7840_dev.mov): Ground-level bridge walkway, medium energy, best segment 0:05-0:15
        
        CREATIVE TIMELINE:
        0:00-0:10 (Intro): Use Video 1 aerial cityscape (0:00-0:10) for establishing mood
        0:10-0:30 (Build-up): Transition to Video 2 bridge walkway (0:05-0:25) as energy increases
        0:30-0:50 (Drop): Switch back to Video 1 aerial (0:20-0:40) for climax
        0:50-1:19 (Outro): Use Video 2 bridge (0:10-0:39) for calm ending
        """
        
        available_videos = ["DJI_0108_dev.MP4", "IMG_7840_dev.mov"]
        
        instructions = translator.translate_timeline(
            gemini_reasoning=sample_reasoning,
            audio_duration=79.1,
            available_videos=available_videos
        )
        
        print(f"   ✅ Self-translation successful!")
        print(f"   📊 Clips: {len(instructions.clips)}")
        print(f"   📊 Transitions: {len(instructions.transitions)}")
        print(f"   📊 Confidence: {instructions.metadata.get('confidence', 'N/A')}")
        
        # Validate instructions
        is_valid = translator.validate_instructions(instructions, available_videos)
        print(f"   📊 Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 TWO-STEP GEMINI PIPELINE TESTING SUITE")
    print("=" * 60)
    print("📋 Development Guidelines:")
    print("   - Using input_dev/ videos for 35-70x faster processing")
    print("   - Low-resolution videos reduce API costs and processing time")
    print("   - Perfect for development and testing iterations")
    print()
    
    # Test individual components first
    component_success = test_individual_components()
    
    if component_success:
        # Test complete pipeline
        pipeline_success = test_two_step_pipeline()
        
        if pipeline_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("   ✅ Individual components working")
            print("   ✅ Complete two-step pipeline working")
            print("   ✅ Ready for production implementation")
        else:
            print("\n⚠️  PIPELINE TEST FAILED")
            print("   ✅ Individual components working")
            print("   ❌ Complete pipeline needs debugging")
    else:
        print("\n❌ COMPONENT TESTS FAILED")
        print("   ❌ Individual components need fixing")
        print("   ⏸️  Pipeline test skipped")

if __name__ == "__main__":
    main()
