"""
Beat-Synchronized Video Editor

Advanced video editor that synchronizes video transitions with musical beats
for professional-quality video editing.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from moviepy.video.fx import resize
import moviepy.video.fx.all as vfx
import numpy as np
from pathlib import Path

from src.core.video_processor import VideoClip
from src.audio.audio_analyzer import AudioAnalyzer, AudioFeatures
from src.editing.video_editor import VideoEditor
from src.editing.music_downloader import MusicDownloader

logger = logging.getLogger(__name__)

@dataclass
class BeatSyncClip:
    """Video clip with beat synchronization information."""
    video_clip: VideoClip
    start_beat: float
    end_beat: float
    transition_type: str
    energy_level: float

class BeatSyncVideoEditor(VideoEditor):
    """Enhanced video editor with beat synchronization capabilities."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize beat-synchronized video editor."""
        super().__init__(output_dir)
        self.audio_analyzer = AudioAnalyzer()
        
    def create_beat_synced_video(self, clips: List[VideoClip], theme: str, 
                               target_duration: int = 45, music_path: Optional[str] = None,
                               reshuffle_clips: bool = True) -> str:
        """
        Create a beat-synchronized themed video.
        
        Args:
            clips: List of video clips to include
            theme: Theme name
            target_duration: Target duration in seconds
            music_path: Path to background music file
            reshuffle_clips: Whether to reshuffle clips for better flow
            
        Returns:
            Path to the rendered video file
        """
        if not clips:
            raise ValueError(f"No clips provided for theme '{theme}'")
        
        print(f"🎬 Creating beat-synced {theme} themed video...")
        print(f"   📊 Using {len(clips)} clips")
        print(f"   ⏱️  Target duration: {target_duration}s")
        
        # Download or find music if not provided
        if not music_path:
            music_path = self._get_theme_music(theme, target_duration)
        
        if not music_path or not os.path.exists(music_path):
            print(f"   ⚠️  No music found, creating video without beat sync")
            return super().create_themed_video(clips, theme, target_duration, music_path)
        
        # Analyze music for beat detection
        print(f"   🎵 Analyzing music for beat synchronization...")
        audio_features = self.audio_analyzer.analyze_audio_file(music_path)
        
        if not audio_features:
            print(f"   ⚠️  Audio analysis failed, creating standard video")
            return super().create_themed_video(clips, theme, target_duration, music_path)
        
        # Reshuffle clips if requested
        if reshuffle_clips:
            clips = self._reshuffle_clips_for_flow(clips, audio_features, theme)
        
        # Create beat-synchronized video
        return self._create_beat_synced_video_internal(clips, theme, target_duration, music_path, audio_features)
    
    def _get_theme_music(self, theme: str, duration: int) -> Optional[str]:
        """Get or download theme music."""
        # For calm/mellow theme, search for appropriate music
        if theme.lower() in ['calm', 'mellow', 'peaceful', 'relaxing']:
            if self.music_downloader:
                try:
                    print(f"   🔍 Searching for {theme} music...")
                    return self.music_downloader.download_theme_music('peaceful', duration)
                except Exception as e:
                    logger.warning(f"Music download failed: {e}")
        
        # Fallback to existing music
        return self._find_theme_music(theme, duration)
    
    def _reshuffle_clips_for_flow(self, clips: List[VideoClip], audio_features: AudioFeatures, theme: str) -> List[VideoClip]:
        """
        Reshuffle clips to create better visual flow based on music characteristics.
        
        Args:
            clips: Original clips
            audio_features: Music analysis results
            theme: Video theme
            
        Returns:
            Reshuffled clips
        """
        print(f"   🔀 Reshuffling clips for optimal flow...")
        
        # Analyze music energy progression
        energy_analysis = self.audio_analyzer.analyze_music_energy(audio_features)
        
        # Sort clips by different criteria based on theme and music
        if theme.lower() in ['calm', 'mellow', 'peaceful']:
            # For calm themes, prioritize smooth motion and scenic beauty
            clips.sort(key=lambda c: (c.motion_score * 0.3 + c.quality_score * 0.7), reverse=False)
        elif energy_analysis['tempo_category'] == 'slow':
            # For slow tempo, start with high quality, end with high motion
            clips.sort(key=lambda c: c.quality_score, reverse=True)
        else:
            # For faster tempo, alternate between high and low motion
            high_motion = sorted([c for c in clips if c.motion_score > np.median([clip.motion_score for clip in clips])], 
                               key=lambda c: c.motion_score, reverse=True)
            low_motion = sorted([c for c in clips if c.motion_score <= np.median([clip.motion_score for clip in clips])], 
                              key=lambda c: c.quality_score, reverse=True)
            
            # Interleave high and low motion clips
            reshuffled = []
            for i in range(max(len(high_motion), len(low_motion))):
                if i < len(high_motion):
                    reshuffled.append(high_motion[i])
                if i < len(low_motion):
                    reshuffled.append(low_motion[i])
            clips = reshuffled
        
        print(f"      ✅ Clips reshuffled based on {energy_analysis['tempo_category']} tempo ({audio_features.tempo:.1f} BPM)")
        return clips
    
    def _create_beat_synced_video_internal(self, clips: List[VideoClip], theme: str, 
                                         target_duration: int, music_path: str, 
                                         audio_features: AudioFeatures) -> str:
        """Internal method to create beat-synchronized video."""
        
        # Calculate optimal transition points based on beats
        transition_points = self.audio_analyzer.find_optimal_transition_points(
            audio_features, target_duration, len(clips)
        )
        
        print(f"   🎯 Beat-aligned transition points: {len(transition_points)}")
        
        # Load and prepare video clips with beat timing
        video_clips = []
        current_time = 0.0
        
        for i, clip in enumerate(clips):
            print(f"   📹 Loading clip {i+1}/{len(clips)}: {os.path.basename(clip.file_path)}")
            
            # Calculate clip duration based on transition points
            if i < len(transition_points):
                clip_duration = transition_points[i] - current_time
            else:
                # Last clip gets remaining time
                clip_duration = target_duration - current_time
            
            # Ensure minimum clip duration
            clip_duration = max(clip_duration, 2.0)
            
            # Load and trim video clip
            video_clip = VideoFileClip(clip.file_path).subclip(clip.start_time, clip.end_time)
            
            # Adjust clip duration to match beat timing
            if video_clip.duration > clip_duration:
                # Trim clip to fit beat timing
                video_clip = video_clip.subclip(0, clip_duration)
            elif video_clip.duration < clip_duration:
                # Loop clip if too short
                loops_needed = int(np.ceil(clip_duration / video_clip.duration))
                if loops_needed > 1:
                    looped_clips = [video_clip] * loops_needed
                    video_clip = concatenate_videoclips(looped_clips)
                    video_clip = video_clip.subclip(0, clip_duration)
            
            # Apply theme-specific effects
            video_clip = self._apply_theme_effects(video_clip, theme)
            
            # Apply beat-synchronized transitions
            video_clip = self._apply_beat_transitions(video_clip, i, len(clips), audio_features)
            
            video_clips.append(video_clip)
            current_time += video_clip.duration
            
            # Stop if we've reached target duration
            if current_time >= target_duration:
                break
        
        # Concatenate all clips
        print(f"   🔗 Concatenating {len(video_clips)} beat-synced clips...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Trim to exact target duration
        if final_video.duration > target_duration:
            print(f"   ✂️  Trimming from {final_video.duration:.1f}s to {target_duration}s")
            final_video = final_video.subclip(0, target_duration)
        
        # Add music overlay
        print(f"   🎵 Adding beat-synced music overlay: {os.path.basename(music_path)}")
        final_video = self._add_music_overlay(final_video, music_path)
        
        # Generate output filename
        output_filename = f"{theme}_beat_synced_{len(clips)}clips_{int(final_video.duration)}s.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Render the final video
        print(f"   🎬 Rendering beat-synced video to: {output_filename}")
        self._render_video(final_video, output_path, theme)
        
        # Clean up
        final_video.close()
        for clip in video_clips:
            clip.close()
        
        print(f"   ✅ Beat-synced {theme} video created successfully!")
        return output_path
    
    def _apply_beat_transitions(self, clip: VideoFileClip, clip_index: int, 
                              total_clips: int, audio_features: AudioFeatures) -> VideoFileClip:
        """
        Apply beat-synchronized transitions to a clip.
        
        Args:
            clip: Video clip to modify
            clip_index: Index of current clip
            total_clips: Total number of clips
            audio_features: Audio analysis results
            
        Returns:
            Modified video clip with transitions
        """
        # Calculate transition duration based on tempo
        beat_interval = audio_features.average_beat_interval
        transition_duration = min(beat_interval / 2, 1.0)  # Half beat or max 1 second
        
        # Apply transitions based on position and tempo
        if clip_index == 0:
            # First clip: fade in
            clip = clip.fx(vfx.fadein, transition_duration)
        elif clip_index == total_clips - 1:
            # Last clip: fade out
            clip = clip.fx(vfx.fadeout, transition_duration)
        else:
            # Middle clips: crossfade
            clip = clip.fx(vfx.fadein, transition_duration).fx(vfx.fadeout, transition_duration)
        
        return clip
    
    def replace_music_in_existing_video(self, video_path: str, new_music_path: str, 
                                      output_suffix: str = "remusic") -> str:
        """
        Replace music in an existing video file.
        
        Args:
            video_path: Path to existing video
            new_music_path: Path to new music file
            output_suffix: Suffix for output filename
            
        Returns:
            Path to new video with replaced music
        """
        print(f"🎵 Replacing music in {Path(video_path).name}...")
        
        try:
            # Load existing video
            video = VideoFileClip(video_path)
            
            # Remove existing audio
            video_no_audio = video.without_audio()
            
            # Add new music
            video_with_new_music = self._add_music_overlay(video_no_audio, new_music_path)
            
            # Generate output filename
            video_stem = Path(video_path).stem
            output_filename = f"{video_stem}_{output_suffix}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Render
            print(f"   🎬 Rendering with new music to: {output_filename}")
            self._render_video(video_with_new_music, output_path, "remusic")
            
            # Clean up
            video.close()
            video_no_audio.close()
            video_with_new_music.close()
            
            print(f"   ✅ Music replacement complete!")
            return output_path
            
        except Exception as e:
            logger.error(f"Music replacement failed: {e}")
            raise
    
    def create_beat_synced_from_cache(self, video_files: List[str], theme: str = "calm", 
                                    target_duration: int = 45) -> str:
        """
        Create beat-synced video using clips from cache.
        
        Args:
            video_files: List of video files to get clips from cache
            theme: Theme for the new video
            target_duration: Target duration in seconds
            
        Returns:
            Path to rendered video
        """
        from src.utils.cache_manager import CacheManager
        
        print(f"🎬 Creating beat-synced video from cached clips...")
        
        # Load clips from cache
        cache_manager = CacheManager()
        all_clips = []
        
        for video_file in video_files:
            if cache_manager.has_cache(video_file):
                cached_result = cache_manager.load_cache(video_file)
                if cached_result and len(cached_result) >= 4:
                    clips, keyframes, motion_scores, scene_changes = cached_result[:4]
                    all_clips.extend(clips)
                    print(f"   ✅ Loaded {len(clips)} clips from {Path(video_file).name}")
                else:
                    print(f"   ⚠️  No valid cache for {Path(video_file).name}")
            else:
                print(f"   ⚠️  No cache found for {Path(video_file).name}")
        
        if not all_clips:
            raise ValueError("No clips found in cache")
        
        print(f"   📊 Total clips available: {len(all_clips)}")
        
        # Download calm/mellow music
        music_path = self._download_calm_music(target_duration)
        
        # Create beat-synced video
        return self.create_beat_synced_video(all_clips, theme, target_duration, music_path, reshuffle_clips=True)
    
    def _download_calm_music(self, duration: int) -> Optional[str]:
        """Download calm/mellow music from Freesound."""
        if not self.music_downloader:
            print(f"   ⚠️  Music downloader not available")
            return None
        
        try:
            print(f"   🔍 Searching for calm/mellow music...")
            
            # Search terms for calm/mellow music
            search_terms = [
                "calm ambient peaceful",
                "mellow chill relaxing", 
                "soft ambient meditation",
                "peaceful nature sounds",
                "gentle acoustic calm"
            ]
            
            for search_term in search_terms:
                try:
                    music_path = self.music_downloader.search_and_download(
                        query=search_term,
                        duration_min=duration,
                        max_results=5,
                        filename_prefix="calm_mellow"
                    )
                    if music_path:
                        print(f"   ✅ Downloaded calm music: {Path(music_path).name}")
                        return music_path
                except Exception as e:
                    logger.debug(f"Search term '{search_term}' failed: {e}")
                    continue
            
            print(f"   ⚠️  Could not download calm music, using existing peaceful music")
            return self._find_theme_music("peaceful", duration)
            
        except Exception as e:
            logger.error(f"Calm music download failed: {e}")
            return None
    
    def _calculate_clip_energy_levels(self, clips: List[VideoClip]) -> List[float]:
        """Calculate energy levels for clips based on motion and quality."""
        energy_levels = []
        
        for clip in clips:
            # Combine motion score and quality score for energy calculation
            motion_energy = min(clip.motion_score / 50.0, 1.0)  # Normalize motion
            quality_energy = clip.quality_score
            
            # Weight motion more for energy calculation
            energy_level = motion_energy * 0.7 + quality_energy * 0.3
            energy_levels.append(energy_level)
        
        return energy_levels
    
    def _create_energy_progression(self, num_clips: int, theme: str) -> List[float]:
        """
        Create an energy progression curve for the video.
        
        Args:
            num_clips: Number of clips
            theme: Video theme
            
        Returns:
            List of target energy levels (0-1) for each clip position
        """
        if theme.lower() in ['calm', 'mellow', 'peaceful']:
            # Calm progression: start medium, dip low, gentle rise, calm end
            progression = np.array([0.6, 0.4, 0.3, 0.5, 0.7, 0.5, 0.4])
        elif theme.lower() in ['exciting', 'adventure']:
            # Exciting progression: build up, peak, maintain, strong finish
            progression = np.array([0.5, 0.7, 0.8, 0.9, 0.8, 0.9, 1.0])
        else:
            # Default progression: gentle build and release
            progression = np.array([0.5, 0.6, 0.8, 0.7, 0.6, 0.7, 0.5])
        
        # Interpolate to match number of clips
        if num_clips != len(progression):
            x_old = np.linspace(0, 1, len(progression))
            x_new = np.linspace(0, 1, num_clips)
            progression = np.interp(x_new, x_old, progression)
        
        return progression.tolist()
    
    def _match_clips_to_energy_curve(self, clips: List[VideoClip], energy_curve: List[float]) -> List[VideoClip]:
        """
        Match clips to desired energy progression curve.
        
        Args:
            clips: Available clips
            energy_curve: Target energy levels for each position
            
        Returns:
            Reordered clips matching energy curve
        """
        clip_energies = self._calculate_clip_energy_levels(clips)
        matched_clips = []
        used_indices = set()
        
        for target_energy in energy_curve:
            # Find unused clip with energy closest to target
            best_clip_idx = None
            best_energy_diff = float('inf')
            
            for i, clip_energy in enumerate(clip_energies):
                if i not in used_indices:
                    energy_diff = abs(clip_energy - target_energy)
                    if energy_diff < best_energy_diff:
                        best_energy_diff = energy_diff
                        best_clip_idx = i
            
            if best_clip_idx is not None:
                matched_clips.append(clips[best_clip_idx])
                used_indices.add(best_clip_idx)
            elif clips:  # Fallback: reuse clips if needed
                matched_clips.append(clips[len(matched_clips) % len(clips)])
        
        return matched_clips
    
    def _reshuffle_clips_for_flow(self, clips: List[VideoClip], audio_features: AudioFeatures, theme: str) -> List[VideoClip]:
        """Enhanced clip reshuffling with energy curve matching."""
        print(f"   🔀 Reshuffling clips for optimal flow...")
        
        # Create energy progression curve
        energy_curve = self._create_energy_progression(len(clips), theme)
        
        # Match clips to energy curve
        reshuffled_clips = self._match_clips_to_energy_curve(clips, energy_curve)
        
        print(f"      ✅ Clips reshuffled for {theme} energy progression")
        return reshuffled_clips

def main():
    """Test beat-synchronized video editor."""
    editor = BeatSyncVideoEditor()
    
    # Test with existing video files
    video_files = [
        "input/DJI_0108.MP4",
        "input/DJI_0110.MP4", 
        "input/DJI_0121.MP4",
        "input/DJI_0131.mp4",
        "input/DJI_0152.MP4",
        "input/DJI_0154.MP4"
    ]
    
    try:
        output_path = editor.create_beat_synced_from_cache(video_files, "calm", 45)
        print(f"✅ Beat-synced video created: {output_path}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
