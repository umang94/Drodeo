#!/usr/bin/env python3
"""
Music-Synchronized Video Creation Script

Creates videos synchronized to input music files using downsampled videos
for faster development. Video duration matches the input audio duration.
"""

import sys
import os
from pathlib import Path
import glob

# Add src to path
sys.path.insert(0, 'src')

from editing.beat_sync_video_editor import BeatSyncVideoEditor
from utils.cache_manager import CacheManager
from core.video_processor import VideoProcessor

def get_audio_duration(audio_path):
    """Get duration of audio file."""
    import librosa
    try:
        y, sr = librosa.load(audio_path)
        duration = librosa.get_duration(y=y, sr=sr)
        return duration
    except Exception as e:
        print(f"   ⚠️  Could not get duration for {audio_path}: {e}")
        return None

def process_downsampled_videos():
    """Process downsampled videos to create cache."""
    print("🎬 Processing downsampled videos for cache...")
    
    # Get all downsampled video files
    video_patterns = [
        "input_dev/*.MP4",
        "input_dev/*.mp4", 
        "input_dev/*.mov"
    ]
    
    video_files = []
    for pattern in video_patterns:
        video_files.extend(glob.glob(pattern))
    
    if not video_files:
        print("❌ No downsampled videos found in input_dev/")
        return False
    
    print(f"   📊 Found {len(video_files)} downsampled videos")
    
    # Process videos to create cache
    processor = VideoProcessor()
    
    for i, video_file in enumerate(video_files, 1):
        print(f"   [{i}/{len(video_files)}] Processing {Path(video_file).name}...")
        try:
            clips, keyframes = processor.process_video(video_file, use_cache=True)
            print(f"      ✅ {len(clips)} clips, {len(keyframes)} keyframes")
        except Exception as e:
            print(f"      ❌ Error: {e}")
            continue
    
    return True

def main():
    """Create music-synchronized videos using downsampled videos."""
    print("🎵 Music-Synchronized Video Creator (Development Mode)")
    print("=" * 60)
    
    # Check for input music files
    music_dir = "music_input"
    if not os.path.exists(music_dir):
        print(f"❌ Music input directory not found: {music_dir}")
        return
    
    music_files = []
    for ext in ['*.mp3', '*.m4a', '*.wav', '*.flac']:
        music_files.extend(glob.glob(os.path.join(music_dir, ext)))
    
    if not music_files:
        print(f"❌ No music files found in {music_dir}/")
        return
    
    print(f"🎵 Found {len(music_files)} music file(s):")
    for music_file in music_files:
        duration = get_audio_duration(music_file)
        duration_str = f"{duration:.1f}s" if duration else "unknown"
        print(f"   🎶 {Path(music_file).name} ({duration_str})")
    
    # Check if we have cached clips from downsampled videos
    cache_manager = CacheManager()
    
    # Get all downsampled video files to check cache
    video_patterns = [
        "input_dev/*.MP4",
        "input_dev/*.mp4", 
        "input_dev/*.mov"
    ]
    
    video_files = []
    for pattern in video_patterns:
        video_files.extend(glob.glob(pattern))
    
    # Check cache availability
    cached_videos = []
    total_clips = 0
    
    for video_file in video_files:
        if cache_manager.has_cache(video_file):
            cached_result = cache_manager.load_cache(video_file)
            if cached_result and len(cached_result) >= 4:
                clips, _, _, _ = cached_result[:4]
                cached_videos.append(video_file)
                total_clips += len(clips)
    
    if not cached_videos:
        print(f"\n🔄 No cached clips found. Processing downsampled videos first...")
        if not process_downsampled_videos():
            print("❌ Failed to process downsampled videos")
            return
        
        # Recheck cache after processing
        cached_videos = []
        total_clips = 0
        for video_file in video_files:
            if cache_manager.has_cache(video_file):
                cached_result = cache_manager.load_cache(video_file)
                if cached_result and len(cached_result) >= 4:
                    clips, _, _, _ = cached_result[:4]
                    cached_videos.append(video_file)
                    total_clips += len(clips)
    
    print(f"\n📊 Cache Summary:")
    print(f"   Available videos: {len(cached_videos)}")
    print(f"   Total cached clips: {total_clips}")
    
    if total_clips == 0:
        print("❌ No clips available for video creation")
        return
    
    # Create beat-synchronized video editor
    print(f"\n🎬 Initializing beat-synchronized video editor...")
    editor = BeatSyncVideoEditor()
    
    # Process each music file
    for music_file in music_files:
        print(f"\n🎵 Processing: {Path(music_file).name}")
        
        # Get audio duration
        audio_duration = get_audio_duration(music_file)
        if not audio_duration:
            print(f"   ⚠️  Skipping due to audio analysis failure")
            continue
        
        target_duration = int(audio_duration)
        print(f"   ⏱️  Target duration: {target_duration}s (matching audio)")
        
        try:
            # Create beat-synced video with specific music
            output_path = editor.create_beat_synced_from_cache_with_music(
                video_files=cached_videos,
                music_path=music_file,
                target_duration=target_duration
            )
            
            # Get video info
            video_info = editor.get_video_info(output_path)
            
            print(f"   🎉 Video created successfully!")
            print(f"   📊 Output Details:")
            print(f"      File: {Path(output_path).name}")
            print(f"      Duration: {video_info.get('duration', 0):.1f}s")
            print(f"      Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
            print(f"      Size: {video_info.get('size_mb', 0):.1f}MB")
            print(f"      Location: {output_path}")
            
        except Exception as e:
            print(f"   ❌ Video creation failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n🎉 Music-synchronized video creation complete!")

if __name__ == "__main__":
    main()
