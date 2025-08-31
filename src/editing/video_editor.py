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

# Define VideoClip dataclass locally since video_processor was removed
@dataclass
class VideoClip:
    """Video clip information for editing"""
    file_path: str
    start_time: float
    end_time: float
    quality_score: float
    theme_scores: Dict[str, float]
    ai_description: str
    
    @property
    def duration(self) -> float:
        """Get clip duration"""
        return self.end_time - self.start_time

# Import multimodal analysis result and self-translation instructions
try:
    from src.core.gemini_multimodal_analyzer import MultimodalAnalysisResult
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False
    MultimodalAnalysisResult = None

try:
    from src.core.gemini_self_translator import EditingInstructions
    SELF_TRANSLATION_AVAILABLE = True
except ImportError:
    SELF_TRANSLATION_AVAILABLE = False
    EditingInstructions = None

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
        
    def create_from_instructions(self, instructions: 'EditingInstructions', 
                                music_name: str, music_path: Optional[str] = None) -> str:
        """
        Create video directly from Gemini self-translation JSON instructions
        
        Args:
            instructions: EditingInstructions from GeminiSelfTranslator
            music_name: Name of the music track (for output filename)
            music_path: Path to background music file
            
        Returns:
            Path to the rendered video file
        """
        if not SELF_TRANSLATION_AVAILABLE or not instructions:
            raise ValueError("EditingInstructions required but not available")
        
        if not instructions.clips:
            raise ValueError(f"No clips found in editing instructions for '{music_name}'")
        
        print(f"🎬 Creating TWO-STEP PIPELINE video for: {music_name}")
        print(f"   📊 Using {len(instructions.clips)} JSON instruction clips")
        print(f"   🎵 Target duration: {instructions.output_settings.get('target_duration', 'N/A')}s")
        print(f"   🔀 Transitions: {len(instructions.transitions)}")
        print(f"   📈 Translation confidence: {instructions.metadata.get('confidence', 'N/A')}")
        
        try:
            # Create video using JSON instructions
            final_video = self._create_instructions_video(instructions, music_name)
            
            # Add music overlay using JSON audio sync settings
            if music_path and os.path.exists(music_path):
                print(f"   🎵 Adding music overlay with JSON settings: {os.path.basename(music_path)}")
                final_video = self._add_music_overlay_with_settings(
                    final_video, music_path, instructions.audio_sync
                )
            
            # Generate output filename
            safe_music_name = "".join(c for c in music_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_filename = f"{safe_music_name}_twostep_{int(final_video.duration)}s.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Render the final video using JSON output settings
            print(f"   🎬 Rendering to: {output_filename}")
            self._render_video_with_settings(final_video, output_path, music_name, instructions.output_settings)
            
            # Clean up
            final_video.close()
            
            print(f"   ✅ Two-step pipeline video created successfully!")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating two-step pipeline video for {music_name}: {str(e)}")
            raise

    def create_from_multimodal_analysis(self, multimodal_result: 'MultimodalAnalysisResult', 
                                       music_name: str, music_path: Optional[str] = None) -> str:
        """
        Create video directly from Gemini multimodal analysis results
        
        Args:
            multimodal_result: Results from GeminiMultimodalAnalyzer.analyze_batch()
            music_name: Name of the music track (for output filename)
            music_path: Path to background music file
            
        Returns:
            Path to the rendered video file
        """
        if not MULTIMODAL_AVAILABLE or not multimodal_result:
            raise ValueError("Multimodal analysis result required but not available")
        
        if not multimodal_result.clip_selections:
            raise ValueError(f"No clip selections found in multimodal analysis for '{music_name}'")
        
        print(f"🎬 Creating MULTIMODAL music-driven video for: {music_name}")
        print(f"   📊 Using {len(multimodal_result.clip_selections)} multimodal clip selections")
        print(f"   🎵 Audio duration: {multimodal_result.audio_duration:.1f}s")
        print(f"   🎯 Cross-video transitions: {len(multimodal_result.cross_video_transitions)}")
        print(f"   🔗 Sequencing plan: {len(multimodal_result.sequencing_plan)} steps")
        print(f"   📈 Sync confidence: {multimodal_result.sync_confidence:.2f}")
        
        try:
            # Create video using multimodal analysis
            final_video = self._create_multimodal_video(multimodal_result, music_name)
            
            # Add music overlay if provided
            if music_path and os.path.exists(music_path):
                print(f"   🎵 Adding music overlay: {os.path.basename(music_path)}")
                final_video = self._add_music_overlay(final_video, music_path)
            
            # Generate output filename
            safe_music_name = "".join(c for c in music_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_filename = f"{safe_music_name}_multimodal_{int(final_video.duration)}s.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Render the final video
            print(f"   🎬 Rendering to: {output_filename}")
            self._render_video(final_video, output_path, music_name)
            
            # Clean up
            final_video.close()
            
            print(f"   ✅ Multimodal music-driven video created successfully!")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating multimodal video for {music_name}: {str(e)}")
            raise

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
        Add background music to a video with robust error handling
        
        Args:
            video: Video clip to add music to
            music_path: Path to music file
            
        Returns:
            Video with music overlay
        """
        try:
            # Validate music file exists
            if not os.path.exists(music_path):
                logger.warning(f"Music file not found: {music_path}")
                return video
            
            # Load audio with comprehensive error handling
            try:
                audio = AudioFileClip(music_path)
            except Exception as e:
                logger.warning(f"Failed to load audio file {music_path}: {e}")
                return video
            
            # Validate audio loaded successfully
            if audio is None:
                logger.warning(f"Audio file loaded as None: {music_path}")
                return video
            
            # Check audio duration
            try:
                audio_duration = audio.duration
                if audio_duration is None or audio_duration <= 0:
                    logger.warning(f"Invalid audio duration: {audio_duration}")
                    audio.close()
                    return video
            except Exception as e:
                logger.warning(f"Failed to get audio duration: {e}")
                audio.close()
                return video
            
            # Trim or loop audio to match video duration
            try:
                if audio_duration > video.duration:
                    # Audio is longer, trim it
                    audio = audio.subclip(0, video.duration)
                elif audio_duration < video.duration:
                    # Audio is shorter, loop it
                    loops_needed = int(np.ceil(video.duration / audio_duration))
                    if loops_needed > 1:
                        audio_clips = [audio] * loops_needed
                        audio = concatenate_audioclips(audio_clips)
                        audio = audio.subclip(0, video.duration)
                
                # Set music volume to 70% for better audibility
                audio = audio.volumex(0.7)
                
            except Exception as e:
                logger.warning(f"Failed to process audio duration: {e}")
                audio.close()
                return video
            
            # Handle original video audio with better error handling
            try:
                if video.audio is not None:
                    try:
                        # Test if original audio is accessible
                        _ = video.audio.duration
                        
                        # Mix original audio with background music
                        original_audio = video.audio.volumex(0.3)  # Lower original audio
                        final_audio = CompositeAudioClip([original_audio, audio])
                    except Exception as e:
                        logger.warning(f"Failed to mix with original audio, using music only: {e}")
                        final_audio = audio
                else:
                    # Use only background music
                    final_audio = audio
                
                # Create video with new audio - remove original audio first to avoid conflicts
                video_no_audio = video.without_audio()
                video_with_audio = video_no_audio.set_audio(final_audio)
                
                # Clean up
                audio.close()
                
                return video_with_audio
                
            except Exception as e:
                logger.warning(f"Failed to set audio to video: {e}")
                audio.close()
                return video
            
        except Exception as e:
            logger.warning(f"Failed to add music overlay: {str(e)}")
            return video  # Return original video if music fails
    
    def _render_video(self, video: VideoFileClip, output_path: str, music_name: str):
        """
        Render video to file with robust error handling
        
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
        
        try:
            # Check if video has audio and handle accordingly
            has_audio = video.audio is not None
            print(f"      Audio: {'Yes' if has_audio else 'No'}")
            
            if has_audio:
                # Try rendering with audio first
                try:
                    print("   🎵 Rendering with audio...")
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
                    print("   ✅ Video rendered successfully with audio")
                    return
                    
                except Exception as audio_error:
                    logger.warning(f"Audio rendering failed: {audio_error}")
                    print("   ⚠️  Audio rendering failed, trying without audio...")
                    
                    # Try rendering without audio as fallback
                    try:
                        video_no_audio = video.without_audio()
                        video_no_audio.write_videofile(
                            output_path,
                            fps=min(fps, 30),
                            codec='libx264',
                            verbose=False,
                            logger=None
                        )
                        video_no_audio.close()
                        print("   ✅ Video rendered successfully without audio")
                        return
                        
                    except Exception as no_audio_error:
                        logger.error(f"Video rendering without audio also failed: {no_audio_error}")
                        raise
            else:
                # No audio, render video only
                print("   📹 Rendering video without audio...")
                video.write_videofile(
                    output_path,
                    fps=min(fps, 30),
                    codec='libx264',
                    verbose=False,
                    logger=None
                )
                print("   ✅ Video rendered successfully")
            
        except Exception as e:
            logger.error(f"Rendering failed: {str(e)}")
            
            # Final fallback: try with minimal settings
            try:
                print("   🔧 Trying fallback rendering with minimal settings...")
                video_fallback = video.without_audio() if video.audio else video
                video_fallback.write_videofile(
                    output_path,
                    fps=24,  # Lower FPS
                    codec='libx264',
                    preset='ultrafast',  # Fastest encoding
                    verbose=False,
                    logger=None
                )
                if video_fallback != video:
                    video_fallback.close()
                print("   ✅ Fallback rendering successful")
                
            except Exception as fallback_error:
                logger.error(f"Fallback rendering also failed: {fallback_error}")
                raise Exception(f"All rendering attempts failed. Last error: {fallback_error}")
    
    def _create_multimodal_video(self, multimodal_result: 'MultimodalAnalysisResult', music_name: str) -> VideoFileClip:
        """
        Create video using Gemini multimodal analysis results with cross-video clip selection
        
        Args:
            multimodal_result: Results from GeminiMultimodalAnalyzer.analyze_batch()
            music_name: Music name for logging
            
        Returns:
            Final video clip
        """
        print(f"   🎯 Creating multimodal video with cross-video clip selection...")
        
        # Load clips based on multimodal analysis selections
        loaded_clips = []
        clip_info = []
        
        for i, clip_selection in enumerate(multimodal_result.clip_selections):
            video_path = clip_selection.get('video_path')
            start_time = clip_selection.get('start_time', 0)
            end_time = clip_selection.get('end_time', 10)
            energy_level = clip_selection.get('energy_level', 'medium')
            
            if not video_path or not os.path.exists(video_path):
                print(f"      ⚠️  Skipping clip {i+1}: Video path not found - {video_path}")
                continue
            
            try:
                print(f"      📹 Loading multimodal clip {i+1}/{len(multimodal_result.clip_selections)}: {os.path.basename(video_path)}")
                print(f"         ⏱️  Time: {start_time:.1f}s - {end_time:.1f}s ({end_time-start_time:.1f}s)")
                print(f"         ⚡ Energy: {energy_level}")
                
                # Load video clip with specified timing
                video_clip = VideoFileClip(video_path).subclip(start_time, end_time)
                video_clip = self._apply_video_effects(video_clip)
                
                loaded_clips.append(video_clip)
                clip_info.append({
                    'path': video_path,
                    'start': start_time,
                    'end': end_time,
                    'energy': energy_level,
                    'duration': end_time - start_time
                })
                
            except Exception as e:
                print(f"         ❌ Failed to load clip: {e}")
                continue
        
        if not loaded_clips:
            raise ValueError("No clips could be loaded from multimodal analysis")
        
        print(f"      ✅ Loaded {len(loaded_clips)} clips from multimodal analysis")
        
        # Create video segments based on cross-video transitions
        if multimodal_result.cross_video_transitions:
            final_video = self._create_cross_video_transitions(
                loaded_clips, clip_info, multimodal_result
            )
        else:
            # Fallback: Use sequencing plan or simple concatenation
            final_video = self._create_sequenced_video(
                loaded_clips, clip_info, multimodal_result
            )
        
        # Clean up loaded clips
        for clip in loaded_clips:
            clip.close()
        
        return final_video
    
    def _create_cross_video_transitions(self, loaded_clips: List[VideoFileClip], 
                                       clip_info: List[Dict], 
                                       multimodal_result: 'MultimodalAnalysisResult') -> VideoFileClip:
        """
        Create video with cross-video transitions based on Gemini recommendations
        
        Args:
            loaded_clips: List of loaded video clips
            clip_info: Information about each clip
            multimodal_result: Multimodal analysis results
            
        Returns:
            Final video with cross-video transitions
        """
        print(f"      🔀 Creating cross-video transitions...")
        
        # Get transition points and sort them
        transitions = sorted(multimodal_result.cross_video_transitions, 
                           key=lambda x: x.get('timestamp', 0))
        
        # Create segments between transition points
        segments = []
        current_time = 0.0
        target_duration = multimodal_result.audio_duration
        
        print(f"         🎵 Target duration: {target_duration:.1f}s")
        print(f"         🔀 Transitions: {len(transitions)}")
        
        # Add final transition at end if not present
        if not transitions or transitions[-1].get('timestamp', 0) < target_duration:
            transitions.append({'timestamp': target_duration, 'type': 'end'})
        
        for i, transition in enumerate(transitions):
            transition_time = transition.get('timestamp', current_time + 10)
            segment_duration = transition_time - current_time
            
            if segment_duration <= 0:
                continue
            
            # Select clip for this segment - prioritize different video sources
            clip_index = self._select_best_clip_for_segment(
                i, segment_duration, loaded_clips, clip_info, current_time
            )
            selected_clip = loaded_clips[clip_index]
            selected_info = clip_info[clip_index]
            
            print(f"         📹 Segment {i+1}: {current_time:.1f}s - {transition_time:.1f}s ({segment_duration:.1f}s)")
            print(f"            Using: {os.path.basename(selected_info['path'])} (Energy: {selected_info['energy']})")
            
            # Create segment of appropriate duration
            if selected_clip.duration >= segment_duration:
                # Clip is long enough, use a portion
                segment = selected_clip.subclip(0, segment_duration)
            else:
                # Extend clip to match segment duration
                segment = self._extend_multimodal_clip(selected_clip, segment_duration, loaded_clips, clip_index)
            
            # Add transitions based on energy and beat alignment
            if i > 0:  # Fade in for all segments except first
                fade_duration = min(0.5, segment_duration * 0.1)
                segment = segment.fx(vfx.fadein, fade_duration)
            
            if i < len(transitions) - 1:  # Fade out for all segments except last
                fade_duration = min(0.5, segment_duration * 0.1)
                segment = segment.fx(vfx.fadeout, fade_duration)
            
            segments.append(segment)
            current_time = transition_time
            
            # Stop if we've reached the target duration
            if current_time >= target_duration:
                break
        
        if not segments:
            # Fallback: use first clip
            print(f"         ⚠️  No segments created, using first clip as fallback")
            return loaded_clips[0].subclip(0, min(target_duration, loaded_clips[0].duration))
        
        # Concatenate all segments
        print(f"      🔗 Concatenating {len(segments)} cross-video segments...")
        final_video = concatenate_videoclips(segments, method="compose")
        
        # Trim to exact target duration if needed
        if final_video.duration > target_duration:
            print(f"      ✂️  Trimming from {final_video.duration:.1f}s to {target_duration:.1f}s")
            trimmed_video = final_video.subclip(0, target_duration)
            final_video.close()
            final_video = trimmed_video
        
        return final_video
    
    def _create_sequenced_video(self, loaded_clips: List[VideoFileClip], 
                               clip_info: List[Dict], 
                               multimodal_result: 'MultimodalAnalysisResult') -> VideoFileClip:
        """
        Create video using sequencing plan (fallback method)
        
        Args:
            loaded_clips: List of loaded video clips
            clip_info: Information about each clip
            multimodal_result: Multimodal analysis results
            
        Returns:
            Final sequenced video
        """
        print(f"      📋 Creating sequenced video using multimodal plan...")
        
        target_duration = multimodal_result.audio_duration
        
        # Use sequencing plan if available
        if multimodal_result.sequencing_plan:
            # Sort by sequence order
            sequencing = sorted(multimodal_result.sequencing_plan, 
                              key=lambda x: x.get('sequence_order', 0))
            
            segments = []
            remaining_duration = target_duration
            
            for seq_item in sequencing:
                if remaining_duration <= 0:
                    break
                
                # Find matching clip
                video_name = seq_item.get('video', '')
                matching_clips = [(i, info) for i, info in enumerate(clip_info) 
                                if os.path.basename(info['path']) == video_name]
                
                if matching_clips:
                    clip_index, info = matching_clips[0]
                    clip = loaded_clips[clip_index]
                    
                    # Use portion of remaining duration
                    segment_duration = min(remaining_duration, clip.duration)
                    segment = clip.subclip(0, segment_duration)
                    
                    # Add transitions
                    if segments:  # Not first segment
                        segment = segment.fx(vfx.fadein, 0.3)
                    
                    segments.append(segment)
                    remaining_duration -= segment_duration
                    
                    print(f"         📹 Added sequence: {video_name} ({segment_duration:.1f}s)")
            
            if segments:
                final_video = concatenate_videoclips(segments, method="compose")
                return final_video
        
        # Final fallback: simple concatenation
        print(f"      📹 Using simple concatenation fallback...")
        segments = []
        remaining_duration = target_duration
        
        for i, clip in enumerate(loaded_clips):
            if remaining_duration <= 0:
                break
            
            segment_duration = min(remaining_duration, clip.duration)
            segment = clip.subclip(0, segment_duration)
            
            # Add transitions
            if i > 0:
                segment = segment.fx(vfx.fadein, 0.3)
            if i < len(loaded_clips) - 1 and remaining_duration > segment_duration:
                segment = segment.fx(vfx.fadeout, 0.3)
            
            segments.append(segment)
            remaining_duration -= segment_duration
        
        if segments:
            return concatenate_videoclips(segments, method="compose")
        else:
            # Ultimate fallback
            return loaded_clips[0].subclip(0, min(target_duration, loaded_clips[0].duration))
    
    def _extend_multimodal_clip(self, short_clip: VideoFileClip, target_duration: float, 
                               all_clips: List[VideoFileClip], current_index: int) -> VideoFileClip:
        """
        Extend a clip for multimodal video creation
        
        Args:
            short_clip: The clip that's too short
            target_duration: Desired duration
            all_clips: All available clips
            current_index: Index of current clip
            
        Returns:
            Extended video clip
        """
        if short_clip.duration >= target_duration:
            return short_clip.subclip(0, target_duration)
        
        # Strategy 1: Slow down the clip slightly (up to 20%)
        speed_factor = short_clip.duration / target_duration
        if speed_factor >= 0.8:  # Don't slow down more than 20%
            print(f"         🔧 Slowing down clip by {(1-speed_factor)*100:.1f}% for multimodal sync")
            return short_clip.fx(vfx.speedx, speed_factor)
        
        # Strategy 2: Combine with another clip
        if len(all_clips) > 1:
            other_index = (current_index + 1) % len(all_clips)
            other_clip = all_clips[other_index]
            
            additional_duration = target_duration - short_clip.duration
            additional_segment = other_clip.subclip(0, min(additional_duration, other_clip.duration))
            additional_segment = additional_segment.fx(vfx.fadein, 0.3)
            
            print(f"         🔧 Combining clips for multimodal segment (+{additional_segment.duration:.1f}s)")
            combined = concatenate_videoclips([short_clip, additional_segment])
            
            # Trim to exact duration
            if combined.duration > target_duration:
                final_clip = combined.subclip(0, target_duration)
                combined.close()
                return final_clip
            
            return combined
        
        # Strategy 3: Freeze frame extension
        freeze_duration = target_duration - short_clip.duration
        last_frame = short_clip.to_ImageClip(t=short_clip.duration-0.1, duration=freeze_duration)
        
        print(f"         🔧 Adding freeze frame extension (+{freeze_duration:.1f}s)")
        return concatenate_videoclips([short_clip, last_frame])

    def _select_best_clip_for_segment(self, segment_index: int, segment_duration: float,
                                     loaded_clips: List[VideoFileClip], clip_info: List[Dict],
                                     current_time: float) -> int:
        """
        Select the best clip for a segment, prioritizing different video sources
        
        Args:
            segment_index: Index of current segment
            segment_duration: Duration needed for this segment
            loaded_clips: List of loaded video clips
            clip_info: Information about each clip
            current_time: Current time in the video
            
        Returns:
            Index of the best clip to use
        """
        if not loaded_clips:
            return 0
        
        # Track which video sources we've used recently
        recent_sources = set()
        lookback = min(3, segment_index)  # Look back at last 3 segments
        
        # For the first few segments, try to use different video sources
        if segment_index < len(loaded_clips):
            # Try to use a different video source for each early segment
            for i, info in enumerate(clip_info):
                video_source = os.path.basename(info['path'])
                if video_source not in recent_sources:
                    print(f"            🎯 Selected different video source: {video_source}")
                    return i
        
        # Find clips that match the segment duration well
        duration_scores = []
        for i, (clip, info) in enumerate(zip(loaded_clips, clip_info)):
            video_source = os.path.basename(info['path'])
            
            # Score based on duration match
            duration_score = 1.0
            if clip.duration >= segment_duration:
                # Prefer clips that are close to the needed duration
                duration_score = min(1.0, segment_duration / clip.duration)
            else:
                # Penalize clips that are too short
                duration_score = clip.duration / segment_duration * 0.8
            
            # Bonus for using different video source
            source_bonus = 0.2 if video_source not in recent_sources else 0.0
            
            # Energy matching bonus (if available)
            energy_bonus = 0.1 if info.get('energy', 'medium') == 'high' else 0.0
            
            total_score = duration_score + source_bonus + energy_bonus
            duration_scores.append((i, total_score, video_source))
        
        # Sort by score and select the best
        duration_scores.sort(key=lambda x: x[1], reverse=True)
        best_index, best_score, best_source = duration_scores[0]
        
        print(f"            🎯 Selected clip {best_index} from {best_source} (score: {best_score:.2f})")
        return best_index

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
    
    def _create_instructions_video(self, instructions: 'EditingInstructions', music_name: str) -> VideoFileClip:
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
        
        # CRITICAL FIX: Validate timestamps against actual video duration
        try:
            # First, get the actual video duration
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
                end_time = min(10, actual_duration)  # Use first 10 seconds or full duration if shorter
            
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
        
        # Apply basic video effects
        clip = self._apply_video_effects(clip)
        
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
        
        # For now, implement simple concatenation with fade transitions
        # This can be enhanced later with more complex transition types
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
    
    def _add_music_overlay_with_settings(self, video: VideoFileClip, music_path: str, 
                                        audio_sync: Dict) -> VideoFileClip:
        """
        Add music overlay using JSON audio sync settings
        
        Args:
            video: Video clip to add music to
            music_path: Path to music file
            audio_sync: Audio synchronization settings from JSON
            
        Returns:
            Video with music overlay
        """
        try:
            # Load audio
            audio = AudioFileClip(music_path)
            
            # Apply JSON volume settings
            music_volume = audio_sync.get('music_volume', 0.7)
            original_audio_volume = audio_sync.get('original_audio_volume', 0.3)
            
            # Trim or loop audio to match video duration
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            elif audio.duration < video.duration:
                loops_needed = int(np.ceil(video.duration / audio.duration))
                if loops_needed > 1:
                    audio_clips = [audio] * loops_needed
                    audio = concatenate_audioclips(audio_clips)
                    audio = audio.subclip(0, video.duration)
            
            # Set music volume from JSON settings
            audio = audio.volumex(music_volume)
            
            # Handle original video audio
            if video.audio is not None:
                try:
                    # Mix original audio with background music using JSON settings
                    original_audio = video.audio.volumex(original_audio_volume)
                    final_audio = CompositeAudioClip([original_audio, audio])
                except Exception as e:
                    logger.warning(f"Failed to mix with original audio, using music only: {e}")
                    final_audio = audio
            else:
                final_audio = audio
            
            # Apply fade settings from JSON
            fade_in_duration = audio_sync.get('fade_in_duration', 0)
            fade_out_duration = audio_sync.get('fade_out_duration', 0)
            
            if fade_in_duration > 0:
                final_audio = final_audio.fx(audio_fadein, fade_in_duration)
            if fade_out_duration > 0:
                final_audio = final_audio.fx(audio_fadeout, fade_out_duration)
            
            # Create video with new audio
            video_no_audio = video.without_audio()
            video_with_audio = video_no_audio.set_audio(final_audio)
            
            # Clean up
            audio.close()
            
            return video_with_audio
            
        except Exception as e:
            logger.warning(f"Failed to add music overlay with JSON settings: {str(e)}")
            return video  # Return original video if music fails
    
    def _render_video_with_settings(self, video: VideoFileClip, output_path: str, 
                                   music_name: str, output_settings: Dict):
        """
        Render video using JSON output settings
        
        Args:
            video: Video to render
            output_path: Output file path
            music_name: Music name for progress display
            output_settings: Output settings from JSON
        """
        # Get settings from JSON or use defaults
        fps = output_settings.get('fps', 30)
        codec = output_settings.get('codec', 'libx264')
        audio_codec = output_settings.get('audio_codec', 'aac')
        
        # Get video properties
        duration = video.duration
        resolution = (video.w, video.h)
        
        print(f"   📊 Video properties (JSON settings):")
        print(f"      Duration: {duration:.1f}s")
        print(f"      FPS: {fps} (from JSON)")
        print(f"      Resolution: {resolution[0]}x{resolution[1]}")
        print(f"      Codec: {codec} (from JSON)")
        
        try:
            # Check if video has audio
            has_audio = video.audio is not None
            print(f"      Audio: {'Yes' if has_audio else 'No'}")
            
            if has_audio:
                # Render with audio using JSON settings
                print("   🎵 Rendering with audio (JSON settings)...")
                video.write_videofile(
                    output_path,
                    fps=fps,
                    codec=codec,
                    audio_codec=audio_codec,
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None
                )
                print("   ✅ Video rendered successfully with JSON settings")
            else:
                # Render without audio
                print("   📹 Rendering video without audio (JSON settings)...")
                video.write_videofile(
                    output_path,
                    fps=fps,
                    codec=codec,
                    verbose=False,
                    logger=None
                )
                print("   ✅ Video rendered successfully")
                
        except Exception as e:
            logger.error(f"JSON settings rendering failed: {str(e)}")
            # Fallback to standard rendering
            print("   🔧 Falling back to standard rendering...")
            self._render_video(video, output_path, music_name)

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
