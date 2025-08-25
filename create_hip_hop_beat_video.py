#!/usr/bin/env python3
"""
Hip Hop Beat-Synchronized Video Creator

Creates a 45-second video with hip hop music using cached clips,
with simplified beat detection and rhythm-based transitions.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from editing.video_editor import VideoEditor
from utils.cache_manager import CacheManager
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import moviepy.video.fx.all as vfx
import numpy as np

class SimpleHipHopEditor(VideoEditor):
    """Simplified hip hop video editor with rhythm-based transitions."""
    
    def create_hip_hop_beat_video(self, clips, target_duration=45, music_path=None):
        """Create hip hop style video with rhythm-based cuts."""
        print(f"🎤 Creating hip hop beat video...")
        print(f"   📊 Using {len(clips)} clips")
        print(f"   ⏱️  Target duration: {target_duration}s")
        
        if not music_path or not os.path.exists(music_path):
            raise ValueError("Hip hop music file required")
        
        # Load music to get duration info
        audio = AudioFileClip(music_path)
        music_duration = audio.duration
        print(f"   🎵 Music duration: {music_duration:.1f}s")
        
        # Hip hop typically has 4/4 time signature, ~120-140 BPM
        # Assume ~130 BPM for beat timing
        estimated_bpm = 130
        beat_interval = 60.0 / estimated_bpm  # ~0.46 seconds per beat
        
        # Create rhythm-based clip durations
        # Hip hop style: short punchy clips with quick cuts
        base_clip_duration = beat_interval * 4  # 4 beats per clip (~1.85s)
        
        print(f"   🥁 Estimated BPM: {estimated_bpm}, Beat interval: {beat_interval:.2f}s")
        print(f"   ✂️  Base clip duration: {base_clip_duration:.2f}s")
        
        # Reshuffle clips for hip hop energy
        clips = self._reshuffle_for_hip_hop(clips)
        
        # Create video clips with rhythm timing
        video_clips = []
        current_time = 0.0
        
        for i, clip in enumerate(clips):
            if current_time >= target_duration:
                break
                
            print(f"   📹 Processing clip {i+1}: {os.path.basename(clip.file_path)}")
            
            # Vary clip duration for hip hop rhythm
            if i % 4 == 0:  # Every 4th clip is longer (8 beats)
                clip_duration = beat_interval * 8
            elif i % 2 == 0:  # Every other clip is medium (6 beats)
                clip_duration = beat_interval * 6
            else:  # Short clips (4 beats)
                clip_duration = base_clip_duration
            
            # Ensure we don't exceed target duration
            remaining_time = target_duration - current_time
            clip_duration = min(clip_duration, remaining_time)
            
            # Load video clip
            video_clip = VideoFileClip(clip.file_path).subclip(clip.start_time, clip.end_time)
            
            # Adjust clip to match rhythm duration
            if video_clip.duration > clip_duration:
                video_clip = video_clip.subclip(0, clip_duration)
            elif video_clip.duration < clip_duration:
                # Loop if too short
                loops = int(np.ceil(clip_duration / video_clip.duration))
                if loops > 1:
                    looped = [video_clip] * loops
                    video_clip = concatenate_videoclips(looped)
                    video_clip = video_clip.subclip(0, clip_duration)
            
            # Apply hip hop style effects
            video_clip = self._apply_hip_hop_effects(video_clip, i)
            
            video_clips.append(video_clip)
            current_time += video_clip.duration
        
        # Concatenate with quick cuts (no fades for hip hop style)
        print(f"   🔗 Concatenating {len(video_clips)} clips with quick cuts...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Trim to exact duration
        if final_video.duration > target_duration:
            final_video = final_video.subclip(0, target_duration)
        
        # Add hip hop music
        print(f"   🎵 Adding hip hop music: {os.path.basename(music_path)}")
        final_video = self._add_music_overlay(final_video, music_path)
        
        # Generate output filename
        output_filename = f"hip_hop_beat_synced_{len(clips)}clips_{int(final_video.duration)}s.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Render
        print(f"   🎬 Rendering hip hop video to: {output_filename}")
        self._render_video(final_video, output_path, "hip_hop")
        
        # Clean up
        audio.close()
        final_video.close()
        for clip in video_clips:
            clip.close()
        
        print(f"   ✅ Hip hop beat video created successfully!")
        return output_path
    
    def _reshuffle_for_hip_hop(self, clips):
        """Reshuffle clips for hip hop energy and flow."""
        print(f"   🔀 Reshuffling clips for hip hop energy...")
        
        # Sort by motion score for dynamic energy
        high_motion = [c for c in clips if c.motion_score > np.median([clip.motion_score for clip in clips])]
        low_motion = [c for c in clips if c.motion_score <= np.median([clip.motion_score for clip in clips])]
        
        # Sort each group
        high_motion.sort(key=lambda c: c.motion_score, reverse=True)
        low_motion.sort(key=lambda c: c.quality_score, reverse=True)
        
        # Create hip hop pattern: start strong, vary energy
        reshuffled = []
        for i in range(max(len(high_motion), len(low_motion))):
            if i < len(high_motion):
                reshuffled.append(high_motion[i])
            if i < len(low_motion) and len(reshuffled) < len(clips):
                reshuffled.append(low_motion[i])
        
        print(f"      ✅ Clips reshuffled for hip hop flow")
        return reshuffled[:len(clips)]
    
    def _apply_hip_hop_effects(self, clip, clip_index):
        """Apply hip hop style effects to clips."""
        # No fades for hip hop - keep cuts sharp and punchy
        # Every few clips, add a slight speed variation for rhythm
        if clip_index % 6 == 0:
            # Slight speed boost for emphasis
            clip = clip.fx(vfx.speedx, 1.05)
        
        return clip

def main():
    """Create hip hop beat-synchronized video."""
    print("🎤 Hip Hop Beat-Synchronized Video Creator")
    print("=" * 50)
    
    # Video files from cache
    video_files = [
        "input/DJI_0108.MP4",
        "input/DJI_0110.MP4", 
        "input/DJI_0121.MP4",
        "input/DJI_0131.mp4",
        "input/DJI_0152.MP4",
        "input/DJI_0154.MP4"
    ]
    
    # Load clips from cache
    print("🔍 Loading clips from cache...")
    cache_manager = CacheManager()
    all_clips = []
    
    for video_file in video_files:
        if os.path.exists(video_file) and cache_manager.has_cache(video_file):
            cached_result = cache_manager.load_cache(video_file)
            if cached_result and len(cached_result) >= 4:
                clips, _, _, _ = cached_result[:4]
                all_clips.extend(clips)
                print(f"   ✅ Loaded {len(clips)} clips from {Path(video_file).name}")
    
    if not all_clips:
        print("❌ No cached clips available")
        return
    
    print(f"   📊 Total clips available: {len(all_clips)}")
    
    # Use the exciting music (which should have good beats)
    music_path = "music/exciting_freesound_335694_Trailerwav.mp3"
    if not os.path.exists(music_path):
        print(f"❌ Hip hop music not found: {music_path}")
        return
    
    # Create hip hop editor and generate video
    editor = SimpleHipHopEditor()
    
    try:
        output_path = editor.create_hip_hop_beat_video(
            clips=all_clips,
            target_duration=45,
            music_path=music_path
        )
        
        # Get video info
        video_info = editor.get_video_info(output_path)
        
        print(f"\n🎉 Hip hop beat video creation complete!")
        print(f"📊 Output Details:")
        print(f"   File: {Path(output_path).name}")
        print(f"   Duration: {video_info.get('duration', 0):.1f}s")
        print(f"   Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
        print(f"   Size: {video_info.get('size_mb', 0):.1f}MB")
        print(f"   Location: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Hip hop video creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
