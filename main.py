#!/usr/bin/env python3
"""
Drone Video Generator MVP - Command Line Interface
A simple tool to process drone videos and create themed outputs.
"""

import argparse
import sys
import os
from pathlib import Path
from tqdm import tqdm

def validate_video_file(file_path):
    """Check if file exists and is a video file."""
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv']
    if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
        return False, f"Unsupported file format. Supported: {', '.join(valid_extensions)}"
    
    return True, "Valid video file"

def process_videos_for_themes(video_paths, use_cache=True):
    """Process multiple videos and assign clips to themes."""
    from video_processor import VideoProcessor
    from clip_selector import select_clips_for_themes
    from cache_manager import CacheManager
    
    processor = VideoProcessor()
    cache_manager = CacheManager() if use_cache else None
    
    all_clips = []
    ai_analyses_by_video = {}
    
    # Process each video
    for i, video_path in enumerate(video_paths, 1):
        print(f"\n[{i}/{len(video_paths)}] Processing {Path(video_path).name}")
        
        try:
            clips, keyframes = processor.process_video(video_path, use_cache=use_cache)
            all_clips.extend(clips)
            
            # Get AI analyses from cache if available
            if cache_manager and cache_manager.has_cache(video_path):
                cached_result = cache_manager.load_cache(video_path)
                if cached_result:
                    # Handle both old (4 elements) and new (5 elements) cache formats
                    if len(cached_result) >= 5:  # New format with AI analyses
                        ai_analyses_by_video[video_path] = cached_result[4]
                    elif len(cached_result) == 4:  # Old format without AI analyses
                        ai_analyses_by_video[video_path] = []  # No AI analyses available
            
            print(f"✓ Completed: {Path(video_path).name} - {len(clips)} clips found")
            
        except Exception as e:
            print(f"❌ Error processing {video_path}: {e}")
            continue
    
    if not all_clips:
        print("❌ No clips found in any videos!")
        return {}
    
    # Assign clips to themes
    print(f"\n🎨 Assigning {len(all_clips)} total clips to themes...")
    theme_pools = select_clips_for_themes(all_clips, ai_analyses_by_video)
    
    return theme_pools

def main():
    parser = argparse.ArgumentParser(
        description="Generate themed videos from drone footage using AI-powered clip detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py video1.mp4 video2.mp4
  python main.py /path/to/drone/videos/*.mp4
  python main.py --help
        """
    )
    
    parser.add_argument(
        'videos',
        nargs='*',
        help='One or more drone video files to process'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Directory to save generated videos (default: output)'
    )
    
    parser.add_argument(
        '--themes',
        nargs='*',
        choices=['happy', 'exciting', 'peaceful', 'adventure', 'cinematic'],
        default=['happy', 'exciting', 'peaceful', 'adventure', 'cinematic'],
        help='Themes to generate (default: all themes)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=180,
        help='Target duration for each themed video in seconds (default: 180)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate inputs without processing'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (force reprocessing)'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear all cached results and exit'
    )
    
    args = parser.parse_args()
    
    # Handle cache management
    if args.clear_cache:
        from cache_manager import CacheManager
        cache_manager = CacheManager()
        cache_manager.clear_cache()
        cache_manager.print_cache_stats()
        return
    
    # Validate input files
    print("🔍 Validating input files...")
    valid_videos = []
    
    for video_path in args.videos:
        is_valid, message = validate_video_file(video_path)
        if is_valid:
            valid_videos.append(video_path)
            print(f"✓ {os.path.basename(video_path)}")
        else:
            print(f"✗ {message}")
    
    if not valid_videos:
        print("❌ No valid video files found!")
        sys.exit(1)
    
    print(f"\n📊 Found {len(valid_videos)} valid video file(s)")
    print(f"🎯 Target themes: {', '.join(args.themes)}")
    print(f"⏱️  Target duration: {args.duration} seconds per theme")
    print(f"📁 Output directory: {args.output_dir}")
    
    if args.dry_run:
        print("\n🏃 Dry run complete - no processing performed")
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process videos and assign to themes
    print(f"\n🚀 Processing {len(valid_videos)} video(s)...")
    
    try:
        theme_pools = process_videos_for_themes(valid_videos, use_cache=not args.no_cache)
        
        if not theme_pools:
            print("❌ No clips were successfully assigned to themes!")
            sys.exit(1)
        
        # Print final summary
        print(f"\n🎉 Processing complete!")
        print(f"📊 Clip assignment summary:")
        
        from config import THEME_CONFIGS
        total_clips = 0
        for theme, pool in theme_pools.items():
            theme_config = THEME_CONFIGS[theme]
            clip_count = len(pool.clips)
            total_clips += clip_count
            print(f"   {theme_config.name}: {clip_count} clips ({pool.total_duration:.1f}s)")
        
        print(f"   Total: {total_clips} clips assigned to themes")
        print(f"\n📁 Ready for video editing pipeline (Step 8)")
        print(f"💡 Next: Implement video editing and music overlay")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
