"""
Clip Selection Logic
Combines clips from multiple videos and assigns them to themes based on AI analysis and motion characteristics.
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict
import random
from config import VideoTheme, THEME_CONFIGS, VIDEO_CONFIG
from video_processor import VideoClip
from ai_analyzer import AIAnalyzer

@dataclass
class ThemeClipPool:
    """Container for clips assigned to a specific theme."""
    theme: VideoTheme
    clips: List[VideoClip]
    total_duration: float
    target_duration: float
    theme_score: float

class ClipSelector:
    """Handles intelligent clip selection and theme assignment."""
    
    def __init__(self):
        self.target_clips_per_theme = VIDEO_CONFIG["target_clips_per_theme"]
        try:
            self.ai_analyzer = AIAnalyzer()
        except Exception as e:
            print(f"   ⚠️  AI analyzer initialization failed: {e}")
            self.ai_analyzer = None
    
    def assign_clips_to_themes(self, all_clips: List[VideoClip], ai_analyses_by_video: Dict[str, List[Dict]]) -> Dict[VideoTheme, ThemeClipPool]:
        """Assign clips from multiple videos to different themes."""
        print(f"\n🎯 Assigning {len(all_clips)} clips to themes...")
        
        # Initialize theme pools
        theme_pools = {}
        for theme in VideoTheme:
            theme_config = THEME_CONFIGS[theme]
            theme_pools[theme] = ThemeClipPool(
                theme=theme,
                clips=[],
                total_duration=0.0,
                target_duration=theme_config.target_duration,
                theme_score=0.0
            )
        
        # Score clips for each theme
        scored_clips = self._score_clips_for_themes(all_clips, ai_analyses_by_video)
        
        # Distribute clips to themes using intelligent selection
        self._distribute_clips_to_themes(scored_clips, theme_pools)
        
        # Balance and optimize theme pools
        self._balance_theme_pools(theme_pools)
        
        # Print summary
        self._print_theme_summary(theme_pools)
        
        return theme_pools
    
    def _score_clips_for_themes(self, clips: List[VideoClip], ai_analyses_by_video: Dict[str, List[Dict]]) -> List[Dict]:
        """Score each clip for its suitability to different themes."""
        print("   📊 Scoring clips for theme suitability...")
        
        scored_clips = []
        
        for clip in clips:
            clip_scores = {
                'clip': clip,
                'theme_scores': {}
            }
            
            # Get AI analysis for this video if available
            video_ai_analyses = ai_analyses_by_video.get(clip.file_path, [])
            
            # Calculate base theme scores
            for theme in VideoTheme:
                score = self._calculate_theme_score(clip, theme, video_ai_analyses)
                clip_scores['theme_scores'][theme] = score
            
            scored_clips.append(clip_scores)
        
        return scored_clips
    
    def _calculate_theme_score(self, clip: VideoClip, theme: VideoTheme, ai_analyses: List[Dict]) -> float:
        """Calculate how well a clip fits a specific theme."""
        theme_config = THEME_CONFIGS[theme]
        score = 0.0
        
        # Base quality score (30% weight)
        score += clip.quality_score * 0.3
        
        # Motion-based scoring (25% weight)
        motion_factor = self._get_motion_factor_for_theme(clip.motion_score, theme)
        score += motion_factor * 0.25
        
        # Brightness/lighting scoring (15% weight)
        brightness_factor = self._get_brightness_factor_for_theme(clip.brightness_score, theme)
        score += brightness_factor * 0.15
        
        # AI-based scoring (30% weight)
        if ai_analyses:
            ai_factor = self._get_ai_factor_for_theme(ai_analyses, theme)
            score += ai_factor * 0.3
        else:
            # Fallback scoring without AI
            score += 0.15  # neutral score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_motion_factor_for_theme(self, motion_score: float, theme: VideoTheme) -> float:
        """Get motion suitability factor for a theme."""
        theme_config = THEME_CONFIGS[theme]
        
        # Normalize motion score (assuming 0-100 range)
        normalized_motion = min(motion_score / 100.0, 1.0)
        
        if theme_config.pacing == "fast":
            # Exciting themes prefer high motion
            return normalized_motion
        elif theme_config.pacing == "slow":
            # Peaceful themes prefer low to medium motion
            return 1.0 - (normalized_motion * 0.7)
        else:  # medium pacing
            # Medium pacing themes prefer moderate motion
            if normalized_motion < 0.3:
                return normalized_motion / 0.3  # Scale up low motion
            elif normalized_motion > 0.7:
                return (1.0 - normalized_motion) / 0.3  # Scale down high motion
            else:
                return 1.0  # Perfect range
    
    def _get_brightness_factor_for_theme(self, brightness_score: float, theme: VideoTheme) -> float:
        """Get brightness suitability factor for a theme."""
        if theme == VideoTheme.HAPPY:
            # Happy themes prefer bright, well-lit scenes
            return brightness_score
        elif theme == VideoTheme.PEACEFUL:
            # Peaceful themes are flexible with lighting
            return 0.8 + (brightness_score * 0.2)
        elif theme == VideoTheme.CINEMATIC:
            # Cinematic themes prefer good lighting but can handle dramatic lighting
            return 0.7 + (brightness_score * 0.3)
        else:
            # Other themes: standard brightness preference
            return brightness_score
    
    def _get_ai_factor_for_theme(self, ai_analyses: List[Dict], theme: VideoTheme) -> float:
        """Get AI-based suitability factor for a theme."""
        if not ai_analyses:
            return 0.5  # neutral score
        
        theme_name = theme.value.lower()
        total_score = 0.0
        count = 0
        
        for analysis in ai_analyses:
            # Direct theme suitability
            suitable_themes = analysis.get('theme_suitability', [])
            if isinstance(suitable_themes, list) and theme_name in [t.lower() for t in suitable_themes]:
                total_score += 0.8
            
            # Scene type influences
            scene_type = analysis.get('scene_type', '').lower()
            scene_score = self._get_scene_score_for_theme(scene_type, theme)
            total_score += scene_score * 0.3
            
            # Visual quality influences
            visual_quality = analysis.get('visual_quality', 5) / 10.0
            interest_level = analysis.get('interest_level', 5) / 10.0
            scenic_beauty = analysis.get('scenic_beauty', 5) / 10.0
            
            # Weight these factors based on theme
            if theme == VideoTheme.CINEMATIC:
                total_score += (visual_quality * 0.4 + scenic_beauty * 0.3 + interest_level * 0.2)
            elif theme == VideoTheme.PEACEFUL:
                total_score += (scenic_beauty * 0.4 + visual_quality * 0.3 + interest_level * 0.1)
            elif theme == VideoTheme.EXCITING:
                total_score += (interest_level * 0.4 + visual_quality * 0.3 + scenic_beauty * 0.2)
            else:
                total_score += (visual_quality * 0.3 + interest_level * 0.3 + scenic_beauty * 0.3)
            
            count += 1
        
        return total_score / count if count > 0 else 0.5
    
    def _get_scene_score_for_theme(self, scene_type: str, theme: VideoTheme) -> float:
        """Get scene type suitability score for a theme."""
        scene_theme_mapping = {
            'water': {'peaceful': 0.9, 'cinematic': 0.7, 'adventure': 0.6, 'happy': 0.5, 'exciting': 0.4},
            'ocean': {'peaceful': 0.9, 'cinematic': 0.8, 'adventure': 0.7, 'happy': 0.5, 'exciting': 0.5},
            'mountain': {'adventure': 0.9, 'cinematic': 0.8, 'peaceful': 0.6, 'exciting': 0.5, 'happy': 0.4},
            'landscape': {'cinematic': 0.8, 'peaceful': 0.7, 'adventure': 0.7, 'happy': 0.6, 'exciting': 0.4},
            'forest': {'peaceful': 0.8, 'adventure': 0.7, 'cinematic': 0.6, 'happy': 0.5, 'exciting': 0.3},
            'city': {'exciting': 0.8, 'cinematic': 0.7, 'adventure': 0.5, 'happy': 0.6, 'peaceful': 0.2},
            'urban': {'exciting': 0.8, 'cinematic': 0.7, 'adventure': 0.5, 'happy': 0.6, 'peaceful': 0.2},
            'buildings': {'exciting': 0.7, 'cinematic': 0.6, 'adventure': 0.4, 'happy': 0.5, 'peaceful': 0.3},
        }
        
        theme_name = theme.value.lower()
        
        for scene_key, theme_scores in scene_theme_mapping.items():
            if scene_key in scene_type:
                return theme_scores.get(theme_name, 0.5)
        
        return 0.5  # neutral score for unknown scene types
    
    def _distribute_clips_to_themes(self, scored_clips: List[Dict], theme_pools: Dict[VideoTheme, ThemeClipPool]):
        """Distribute clips to themes using intelligent selection."""
        print("   🎲 Distributing clips to themes...")
        
        # Sort clips by their best theme score
        for clip_data in scored_clips:
            best_theme = max(clip_data['theme_scores'], key=clip_data['theme_scores'].get)
            best_score = clip_data['theme_scores'][best_theme]
            clip_data['best_theme'] = best_theme
            clip_data['best_score'] = best_score
        
        # Sort by best score descending
        scored_clips.sort(key=lambda x: x['best_score'], reverse=True)
        
        # For MVP: Allow clip reuse across themes to ensure variety
        # This helps when we have limited clips but want multiple themed videos
        min_clips_per_theme = 1  # Minimum clips needed to create a video
        
        # First pass: assign clips to their best-fitting theme
        for clip_data in scored_clips:
            clip = clip_data['clip']
            best_theme = clip_data['best_theme']
            pool = theme_pools[best_theme]
            
            # Always add to best theme if it needs clips
            if len(pool.clips) < self.target_clips_per_theme:
                pool.clips.append(clip)
                pool.total_duration += clip.duration
                pool.theme_score += clip_data['best_score']
        
        # Second pass: ensure all themes have at least some clips for variety
        # Allow clips to be reused if their theme score is reasonable (>0.3)
        for theme in VideoTheme:
            pool = theme_pools[theme]
            if len(pool.clips) < min_clips_per_theme:
                # Find clips that could work for this theme
                suitable_clips = []
                for clip_data in scored_clips:
                    theme_score = clip_data['theme_scores'][theme]
                    if theme_score > 0.3:  # Reasonable fit
                        suitable_clips.append((clip_data, theme_score))
                
                # Sort by theme-specific score
                suitable_clips.sort(key=lambda x: x[1], reverse=True)
                
                # Add clips until we have enough
                for clip_data, theme_score in suitable_clips:
                    if len(pool.clips) >= self.target_clips_per_theme:
                        break
                    
                    clip = clip_data['clip']
                    # Check if this clip is already in this theme pool
                    if not any(existing_clip.file_path == clip.file_path and 
                             existing_clip.start_time == clip.start_time 
                             for existing_clip in pool.clips):
                        pool.clips.append(clip)
                        pool.total_duration += clip.duration
                        pool.theme_score += theme_score
    
    def _balance_theme_pools(self, theme_pools: Dict[VideoTheme, ThemeClipPool]):
        """Balance theme pools to ensure good variety and duration."""
        print("   ⚖️  Balancing theme pools...")
        
        for theme, pool in theme_pools.items():
            if len(pool.clips) == 0:
                continue
            
            # Sort clips by quality within each theme
            pool.clips.sort(key=lambda x: x.quality_score, reverse=True)
            
            # Calculate average theme score
            if len(pool.clips) > 0:
                pool.theme_score = pool.theme_score / len(pool.clips)
            
            # Ensure variety by removing duplicate clips from same video if we have too many
            self._ensure_video_variety(pool)
    
    def _ensure_video_variety(self, pool: ThemeClipPool):
        """Ensure clips come from different videos for variety."""
        if len(pool.clips) <= 3:
            return  # Too few clips to worry about variety
        
        video_counts = defaultdict(int)
        for clip in pool.clips:
            video_counts[clip.file_path] += 1
        
        # If any video has more than 40% of clips, reduce it
        max_clips_per_video = max(2, len(pool.clips) // 3)
        
        filtered_clips = []
        video_clip_counts = defaultdict(int)
        
        for clip in pool.clips:
            if video_clip_counts[clip.file_path] < max_clips_per_video:
                filtered_clips.append(clip)
                video_clip_counts[clip.file_path] += 1
        
        pool.clips = filtered_clips
        pool.total_duration = sum(clip.duration for clip in pool.clips)
    
    def _print_theme_summary(self, theme_pools: Dict[VideoTheme, ThemeClipPool]):
        """Print summary of clip distribution across themes."""
        print("\n📋 Theme Distribution Summary:")
        print("=" * 60)
        
        for theme, pool in theme_pools.items():
            theme_config = THEME_CONFIGS[theme]
            clip_count = len(pool.clips)
            duration = pool.total_duration
            avg_score = pool.theme_score if pool.theme_score > 0 else 0
            
            # Get video sources
            video_sources = set(clip.file_path for clip in pool.clips)
            source_count = len(video_sources)
            
            print(f"{theme_config.name:12} | {clip_count:2d} clips | {duration:5.1f}s | "
                  f"Score: {avg_score:.2f} | {source_count} videos")
        
        print("=" * 60)
        
        total_clips = sum(len(pool.clips) for pool in theme_pools.values())
        total_duration = sum(pool.total_duration for pool in theme_pools.values())
        print(f"{'TOTAL':12} | {total_clips:2d} clips | {total_duration:5.1f}s")
    
    def get_clips_for_theme(self, theme: VideoTheme, theme_pools: Dict[VideoTheme, ThemeClipPool]) -> List[VideoClip]:
        """Get clips assigned to a specific theme."""
        if theme in theme_pools:
            return theme_pools[theme].clips
        return []
    
    def get_theme_statistics(self, theme_pools: Dict[VideoTheme, ThemeClipPool]) -> Dict[str, Dict]:
        """Get detailed statistics for each theme."""
        stats = {}
        
        for theme, pool in theme_pools.items():
            theme_config = THEME_CONFIGS[theme]
            
            if len(pool.clips) > 0:
                quality_scores = [clip.quality_score for clip in pool.clips]
                motion_scores = [clip.motion_score for clip in pool.clips]
                durations = [clip.duration for clip in pool.clips]
                
                stats[theme.value] = {
                    'clip_count': len(pool.clips),
                    'total_duration': pool.total_duration,
                    'target_duration': pool.target_duration,
                    'avg_quality': np.mean(quality_scores),
                    'avg_motion': np.mean(motion_scores),
                    'avg_clip_duration': np.mean(durations),
                    'theme_score': pool.theme_score,
                    'video_sources': len(set(clip.file_path for clip in pool.clips)),
                    'pacing': theme_config.pacing
                }
            else:
                stats[theme.value] = {
                    'clip_count': 0,
                    'total_duration': 0.0,
                    'target_duration': pool.target_duration,
                    'avg_quality': 0.0,
                    'avg_motion': 0.0,
                    'avg_clip_duration': 0.0,
                    'theme_score': 0.0,
                    'video_sources': 0,
                    'pacing': theme_config.pacing
                }
        
        return stats

def select_clips_for_themes(all_clips: List[VideoClip], ai_analyses_by_video: Dict[str, List[Dict]] = None) -> Dict[VideoTheme, ThemeClipPool]:
    """Convenience function to select and assign clips to themes."""
    if ai_analyses_by_video is None:
        ai_analyses_by_video = {}
    
    selector = ClipSelector()
    return selector.assign_clips_to_themes(all_clips, ai_analyses_by_video)

if __name__ == "__main__":
    # Test the clip selector
    print("Testing Clip Selector...")
    
    # This would normally be called with real clips and AI analyses
    # For testing, we'll just verify the imports work
    from config import VideoTheme, THEME_CONFIGS
    print(f"Available themes: {[theme.value for theme in VideoTheme]}")
    print("Clip Selector module loaded successfully!")
