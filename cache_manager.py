"""
Cache Manager for Video Processing
Handles caching of video analysis results to avoid reprocessing unchanged videos.
"""

import json
import os
import hashlib
import base64
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import asdict
from video_processor import VideoClip

class CacheManager:
    """Manages caching of video processing results."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.video_cache_dir = self.cache_dir / "video_analysis"
        self.keyframes_cache_dir = self.cache_dir / "keyframes"
        
        # Create cache directories
        self.video_cache_dir.mkdir(parents=True, exist_ok=True)
        self.keyframes_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, video_path: str) -> str:
        """Generate a unique hash for a video file based on path, size, and modification time."""
        stat = os.stat(video_path)
        file_info = f"{video_path}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(file_info.encode()).hexdigest()
    
    def _get_cache_filename(self, video_path: str) -> str:
        """Generate cache filename for a video."""
        video_name = Path(video_path).stem
        file_hash = self._get_file_hash(video_path)
        return f"{video_name}_{file_hash}.json"
    
    def _get_keyframe_prefix(self, video_path: str) -> str:
        """Generate keyframe filename prefix for a video."""
        video_name = Path(video_path).stem
        file_hash = self._get_file_hash(video_path)
        return f"{video_name}_{file_hash}"
    
    def _save_keyframes(self, video_path: str, keyframes: List[np.ndarray]) -> List[str]:
        """Save keyframes as image files and return their paths."""
        prefix = self._get_keyframe_prefix(video_path)
        keyframe_paths = []
        
        for i, frame in enumerate(keyframes):
            filename = f"{prefix}_frame_{i}.jpg"
            filepath = self.keyframes_cache_dir / filename
            
            # Save frame as JPEG
            cv2.imwrite(str(filepath), frame)
            keyframe_paths.append(str(filepath))
        
        return keyframe_paths
    
    def _load_keyframes(self, keyframe_paths: List[str]) -> List[np.ndarray]:
        """Load keyframes from image files."""
        keyframes = []
        
        for path in keyframe_paths:
            if os.path.exists(path):
                frame = cv2.imread(path)
                if frame is not None:
                    keyframes.append(frame)
        
        return keyframes
    
    def _cleanup_old_keyframes(self, video_path: str):
        """Remove old keyframe files for a video."""
        video_name = Path(video_path).stem
        
        # Find all keyframe files for this video (any hash)
        pattern = f"{video_name}_*_frame_*.jpg"
        for filepath in self.keyframes_cache_dir.glob(pattern):
            try:
                filepath.unlink()
            except OSError:
                pass  # File might be in use or already deleted
    
    def has_cache(self, video_path: str) -> bool:
        """Check if cache exists for a video file."""
        cache_file = self.video_cache_dir / self._get_cache_filename(video_path)
        return cache_file.exists()
    
    def save_cache(self, video_path: str, clips: List[VideoClip], keyframes: List[np.ndarray], 
                   motion_scores: List[float], scene_changes: List[float], ai_analyses: List[Dict] = None) -> None:
        """Save video processing results to cache."""
        try:
            # Clean up old keyframes first
            self._cleanup_old_keyframes(video_path)
            
            # Save keyframes
            keyframe_paths = self._save_keyframes(video_path, keyframes)
            
            # Prepare cache data
            cache_data = {
                'video_path': video_path,
                'file_hash': self._get_file_hash(video_path),
                'clips': [asdict(clip) for clip in clips],
                'keyframe_paths': keyframe_paths,
                'motion_scores': motion_scores,
                'scene_changes': scene_changes,
                'ai_analyses': ai_analyses or [],
                'cached_at': os.path.getctime(video_path)
            }
            
            # Save cache file
            cache_file = self.video_cache_dir / self._get_cache_filename(video_path)
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"   💾 Cached results for {Path(video_path).name}")
            
        except Exception as e:
            print(f"   ⚠️  Failed to save cache: {e}")
    
    def load_cache(self, video_path: str) -> Optional[Tuple[List[VideoClip], List[np.ndarray], List[float], List[float]]]:
        """Load video processing results from cache."""
        try:
            cache_file = self.video_cache_dir / self._get_cache_filename(video_path)
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Verify cache is still valid (file hasn't changed)
            current_hash = self._get_file_hash(video_path)
            if cache_data.get('file_hash') != current_hash:
                print(f"   🔄 Cache invalid for {Path(video_path).name} (file changed)")
                return None
            
            # Load clips
            clips = []
            for clip_data in cache_data['clips']:
                clip = VideoClip(**clip_data)
                clips.append(clip)
            
            # Load keyframes
            keyframes = self._load_keyframes(cache_data['keyframe_paths'])
            
            # Load other data
            motion_scores = cache_data['motion_scores']
            scene_changes = cache_data['scene_changes']
            
            print(f"   ⚡ Loaded from cache: {Path(video_path).name}")
            return clips, keyframes, motion_scores, scene_changes
            
        except Exception as e:
            print(f"   ⚠️  Failed to load cache: {e}")
            return None
    
    def clear_cache(self, video_path: str = None) -> None:
        """Clear cache for a specific video or all videos."""
        if video_path:
            # Clear cache for specific video
            cache_file = self.video_cache_dir / self._get_cache_filename(video_path)
            if cache_file.exists():
                cache_file.unlink()
            
            self._cleanup_old_keyframes(video_path)
            print(f"   🗑️  Cleared cache for {Path(video_path).name}")
        else:
            # Clear all cache
            for cache_file in self.video_cache_dir.glob("*.json"):
                cache_file.unlink()
            
            for keyframe_file in self.keyframes_cache_dir.glob("*.jpg"):
                keyframe_file.unlink()
            
            print("   🗑️  Cleared all cache")
    
    def get_cache_info(self) -> Dict:
        """Get information about current cache."""
        video_cache_files = list(self.video_cache_dir.glob("*.json"))
        keyframe_files = list(self.keyframes_cache_dir.glob("*.jpg"))
        
        total_size = 0
        for file_path in video_cache_files + keyframe_files:
            total_size += file_path.stat().st_size
        
        return {
            'cached_videos': len(video_cache_files),
            'keyframe_files': len(keyframe_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }
    
    def print_cache_stats(self) -> None:
        """Print cache statistics."""
        info = self.get_cache_info()
        print(f"\n📊 Cache Statistics:")
        print(f"   Cached videos: {info['cached_videos']}")
        print(f"   Keyframe files: {info['keyframe_files']}")
        print(f"   Total size: {info['total_size_mb']:.1f} MB")
        print(f"   Cache directory: {info['cache_dir']}")
