#!/usr/bin/env python3
"""
Enhanced Hip Hop Beat-Synchronized Video Creator

Creates a full 45-second hip hop video using available cached clips
with creative repetition, variations, and rhythm-based editing.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from editing.video_editor import VideoEditor
from utils.cache_manager import CacheManager
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip
import moviepy.video.fx.all as vfx
import numpy as np
import random

def main():
    """Create enhanced hip hop beat-synchronized video."""
    print("🎤 Enhanced Hip Hop Beat-Synchronized Video Creator")
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
    
    # Use the exciting music for hip hop beats
    music_path = "music/exciting_freesound_335694_Trailerwav.mp3"
    if not os.path.exists(music_path):
        print(f"❌ Hip hop music not found: {music_path}")
        return
    
    # Create enhanced hip hop video
    target_duration = 45
    estimated_bpm = 130
    beat_interval = 60.0 / estimated_bpm
    
    print(f"🎤 Creating enhanced hip hop beat video...")
    print(f"   📊 Using {len(all_clips)} unique clips")
    print(f"   ⏱️  Target duration: {target_duration}s")
    print(f"   🥁 Hip hop rhythm: {estimated_bpm} BPM, {beat_interval:.2f}s per beat")
    
    # Calculate total available clip duration
    total_clip_duration = sum(c.duration for c in all_clips)
    print(f"   📊 Available clip content: {total_clip_duration:.1f}s")
    
    # Create clip variations to fill duration
    repetition_factor = max(2, int(np.ceil(target_duration / total_clip_duration)))
    extended_clips = all_clips * repetition_factor
    print(f"   🔄 Extended to {len(extended_clips)} clips with {repetition_factor}x repetition")
    
    # Shuffle for variety
    random.shuffle(extended_clips)
    
    # Create hip hop rhythm sequence
    video_clips = []
    current_time = 0.0
    
    # Hip hop rhythm patterns (in beats)
    rhythm_patterns = [
        [4, 4, 8, 4],      # Standard pattern
        [2, 2, 4, 8],      # Quick start, long end
        [8, 2, 2, 4],      # Long start, quick cuts
        [4, 2, 6, 4],      # Varied pattern
    ]
    
    pattern_index = 0
    pattern_position = 0
    
    for i, clip in enumerate(extended_clips):
        if current_time >= target_duration:
            break
        
        # Get rhythm pattern
        current_pattern = rhythm_patterns[pattern_index % len(rhythm_patterns)]
        beats_for_clip = current_pattern[pattern_position % len(current_pattern)]
        clip_duration = beat_interval * beats_for_clip
        
        # Ensure we don't exceed target
        remaining_time = target_duration - current_time
        clip_duration = min(clip_duration, remaining_time)
        
        if clip_duration < 0.5:
            break
        
        print(f"   📹 Clip {i+1}: {os.path.basename(clip.file_path)} ({beats_for_clip} beats, {clip_duration:.1f}s)")
        
        # Load and adjust video clip
        video_clip = VideoFileClip(clip.file_path).subclip(clip.start_time, clip.end_time)
        
        if video_clip.duration > clip_duration:
            # Random start position for variety
            max_start = max(0, video_clip.duration - clip_duration)
            start_offset = random.uniform(0, max_start) if max_start > 0 else 0
            video_clip = video_clip.subclip(start_offset, start_offset + clip_duration)
        elif video_clip.duration < clip_duration:
            # Loop if needed
            loops = int(np.ceil(clip_duration / video_clip.duration))
            if loops > 1:
                looped = [video_clip] * loops
                video_clip = concatenate_videoclips(looped)
                video_clip = video_clip.subclip(0, clip_duration)
        
        # Hip hop effects: sharp cuts, occasional speed changes
        if beats_for_clip >= 8 and i % 3 == 0:
            video_clip = video_clip.fx(vfx.speedx, 1.05)  # Speed up long clips
        elif beats_for_clip <= 2 and i % 5 == 0:
            video_clip = video_clip.fx(vfx.speedx, 0.95)  # Slow down short clips for emphasis
        
        video_clips.append(video_clip)
        current_time += video_clip.duration
        
        # Move pattern
        pattern_position += 1
        if pattern_position >= len(current_pattern):
            pattern_position = 0
            pattern_index += 1
    
    # Concatenate with sharp cuts
    print(f"   🔗 Concatenating {len(video_clips)} rhythm clips...")
    final_video = concatenate_videoclips(video_clips, method="compose")
    
    # Trim to exact duration
    if final_video.duration > target_duration:
        final_video = final_video.subclip(0, target_duration)
    
    # Add hip hop music
    print(f"   🎵 Adding hip hop music: {os.path.basename(music_path)}")
    
    # Load and prepare music
    audio = AudioFileClip(music_path)
    if audio.duration < final_video.duration:
        loops = int(np.ceil(final_video.duration / audio.duration))
        audio_clips = [audio] * loops
        audio = concatenate_audioclips(audio_clips)
    audio = audio.subclip(0, final_video.duration)
    
    # Set prominent music volume
    audio = audio.volumex(0.8)
    
    # Mix with original if present
    if final_video.audio is not None:
        original_audio = final_video.audio.volumex(0.3)
        final_audio = CompositeAudioClip([original_audio, audio])
    else:
        final_audio = audio
    
    final_audio = final_audio.volumex(1.1)
    final_video = final_video.set_audio(final_audio)
    
    # Generate output
    output_filename = f"enhanced_hip_hop_{len(all_clips)}clips_{int(final_video.duration)}s.mp4"
    output_path = os.path.join("output", output_filename)
    
    # Render
    print(f"   🎬 Rendering enhanced hip hop video to: {output_filename}")
    
    final_video.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        verbose=False,
        logger=None
    )
    
    # Get video info
    video_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    
    print(f"\n🎉 Enhanced hip hop video creation complete!")
    print(f"📊 Output Details:")
    print(f"   File: {output_filename}")
    print(f"   Duration: {final_video.duration:.1f}s")
    print(f"   Resolution: {final_video.w}x{final_video.h}")
    print(f"   Size: {video_size_mb:.1f}MB")
    print(f"   Location: {output_path}")
    
    # Clean up
    audio.close()
    final_video.close()
    for clip in video_clips:
        clip.close()
    
    return output_path

if __name__ == "__main__":
    main()
