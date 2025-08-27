"""
Music Analysis and Input Management

Handles music input scanning, analysis, and audio-driven creative direction.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
from dataclasses import dataclass
from src.audio.audio_analyzer import AudioAnalyzer, AudioFeatures

logger = logging.getLogger(__name__)

@dataclass
class MusicTrack:
    """Container for music track information."""
    file_path: str
    filename: str
    duration: float
    audio_features: Optional[AudioFeatures]
    genre_hint: str  # extracted from filename or metadata
    energy_profile: str  # calm, medium, energetic
    suitable_themes: List[str]

class MusicInputManager:
    """Manages music input folder and track analysis."""
    
    def __init__(self, music_input_dir: str = "music_input"):
        """Initialize music input manager."""
        self.music_input_dir = music_input_dir
        self.audio_analyzer = AudioAnalyzer()
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.flac', '.aac']
        
    def scan_music_folder(self) -> List[MusicTrack]:
        """Scan music_input folder for audio files."""
        print(f"🎵 Scanning {self.music_input_dir}/ for music files...")
        
        if not os.path.exists(self.music_input_dir):
            print(f"   ⚠️  Music input directory not found: {self.music_input_dir}")
            return []
        
        music_tracks = []
        music_path = Path(self.music_input_dir)
        
        # Find all audio files
        audio_files = []
        for ext in self.supported_formats:
            audio_files.extend(music_path.glob(f"*{ext}"))
            audio_files.extend(music_path.glob(f"*{ext.upper()}"))
        
        if not audio_files:
            print(f"   ⚠️  No audio files found in {self.music_input_dir}/")
            print(f"   📝 Supported formats: {', '.join(self.supported_formats)}")
            return []
        
        print(f"   🎶 Found {len(audio_files)} audio files")
        
        for audio_file in audio_files:
            try:
                track = self._analyze_music_track(str(audio_file))
                if track:
                    music_tracks.append(track)
                    print(f"   ✅ {track.filename}: {track.duration:.1f}s, {track.energy_profile}")
                else:
                    print(f"   ❌ Failed to analyze: {audio_file.name}")
                    
            except Exception as e:
                logger.error(f"Error analyzing {audio_file}: {e}")
                print(f"   ❌ Error analyzing {audio_file.name}: {e}")
        
        print(f"   📊 Successfully analyzed {len(music_tracks)} tracks")
        return music_tracks
    
    def _analyze_music_track(self, file_path: str) -> Optional[MusicTrack]:
        """Analyze a single music track."""
        try:
            # Get basic file info
            filename = Path(file_path).name
            
            # Analyze audio features
            audio_features = self.audio_analyzer.analyze_audio_file(file_path)
            if not audio_features:
                return None
            
            # Extract genre hint from filename
            genre_hint = self._extract_genre_hint(filename)
            
            # Determine energy profile
            energy_profile = self._determine_energy_profile(audio_features)
            
            # Suggest suitable themes
            suitable_themes = self._suggest_themes(audio_features, genre_hint, energy_profile)
            
            return MusicTrack(
                file_path=file_path,
                filename=filename,
                duration=audio_features.duration,
                audio_features=audio_features,
                genre_hint=genre_hint,
                energy_profile=energy_profile,
                suitable_themes=suitable_themes
            )
            
        except Exception as e:
            logger.error(f"Error analyzing music track {file_path}: {e}")
            return None
    
    def _extract_genre_hint(self, filename: str) -> str:
        """Extract genre hints from filename."""
        filename_lower = filename.lower()
        
        # Common genre keywords
        genre_keywords = {
            'ambient': ['ambient', 'atmospheric', 'drone'],
            'acoustic': ['acoustic', 'guitar', 'folk'],
            'electronic': ['electronic', 'synth', 'digital'],
            'classical': ['classical', 'orchestral', 'piano', 'strings'],
            'jazz': ['jazz', 'smooth', 'saxophone'],
            'rock': ['rock', 'metal', 'electric'],
            'pop': ['pop', 'vocal', 'mainstream'],
            'instrumental': ['instrumental', 'background', 'royalty'],
            'cinematic': ['cinematic', 'epic', 'dramatic', 'film'],
            'chill': ['chill', 'lofi', 'relaxing', 'calm'],
            'upbeat': ['upbeat', 'energetic', 'happy', 'positive']
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                return genre
        
        return 'unknown'
    
    def _determine_energy_profile(self, audio_features: AudioFeatures) -> str:
        """Determine energy profile from audio features."""
        # Use tempo and energy characteristics
        tempo = audio_features.tempo
        avg_energy = sum(audio_features.energy_profile) / len(audio_features.energy_profile) if audio_features.energy_profile else 0.5
        
        # Classify based on tempo and energy
        if tempo < 80 and avg_energy < 0.3:
            return 'very_calm'
        elif tempo < 100 and avg_energy < 0.5:
            return 'calm'
        elif tempo < 120 and avg_energy < 0.7:
            return 'medium'
        elif tempo < 140 and avg_energy < 0.8:
            return 'energetic'
        else:
            return 'high_energy'
    
    def _suggest_themes(self, audio_features: AudioFeatures, genre_hint: str, energy_profile: str) -> List[str]:
        """Suggest suitable video themes for this music."""
        themes = []
        
        # Theme suggestions based on energy profile
        energy_theme_map = {
            'very_calm': ['peaceful', 'cinematic'],
            'calm': ['peaceful', 'cinematic', 'happy'],
            'medium': ['happy', 'adventure', 'cinematic'],
            'energetic': ['exciting', 'adventure', 'happy'],
            'high_energy': ['exciting', 'adventure']
        }
        
        themes.extend(energy_theme_map.get(energy_profile, ['happy']))
        
        # Additional themes based on genre
        genre_theme_map = {
            'ambient': ['peaceful', 'cinematic'],
            'acoustic': ['peaceful', 'happy'],
            'classical': ['cinematic', 'peaceful'],
            'cinematic': ['cinematic', 'adventure'],
            'chill': ['peaceful', 'happy'],
            'instrumental': ['cinematic', 'peaceful']
        }
        
        if genre_hint in genre_theme_map:
            themes.extend(genre_theme_map[genre_hint])
        
        # Remove duplicates and return
        return list(set(themes))
    
    def get_tracks_for_theme(self, tracks: List[MusicTrack], theme: str) -> List[MusicTrack]:
        """Get tracks suitable for a specific theme."""
        suitable_tracks = [track for track in tracks if theme in track.suitable_themes]
        
        # Sort by energy profile match
        theme_energy_preference = {
            'peaceful': ['very_calm', 'calm'],
            'happy': ['medium', 'energetic'],
            'exciting': ['energetic', 'high_energy'],
            'adventure': ['medium', 'energetic'],
            'cinematic': ['calm', 'medium']
        }
        
        preferred_energies = theme_energy_preference.get(theme, ['medium'])
        
        def energy_score(track):
            if track.energy_profile in preferred_energies:
                return preferred_energies.index(track.energy_profile)
            return len(preferred_energies)
        
        suitable_tracks.sort(key=energy_score)
        return suitable_tracks
    
    def save_music_catalog(self, tracks: List[MusicTrack], catalog_file: str = "music_catalog.json"):
        """Save music catalog to file."""
        try:
            catalog_data = []
            for track in tracks:
                track_data = {
                    'file_path': track.file_path,
                    'filename': track.filename,
                    'duration': track.duration,
                    'genre_hint': track.genre_hint,
                    'energy_profile': track.energy_profile,
                    'suitable_themes': track.suitable_themes
                }
                
                # Add audio features if available
                if track.audio_features:
                    track_data['audio_features'] = {
                        'tempo': track.audio_features.tempo,
                        'beats': track.audio_features.beats[:10],  # First 10 beats only
                        'duration': track.audio_features.duration,
                        'beat_consistency': len(track.audio_features.beat_intervals) > 0
                    }
                
                catalog_data.append(track_data)
            
            with open(catalog_file, 'w') as f:
                json.dump(catalog_data, f, indent=2)
            
            print(f"   💾 Music catalog saved to {catalog_file}")
            
        except Exception as e:
            logger.error(f"Failed to save music catalog: {e}")

class AudioDrivenCreativeDirector:
    """Creates creative direction based on audio analysis and video content."""
    
    def __init__(self):
        """Initialize audio-driven creative director."""
        pass
    
    def create_video_plan(self, music_track: MusicTrack, video_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a video editing plan based on music and video content.
        
        Args:
            music_track: Analyzed music track
            video_analyses: Dictionary of video analysis results
            
        Returns:
            Comprehensive video editing plan
        """
        print(f"🎬 Creating video plan for: {music_track.filename}")
        
        # Basic plan structure
        plan = {
            'music_file': music_track.file_path,
            'target_duration': min(music_track.duration, 60),  # Max 60 seconds for now
            'energy_profile': music_track.energy_profile,
            'tempo': music_track.audio_features.tempo if music_track.audio_features else 120,
            'suggested_themes': music_track.suitable_themes,
            'video_selection': [],
            'cut_points': [],
            'transition_style': 'smooth',
            'pacing': 'medium'
        }
        
        # Determine pacing based on music
        if music_track.audio_features:
            tempo = music_track.audio_features.tempo
            if tempo < 90:
                plan['pacing'] = 'slow'
                plan['transition_style'] = 'fade'
            elif tempo > 130:
                plan['pacing'] = 'fast'
                plan['transition_style'] = 'cut'
            
            # Use beat information for cut points
            if music_track.audio_features.beats:
                target_duration = plan['target_duration']
                relevant_beats = [b for b in music_track.audio_features.beats if b <= target_duration]
                
                # Select every 4th beat for cuts (typical musical phrase)
                plan['cut_points'] = relevant_beats[::4][:8]  # Max 8 cuts
        
        # Select best videos based on energy matching
        plan['video_selection'] = self._select_videos_for_music(music_track, video_analyses)
        
        print(f"   ✅ Plan created: {len(plan['video_selection'])} videos, {len(plan['cut_points'])} cuts")
        return plan
    
    def _select_videos_for_music(self, music_track: MusicTrack, video_analyses: Dict[str, Any]) -> List[Dict]:
        """Select and order videos based on music characteristics."""
        video_selection = []
        
        # For now, create a simple selection based on energy matching
        # In a full implementation, this would use the LLM video analyses
        
        available_videos = list(video_analyses.keys()) if video_analyses else []
        
        # Simple energy-based selection
        energy_video_preference = {
            'very_calm': 'slow_motion',
            'calm': 'peaceful_scenes', 
            'medium': 'mixed_content',
            'energetic': 'dynamic_movement',
            'high_energy': 'fast_action'
        }
        
        preferred_style = energy_video_preference.get(music_track.energy_profile, 'mixed_content')
        
        for video_path in available_videos[:6]:  # Use up to 6 videos
            video_selection.append({
                'video_path': video_path,
                'preferred_style': preferred_style,
                'usage_priority': 1.0
            })
        
        return video_selection

def test_music_analysis():
    """Test the music input manager."""
    manager = MusicInputManager()
    
    # Scan music folder
    tracks = manager.scan_music_folder()
    
    if tracks:
        print(f"\n📊 Music Analysis Results:")
        for track in tracks:
            print(f"   🎵 {track.filename}")
            print(f"      Duration: {track.duration:.1f}s")
            print(f"      Genre: {track.genre_hint}")
            print(f"      Energy: {track.energy_profile}")
            print(f"      Themes: {', '.join(track.suitable_themes)}")
            if track.audio_features:
                print(f"      Tempo: {track.audio_features.tempo:.1f} BPM")
                print(f"      Beats: {len(track.audio_features.beats)} detected")
        
        # Save catalog
        manager.save_music_catalog(tracks)
        
        # Test creative director
        if tracks:
            director = AudioDrivenCreativeDirector()
            plan = director.create_video_plan(tracks[0], {})
            print(f"\n🎬 Sample Video Plan:")
            print(f"   Target duration: {plan['target_duration']}s")
            print(f"   Pacing: {plan['pacing']}")
            print(f"   Cut points: {plan['cut_points']}")
    else:
        print("❌ No music tracks found for testing")

if __name__ == "__main__":
    test_music_analysis()
