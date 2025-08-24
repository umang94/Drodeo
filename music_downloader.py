#!/usr/bin/env python3
"""
Music Downloader Module for Drone Video Generator

This module handles downloading and managing royalty-free music for themed videos:
- Downloads theme-appropriate music from various sources
- Manages local music library
- Provides fallback music options
- Integrates with video editor for background music
"""

import os
import logging
import requests
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import yt_dlp
from urllib.parse import urlparse
import time
import random

from config import MUSIC_CONFIG, THEME_CONFIGS, VideoTheme

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicDownloader:
    """Handles downloading and managing royalty-free music"""
    
    def __init__(self, music_dir: str = "music"):
        """
        Initialize the music downloader
        
        Args:
            music_dir: Directory to store downloaded music files
        """
        self.music_dir = music_dir
        self.ensure_music_directory()
        self.downloaded_tracks = {}
        self._load_music_index()
        
    def ensure_music_directory(self):
        """Create music directory if it doesn't exist"""
        os.makedirs(self.music_dir, exist_ok=True)
        
    def _load_music_index(self):
        """Load index of downloaded music tracks"""
        index_file = os.path.join(self.music_dir, "music_index.json")
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r') as f:
                    self.downloaded_tracks = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load music index: {e}")
                self.downloaded_tracks = {}
        else:
            self.downloaded_tracks = {}
    
    def _save_music_index(self):
        """Save index of downloaded music tracks"""
        index_file = os.path.join(self.music_dir, "music_index.json")
        try:
            with open(index_file, 'w') as f:
                json.dump(self.downloaded_tracks, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save music index: {e}")
    
    def get_theme_music(self, theme: str, duration: int = 180) -> Optional[str]:
        """
        Get music file for a specific theme
        
        Args:
            theme: Theme name (happy, exciting, peaceful, adventure, cinematic)
            duration: Target duration in seconds
            
        Returns:
            Path to music file or None if not available
        """
        print(f"🎵 Looking for {theme} music...")
        
        # First, check if we already have music for this theme
        existing_music = self._find_existing_music(theme)
        if existing_music:
            print(f"   ✅ Found existing music: {os.path.basename(existing_music)}")
            return existing_music
        
        # Try to download new music for this theme
        try:
            downloaded_path = self._download_theme_music(theme, duration)
            if downloaded_path:
                print(f"   ✅ Downloaded new music: {os.path.basename(downloaded_path)}")
                return downloaded_path
        except Exception as e:
            logger.warning(f"Failed to download music for {theme}: {e}")
        
        # Fallback to any available music
        fallback_music = self._get_fallback_music()
        if fallback_music:
            print(f"   ⚠️  Using fallback music: {os.path.basename(fallback_music)}")
            return fallback_music
        
        print(f"   ❌ No music available for {theme}")
        return None
    
    def _find_existing_music(self, theme: str) -> Optional[str]:
        """Find existing music file for a theme"""
        # Check theme-specific files
        theme_files = [
            f"{theme}.mp3",
            f"{theme}.wav",
            f"{theme}.m4a",
            f"{theme}_music.mp3",
            f"{theme}_background.mp3",
            f"{theme}_sample.wav"
        ]
        
        for filename in theme_files:
            path = os.path.join(self.music_dir, filename)
            if os.path.exists(path):
                return path
        
        # Check downloaded tracks index
        if theme in self.downloaded_tracks:
            for track_info in self.downloaded_tracks[theme]:
                path = track_info.get('path')
                if path and os.path.exists(path):
                    return path
        
        return None
    
    def _download_theme_music(self, theme: str, duration: int) -> Optional[str]:
        """
        Download music for a specific theme
        
        Args:
            theme: Theme name
            duration: Target duration in seconds
            
        Returns:
            Path to downloaded music file
        """
        # Try different music sources
        sources = [
            self._download_from_youtube_audio_library,
            self._download_from_freesound,
            self._download_from_pixabay
        ]
        
        for source_func in sources:
            try:
                result = source_func(theme, duration)
                if result:
                    return result
            except Exception as e:
                logger.debug(f"Source {source_func.__name__} failed: {e}")
                continue
        
        return None
    
    def _download_from_youtube_audio_library(self, theme: str, duration: int) -> Optional[str]:
        """
        Download music from YouTube Audio Library using yt-dlp
        
        Args:
            theme: Theme name
            duration: Target duration in seconds
            
        Returns:
            Path to downloaded music file
        """
        print(f"   🔍 Searching YouTube Audio Library for {theme} music...")
        
        # Get search terms for the theme
        theme_config = None
        for theme_enum in VideoTheme:
            if theme_enum.value == theme:
                theme_config = THEME_CONFIGS[theme_enum]
                break
        
        if not theme_config:
            return None
        
        # Create search query
        keywords = theme_config.music_keywords[:3]  # Use top 3 keywords
        search_query = f"royalty free {' '.join(keywords)} music instrumental"
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.music_dir, f'{theme}_%(title)s.%(ext)s'),
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192K',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for videos
                search_results = ydl.extract_info(
                    f"ytsearch5:{search_query}",
                    download=False
                )
                
                if not search_results or 'entries' not in search_results:
                    return None
                
                # Filter for appropriate duration and download first suitable track
                for entry in search_results['entries']:
                    if not entry:
                        continue
                    
                    video_duration = entry.get('duration', 0)
                    title = entry.get('title', 'Unknown')
                    
                    # Check if duration is suitable (within 50% of target)
                    if video_duration and abs(video_duration - duration) <= duration * 0.5:
                        print(f"   📥 Downloading: {title[:50]}...")
                        
                        # Download the track
                        ydl.download([entry['webpage_url']])
                        
                        # Find the downloaded file
                        expected_path = os.path.join(self.music_dir, f"{theme}_{title}.mp3")
                        
                        # Look for any new mp3 files in the music directory
                        for file in os.listdir(self.music_dir):
                            if file.startswith(theme) and file.endswith('.mp3'):
                                file_path = os.path.join(self.music_dir, file)
                                
                                # Update index
                                if theme not in self.downloaded_tracks:
                                    self.downloaded_tracks[theme] = []
                                
                                self.downloaded_tracks[theme].append({
                                    'title': title,
                                    'path': file_path,
                                    'duration': video_duration,
                                    'source': 'youtube_audio_library'
                                })
                                self._save_music_index()
                                
                                return file_path
                
        except Exception as e:
            logger.debug(f"YouTube Audio Library download failed: {e}")
        
        return None
    
    def _download_from_freesound(self, theme: str, duration: int) -> Optional[str]:
        """
        Download music from Freesound (requires API key)
        
        Args:
            theme: Theme name
            duration: Target duration in seconds
            
        Returns:
            Path to downloaded music file
        """
        # This would require a Freesound API key
        # For now, we'll skip this implementation
        logger.debug("Freesound integration not implemented (requires API key)")
        return None
    
    def _download_from_pixabay(self, theme: str, duration: int) -> Optional[str]:
        """
        Download music from Pixabay (requires API key)
        
        Args:
            theme: Theme name
            duration: Target duration in seconds
            
        Returns:
            Path to downloaded music file
        """
        # This would require a Pixabay API key
        # For now, we'll skip this implementation
        logger.debug("Pixabay integration not implemented (requires API key)")
        return None
    
    def _get_fallback_music(self) -> Optional[str]:
        """Get any available music file as fallback"""
        # Look for any existing music files
        music_extensions = ['.mp3', '.wav', '.m4a', '.aac']
        
        for file in os.listdir(self.music_dir):
            if any(file.lower().endswith(ext) for ext in music_extensions):
                path = os.path.join(self.music_dir, file)
                if os.path.isfile(path):
                    return path
        
        return None
    
    def create_sample_music_files(self):
        """
        Create sample music files for testing (silent audio files)
        This is useful for testing the video editing pipeline without actual music
        """
        print("🎵 Creating sample music files for testing...")
        
        try:
            # Try to create simple sine wave audio files using numpy and scipy
            import numpy as np
            from scipy.io import wavfile
            
            sample_rate = 44100
            duration = 30  # 30 seconds
            
            for theme in ['happy', 'exciting', 'peaceful', 'adventure', 'cinematic']:
                filename = f"{theme}_sample.wav"
                filepath = os.path.join(self.music_dir, filename)
                
                if not os.path.exists(filepath):
                    # Create a simple sine wave (different frequency for each theme)
                    frequencies = {
                        'happy': 440,      # A4
                        'exciting': 523,   # C5
                        'peaceful': 261,   # C4
                        'adventure': 349,  # F4
                        'cinematic': 196   # G3
                    }
                    
                    freq = frequencies.get(theme, 440)
                    t = np.linspace(0, duration, int(sample_rate * duration), False)
                    
                    # Create a gentle sine wave with fade in/out
                    wave = np.sin(2 * np.pi * freq * t) * 0.1  # Low volume
                    
                    # Add fade in/out
                    fade_samples = int(sample_rate * 2)  # 2 second fade
                    wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
                    wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
                    
                    # Convert to 16-bit integers
                    wave_int = (wave * 32767).astype(np.int16)
                    
                    # Save as WAV file
                    wavfile.write(filepath, sample_rate, wave_int)
                    print(f"   ✅ Created sample music: {filename}")
                    
        except ImportError:
            # If scipy is not available, create silent files using a different method
            print("   ⚠️  scipy not available, creating placeholder files...")
            
            for theme in ['happy', 'exciting', 'peaceful', 'adventure', 'cinematic']:
                filename = f"{theme}_sample.txt"
                filepath = os.path.join(self.music_dir, filename)
                
                if not os.path.exists(filepath):
                    with open(filepath, 'w') as f:
                        f.write(f"Sample music placeholder for {theme} theme\n")
                        f.write("Replace with actual music file (.mp3, .wav, .m4a)\n")
                    print(f"   ✅ Created placeholder: {filename}")
        
        except Exception as e:
            logger.warning(f"Failed to create sample music files: {e}")
    
    def ensure_music_library(self):
        """Ensure we have music available for all themes"""
        print("🎵 Ensuring music library is available...")
        
        available_themes = []
        missing_themes = []
        
        for theme in ['happy', 'exciting', 'peaceful', 'adventure', 'cinematic']:
            if self._find_existing_music(theme):
                available_themes.append(theme)
            else:
                missing_themes.append(theme)
        
        if available_themes:
            print(f"   ✅ Music available for: {', '.join(available_themes)}")
        
        if missing_themes:
            print(f"   ⚠️  Missing music for: {', '.join(missing_themes)}")
            
            # Try to download missing music
            for theme in missing_themes[:2]:  # Limit to 2 downloads to avoid rate limiting
                try:
                    result = self._download_theme_music(theme, 180)
                    if result:
                        print(f"   ✅ Downloaded music for {theme}")
                    else:
                        print(f"   ❌ Failed to download music for {theme}")
                except Exception as e:
                    logger.warning(f"Failed to download music for {theme}: {e}")
            
            # Create sample files for remaining themes
            if len(missing_themes) > 2:
                print("   🎵 Creating sample music files for remaining themes...")
                self.create_sample_music_files()
    
    def list_available_music(self) -> Dict[str, List[str]]:
        """List all available music files by theme"""
        music_by_theme = {}
        
        for theme in ['happy', 'exciting', 'peaceful', 'adventure', 'cinematic']:
            music_files = []
            
            # Check for theme-specific files
            theme_files = [
                f"{theme}.mp3", f"{theme}.wav", f"{theme}.m4a",
                f"{theme}_music.mp3", f"{theme}_sample.wav"
            ]
            
            for filename in theme_files:
                path = os.path.join(self.music_dir, filename)
                if os.path.exists(path):
                    music_files.append(filename)
            
            # Check downloaded tracks
            if theme in self.downloaded_tracks:
                for track_info in self.downloaded_tracks[theme]:
                    path = track_info.get('path')
                    if path and os.path.exists(path):
                        music_files.append(os.path.basename(path))
            
            music_by_theme[theme] = music_files
        
        return music_by_theme
    
    def get_music_info(self, music_path: str) -> Dict:
        """Get information about a music file"""
        try:
            file_size = os.path.getsize(music_path)
            return {
                'path': music_path,
                'filename': os.path.basename(music_path),
                'size_mb': file_size / (1024 * 1024),
                'exists': True
            }
        except Exception as e:
            return {
                'path': music_path,
                'filename': os.path.basename(music_path) if music_path else 'Unknown',
                'size_mb': 0,
                'exists': False,
                'error': str(e)
            }

def main():
    """Test the music downloader functionality"""
    downloader = MusicDownloader()
    
    # Ensure music library
    downloader.ensure_music_library()
    
    # List available music
    music_library = downloader.list_available_music()
    print("\n🎵 Music Library:")
    for theme, files in music_library.items():
        if files:
            print(f"   {theme}: {', '.join(files)}")
        else:
            print(f"   {theme}: No music available")
    
    # Test getting music for a theme
    peaceful_music = downloader.get_theme_music('peaceful', 180)
    if peaceful_music:
        info = downloader.get_music_info(peaceful_music)
        print(f"\n🎵 Peaceful music: {info['filename']} ({info['size_mb']:.1f}MB)")
    else:
        print("\n❌ No peaceful music available")

if __name__ == "__main__":
    main()
