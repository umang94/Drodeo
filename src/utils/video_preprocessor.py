"""
Video Preprocessing Utilities

Handles audio stripping, video downsampling, and development optimization
for fast iteration during development.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import subprocess
from moviepy.editor import VideoFileClip
from src.gpu.gpu_detector import GPUDetector

logger = logging.getLogger(__name__)

class VideoPreprocessor:
    """Handles video preprocessing for development optimization."""
    
    def __init__(self):
        """Initialize video preprocessor."""
        self.gpu_detector = GPUDetector()
        self.gpu_available = self.gpu_detector.is_gpu_available()
        
    def create_dev_versions(self, input_dir: str = "input", 
                           output_dir: str = "input_dev",
                           target_height: int = 360,
                           force_recreate: bool = False) -> List[str]:
        """
        Create development versions of all videos in input directory.
        
        Args:
            input_dir: Source directory with original videos
            output_dir: Output directory for dev versions
            target_height: Target height for downsampling (360p default)
            force_recreate: Force recreation even if dev version exists
            
        Returns:
            List of created dev video paths
        """
        print(f"🔧 Creating development versions of videos...")
        print(f"   Source: {input_dir}/")
        print(f"   Target: {output_dir}/")
        print(f"   Resolution: {target_height}p")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV']
        input_path = Path(input_dir)
        
        video_files = []
        for ext in video_extensions:
            video_files.extend(input_path.glob(f"*{ext}"))
        
        if not video_files:
            print(f"   ⚠️  No video files found in {input_dir}/")
            return []
        
        print(f"   📹 Found {len(video_files)} video files")
        
        created_files = []
        
        for video_file in video_files:
            dev_path = self._create_dev_version(
                str(video_file), 
                output_dir, 
                target_height, 
                force_recreate
            )
            if dev_path:
                created_files.append(dev_path)
        
        print(f"   ✅ Created {len(created_files)} development versions")
        return created_files
    
    def _create_dev_version(self, video_path: str, output_dir: str, 
                           target_height: int, force_recreate: bool) -> Optional[str]:
        """Create a single development version of a video."""
        video_file = Path(video_path)
        dev_filename = f"{video_file.stem}_dev{video_file.suffix}"
        dev_path = os.path.join(output_dir, dev_filename)
        
        # Check if dev version already exists
        if os.path.exists(dev_path) and not force_recreate:
            print(f"   ⚡ Using existing: {dev_filename}")
            return dev_path
        
        print(f"   🔄 Processing: {video_file.name}")
        
        try:
            # Get original video info
            original_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            
            # Use FFmpeg for efficient processing
            success = self._process_with_ffmpeg(video_path, dev_path, target_height)
            
            if success and os.path.exists(dev_path):
                dev_size = os.path.getsize(dev_path) / (1024 * 1024)  # MB
                compression_ratio = original_size / dev_size if dev_size > 0 else 0
                
                print(f"      ✅ {video_file.name}: {original_size:.1f}MB → {dev_size:.1f}MB ({compression_ratio:.1f}x smaller)")
                return dev_path
            else:
                print(f"      ❌ Failed to process {video_file.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing {video_path}: {e}")
            print(f"      ❌ Error: {e}")
            return None
    
    def _process_with_ffmpeg(self, input_path: str, output_path: str, 
                            target_height: int) -> bool:
        """Process video using FFmpeg for optimal performance."""
        try:
            # FFmpeg command for aggressive compression and audio removal
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-an',  # Remove audio
                '-vf', f'scale=-2:{target_height}',  # Scale to target height, maintain aspect ratio
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'fast',  # Fast encoding
                '-crf', '28',  # Aggressive compression (higher = smaller file)
                '-movflags', '+faststart',  # Optimize for streaming
                '-y',  # Overwrite output file
                output_path
            ]
            
            # Add GPU acceleration if available (NVIDIA)
            if self.gpu_available:
                gpu_capabilities = self.gpu_detector.get_capabilities()
                if gpu_capabilities.has_cuda:
                    # Use NVIDIA hardware acceleration
                    cmd = [
                        'ffmpeg',
                        '-hwaccel', 'cuda',
                        '-i', input_path,
                        '-an',  # Remove audio
                        '-vf', f'scale_cuda=-2:{target_height}',
                        '-c:v', 'h264_nvenc',  # NVIDIA encoder
                        '-preset', 'fast',
                        '-cq', '28',  # Quality for NVENC
                        '-movflags', '+faststart',
                        '-y',
                        output_path
                    ]
            
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout processing {input_path}")
            return False
        except FileNotFoundError:
            # FFmpeg not available, fall back to MoviePy
            logger.warning("FFmpeg not found, using MoviePy (slower)")
            return self._process_with_moviepy(input_path, output_path, target_height)
        except Exception as e:
            logger.error(f"FFmpeg processing failed: {e}")
            return False
    
    def _process_with_moviepy(self, input_path: str, output_path: str, 
                             target_height: int) -> bool:
        """Fallback processing using MoviePy."""
        try:
            print(f"      🐍 Using MoviePy fallback...")
            
            # Load video and remove audio
            clip = VideoFileClip(input_path).without_audio()
            
            # Calculate target width maintaining aspect ratio
            original_height = clip.h
            original_width = clip.w
            target_width = int((target_height / original_height) * original_width)
            
            # Ensure even dimensions for encoding
            target_width = target_width if target_width % 2 == 0 else target_width - 1
            target_height = target_height if target_height % 2 == 0 else target_height - 1
            
            # Resize video
            resized_clip = clip.resize((target_width, target_height))
            
            # Write with aggressive compression
            resized_clip.write_videofile(
                output_path,
                codec='libx264',
                audio=False,
                temp_audiofile=None,
                remove_temp=True,
                preset='fast',
                ffmpeg_params=['-crf', '28']
            )
            
            # Clean up
            clip.close()
            resized_clip.close()
            
            return True
            
        except Exception as e:
            logger.error(f"MoviePy processing failed: {e}")
            return False
    
    def strip_audio_from_videos(self, video_paths: List[str], 
                               output_suffix: str = "_no_audio") -> List[str]:
        """
        Strip audio from multiple videos.
        
        Args:
            video_paths: List of video file paths
            output_suffix: Suffix to add to output filenames
            
        Returns:
            List of paths to videos without audio
        """
        print(f"🔇 Stripping audio from {len(video_paths)} videos...")
        
        processed_paths = []
        
        for video_path in video_paths:
            try:
                video_file = Path(video_path)
                output_path = video_file.parent / f"{video_file.stem}{output_suffix}{video_file.suffix}"
                
                if os.path.exists(output_path):
                    print(f"   ⚡ Already exists: {output_path.name}")
                    processed_paths.append(str(output_path))
                    continue
                
                print(f"   🔄 Processing: {video_file.name}")
                
                # Use FFmpeg for audio removal
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-an',  # Remove audio
                    '-c:v', 'copy',  # Copy video stream without re-encoding
                    '-y',  # Overwrite
                    str(output_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"      ✅ Audio stripped: {output_path.name}")
                    processed_paths.append(str(output_path))
                else:
                    print(f"      ❌ Failed to strip audio from {video_file.name}")
                    
            except Exception as e:
                logger.error(f"Error stripping audio from {video_path}: {e}")
                print(f"      ❌ Error: {e}")
        
        print(f"   ✅ Processed {len(processed_paths)} videos")
        return processed_paths
    
    def get_video_info(self, video_path: str) -> dict:
        """Get basic information about a video file."""
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': (clip.w, clip.h),
                'has_audio': clip.audio is not None,
                'file_size_mb': os.path.getsize(video_path) / (1024 * 1024)
            }
            clip.close()
            return info
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {e}")
            return {}
    
    def cleanup_temp_files(self, directory: str):
        """Clean up temporary files created during processing."""
        temp_patterns = ['*.tmp', '*.temp', '*_temp.*']
        
        for pattern in temp_patterns:
            for temp_file in Path(directory).glob(pattern):
                try:
                    temp_file.unlink()
                    print(f"   🗑️  Cleaned up: {temp_file.name}")
                except Exception as e:
                    logger.debug(f"Could not remove temp file {temp_file}: {e}")

def create_development_environment(force_recreate: bool = False) -> dict:
    """
    Set up complete development environment with downsampled videos.
    
    Args:
        force_recreate: Force recreation of all dev files
        
    Returns:
        Dictionary with setup results
    """
    preprocessor = VideoPreprocessor()
    
    print("🚀 Setting up development environment...")
    
    # Create dev versions
    dev_videos = preprocessor.create_dev_versions(
        input_dir="input",
        output_dir="input_dev", 
        target_height=360,
        force_recreate=force_recreate
    )
    
    # Get statistics
    total_original_size = 0
    total_dev_size = 0
    
    for dev_video in dev_videos:
        original_video = dev_video.replace("input_dev", "input").replace("_dev", "")
        
        if os.path.exists(original_video):
            total_original_size += os.path.getsize(original_video)
        
        if os.path.exists(dev_video):
            total_dev_size += os.path.getsize(dev_video)
    
    # Convert to MB
    total_original_size_mb = total_original_size / (1024 * 1024)
    total_dev_size_mb = total_dev_size / (1024 * 1024)
    compression_ratio = total_original_size_mb / total_dev_size_mb if total_dev_size_mb > 0 else 0
    
    results = {
        'dev_videos_created': len(dev_videos),
        'total_original_size_mb': total_original_size_mb,
        'total_dev_size_mb': total_dev_size_mb,
        'compression_ratio': compression_ratio,
        'dev_video_paths': dev_videos
    }
    
    print(f"\n📊 Development Environment Summary:")
    print(f"   Videos processed: {results['dev_videos_created']}")
    print(f"   Original size: {results['total_original_size_mb']:.1f}MB")
    print(f"   Dev size: {results['total_dev_size_mb']:.1f}MB")
    print(f"   Compression: {results['compression_ratio']:.1f}x smaller")
    print(f"   🚀 Ready for fast development iteration!")
    
    return results

if __name__ == "__main__":
    # Test the preprocessor
    results = create_development_environment()
    print(f"✅ Development environment ready: {results}")
