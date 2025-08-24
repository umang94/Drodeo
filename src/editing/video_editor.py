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

from src.utils.config import THEME_CONFIGS, VIDEO_CONFIG
from src.core.video_processor import VideoClip
from src.editing.music_downloader import MusicDownloader

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
        
        # Initialize music downloader
        try:
            self.music_downloader = MusicDownloader()
        except Exception as e:
            logger.warning(f"Failed to initialize music downloader: {e}")
            self.music_downloader = None
        
    def ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_themed_video(self, clips: List[VideoClip], theme: str, 
                          target_duration: int = 180, music_path: Optional[str] = None) -> str:
        """
        Create a themed video from selected clips
        
        Args:
            clips: List of video clips to include
            theme: Theme name (happy, exciting, peaceful, adventure, cinematic)
            target_duration: Target duration in seconds
            music_path: Path to background music file
            
        Returns:
            Path to the rendered video file
        """
        if not clips:
            raise ValueError(f"No clips provided for theme '{theme}'")
            
        print(f"🎬 Creating {theme} themed video...")
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
                
                # Apply theme-specific effects
                video_clip = self._apply_theme_effects(video_clip, theme)
                
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
            output_filename = f"{theme}_video_{len(clips)}clips_{int(final_video.duration)}s.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Render the final video
            print(f"   🎬 Rendering to: {output_filename}")
            self._render_video(final_video, output_path, theme)
            
            # Clean up
            final_video.close()
            for clip in video_clips:
                clip.close()
            
            print(f"   ✅ {theme} video created successfully!")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating {theme} themed video: {str(e)}")
            raise
    
    def _apply_theme_effects(self, clip: VideoFileClip, theme: str) -> VideoFileClip:
        """
        Apply theme-specific visual effects to a clip
        
        Args:
            clip: Video clip to modify
            theme: Theme name
            
        Returns:
            Modified video clip
        """
        # Apply theme-specific effects based on configuration
        if theme == "exciting":
            # Slightly increase saturation and contrast for exciting theme
            # Note: MoviePy doesn't have built-in color correction, so we keep it simple
            pass
        elif theme == "peaceful":
            # Softer transitions and potentially slower pacing
            pass
        elif theme == "cinematic":
            # Add letterbox effect for cinematic feel
            if clip.h > clip.w * 9/16:  # If taller than 16:9
                target_height = int(clip.w * 9/16)
                clip = clip.crop(y1=(clip.h - target_height)//2, y2=(clip.h + target_height)//2)
        
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
    
    def _render_video(self, video: VideoFileClip, output_path: str, theme: str):
        """
        Render video to file with progress tracking
        
        Args:
            video: Video to render
            output_path: Output file path
            theme: Theme name for progress display
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
    
    def create_multiple_themed_videos(self, theme_clips: Dict[str, List[VideoClip]], 
                                    target_duration: int = 180) -> Dict[str, str]:
        """
        Create multiple themed videos from clip assignments
        
        Args:
            theme_clips: Dictionary mapping theme names to clip lists
            target_duration: Target duration for each video
            
        Returns:
            Dictionary mapping theme names to output file paths
        """
        output_paths = {}
        
        print(f"\n🎬 Creating themed videos...")
        print(f"📊 Themes to process: {len(theme_clips)}")
        
        for theme, clips in theme_clips.items():
            if not clips:
                print(f"⚠️  Skipping {theme} - no clips assigned")
                continue
                
            try:
                # Look for theme music
                music_path = self._find_theme_music(theme, target_duration)
                
                # Create themed video
                output_path = self.create_themed_video(
                    clips, theme, target_duration, music_path
                )
                output_paths[theme] = output_path
                
            except Exception as e:
                logger.error(f"Failed to create {theme} video: {str(e)}")
                continue
        
        return output_paths
    
    def _find_theme_music(self, theme: str, target_duration: int = 180) -> Optional[str]:
        """
        Find or download music file for a theme
        
        Args:
            theme: Theme name
            target_duration: Target duration in seconds
            
        Returns:
            Path to music file or None if not found
        """
        if self.music_downloader:
            try:
                return self.music_downloader.get_theme_music(theme, target_duration)
            except Exception as e:
                logger.warning(f"Music downloader failed for {theme}: {e}")
        
        # Fallback to manual search
        music_dir = "music"
        if not os.path.exists(music_dir):
            return None
            
        # Look for theme-specific music files
        possible_names = [
            f"{theme}.mp3",
            f"{theme}.wav",
            f"{theme}.m4a",
            f"{theme}_music.mp3",
            f"{theme}_background.mp3",
            f"{theme}_sample.wav"
        ]
        
        for name in possible_names:
            path = os.path.join(music_dir, name)
            if os.path.exists(path):
                return path
                
        return None
    
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
        output_path = editor.create_themed_video(test_clips, "peaceful", 10)
        print(f"Test video created: {output_path}")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
