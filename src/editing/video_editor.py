#!/usr/bin/env python3
"""
Video Editor Module for Drone Video Generator

This module handles the actual video editing using MoviePy, including:
- Creating themed videos from selected clips
- Adding music overlays
- Rendering final output videos
- Progress tracking during rendering
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip, concatenate_audioclips, CompositeAudioClip
from moviepy.video.fx import resize
from moviepy.audio.fx.audio_fadein import audio_fadein
from moviepy.audio.fx.audio_fadeout import audio_fadeout
import moviepy.video.fx.all as vfx
import numpy as np
from tqdm import tqdm

from src.utils.config import VIDEO_CONFIG
from src.core.video_processor import VideoClip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoEditor:
    """Handles video editing operations using MoviePy"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the video editor
        
        Args:
            output_dir: Directory to save rendered videos
        """
        self.output_dir = output_dir
        self.ensure_output_directory()
        
        # Music-driven approach - no automatic music downloader needed
        self.music_downloader = None
        
    def ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_music_driven_video(self, clips: List[VideoClip], music_name: str, 
                          target_duration: int = 180, music_path: Optional[str] = None) -> str:
        """
        Create a music-driven video from selected clips
        
        Args:
            clips: List of video clips to include
            music_name: Name of the music track (for output filename)
            target_duration: Target duration in seconds
            music_path: Path to background music file
            
        Returns:
            Path to the rendered video file
        """
        if not clips:
            raise ValueError(f"No clips provided for music '{music_name}'")
            
        print(f"🎬 Creating music-driven video for: {music_name}")
        print(f"   📊 Using {len(clips)} clips")
        print(f"   ⏱️  Target duration: {target_duration}s")
        
        try:
            # Load and prepare video clips
            video_clips = []
            total_duration = 0
            
            # First pass: load all available clips
            loaded_clips = []
            for i, clip in enumerate(clips):
                print(f"   📹 Loading clip {i+1}/{len(clips)}: {os.path.basename(clip.file_path)}")
                
                # Load video clip
                video_clip = VideoFileClip(clip.file_path).subclip(clip.start_time, clip.end_time)
                clip_duration = video_clip.duration
                
                # Apply basic video effects
                video_clip = self._apply_video_effects(video_clip)
                
                loaded_clips.append(video_clip)
                total_duration += clip_duration
            
            print(f"   📊 Total available clip duration: {total_duration:.1f}s")
            print(f"   🎯 Target duration: {target_duration}s")
            
            # If we don't have enough content, repeat clips to reach target duration
            if total_duration < target_duration:
                print(f"   🔄 Repeating clips to reach target duration...")
                clips_needed = int(np.ceil(target_duration / total_duration))
                extended_clips = loaded_clips * clips_needed
            else:
                extended_clips = loaded_clips
            
            # Add transitions and build final clip list
            for i, video_clip in enumerate(extended_clips):
                # Add transitions
                if i > 0:  # Add fade in for all clips except first
                    video_clip = video_clip.fx(vfx.fadein, 0.5)
                if i < len(extended_clips) - 1:  # Add fade out for all clips except last
                    video_clip = video_clip.fx(vfx.fadeout, 0.5)
                
                video_clips.append(video_clip)
                
                # Check if we have enough duration
                current_duration = sum(clip.duration for clip in video_clips)
                if current_duration >= target_duration:
                    break
            
            # Concatenate all clips
            print(f"   🔗 Concatenating {len(video_clips)} clips...")
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Trim to exact target duration
            if final_video.duration > target_duration:
                print(f"   ✂️  Trimming from {final_video.duration:.1f}s to {target_duration}s")
                final_video = final_video.subclip(0, target_duration)
            
            # Clean up loaded clips that weren't used
            for clip in loaded_clips:
                if clip not in video_clips:
                    clip.close()
            
            # Add music overlay if provided
            if music_path and os.path.exists(music_path):
                print(f"   🎵 Adding music overlay: {os.path.basename(music_path)}")
                final_video = self._add_music_overlay(final_video, music_path)
            
            # Generate output filename
            safe_music_name = "".join(c for c in music_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_filename = f"{safe_music_name}_{len(clips)}clips_{int(final_video.duration)}s.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Render the final video
            print(f"   🎬 Rendering to: {output_filename}")
            self._render_video(final_video, output_path, music_name)
            
            # Clean up
            final_video.close()
            for clip in video_clips:
                clip.close()
            
            print(f"   ✅ Music-driven video created successfully!")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating music-driven video for {music_name}: {str(e)}")
            raise
    
    def _apply_video_effects(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Apply basic video effects to a clip
        
        Args:
            clip: Video clip to modify
            
        Returns:
            Modified video clip
        """
        # Apply basic video enhancements
        # Keep aspect ratio and basic quality improvements
        return clip
    
    def _add_music_overlay(self, video: VideoFileClip, music_path: str) -> VideoFileClip:
        """
        Add background music to a video
        
        Args:
            video: Video clip to add music to
            music_path: Path to music file
            
        Returns:
            Video with music overlay
        """
        try:
            # Load audio
            audio = AudioFileClip(music_path)
            
            # Loop audio if it's shorter than video
            if audio.duration < video.duration:
                # Calculate how many loops we need
                loops_needed = int(np.ceil(video.duration / audio.duration))
                audio_clips = [audio] * loops_needed
                audio = concatenate_audioclips(audio_clips)
            
            # Trim audio to match video duration
            audio = audio.subclip(0, video.duration)
            
            # Set music volume to 60% for better audibility
            audio = audio.volumex(0.6)
            
            # Combine original audio with music
            if video.audio is not None:
                # Boost original audio slightly and mix with background music
                boosted_original = video.audio.volumex(1.5)
                final_audio = CompositeAudioClip([boosted_original, audio])
            else:
                # Use only background music
                final_audio = audio
            
            # Apply overall volume boost to ensure audibility
            final_audio = final_audio.volumex(1.2)
            
            # Set the audio to the video
            video = video.set_audio(final_audio)
            
            return video
            
        except Exception as e:
            logger.warning(f"Failed to add music overlay: {str(e)}")
            return video  # Return original video if music fails
    
    def _render_video(self, video: VideoFileClip, output_path: str, music_name: str):
        """
        Render video to file with progress tracking
        
        Args:
            video: Video to render
            output_path: Output file path
            music_name: Music name for progress display
        """
        # Get video properties
        duration = video.duration
        fps = video.fps
        resolution = (video.w, video.h)
        
        print(f"   📊 Video properties:")
        print(f"      Duration: {duration:.1f}s")
        print(f"      FPS: {fps}")
        print(f"      Resolution: {resolution[0]}x{resolution[1]}")
        
        # Render with progress bar
        def progress_callback(get_frame, t):
            """Callback for rendering progress"""
            progress = int((t / duration) * 100)
            return get_frame(t)
        
        try:
            # Use optimized settings for faster rendering
            video.write_videofile(
                output_path,
                fps=min(fps, 30),  # Cap at 30fps for smaller files
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None  # Disable MoviePy's verbose logging
            )
            
        except Exception as e:
            logger.error(f"Rendering failed: {str(e)}")
            raise
    
    def create_music_driven_videos(self, music_clips: Dict[str, List[VideoClip]], 
                                 music_paths: Dict[str, str],
                                 target_duration: int = 180) -> Dict[str, str]:
        """
        Create multiple music-driven videos from clip assignments
        
        Args:
            music_clips: Dictionary mapping music names to clip lists
            music_paths: Dictionary mapping music names to file paths
            target_duration: Target duration for each video
            
        Returns:
            Dictionary mapping music names to output file paths
        """
        output_paths = {}
        
        print(f"\n🎬 Creating music-driven videos...")
        print(f"📊 Music tracks to process: {len(music_clips)}")
        
        for music_name, clips in music_clips.items():
            if not clips:
                print(f"⚠️  Skipping {music_name} - no clips assigned")
                continue
                
            try:
                # Get music file path
                music_path = music_paths.get(music_name)
                
                # Create music-driven video
                output_path = self.create_music_driven_video(
                    clips, music_name, target_duration, music_path
                )
                output_paths[music_name] = output_path
                
            except Exception as e:
                logger.error(f"Failed to create video for {music_name}: {str(e)}")
                continue
        
        return output_paths
    
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        Get information about a video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'width': clip.w,
                'height': clip.h,
                'has_audio': clip.audio is not None,
                'size_mb': os.path.getsize(video_path) / (1024 * 1024)
            }
            clip.close()
            return info
        except Exception as e:
            logger.error(f"Failed to get video info for {video_path}: {str(e)}")
            return {}

def main():
    """Test the video editor functionality"""
    editor = VideoEditor()
    
    # Test with sample clips (this would normally come from clip selector)
    test_clips = [
        VideoClip(
            file_path="uploads/DJI_0131.mp4",
            start_time=0,
            end_time=5,
            quality_score=0.8,
            theme_scores={"peaceful": 0.9},
            ai_description="Peaceful drone footage"
        )
    ]
    
    try:
        output_path = editor.create_music_driven_video(test_clips, "test_music", 10, None)
        print(f"Test video created: {output_path}")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
