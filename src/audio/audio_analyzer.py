"""
Audio Analysis Module for Beat Detection and Music Synchronization

This module provides audio analysis capabilities including beat detection,
tempo analysis, and music synchronization for video editing.
"""

import librosa
import numpy as np
from typing import List, Tuple, Dict, Optional
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AudioFeatures:
    """Container for audio analysis features."""
    tempo: float
    beats: List[float]  # Beat timestamps in seconds
    onset_frames: List[int]
    onset_times: List[float]
    spectral_centroid: np.ndarray
    zero_crossing_rate: np.ndarray
    mfcc: np.ndarray
    duration: float
    sample_rate: int
    energy_profile: List[float]  # Energy levels over time
    
    @property
    def beat_intervals(self) -> List[float]:
        """Get intervals between beats."""
        if len(self.beats) < 2:
            return []
        return [self.beats[i+1] - self.beats[i] for i in range(len(self.beats)-1)]
    
    @property
    def average_beat_interval(self) -> float:
        """Get average time between beats."""
        intervals = self.beat_intervals
        return np.mean(intervals) if intervals else 60.0 / max(self.tempo, 60)

class AudioAnalyzer:
    """Analyzes audio files for beat detection and music synchronization."""
    
    def __init__(self):
        """Initialize audio analyzer."""
        self.sample_rate = 22050  # Standard sample rate for analysis
        self.hop_length = 512     # Frame hop length
        
    def analyze_audio_file(self, audio_path: str) -> Optional[AudioFeatures]:
        """
        Analyze an audio file and extract musical features.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            AudioFeatures object or None if analysis fails
        """
        try:
            print(f"   🎵 Analyzing audio: {Path(audio_path).name}")
            
            # Load audio file
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = librosa.get_duration(y=y, sr=sr)
            
            print(f"      Duration: {duration:.1f}s, Sample rate: {sr}Hz")
            
            # Extract tempo and beats with error handling
            try:
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
                beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=self.hop_length)
            except Exception as e:
                print(f"      ⚠️  Beat detection failed, using fallback: {e}")
                # Fallback: estimate tempo and create artificial beats
                tempo = 120.0  # Default tempo
                beat_interval = 60.0 / tempo
                num_beats = int(duration / beat_interval)
                beat_times = [i * beat_interval for i in range(num_beats)]
                beats = librosa.time_to_frames(beat_times, sr=sr, hop_length=self.hop_length)
            
            print(f"      Tempo: {tempo:.1f} BPM, Beats detected: {len(beat_times)}")
            
            # Extract onset detection with error handling
            try:
                onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=self.hop_length)
                onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)
            except Exception as e:
                print(f"      ⚠️  Onset detection failed, using fallback: {e}")
                # Fallback: create artificial onsets
                onset_times = beat_times  # Use beat times as onsets
                onset_frames = beats
            
            # Extract spectral features with error handling
            try:
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=self.hop_length)[0]
                zero_crossing_rate = librosa.feature.zero_crossing_rate(y, hop_length=self.hop_length)[0]
                mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=self.hop_length, n_mfcc=13)
            except Exception as e:
                print(f"      ⚠️  Spectral analysis failed, using fallback: {e}")
                # Fallback: create dummy features
                num_frames = len(y) // self.hop_length
                spectral_centroid = np.full(num_frames, 2000.0)  # Default centroid
                zero_crossing_rate = np.full(num_frames, 0.1)   # Default ZCR
                mfcc = np.zeros((13, num_frames))                # Zero MFCC
            
            # Calculate energy profile
            energy_profile = self._calculate_energy_profile(y, sr)
            
            features = AudioFeatures(
                tempo=float(tempo),
                beats=beat_times.tolist() if hasattr(beat_times, 'tolist') else list(beat_times),
                onset_frames=onset_frames.tolist() if hasattr(onset_frames, 'tolist') else list(onset_frames),
                onset_times=onset_times.tolist() if hasattr(onset_times, 'tolist') else list(onset_times),
                spectral_centroid=spectral_centroid,
                zero_crossing_rate=zero_crossing_rate,
                mfcc=mfcc,
                duration=duration,
                sample_rate=sr,
                energy_profile=energy_profile
            )
            
            print(f"      ✅ Audio analysis complete")
            return features
            
        except Exception as e:
            logger.error(f"Audio analysis failed for {audio_path}: {e}")
            return None
    
    def _calculate_energy_profile(self, y: np.ndarray, sr: int, window_size: float = 1.0) -> List[float]:
        """
        Calculate energy profile over time windows.
        
        Args:
            y: Audio signal
            sr: Sample rate
            window_size: Window size in seconds
            
        Returns:
            List of energy values over time
        """
        window_samples = int(window_size * sr)
        energy_profile = []
        
        for i in range(0, len(y), window_samples):
            window = y[i:i + window_samples]
            if len(window) > 0:
                # Calculate RMS energy
                energy = np.sqrt(np.mean(window ** 2))
                energy_profile.append(float(energy))
        
        return energy_profile
    
    def find_optimal_transition_points(self, audio_features: AudioFeatures, 
                                     video_duration: float, num_clips: int) -> List[float]:
        """
        Find optimal transition points aligned with musical beats.
        
        Args:
            audio_features: Audio analysis results
            video_duration: Total video duration
            num_clips: Number of video clips to transition between
            
        Returns:
            List of transition timestamps
        """
        if num_clips <= 1:
            return []
        
        # Calculate ideal transition spacing
        ideal_spacing = video_duration / num_clips
        
        # Find beats that are close to ideal transition points
        transition_points = []
        
        for i in range(1, num_clips):
            target_time = i * ideal_spacing
            
            # Find the closest beat to the target time
            closest_beat = self._find_closest_beat(audio_features.beats, target_time)
            
            if closest_beat is not None:
                transition_points.append(closest_beat)
            else:
                # Fallback to ideal spacing if no beat found
                transition_points.append(target_time)
        
        return transition_points
    
    def _find_closest_beat(self, beats: List[float], target_time: float, 
                          max_deviation: float = 2.0) -> Optional[float]:
        """
        Find the closest beat to a target time within acceptable deviation.
        
        Args:
            beats: List of beat timestamps
            target_time: Target timestamp
            max_deviation: Maximum acceptable deviation in seconds
            
        Returns:
            Closest beat timestamp or None if none within deviation
        """
        if not beats:
            return None
        
        # Find closest beat
        distances = [abs(beat - target_time) for beat in beats]
        min_distance = min(distances)
        
        if min_distance <= max_deviation:
            closest_index = distances.index(min_distance)
            return beats[closest_index]
        
        return None
    
    def get_music_sections(self, audio_features: AudioFeatures, 
                          section_duration: float = 15.0) -> List[Tuple[float, float]]:
        """
        Divide music into sections based on musical structure.
        
        Args:
            audio_features: Audio analysis results
            section_duration: Target duration for each section
            
        Returns:
            List of (start_time, end_time) tuples for music sections
        """
        sections = []
        current_time = 0.0
        
        while current_time < audio_features.duration:
            section_start = current_time
            section_end = min(current_time + section_duration, audio_features.duration)
            
            # Try to align section end with a beat
            if section_end < audio_features.duration:
                closest_beat = self._find_closest_beat(audio_features.beats, section_end, max_deviation=1.0)
                if closest_beat:
                    section_end = closest_beat
            
            sections.append((section_start, section_end))
            current_time = section_end
        
        return sections
    
    def analyze_music_energy(self, audio_features: AudioFeatures) -> Dict[str, float]:
        """
        Analyze overall music energy characteristics.
        
        Args:
            audio_features: Audio analysis results
            
        Returns:
            Dictionary with energy characteristics
        """
        # Calculate various energy metrics
        avg_energy = np.mean(audio_features.energy_profile)
        max_energy = np.max(audio_features.energy_profile)
        energy_variance = np.var(audio_features.energy_profile)
        
        # Spectral characteristics
        avg_spectral_centroid = np.mean(audio_features.spectral_centroid)
        avg_zero_crossing = np.mean(audio_features.zero_crossing_rate)
        
        # Tempo characteristics
        tempo_category = "slow" if audio_features.tempo < 90 else "medium" if audio_features.tempo < 130 else "fast"
        
        return {
            'average_energy': float(avg_energy),
            'max_energy': float(max_energy),
            'energy_variance': float(energy_variance),
            'spectral_brightness': float(avg_spectral_centroid),
            'rhythmic_complexity': float(avg_zero_crossing),
            'tempo': audio_features.tempo,
            'tempo_category': tempo_category,
            'beat_consistency': self._calculate_beat_consistency(audio_features.beat_intervals)
        }
    
    def _calculate_beat_consistency(self, beat_intervals: List[float]) -> float:
        """Calculate how consistent the beat timing is (0-1 scale)."""
        if len(beat_intervals) < 2:
            return 0.0
        
        # Calculate coefficient of variation (lower = more consistent)
        mean_interval = np.mean(beat_intervals)
        std_interval = np.std(beat_intervals)
        
        if mean_interval == 0:
            return 0.0
        
        cv = std_interval / mean_interval
        # Convert to 0-1 scale where 1 = very consistent
        consistency = max(0.0, 1.0 - cv)
        
        return consistency

def analyze_audio_for_video_sync(audio_path: str) -> Optional[AudioFeatures]:
    """
    Convenience function to analyze audio for video synchronization.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        AudioFeatures object or None if analysis fails
    """
    analyzer = AudioAnalyzer()
    return analyzer.analyze_audio_file(audio_path)

if __name__ == "__main__":
    # Test audio analysis
    import sys
    
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        features = analyze_audio_for_video_sync(audio_path)
        
        if features:
            print(f"\n📊 Audio Analysis Results:")
            print(f"   Tempo: {features.tempo:.1f} BPM")
            print(f"   Duration: {features.duration:.1f}s")
            print(f"   Beats detected: {len(features.beats)}")
            print(f"   Average beat interval: {features.average_beat_interval:.2f}s")
            
            analyzer = AudioAnalyzer()
            energy_analysis = analyzer.analyze_music_energy(features)
            print(f"   Energy characteristics: {energy_analysis}")
        else:
            print("❌ Audio analysis failed")
    else:
        print("Usage: python audio_analyzer.py <audio_file>")
