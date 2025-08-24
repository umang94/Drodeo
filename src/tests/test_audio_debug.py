#!/usr/bin/env python3
"""
Debug script to test audio integration in video editing
"""

import os
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from music_downloader import MusicDownloader

def test_audio_integration():
    """Test audio integration step by step"""
    
    # Paths
    video_path = "output/peaceful_video_1clips_4s.mp4"
    music_dir = Path("music")
    
    print("🎵 Testing Audio Integration Debug")
    print("=" * 50)
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"✅ Video file found: {video_path}")
    
    # Check video properties
    try:
        video_clip = VideoFileClip(video_path)
        print(f"   Duration: {video_clip.duration:.2f}s")
        print(f"   Has audio: {video_clip.audio is not None}")
        if video_clip.audio:
            print(f"   Audio duration: {video_clip.audio.duration:.2f}s")
        video_clip.close()
    except Exception as e:
        print(f"❌ Error reading video: {e}")
        return
    
    # Test music downloader
    print("\n🎼 Testing Music Downloader")
    try:
        music_downloader = MusicDownloader()
        music_downloader.ensure_music_library()
        
        # Get peaceful theme music
        music_path = music_downloader.get_theme_music("peaceful")
        print(f"✅ Music path: {music_path}")
        
        if not os.path.exists(music_path):
            print(f"❌ Music file not found: {music_path}")
            return
        
        # Check music file properties
        audio_clip = AudioFileClip(music_path)
        print(f"   Music duration: {audio_clip.duration:.2f}s")
        print(f"   Music file size: {os.path.getsize(music_path)} bytes")
        audio_clip.close()
        
    except Exception as e:
        print(f"❌ Error with music downloader: {e}")
        return
    
    # Test audio mixing
    print("\n🎛️  Testing Audio Mixing")
    try:
        # Load video and music
        video_clip = VideoFileClip(video_path)
        music_clip = AudioFileClip(music_path)
        
        # Trim music to video duration
        if music_clip.duration > video_clip.duration:
            music_clip = music_clip.subclip(0, video_clip.duration)
        
        # Reduce music volume
        music_clip = music_clip.volumex(0.3)
        print(f"✅ Music volume reduced to 30%")
        
        # Create composite audio
        if video_clip.audio is not None:
            print("   Video has existing audio - mixing with music")
            final_audio = CompositeAudioClip([video_clip.audio, music_clip])
        else:
            print("   Video has no audio - using music only")
            final_audio = music_clip
        
        # Set audio to video
        final_video = video_clip.set_audio(final_audio)
        
        # Test output
        test_output = "test_audio_output.mp4"
        print(f"   Writing test video: {test_output}")
        
        final_video.write_videofile(
            test_output,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        print(f"✅ Test video created: {test_output}")
        
        # Check output properties
        test_clip = VideoFileClip(test_output)
        print(f"   Output duration: {test_clip.duration:.2f}s")
        print(f"   Output has audio: {test_clip.audio is not None}")
        if test_clip.audio:
            print(f"   Output audio duration: {test_clip.audio.duration:.2f}s")
        test_clip.close()
        
        # Cleanup
        final_video.close()
        video_clip.close()
        music_clip.close()
        final_audio.close()
        
    except Exception as e:
        print(f"❌ Error in audio mixing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ Audio integration test completed!")
    print(f"Check the test output file: {test_output}")

if __name__ == "__main__":
    test_audio_integration()
