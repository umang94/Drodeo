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
from urllib.parse import urlparse
import time
import random
from dotenv import load_dotenv

from config import MUSIC_CONFIG, THEME_CONFIGS, VideoTheme

# Load environment variables
load_dotenv()

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
            self._download_from_freesound
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
    
    
    def _download_from_freesound(self, theme: str, duration: int) -> Optional[str]:
        """
        Download music from Freesound API
        
        Args:
            theme: Theme name
            duration: Target duration in seconds
            
        Returns:
            Path to downloaded music file
        """
        print(f"   🔍 Searching Freesound for {theme} music...")
        
        # Get API key from environment
        api_key = os.getenv('FREESOUND_API_KEY')
        if not api_key:
            logger.debug("Freesound API key not found in environment")
            return None
        
        # Get theme-specific search terms
        search_terms = self._get_freesound_search_terms(theme)
        
        try:
            # Search for tracks
            tracks = self._search_freesound_tracks(api_key, search_terms, duration)
            if not tracks:
                print(f"   ⚠️  No suitable tracks found for {theme}")
                return None
            
            # Select best track
            best_track = self._select_best_freesound_track(tracks, duration)
            if not best_track:
                print(f"   ⚠️  No suitable tracks found for {theme}")
                return None
            
            # Download the track
            return self._download_freesound_track(best_track, theme, api_key)
            
        except Exception as e:
            logger.debug(f"Freesound integration error: {e}")
            return None
    
    def _get_freesound_search_terms(self, theme: str) -> List[str]:
        """Get Freesound search terms for a theme"""
        search_mapping = {
            'happy': ['upbeat', 'cheerful', 'positive music', 'joyful', 'bright music'],
            'exciting': ['energetic', 'action', 'intense music', 'dynamic', 'powerful music'],
            'peaceful': ['ambient', 'calm', 'relaxing music', 'serene', 'meditation music'],
            'adventure': ['epic', 'cinematic', 'dramatic music', 'heroic', 'inspiring music'],
            'cinematic': ['orchestral', 'soundtrack', 'film music', 'emotional music', 'dramatic']
        }
        
        return search_mapping.get(theme, ['instrumental', 'background music'])
    
    def _search_freesound_tracks(self, api_key: str, search_terms: List[str], target_duration: int) -> List[Dict]:
        """Search for tracks on Freesound"""
        all_tracks = []
        
        # Try each search term
        for term in search_terms[:2]:  # Limit to 2 terms to avoid rate limiting
            try:
                # Freesound API search parameters
                params = {
                    'token': api_key,
                    'query': term,
                    'filter': f'duration:[{max(30, target_duration-60)} TO {target_duration+120}] type:wav OR type:mp3',
                    'sort': 'downloads_desc',  # Sort by popularity
                    'fields': 'id,name,description,duration,download,previews,license,username,download_count',
                    'page_size': 10
                }
                
                response = requests.get('https://freesound.org/apiv2/search/text/', 
                                      params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                tracks = data.get('results', [])
                
                # Filter for suitable licenses (CC0 or CC BY)
                suitable_tracks = []
                for track in tracks:
                    license_url = track.get('license', '').lower()
                    # Check for Creative Commons licenses by URL patterns
                    is_cc = any(pattern in license_url for pattern in [
                        'creativecommons.org/publicdomain/zero',  # CC0
                        'creativecommons.org/licenses/by',        # CC BY
                        'cc0',
                        'cc by'
                    ])
                    if is_cc:
                        suitable_tracks.append(track)
                
                all_tracks.extend(suitable_tracks)
                
                # Add small delay to respect rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"Failed to search Freesound for '{term}': {e}")
                continue
        
        return all_tracks
    
    def _select_best_freesound_track(self, tracks: List[Dict], target_duration: int) -> Optional[Dict]:
        """Select the best track from Freesound results"""
        if not tracks:
            return None
        
        scored_tracks = []
        
        for track in tracks:
            duration = track.get('duration', 0)
            
            # Skip tracks that are too short or too long
            if duration < 20 or duration > target_duration * 2:
                continue
            
            # Calculate duration score (prefer close to target)
            duration_diff = abs(duration - target_duration)
            duration_score = max(0, 1 - (duration_diff / target_duration))
            
            # Popularity score based on download count
            downloads = track.get('download_count', 0)
            popularity_score = min(1.0, downloads / 100)  # Normalize to 0-1
            
            # License preference (CC0 is better than CC BY)
            license_name = track.get('license', '').lower()
            license_score = 1.0 if 'cc0' in license_name else 0.8
            
            # Combined score
            total_score = (duration_score * 0.5 + 
                          popularity_score * 0.3 + 
                          license_score * 0.2)
            
            scored_tracks.append((total_score, track))
        
        if not scored_tracks:
            return None
        
        # Return best scoring track
        scored_tracks.sort(key=lambda x: x[0], reverse=True)
        return scored_tracks[0][1]
    
    def _download_freesound_track(self, track: Dict, theme: str, api_key: str) -> Optional[str]:
        """Download a specific track from Freesound using preview (full downloads require OAuth)"""
        try:
            track_id = track.get('id')
            track_name = track.get('name', 'Unknown')
            
            # Create filename
            safe_name = "".join(c for c in track_name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
            filename = f"{theme}_freesound_{track_id}_{safe_name}.mp3"
            filepath = os.path.join(self.music_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                print(f"   ✅ Using cached Freesound track: {filename}")
                return filepath
            
            print(f"   📥 Downloading preview: {track_name}...")
            
            # First get the full track details to access preview URLs
            sound_url = f'https://freesound.org/apiv2/sounds/{track_id}/'
            params = {'token': api_key}
            
            response = requests.get(sound_url, params=params, timeout=10)
            response.raise_for_status()
            
            sound_data = response.json()
            previews = sound_data.get('previews', {})
            
            # Try to get the best quality preview
            preview_url = None
            for quality in ['preview-hq-mp3', 'preview-lq-mp3']:
                if quality in previews:
                    preview_url = previews[quality]
                    break
            
            if not preview_url:
                logger.debug(f"No preview URL available for track {track_id}")
                return None
            
            # Download the preview file
            preview_response = requests.get(preview_url, timeout=30)
            preview_response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(preview_response.content)
            
            # Update music index
            if theme not in self.downloaded_tracks:
                self.downloaded_tracks[theme] = []
            
            self.downloaded_tracks[theme].append({
                'title': track_name,
                'path': filepath,
                'duration': sound_data.get('duration', 0),
                'source': 'freesound',
                'track_id': track_id,
                'license': sound_data.get('license', 'Unknown'),
                'username': sound_data.get('username', 'Unknown'),
                'download_count': sound_data.get('download_count', 0),
                'note': 'Preview version (full download requires OAuth)'
            })
            self._save_music_index()
            
            print(f"   ✅ Downloaded Freesound preview: {filename}")
            return filepath
            
        except Exception as e:
            logger.debug(f"Failed to download Freesound track: {e}")
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
