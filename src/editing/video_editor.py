"""
Simplified Video Editor Module for Drodeo

Handles video editing using MoviePy with focus on Gemini two-step pipeline.
Only includes essential functionality for processing JSON instructions from Gemini.
"""

import os
import logging
from typing import Dict, List
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import moviepy.video.fx.all as vfx

from src.core.gemini_self_translator import EditingInstructions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoEditor:
    """Simplified video editor focused on Gemini two-step pipeline."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the video editor
        
        Args:
            output_dir: Directory to save rendered videos
        """
        self.output_dir = output_dir
        self.ensure_output_directory()
        
    def ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_from_instructions(self, instructions: EditingInstructions, 
                                music_name: str, music_path: str = None) -> str:
        """
        Create video directly from Gemini self-translation JSON instructions
        
        Args:
            instructions: EditingInstructions from GeminiSelfTranslator
            music_name: Name of the music track (for output filename)
            music_path: Path to background music file
            
        Returns:
            Path to the rendered video file
        """
        if not instructions or not instructions.clips:
            raise ValueError(f"No clips found in editing instructions for '{music_name}'")
        
        print(f"🎬 Creating TWO-STEP PIPELINE video for: {music_name}")
        print(f"   📊 Using {len(instructions.clips)} JSON instruction clips")
        print(f"   🎵 Target duration: {instructions.output_settings.get('target_duration', 'N/A')}s")
        print(f"   🔀 Transitions: {len(instructions.transitions)}")
        print(f"   📈 Translation confidence: {instructions.metadata.get('confidence', 'N/A')}")
        
        try:
            # Create video using JSON instructions
            final_video = self._create_instructions_video(instructions, music_name)
            
            # Add music overlay if provided
            if music_path and os.path.exists(music_path):
                print(f"   🎵 Adding music overlay: {os.path.basename(music_path)}")
                final_video = self._add_music_overlay(final_video, music_path)
            
            # Generate output filename
            safe_music_name = "".join(c for c in music_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_filename = f"{safe_music_name}_twostep_{int(final_video.duration)}s.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Render the final video
            print(f"   🎬 Rendering to: {output_filename}")
            self._render_video(final_video, output_path, music_name)
            
            # Clean up
            final_video.close()
            
            print(f"   ✅ Two-step pipeline video created successfully!")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating two-step pipeline video for {music_name}: {str(e)}")
            raise

    def _create_instructions_video(self, instructions: EditingInstructions, music_name: str) -> VideoFileClip:
        """
        Create video using JSON editing instructions from Gemini self-translation
        
        Args:
            instructions: EditingInstructions with MoviePy-compatible parameters
            music_name: Music name for logging
            
        Returns:
            Final video clip
        """
        print(f"   🎯 Creating video from JSON instructions...")
        
        # Load clips based on JSON instructions
        loaded_clips = []
        
        for i, clip_data in enumerate(instructions.clips):
            video_path = clip_data.get('video_path')
            start_time = clip_data.get('start_time', 0)
            end_time = clip_data.get('end_time', 10)
            
            if not video_path or not os.path.exists(video_path):
                print(f"      ⚠️  Skipping clip {i+1}: Video path not found - {video_path}")
                continue
            
            try:
                print(f"      📹 Loading JSON clip {i+1}/{len(instructions.clips)}: {os.path.basename(video_path)}")
                print(f"         ⏱️  Time: {start_time:.1f}s - {end_time:.1f}s ({end_time-start_time:.1f}s)")
                print(f"         ⚡ Energy: {clip_data.get('energy_level', 'medium')}")
                
                # Load and process clip with JSON parameters
                video_clip = self._process_clip_instructions(clip_data)
                loaded_clips.append(video_clip)
                
            except Exception as e:
                print(f"         ❌ Failed to load clip: {e}")
                continue
        
        if not loaded_clips:
            raise ValueError("No clips could be loaded from JSON instructions")
        
        print(f"      ✅ Loaded {len(loaded_clips)} clips from JSON instructions")
        
        # Apply transitions if specified
        if instructions.transitions:
            final_video = self._apply_json_transitions(loaded_clips, instructions.transitions)
        else:
            # Simple concatenation
            print(f"      🔗 Concatenating {len(loaded_clips)} clips...")
            final_video = concatenate_videoclips(loaded_clips, method="compose")
        
        # Trim to target duration to prevent excessive video length
        target_duration = instructions.output_settings.get('target_duration')
        if target_duration and final_video.duration > target_duration:
            print(f"      ✂️  Trimming from {final_video.duration:.1f}s to {target_duration:.1f}s")
            trimmed_video = final_video.subclip(0, target_duration)
            final_video.close()
            final_video = trimmed_video
        
        # Clean up loaded clips
        for clip in loaded_clips:
            clip.close()
        
        return final_video
    
    def _process_clip_instructions(self, clip_data: Dict) -> VideoFileClip:
        """
        Load and process video clip based on JSON instructions
        
        Args:
            clip_data: Dictionary with MoviePy-compatible clip parameters
            
        Returns:
            Processed video clip
        """
        video_path = clip_data['video_path']
        start_time = clip_data.get('start_time', 0)
        end_time = clip_data.get('end_time', 10)
        
        # Validate timestamps against actual video duration
        try:
            # Get the actual video duration
            temp_clip = VideoFileClip(video_path)
            actual_duration = temp_clip.duration
            temp_clip.close()
            
            # Validate and clamp timestamps
            if start_time >= actual_duration:
                logger.warning(f"Start time {start_time:.1f}s >= video duration {actual_duration:.1f}s for {os.path.basename(video_path)}, using 0")
                start_time = 0
            
            if end_time > actual_duration:
                logger.warning(f"End time {end_time:.1f}s > video duration {actual_duration:.1f}s for {os.path.basename(video_path)}, clamping to {actual_duration:.1f}s")
                end_time = actual_duration
            
            if start_time >= end_time:
                logger.warning(f"Start time {start_time:.1f}s >= end time {end_time:.1f}s for {os.path.basename(video_path)}, using full duration")
                start_time = 0
                end_time = min(10, actual_duration)
            
            print(f"         ✅ Validated timestamps: {start_time:.1f}s - {end_time:.1f}s (duration: {end_time-start_time:.1f}s)")
            
        except Exception as e:
            logger.error(f"Failed to validate timestamps for {video_path}: {e}")
            # Fallback to safe defaults
            start_time = 0
            end_time = 10
        
        # Load video with validated timestamps
        clip = VideoFileClip(video_path).subclip(start_time, end_time)
        
        # Apply effects based on JSON parameters
        if clip_data.get('fade_in', 0) > 0:
            clip = clip.fx(vfx.fadein, clip_data['fade_in'])
        
        if clip_data.get('fade_out', 0) > 0:
            clip = clip.fx(vfx.fadeout, clip_data['fade_out'])
        
        if clip_data.get('speed_factor', 1.0) != 1.0:
            clip = clip.fx(vfx.speedx, clip_data['speed_factor'])
        
        return clip
    
    def _apply_json_transitions(self, loaded_clips: List[VideoFileClip], 
                               transitions: List[Dict]) -> VideoFileClip:
        """
        Apply transitions based on JSON instructions
        
        Args:
            loaded_clips: List of loaded video clips
            transitions: List of transition instructions
            
        Returns:
            Final video with transitions applied
        """
        print(f"      🔀 Applying {len(transitions)} JSON transitions...")
        
        if not loaded_clips:
            raise ValueError("No clips to apply transitions to")
        
        # Simple concatenation with fade transitions
        segments = []
        
        for i, clip in enumerate(loaded_clips):
            segment = clip
            
            # Apply fade transitions based on JSON instructions
            matching_transitions = [t for t in transitions if t.get('next_clip_index') == i]
            
            if matching_transitions:
                transition = matching_transitions[0]
                fade_duration = transition.get('duration', 0.5)
                
                if i > 0:  # Fade in
                    segment = segment.fx(vfx.fadein, fade_duration)
                if i < len(loaded_clips) - 1:  # Fade out
                    segment = segment.fx(vfx.fadeout, fade_duration)
            
            segments.append(segment)
        
        # Concatenate all segments
        final_video = concatenate_videoclips(segments, method="compose")
        return final_video
    
    def _add_music_overlay(self, video: VideoFileClip, music_path: str) -> VideoFileClip:
        """
        Add background music to a video using simple approach
        
        Args:
            video: Video clip to add music to
            music_path: Path to music file
            
        Returns:
            Video with music overlay
        """
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"Music file not found: {music_path}")
        
        print(f"   🎵 Loading music file: {os.path.basename(music_path)}")
        
        # Load audio file
        audio = AudioFileClip(music_path)
        if audio is None:
            raise ValueError(f"Failed to load audio file: {music_path}")
        
        # Validate audio properties
        audio_duration = audio.duration
        if audio_duration is None or audio_duration <= 0:
            audio.close()
            raise ValueError(f"Invalid audio duration ({audio_duration}s) for: {music_path}")
        
        print(f"   🎵 Music duration: {audio_duration:.1f}s, Video duration: {video.duration:.1f}s")
        print(f"   🎵 Using raw audio file directly")
        
        # Create video with new audio
        video_no_audio = video.without_audio()
        video_with_audio = video_no_audio.set_audio(audio)
        
        print(f"   ✅ Audio overlay completed successfully")
        return video_with_audio
    
    def _render_video(self, video: VideoFileClip, output_path: str, music_name: str):
        """
        Render video to file with simplified error handling
        
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
        print(f"      Audio: {'Yes' if video.audio is not None else 'No'}")
        
        # Render video with appropriate settings
        if video.audio is not None:
            print("   🎵 Rendering with audio...")
            video.write_videofile(
                output_path,
                fps=min(fps, 30),
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            print("   ✅ Video rendered successfully with audio")
        else:
            print("   📹 Rendering video without audio...")
            video.write_videofile(
                output_path,
                fps=min(fps, 30),
                codec='libx264',
                verbose=False,
                logger=None
            )
            print("   ✅ Video rendered successfully without audio")

def main():
    """Test the simplified video editor functionality"""
    editor = VideoEditor()
    print("✅ Simplified video editor initialized successfully")

if __name__ == "__main__":
    main()
