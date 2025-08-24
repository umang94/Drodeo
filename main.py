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

def process_single_video(video_path, use_cache=True):
    """Process a single video file using real video analysis."""
    from video_processor import VideoProcessor
    
    try:
        processor = VideoProcessor()
        clips, keyframes = processor.process_video(video_path, use_cache=use_cache)
        
        print(f"✓ Completed: {os.path.basename(video_path)} - {len(clips)} clips found")
        return clips, keyframes
    except Exception as e:
        print(f"❌ Error processing {video_path}: {e}")
        return [], []

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
        nargs='+',
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
    
    # Process videos
    print(f"\n🚀 Processing {len(valid_videos)} video(s)...")
    
    for i, video_path in enumerate(valid_videos, 1):
        print(f"\n[{i}/{len(valid_videos)}] {os.path.basename(video_path)}")
        try:
            success = process_single_video(video_path, use_cache=not args.no_cache)
            if not success:
                print(f"❌ Failed to process {video_path}")
        except KeyboardInterrupt:
            print("\n⏹️  Processing interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error processing {video_path}: {str(e)}")
    
    print(f"\n🎉 Processing complete!")
    print(f"📁 Check {args.output_dir}/ for generated videos")

if __name__ == "__main__":
    main()
