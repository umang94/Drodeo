#!/usr/bin/env python3
"""
Drodeo - Music-Driven Video Generator
A tool to create videos from user-provided music and video content.
"""

import argparse
import sys
import os
from pathlib import Path

def validate_video_file(file_path):
    """Check if file exists and is a video file."""
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv']
    if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
        return False, f"Unsupported file format. Supported: {', '.join(valid_extensions)}"
    
    return True, "Valid video file"

def validate_audio_file(file_path):
    """Check if file exists and is an audio file."""
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    valid_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.flac']
    if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
        return False, f"Unsupported file format. Supported: {', '.join(valid_extensions)}"
    
    return True, "Valid audio file"

def main():
    parser = argparse.ArgumentParser(
        description="Generate music-driven videos from your own content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use batch processor (recommended)
  python batch_video_generator.py
  
  # Process specific files
  python main.py --music song.mp3 --videos video1.mp4 video2.mp4
  
  # Use development videos (faster processing)
  python main.py --use-dev-videos
        """
    )
    
    parser.add_argument(
        '--music',
        help='Music file to use for video generation'
    )
    
    parser.add_argument(
        '--videos',
        nargs='*',
        help='Video files to process'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Directory to save generated videos (default: output)'
    )
    
    parser.add_argument(
        '--use-dev-videos',
        action='store_true',
        help='Use downsampled development videos for faster processing'
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
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate inputs without processing'
    )
    
    args = parser.parse_args()
    
    # Handle cache management
    if args.clear_cache:
        from src.utils.cache_manager import CacheManager
        cache_manager = CacheManager()
        cache_manager.clear_cache()
        cache_manager.print_cache_stats()
        return
    
    # If no specific files provided, suggest using batch processor
    if not args.music and not args.videos:
        print("🎵 Drodeo - Music-Driven Video Generator")
        print("\nFor the best experience, use the batch processor:")
        print("  python batch_video_generator.py")
        print("\nThis will process all music files in music_input/ with all videos in input/")
        print("\nOr specify files manually with --music and --videos options")
        return
    
    # Validate music file
    if args.music:
        is_valid, message = validate_audio_file(args.music)
        if not is_valid:
            print(f"❌ Music file error: {message}")
            sys.exit(1)
        print(f"✓ Music: {os.path.basename(args.music)}")
    
    # Validate video files
    valid_videos = []
    if args.videos:
        print("🔍 Validating video files...")
        for video_path in args.videos:
            is_valid, message = validate_video_file(video_path)
            if is_valid:
                valid_videos.append(video_path)
                print(f"✓ {os.path.basename(video_path)}")
            else:
                print(f"✗ {message}")
    
    if args.videos and not valid_videos:
        print("❌ No valid video files found!")
        sys.exit(1)
    
    if args.dry_run:
        print("\n🏃 Dry run complete - inputs validated")
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"\n🚀 Processing with music-driven approach...")
    print("💡 For full batch processing, use: python batch_video_generator.py")
    
    try:
        # Import and use the batch video generator for single file processing
        from batch_video_generator import BatchVideoGenerator
        
        # Determine video input directory
        video_input_dir = "input_dev" if args.use_dev_videos else "input"
        
        generator = BatchVideoGenerator(
            music_input_dir="music_input" if not args.music else None,
            video_input_dir=video_input_dir if not args.videos else None,
            output_dir=args.output_dir,
            use_cache=not args.no_cache
        )
        
        if args.music and args.videos:
            # Process single music file with specific videos
            print(f"🎵 Processing: {os.path.basename(args.music)}")
            print(f"🎬 With {len(valid_videos)} video(s)")
            
            # Create a temporary music input for single file processing
            temp_music_dir = "temp_music_input"
            os.makedirs(temp_music_dir, exist_ok=True)
            
            # Copy music file to temp directory
            import shutil
            temp_music_path = os.path.join(temp_music_dir, os.path.basename(args.music))
            shutil.copy2(args.music, temp_music_path)
            
            # Process with specific videos
            generator.music_input_dir = temp_music_dir
            generator.video_input_dir = None  # Will use provided video list
            
            # Override video discovery to use provided videos
            generator.video_files = valid_videos
            
            results = generator.process_all()
            
            # Clean up temp directory
            shutil.rmtree(temp_music_dir)
            
        else:
            # Use standard batch processing
            results = generator.process_all()
        
        if results:
            print(f"\n🎉 Processing complete!")
            print(f"📊 Generated {len(results)} video(s)")
            for result in results:
                print(f"   ✅ {result}")
        else:
            print("❌ No videos were generated!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
