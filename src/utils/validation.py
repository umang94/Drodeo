"""
Validation utilities for Drodeo build validation and environment checks.
Provides robust validation for environment variables, directories, and video setup.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def validate_environment():
    """
    Validate the environment setup including .env file and required API keys.
    
    Returns:
        bool: True if environment is valid, False otherwise
    """
    print("🔍 Validating environment setup...")
    
    # Load environment variables (without override to prevent issues)
    env_loaded = load_dotenv(override=False)
    
    if not env_loaded:
        print("   ⚠️  No .env file found, using system environment variables")
    else:
        print("   ✅ .env file loaded successfully")
    
    # Check for required Gemini API key
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key or gemini_api_key == 'your_gemini_api_key_here':
        print("❌ GEMINI_API_KEY not found or not configured")
        print("   Please add your Gemini API key to .env file:")
        print("   GEMINI_API_KEY=your_actual_api_key_here")
        print("   Get your key from: https://aistudio.google.com/app/apikey")
        return False
    
    print("   ✅ GEMINI_API_KEY is configured")
    
    # Check Python dependencies
    try:
        import google.generativeai
        import moviepy
        import numpy
        import tqdm
        print("   ✅ All Python dependencies are available")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def validate_directories():
    """
    Validate that all required directories exist and are accessible.
    
    Returns:
        bool: True if directories are valid, False otherwise
    """
    print("📂 Validating directory structure...")
    
    required_dirs = [
        "music",
        "input",
        "input_dev", 
        "output",
        "cache",
        "logs"
    ]
    
    all_valid = True
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"   ✅ {dir_name}/ directory exists")
        else:
            print(f"   ⚠️  {dir_name}/ directory missing, creating...")
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"   ✅ Created {dir_name}/ directory")
            except Exception as e:
                print(f"❌ Failed to create {dir_name}/ directory: {e}")
                all_valid = False
    
    # Check if input directory has videos (recursive search)
    input_dir = Path("input")
    if input_dir.exists():
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV', '.AVI', '.MKV']
        video_files = []
        
        # Recursively search for video files
        for ext in video_extensions:
            video_files.extend(input_dir.rglob(f"*{ext}"))
        
        # Filter out directories and only keep files
        video_files = [f for f in video_files if f.is_file()]
        
        if not video_files:
            print("   ⚠️  input/ directory is empty - add video files for processing")
        else:
            print(f"   ✅ Found {len(video_files)} video files in input/ (recursive search)")
            # Show directory structure if multiple subdirectories found
            subdirs = {f.parent for f in video_files if f.parent != input_dir}
            if subdirs:
                print(f"      📁 Found videos in {len(subdirs)} subdirectories")
    
    # Check if music directory has audio files
    music_dir = Path("music")
    if music_dir.exists():
        audio_files = list(music_dir.glob("*.[mM][pP][3]")) + list(music_dir.glob("*.[mM][4][aA]"))
        if not audio_files:
            print("   ⚠️  music/ directory is empty - add audio files for processing")
        else:
            print(f"   ✅ Found {len(audio_files)} audio files in music/")
    
    return all_valid

def setup_development_videos(force=False, source_dir="input"):
    """
    Set up development videos with smart caching.
    Auto-creates low-res videos on first run, uses cached copies thereafter.
    
    Args:
        force (bool): Force recreation of development videos even if they exist
        source_dir (str): Source directory containing video files
    
    Returns:
        bool: True if setup was successful, False otherwise
    """
    print("🎥 Setting up development videos...")
    
    source_path = Path(source_dir)
    source_dir_name = source_path.name
    
    # For "input" directory, use input_dev directly for backward compatibility
    if source_dir_name == "input":
        input_dev_dir = Path("input_dev")
    else:
        # For custom directories, create subdirectory under input_dev
        input_dev_dir = Path("input_dev") / source_dir_name
    
    input_dir = source_path
    
    # Check if input directory exists and has videos (recursive search)
    if not input_dir.exists():
        print("   ⚠️  input/ directory not found - no videos to process")
        return True
    
    # Recursively search for video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV', '.AVI', '.MKV']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(input_dir.rglob(f"*{ext}"))
    
    # Filter out directories and only keep files
    video_files = [f for f in video_files if f.is_file()]
    
    if not video_files:
        print("   ⚠️  No video files found in input/ directory (recursive search)")
        return True
    
    # Check if development videos already exist
    dev_video_files = list(input_dev_dir.glob("*.[mM][pP][4]")) + list(input_dev_dir.glob("*.[mM][oO][vV]"))
    
    if dev_video_files and not force:
        print(f"   ✅ Using {len(dev_video_files)} cached development videos")
        for video in dev_video_files[:3]:  # Show first 3 files
            size_mb = video.stat().st_size / (1024 * 1024)
            print(f"      📹 {video.name} ({size_mb:.1f} MB)")
        if len(dev_video_files) > 3:
            print(f"      ... and {len(dev_video_files) - 3} more")
        return True
    
    # Create development videos
    print(f"   🔄 Creating development videos from {len(video_files)} source files...")
    
    try:
        # Run create_dev_videos.py script with source and target directories
        result = subprocess.run(
            [sys.executable, "scripts/create_dev_videos.py", str(input_dir), str(input_dev_dir)],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            # Verify development videos were created
            new_dev_videos = list(input_dev_dir.glob("*.[mM][pP][4]")) + list(input_dev_dir.glob("*.[mM][oO][vV]"))
            if new_dev_videos:
                print(f"   ✅ Created {len(new_dev_videos)} development videos")
                for video in new_dev_videos[:3]:
                    size_mb = video.stat().st_size / (1024 * 1024)
                    print(f"      📹 {video.name} ({size_mb:.1f} MB)")
                return True
            else:
                print("   ⚠️  create_dev_videos.py ran but no videos were created")
                return False
        else:
            print(f"❌ Failed to create development videos: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating development videos: {e}")
        return False

def check_ffmpeg_available():
    """
    Check if FFmpeg is available for video processing.
    
    Returns:
        bool: True if FFmpeg is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ FFmpeg is available for video processing")
            return True
        else:
            print("❌ FFmpeg is not available or not working properly")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg is not installed")
        print("   Install FFmpeg: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")
        return False

if __name__ == "__main__":
    # Test the validation functions
    print("Testing validation utilities...")
    print("Environment validation:", validate_environment())
    print("Directory validation:", validate_directories())
    print("FFmpeg check:", check_ffmpeg_available())
