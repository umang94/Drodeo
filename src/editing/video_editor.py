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
from typing import List, Dict, Optional, Tuple, Any
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
                          sync_plan: Optional[Any] = None, music_path: Optional[str] = None) -> str:
        """
        Create a music-driven video from selected clips using sync plan
        
        Args:
            clips: List of video clips to include
            music_name: Name of the music track (for output filename)
            sync_plan: AudioVisualSyncPlan for full-length beat-synchronized video
            music_path: Path to background music file
            
        Returns:
            Path to the rendered video file
        """
        if not clips:
            raise ValueError(f"No clips provided for music '{music_name}'")
        
        # Determine target duration from sync plan or use default
        if sync_plan and hasattr(sync_plan, 'music_duration'):
            target_duration = sync_plan.music_duration
            print(f"🎬 Creating FULL-LENGTH music-driven video for: {music_name}")
            print(f"   📊 Using {len(clips)} clips")
            print(f"   🎵 Full music duration: {target_duration:.1f}s")
            print(f"   🎯 Beat-synchronized transitions: {len(sync_plan.transition_points) if sync_plan.transition_points else 0}")
        else:
            target_duration = 180  # Fallback duration
            print(f"🎬 Creating music-driven video for: {music_name}")
            print(f"   📊 Using {len(clips)} clips")
            print(f"   ⏱️  Fallback duration: {target_duration}s")
        
        try:
            if sync_plan and hasattr(sync_plan, 'transition_points'):
                # Enhanced: Use sync plan for beat-precise video creation
                final_video = self._create_sync_plan_video(clips, sync_plan, music_name)
            else:
                # Fallback: Use original method
                final_video = self._create_traditional_video(clips, target_duration)
            
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
    
    
    def _create_sync_plan_video(self, clips: List[VideoClip], sync_plan: Any, music_name: str) -> VideoFileClip:
        """
        Create video using sync plan with beat-precise transitions
        
        Args:
            clips: List of video clips
            sync_plan: AudioVisualSyncPlan with transition points
            music_name: Music name for logging
            
        Returns:
            Final video clip
        """
        print(f"   🎯 Creating beat-synchronized video...")
        
        # Load all clips
        loaded_clips = []
        for i, clip in enumerate(clips):
            print(f"      📹 Loading clip {i+1}/{len(clips)}: {os.path.basename(clip.file_path)}")
            video_clip = VideoFileClip(clip.file_path).subclip(clip.start_time, clip.end_time)
            video_clip = self._apply_video_effects(video_clip)
            loaded_clips.append(video_clip)
        
        # Create segments based on transition points
        transition_points = sync_plan.transition_points
        target_duration = sync_plan.music_duration
        
        if not transition_points:
            # Fallback to traditional method if no transitions
            return self._create_traditional_video(clips, target_duration)
        
        # Add start and end points
        all_points = [0.0] + sorted(transition_points) + [target_duration]
        segments = []
        
        print(f"      🎵 Creating {len(all_points)-1} beat-aligned segments...")
        
        for i in range(len(all_points) - 1):
            start_time = all_points[i]
            end_time = all_points[i + 1]
            segment_duration = end_time - start_time
            
            # Select clip for this segment (cycle through available clips)
            clip_index = i % len(loaded_clips)
            selected_clip = loaded_clips[clip_index]
            
            # Create segment of appropriate duration with intelligent extension
            if selected_clip.duration >= segment_duration:
                # Clip is long enough, use a portion
                segment = selected_clip.subclip(0, segment_duration)
            else:
                # Phase 1: Intelligent clip extension instead of looping
                segment = self._extend_clip_intelligently(selected_clip, segment_duration, clips, clip_index)
            
            # Add beat-precise transitions
            if i > 0:  # Fade in for all segments except first
                segment = segment.fx(vfx.fadein, 0.3)
            if i < len(all_points) - 2:  # Fade out for all segments except last
                segment = segment.fx(vfx.fadeout, 0.3)
            
            segments.append(segment)
        
        # Concatenate all segments
        print(f"      🔗 Concatenating {len(segments)} beat-aligned segments...")
        final_video = concatenate_videoclips(segments, method="compose")
        
        # Clean up
        for clip in loaded_clips:
            clip.close()
        
        return final_video
    
    def _create_traditional_video(self, clips: List[VideoClip], target_duration: float) -> VideoFileClip:
        """
        Create video using traditional method (fallback)
        
        Args:
            clips: List of video clips
            target_duration: Target duration in seconds
            
        Returns:
            Final video clip
        """
        print(f"   📹 Creating traditional video (fallback method)...")
        
        # Load and prepare video clips
        video_clips = []
        total_duration = 0
        
        # First pass: load all available clips
        loaded_clips = []
        for i, clip in enumerate(clips):
            print(f"      📹 Loading clip {i+1}/{len(clips)}: {os.path.basename(clip.file_path)}")
            
            # Load video clip
            video_clip = VideoFileClip(clip.file_path).subclip(clip.start_time, clip.end_time)
            clip_duration = video_clip.duration
            
            # Apply basic video effects
            video_clip = self._apply_video_effects(video_clip)
            
            loaded_clips.append(video_clip)
            total_duration += clip_duration
        
        print(f"      📊 Total available clip duration: {total_duration:.1f}s")
        print(f"      🎯 Target duration: {target_duration:.1f}s")
        
        # If we don't have enough content, repeat clips to reach target duration
        if total_duration < target_duration:
            print(f"      🔄 Repeating clips to reach target duration...")
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
        print(f"      🔗 Concatenating {len(video_clips)} clips...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Trim to exact target duration
        if final_video.duration > target_duration:
            print(f"      ✂️  Trimming from {final_video.duration:.1f}s to {target_duration:.1f}s")
            final_video = final_video.subclip(0, target_duration)
        
        # Clean up loaded clips that weren't used
        for clip in loaded_clips:
            if clip not in video_clips:
                clip.close()
        
        return final_video
    
    def _extend_clip_intelligently(self, short_clip: VideoFileClip, target_duration: float, 
                                 all_clips: List[VideoClip], current_index: int) -> VideoFileClip:
        """
        Phase 1: Intelligently extend a short clip instead of looping it.
        
        Args:
            short_clip: The clip that's too short
            target_duration: Desired duration
            all_clips: All available clips for potential extension
            current_index: Index of current clip
            
        Returns:
            Extended video clip
        """
        try:
            # Validate inputs
            if short_clip is None:
                logger.warning("Short clip is None, cannot extend")
                return short_clip
            
            if target_duration <= short_clip.duration:
                # Already long enough
                return short_clip
            
            # Strategy 1: Try to extend from the same source video
            original_clip_info = all_clips[current_index]
            source_video = None
            
            try:
                source_video = VideoFileClip(original_clip_info.file_path)
                
                # Calculate how much more content we need
                additional_duration = target_duration - short_clip.duration
                
                # Try to extend by using content after the original clip
                extended_end_time = original_clip_info.end_time + additional_duration
                
                if extended_end_time <= source_video.duration:
                    # We can extend from the same video
                    print(f"         🔧 Extending clip from same source (+{additional_duration:.1f}s)")
                    extended_clip = source_video.subclip(original_clip_info.start_time, extended_end_time)
                    
                    # Validate the extended clip
                    if extended_clip is not None and hasattr(extended_clip, 'duration'):
                        source_video.close()
                        return extended_clip
                    else:
                        logger.warning("Extended clip is None or invalid")
                        if extended_clip:
                            extended_clip.close()
                
                source_video.close()
            except Exception as e:
                logger.warning(f"Failed to extend from same source: {e}")
                if 'source_video' in locals() and source_video:
                    source_video.close()
            
            # Strategy 2: Try to extend by using content before the original clip
            try:
                source_video = VideoFileClip(original_clip_info.file_path)
                additional_duration = target_duration - short_clip.duration
                extended_start_time = max(0, original_clip_info.start_time - additional_duration)
                if extended_start_time < original_clip_info.start_time:
                    print(f"         🔧 Extending clip backwards from same source (+{additional_duration:.1f}s)")
                    extended_clip = source_video.subclip(extended_start_time, original_clip_info.end_time)
                    
                    # Validate the extended clip
                    if extended_clip is not None and hasattr(extended_clip, 'duration'):
                        source_video.close()
                        return extended_clip
                    else:
                        logger.warning("Backwards extended clip is None or invalid")
                        if extended_clip:
                            extended_clip.close()
                
                source_video.close()
            except Exception as e:
                logger.warning(f"Failed to extend backwards from same source: {e}")
                if 'source_video' in locals() and source_video:
                    source_video.close()
            
            # Strategy 3: Find a different clip from the same video that's longer
            try:
                same_video_clips = [clip for clip in all_clips if clip.file_path == original_clip_info.file_path]
                for alt_clip in same_video_clips:
                    if alt_clip.duration >= target_duration:
                        print(f"         🔧 Using longer clip from same source ({alt_clip.duration:.1f}s)")
                        alt_video = VideoFileClip(alt_clip.file_path).subclip(alt_clip.start_time, alt_clip.end_time)
                        if alt_video is not None:
                            return alt_video.subclip(0, target_duration)
                        alt_video.close()
            except Exception as e:
                logger.warning(f"Failed to find longer clip from same source: {e}")
            
            # Strategy 4: Combine with a different clip for variety
            try:
                if len(all_clips) > 1:
                    # Find a different clip to combine with
                    other_clips = [clip for i, clip in enumerate(all_clips) if i != current_index]
                    if other_clips:
                        # Sort by quality and pick the best one
                        other_clips.sort(key=lambda x: x.quality_score, reverse=True)
                        complement_clip_info = other_clips[0]
                        
                        complement_video = VideoFileClip(complement_clip_info.file_path).subclip(
                            complement_clip_info.start_time, complement_clip_info.end_time
                        )
                        
                        if complement_video is not None:
                            # Calculate how much we need from the complement clip
                            additional_duration = target_duration - short_clip.duration
                            complement_duration = min(additional_duration, complement_video.duration)
                            complement_segment = complement_video.subclip(0, complement_duration)
                            
                            print(f"         🔧 Combining with different clip (+{complement_duration:.1f}s)")
                            
                            # Combine the clips with a smooth transition
                            complement_segment = complement_segment.fx(vfx.fadein, 0.5)
                            combined_clip = concatenate_videoclips([short_clip, complement_segment])
                            
                            complement_video.close()
                            
                            # Trim to exact target duration if needed
                            if combined_clip.duration > target_duration:
                                final_clip = combined_clip.subclip(0, target_duration)
                                combined_clip.close()
                                return final_clip
                            
                            return combined_clip
                        
                        complement_video.close()
            except Exception as e:
                logger.warning(f"Failed to combine with different clip: {e}")
            
            # Strategy 5: Last resort - slow down the clip slightly to reach target duration
            try:
                if short_clip.duration > 0:
                    speed_factor = short_clip.duration / target_duration
                    if speed_factor >= 0.7:  # Don't slow down more than 30%
                        print(f"         🔧 Slowing down clip by {(1-speed_factor)*100:.1f}% to reach target duration")
                        slowed_clip = short_clip.fx(vfx.speedx, speed_factor)
                        
                        # Validate the slowed clip
                        if slowed_clip is not None and hasattr(slowed_clip, 'duration'):
                            return slowed_clip
                        else:
                            logger.warning("Slowed clip is None or invalid")
                            if slowed_clip:
                                slowed_clip.close()
            except Exception as e:
                logger.warning(f"Failed to slow down clip: {e}")
            
            # Final fallback: Use the short clip as-is and pad with freeze frame
            try:
                print(f"         🔧 Padding short clip with freeze frame")
                freeze_duration = target_duration - short_clip.duration
                if freeze_duration > 0:
                    # Get the last frame and extend it
                    last_frame = short_clip.to_ImageClip(t=max(0, short_clip.duration-0.1), duration=freeze_duration)
                    if last_frame is not None:
                        extended_clip = concatenate_videoclips([short_clip, last_frame])
                        
                        # Validate the extended clip
                        if extended_clip is not None and hasattr(extended_clip, 'duration'):
                            return extended_clip
                        else:
                            logger.warning("Freeze frame extended clip is None or invalid")
                            if extended_clip:
                                extended_clip.close()
                    else:
                        logger.warning("Failed to create freeze frame")
            except Exception as e:
                logger.warning(f"Failed to pad with freeze frame: {e}")
            
            # Absolute fallback: return the original clip
            return short_clip
            
        except Exception as e:
            logger.warning(f"Intelligent clip extension failed: {e}, using original clip")
            return short_clip
    
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
