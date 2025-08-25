#!/usr/bin/env python3
"""
Beat-Synchronized Video Creation Script

Creates a new 45-second video with calm/mellow music using cached clips
from the previous video generation, with beat-synchronized transitions.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from editing.beat_sync_video_editor import BeatSyncVideoEditor
from utils.cache_manager import CacheManager

def main():
    """Create beat-synchronized video with calm/mellow music."""
    print("🎵 Beat-Synchronized Video Creator")
    print("=" * 50)
    
    # Video files that were used in the previous 45-second generation
    video_files = [
        "input/DJI_0108.MP4",
        "input/DJI_0110.MP4", 
        "input/DJI_0121.MP4",
        "input/DJI_0131.mp4",
        "input/DJI_0152.MP4",
        "input/DJI_0154.MP4"
    ]
    
    # Check cache availability
    print("🔍 Checking cache availability...")
    cache_manager = CacheManager()
    
    available_videos = []
    total_clips = 0
    
    for video_file in video_files:
        if os.path.exists(video_file) and cache_manager.has_cache(video_file):
            cached_result = cache_manager.load_cache(video_file)
            if cached_result and len(cached_result) >= 4:
                clips, _, _, _ = cached_result[:4]
                available_videos.append(video_file)
                total_clips += len(clips)
                print(f"   ✅ {Path(video_file).name}: {len(clips)} clips cached")
            else:
                print(f"   ⚠️  {Path(video_file).name}: Invalid cache")
        else:
            print(f"   ❌ {Path(video_file).name}: No cache or file missing")
    
    if not available_videos:
        print("❌ No cached clips available. Please run video processing first.")
        return
    
    print(f"\n📊 Summary:")
    print(f"   Available videos: {len(available_videos)}")
    print(f"   Total cached clips: {total_clips}")
    
    # Create beat-synchronized video editor
    print(f"\n🎬 Initializing beat-synchronized video editor...")
    editor = BeatSyncVideoEditor()
    
    try:
        # Create beat-synced video with calm/mellow theme
        output_path = editor.create_beat_synced_from_cache(
            video_files=available_videos,
            theme="calm",
            target_duration=45
        )
        
        # Get video info
        video_info = editor.get_video_info(output_path)
        
        print(f"\n🎉 Beat-synchronized video creation complete!")
        print(f"📊 Output Details:")
        print(f"   File: {Path(output_path).name}")
        print(f"   Duration: {video_info.get('duration', 0):.1f}s")
        print(f"   Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
        print(f"   Size: {video_info.get('size_mb', 0):.1f}MB")
        print(f"   Location: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Beat-synchronized video creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
