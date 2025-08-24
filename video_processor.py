"""
Video Processing Core
Handles video analysis, keyframe extraction, and clip detection for drone videos.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
from pathlib import Path
import os
from tqdm import tqdm

@dataclass
class VideoClip:
    start_time: float
    end_time: float
    duration: float
    quality_score: float
    motion_score: float
    brightness_score: float
    file_path: str
    description: str = ""

class VideoProcessor:
    """Main video processing coordinator."""
    
    def __init__(self):
        self.frame_sample_rate = 30  # analyze every 30th frame for speed
        self.min_clip_duration = 2.0  # minimum 2 seconds
        self.max_clip_duration = 15.0  # maximum 15 seconds
        self.keyframes_per_video = 8  # number of keyframes to extract for AI analysis
    
    def get_video_info(self, video_path: str) -> Dict:
        """Extract basic video information."""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        cap.release()
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'width': width,
            'height': height,
            'file_size': os.path.getsize(video_path)
        }
    
    def extract_keyframes(self, video_path: str, num_frames: int = None) -> List[np.ndarray]:
        """Extract evenly distributed keyframes from video for AI analysis."""
        if num_frames is None:
            num_frames = self.keyframes_per_video
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame indices to extract
        if frame_count <= num_frames:
            frame_indices = list(range(frame_count))
        else:
            frame_indices = np.linspace(0, frame_count - 1, num_frames, dtype=int)
        
        keyframes = []
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                # Resize frame for AI processing (smaller = faster/cheaper)
                frame_resized = cv2.resize(frame, (640, 360))
                keyframes.append(frame_resized)
        
        cap.release()
        return keyframes
    
    def analyze_motion(self, video_path: str) -> List[float]:
        """Analyze motion intensity throughout the video."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        motion_scores = []
        prev_frame = None
        frame_idx = 0
        
        # Get total frames for progress bar
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        with tqdm(total=total_frames//self.frame_sample_rate, desc="Analyzing motion", leave=False) as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample frames for performance
                if frame_idx % self.frame_sample_rate == 0:
                    # Convert to grayscale for motion detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)
                    
                    if prev_frame is not None:
                        # Calculate frame difference
                        frame_diff = cv2.absdiff(prev_frame, gray)
                        motion_score = np.mean(frame_diff)
                        motion_scores.append(motion_score)
                        
                        # Calculate timestamp
                        timestamp = frame_idx / fps
                        
                    prev_frame = gray
                    pbar.update(1)
                
                frame_idx += 1
        
        cap.release()
        return motion_scores
    
    def calculate_brightness_score(self, frame: np.ndarray) -> float:
        """Calculate brightness/exposure quality of a frame."""
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Calculate mean brightness
        brightness = np.mean(gray)
        
        # Penalize over/under exposure
        # Optimal range is roughly 80-180 for 8-bit images
        if brightness < 50:  # too dark
            score = brightness / 50.0
        elif brightness > 200:  # too bright
            score = (255 - brightness) / 55.0
        else:  # good range
            score = 1.0
        
        return max(0.0, min(1.0, score))
    
    def detect_scene_changes(self, video_path: str, threshold: float = 30.0) -> List[float]:
        """Detect major scene changes in the video."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        scene_changes = []
        prev_hist = None
        frame_idx = 0
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames for performance
            if frame_idx % self.frame_sample_rate == 0:
                # Calculate color histogram
                hist = cv2.calcHist([frame], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
                
                if prev_hist is not None:
                    # Compare histograms
                    correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    
                    # If correlation is low, it's a scene change
                    if correlation < (1.0 - threshold / 100.0):
                        timestamp = frame_idx / fps
                        scene_changes.append(timestamp)
                
                prev_hist = hist
            
            frame_idx += 1
        
        cap.release()
        return scene_changes
    
    def select_best_clips(self, video_path: str, motion_scores: List[float], scene_changes: List[float]) -> List[VideoClip]:
        """Select the best clips based on motion analysis and scene changes."""
        video_info = self.get_video_info(video_path)
        duration = video_info['duration']
        fps = video_info['fps']
        
        clips = []
        
        # Convert motion scores to timestamps
        motion_timestamps = []
        for i, score in enumerate(motion_scores):
            timestamp = (i * self.frame_sample_rate) / fps
            motion_timestamps.append((timestamp, score))
        
        # Find high-motion segments
        motion_threshold = np.percentile(motion_scores, 70)  # Top 30% motion
        
        current_clip_start = None
        current_clip_scores = []
        
        for timestamp, motion_score in motion_timestamps:
            if motion_score > motion_threshold:
                if current_clip_start is None:
                    current_clip_start = timestamp
                current_clip_scores.append(motion_score)
            else:
                # End of high-motion segment
                if current_clip_start is not None and len(current_clip_scores) > 0:
                    clip_duration = timestamp - current_clip_start
                    
                    # Only keep clips within duration limits
                    if self.min_clip_duration <= clip_duration <= self.max_clip_duration:
                        avg_motion = np.mean(current_clip_scores)
                        
                        # Extract a frame for brightness analysis
                        mid_timestamp = current_clip_start + clip_duration / 2
                        brightness_score = self._get_frame_brightness(video_path, mid_timestamp)
                        
                        # Calculate overall quality score
                        quality_score = (avg_motion / 100.0) * 0.7 + brightness_score * 0.3
                        
                        clip = VideoClip(
                            start_time=current_clip_start,
                            end_time=timestamp,
                            duration=clip_duration,
                            quality_score=quality_score,
                            motion_score=avg_motion,
                            brightness_score=brightness_score,
                            file_path=video_path,
                            description=f"High motion segment ({clip_duration:.1f}s)"
                        )
                        clips.append(clip)
                    
                    current_clip_start = None
                    current_clip_scores = []
        
        # Sort clips by quality score and return top ones
        clips.sort(key=lambda x: x.quality_score, reverse=True)
        return clips[:15]  # Return top 15 clips per video
    
    def _get_frame_brightness(self, video_path: str, timestamp: float) -> float:
        """Get brightness score for a frame at specific timestamp."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0.5  # default score
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return self.calculate_brightness_score(frame)
        return 0.5
    
    def process_video(self, video_path: str, use_cache: bool = True, use_ai: bool = True) -> Tuple[List[VideoClip], List[np.ndarray]]:
        """Process a single video and return clips and keyframes."""
        from cache_manager import CacheManager
        from ai_analyzer import analyze_video_with_ai, AIAnalyzer
        
        print(f"🎬 Analyzing {Path(video_path).name}...")
        
        # Initialize cache manager
        cache_manager = CacheManager() if use_cache else None
        
        # Try to load from cache first
        if cache_manager and cache_manager.has_cache(video_path):
            cached_result = cache_manager.load_cache(video_path)
            if cached_result:
                # Handle both old (4 elements) and new (5 elements) cache formats
                if len(cached_result) >= 5:
                    clips, keyframes, motion_scores, scene_changes, ai_analyses = cached_result
                elif len(cached_result) == 4:
                    clips, keyframes, motion_scores, scene_changes = cached_result
                    ai_analyses = []  # No AI analyses in old format
                else:
                    # Invalid cache format, skip
                    cached_result = None
                
                if cached_result:
                    print(f"   ✅ Found {len(clips)} good clips, {len(keyframes)} keyframes (cached)")
                    return clips, keyframes
        
        # Get video info
        video_info = self.get_video_info(video_path)
        print(f"   Duration: {video_info['duration']:.1f}s, Resolution: {video_info['width']}x{video_info['height']}")
        
        # Extract keyframes for AI analysis
        print("   Extracting keyframes...")
        keyframes = self.extract_keyframes(video_path)
        
        # AI Analysis of keyframes
        ai_analyses = []
        if use_ai:
            try:
                ai_analyses = analyze_video_with_ai(keyframes, Path(video_path).name)
                if not ai_analyses:
                    ai_analyses = []
            except Exception as e:
                print(f"   ⚠️  AI analysis skipped: {e}")
                ai_analyses = []
        
        # Analyze motion
        print("   Analyzing motion patterns...")
        motion_scores = self.analyze_motion(video_path)
        
        # Detect scene changes
        print("   Detecting scene changes...")
        scene_changes = self.detect_scene_changes(video_path)
        
        # Select best clips
        print("   Selecting best clips...")
        clips = self.select_best_clips(video_path, motion_scores, scene_changes)
        
        # Enhance clips with AI analysis
        if ai_analyses and use_ai:
            try:
                analyzer = AIAnalyzer()
                clips = analyzer.enhance_clip_scoring(clips, ai_analyses)
            except Exception as e:
                print(f"   ⚠️  AI enhancement skipped: {e}")
        
        # Save to cache
        if cache_manager:
            cache_manager.save_cache(video_path, clips, keyframes, motion_scores, scene_changes, ai_analyses)
        
        print(f"   ✅ Found {len(clips)} good clips, {len(keyframes)} keyframes")
        
        return clips, keyframes

def process_videos(video_paths: List[str]) -> Tuple[List[VideoClip], List[np.ndarray]]:
    """Process multiple videos and return combined clips and keyframes."""
    processor = VideoProcessor()
    
    all_clips = []
    all_keyframes = []
    
    for i, video_path in enumerate(video_paths, 1):
        print(f"\n[{i}/{len(video_paths)}] Processing {Path(video_path).name}")
        
        try:
            clips, keyframes = processor.process_video(video_path)
            all_clips.extend(clips)
            all_keyframes.extend(keyframes)
        except Exception as e:
            print(f"❌ Error processing {video_path}: {e}")
            continue
    
    print(f"\n🎉 Total: {len(all_clips)} clips from {len(video_paths)} videos")
    return all_clips, all_keyframes
