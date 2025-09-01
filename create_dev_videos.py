#!/usr/bin/env python3
"""
Create Development Videos

Automatically creates 360p development versions of high-resolution videos
for faster processing during development and testing.

Usage:
    python create_dev_videos.py
    python create_dev_videos.py --force  # Overwrite existing dev videos
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse
from typing import List, Tuple

def get_video_info(video_path: str) -> Tuple[int, int, float]:
    """Get video resolution and duration using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if video_stream:
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            duration = float(data['format']['duration'])
            return width, height, duration
        else:
            return 0, 0, 0.0
            
    except Exception as e:
        print(f"   ⚠️  Could not get info for {video_path}: {e}")
        return 0, 0, 0.0

def create_dev_video(input_path: str, output_path: str, target_resolution: Tuple[int, int] = (640, 360)) -> bool:
    """Create a downsampled development version of a video."""
    try:
        target_width, target_height = target_resolution
        
        # FFmpeg command for high-quality downsampling
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-crf', '23',  # Good quality
            '-preset', 'medium',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',  # Overwrite output file
            output_path
        ]
        
        print(f"      🔄 Creating {Path(output_path).name}...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Verify output file was created
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"      ✅ Created {Path(output_path).name} ({output_size:.1f}MB)")
            return True
        else:
            print(f"      ❌ Failed to create {Path(output_path).name}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"      ❌ FFmpeg error: {e}")
        if e.stderr:
            print(f"         Error details: {e.stderr}")
        return False
    except Exception as e:
        print(f"      ❌ Unexpected error: {e}")
        return False

def get_dev_filename(original_filename: str) -> str:
    """Generate development filename with _dev suffix."""
    path = Path(original_filename)
    stem = path.stem
    suffix = path.suffix
    
    # Add _dev suffix if not already present
    if not stem.endswith('_dev'):
        return f"{stem}_dev{suffix}"
    else:
        return original_filename

def main():
    """Main function to create development videos."""
    parser = argparse.ArgumentParser(description='Create 360p development videos from high-resolution sources')
    parser.add_argument('--force', action='store_true', help='Overwrite existing development videos')
    parser.add_argument('--input-dir', default='input', help='Input directory containing high-res videos')
    parser.add_argument('--output-dir', default='input_dev', help='Output directory for development videos')
    parser.add_argument('--resolution', default='640x360', help='Target resolution (default: 640x360)')
    
    args = parser.parse_args()
    
    # Parse resolution
    try:
        width, height = map(int, args.resolution.split('x'))
        target_resolution = (width, height)
    except ValueError:
        print(f"❌ Invalid resolution format: {args.resolution}. Use format like '640x360'")
        return 1
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    print("🎬 Drodeo Development Video Creator")
    print("=" * 50)
    print(f"📂 Input directory: {input_dir}")
    print(f"📂 Output directory: {output_dir}")
    print(f"📺 Target resolution: {target_resolution[0]}x{target_resolution[1]}")
    print(f"🔄 Force overwrite: {'Yes' if args.force else 'No'}")
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Find video files in input directory
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV', '.AVI', '.MKV']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(input_dir.glob(f"*{ext}"))
    
    # Filter out subdirectories and files that are already dev versions
    video_files = [f for f in video_files if f.is_file() and not f.stem.endswith('_dev')]
    
    if not video_files:
        print(f"❌ No video files found in {input_dir}")
        return 1
    
    print(f"\n📊 Found {len(video_files)} high-resolution videos:")
    
    # Process each video
    created_count = 0
    skipped_count = 0
    failed_count = 0
    
    for video_file in video_files:
        print(f"\n📹 Processing: {video_file.name}")
        
        # Get video info
        width, height, duration = get_video_info(str(video_file))
        if width > 0:
            file_size = video_file.stat().st_size / (1024 * 1024)  # MB
            print(f"   📊 Original: {width}x{height}, {duration:.1f}s, {file_size:.1f}MB")
        
        # Generate output filename
        dev_filename = get_dev_filename(video_file.name)
        output_path = output_dir / dev_filename
        
        # Check if output already exists
        if output_path.exists() and not args.force:
            existing_size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"   ⏭️  Skipping: {dev_filename} already exists ({existing_size:.1f}MB)")
            skipped_count += 1
            continue
        
        # Create development video
        success = create_dev_video(str(video_file), str(output_path), target_resolution)
        
        if success:
            created_count += 1
        else:
            failed_count += 1
    
    # Summary
    print(f"\n🎉 Development Video Creation Complete!")
    print(f"   ✅ Created: {created_count} videos")
    print(f"   ⏭️  Skipped: {skipped_count} videos (already exist)")
    print(f"   ❌ Failed: {failed_count} videos")
    
    if created_count > 0:
        print(f"\n📂 Development videos saved to: {output_dir}")
        print("   Ready for fast development and testing!")
        print("   Use these videos with batch_video_generator.py or test_two_step_pipeline.py")
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
