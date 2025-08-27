"""
Batch Video Generator

Creates one video for each music track using LLM-driven creative direction
and all available video content.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import json
from dataclasses import asdict

# Add src to path for imports
sys.path.append('src')

from src.core.music_analyzer import MusicInputManager, AudioDrivenCreativeDirector
from src.core.llm_video_analyzer import LLMVideoAnalyzer
from src.utils.video_preprocessor import VideoPreprocessor
from src.editing.video_editor import VideoEditor
from src.core.video_processor import VideoProcessor

logger = logging.getLogger(__name__)

class BatchVideoGenerator:
    """Generates videos for all music tracks using intelligent analysis."""
    
    def __init__(self, use_dev_videos: bool = True):
        """Initialize batch video generator."""
        self.use_dev_videos = use_dev_videos
        self.music_manager = MusicInputManager()
        self.video_analyzer = LLMVideoAnalyzer()
        self.creative_director = AudioDrivenCreativeDirector()
        self.video_processor = VideoProcessor()
        self.video_editor = VideoEditor()
        
        print("🚀 Batch Video Generator initialized")
        print(f"   Using development videos: {use_dev_videos}")
    
    def generate_all_videos(self, max_duration: int = 60) -> Dict[str, str]:
        """
        Generate videos for all music tracks.
        
        Args:
            max_duration: Maximum video duration in seconds
            
        Returns:
            Dictionary mapping music filename to output video path
        """
        print("🎬 Starting batch video generation...")
        
        # Step 1: Scan and analyze music
        print("\n📊 Step 1: Analyzing music tracks...")
        music_tracks = self.music_manager.scan_music_folder()
        
        if not music_tracks:
            print("❌ No music tracks found in music_input/ folder")
            return {}
        
        # Step 2: Get available videos
        print(f"\n📹 Step 2: Scanning video files...")
        video_dir = "input_dev" if self.use_dev_videos else "input"
        video_files = self._get_video_files(video_dir)
        
        if not video_files:
            print(f"❌ No video files found in {video_dir}/ folder")
            return {}
        
        print(f"   Found {len(video_files)} video files")
        
        # Step 3: Analyze videos (simplified for now without LLM)
        print(f"\n🎯 Step 3: Processing video content...")
        video_analyses = self._analyze_videos_simple(video_files)
        
        # Step 4: Generate videos for each music track
        print(f"\n🎵 Step 4: Creating videos for each music track...")
        generated_videos = {}
        
        for i, music_track in enumerate(music_tracks, 1):
            print(f"\n[{i}/{len(music_tracks)}] Processing: {music_track.filename}")
            
            try:
                # Create video plan
                video_plan = self.creative_director.create_video_plan(music_track, video_analyses)
                
                # Generate video
                output_path = self._create_video_from_plan(music_track, video_plan, video_files, max_duration)
                
                if output_path:
                    generated_videos[music_track.filename] = output_path
                    print(f"   ✅ Video created: {Path(output_path).name}")
                else:
                    print(f"   ❌ Failed to create video for {music_track.filename}")
                    
            except Exception as e:
                logger.error(f"Error creating video for {music_track.filename}: {e}")
                print(f"   ❌ Error: {e}")
        
        # Step 5: Summary
        print(f"\n🎉 Batch generation complete!")
        print(f"   Music tracks processed: {len(music_tracks)}")
        print(f"   Videos created: {len(generated_videos)}")
        
        if generated_videos:
            print(f"\n📊 Generated Videos:")
            for music_file, video_path in generated_videos.items():
                file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                print(f"   🎵 {music_file}")
                print(f"      → {Path(video_path).name} ({file_size_mb:.1f}MB)")
        
        return generated_videos
    
    def _get_video_files(self, video_dir: str) -> List[str]:
        """Get list of video files from directory."""
        if not os.path.exists(video_dir):
            return []
        
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(Path(video_dir).glob(f"*{ext}"))
        
        return [str(f) for f in video_files]
    
    def _analyze_videos_simple(self, video_files: List[str]) -> Dict[str, Any]:
        """Simple video analysis without LLM (for now)."""
        analyses = {}
        
        for video_file in video_files:
            try:
                # Get basic video info
                from moviepy.editor import VideoFileClip
                clip = VideoFileClip(video_file)
                
                # Simple analysis based on filename and duration
                filename = Path(video_file).name.lower()
                
                analysis = {
                    'duration': clip.duration,
                    'fps': clip.fps,
                    'size': (clip.w, clip.h),
                    'content_type': self._guess_content_type(filename),
                    'energy_level': self._guess_energy_level(filename, clip.duration),
                    'suitable_themes': self._guess_suitable_themes(filename)
                }
                
                analyses[video_file] = analysis
                clip.close()
                
            except Exception as e:
                logger.warning(f"Failed to analyze {video_file}: {e}")
        
        return analyses
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename."""
        if 'dji' in filename:
            return 'drone_aerial'
        elif 'img' in filename:
            return 'handheld_mobile'
        else:
            return 'unknown'
    
    def _guess_energy_level(self, filename: str, duration: float) -> str:
        """Guess energy level from filename and duration."""
        if duration < 10:
            return 'high'
        elif duration < 30:
            return 'medium'
        else:
            return 'low'
    
    def _guess_suitable_themes(self, filename: str) -> List[str]:
        """Guess suitable themes from filename."""
        if 'dji' in filename:
            return ['cinematic', 'adventure', 'peaceful']
        elif 'img' in filename:
            return ['happy', 'exciting', 'adventure']
        else:
            return ['happy', 'cinematic']
    
    def _create_video_from_plan(self, music_track, video_plan: Dict[str, Any], 
                               video_files: List[str], max_duration: int) -> str:
        """Create video from the generated plan."""
        try:
            # Use existing video processing pipeline
            print(f"   🎬 Creating video with {len(video_files)} source videos...")
            
            # Process videos to get clips
            all_clips = []
            
            for video_file in video_files[:6]:  # Use up to 6 videos
                try:
                    clips, keyframes = self.video_processor.process_video(video_file, use_cache=True)
                    all_clips.extend(clips[:3])  # Use up to 3 clips per video
                    print(f"      📹 {Path(video_file).name}: {len(clips)} clips")
                except Exception as e:
                    logger.warning(f"Failed to process {video_file}: {e}")
            
            if not all_clips:
                print(f"      ❌ No clips extracted from videos")
                return None
            
            print(f"      📊 Total clips available: {len(all_clips)}")
            
            # Create themed video using existing editor
            target_duration = min(video_plan['target_duration'], max_duration)
            
            # Determine theme based on music
            primary_theme = music_track.suitable_themes[0] if music_track.suitable_themes else 'happy'
            
            # Create output filename
            music_stem = Path(music_track.filename).stem
            output_filename = f"{music_stem}_{primary_theme}_{len(all_clips)}clips_{target_duration}s.mp4"
            output_path = os.path.join("output", output_filename)
            
            # Use the video editor to create the final video
            final_video = self.video_editor.create_music_driven_video(
                clips=all_clips,
                music_name=music_stem,
                target_duration=target_duration,
                music_path=music_track.file_path
            )
            
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating video from plan: {e}")
            return None
    
    def save_generation_report(self, generated_videos: Dict[str, str], 
                             report_file: str = "generation_report.json"):
        """Save generation report to file."""
        try:
            report = {
                'timestamp': str(Path().cwd()),
                'total_videos_generated': len(generated_videos),
                'videos': {}
            }
            
            for music_file, video_path in generated_videos.items():
                if os.path.exists(video_path):
                    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                    
                    report['videos'][music_file] = {
                        'output_path': video_path,
                        'file_size_mb': round(file_size_mb, 1),
                        'exists': True
                    }
                else:
                    report['videos'][music_file] = {
                        'output_path': video_path,
                        'file_size_mb': 0,
                        'exists': False
                    }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"   📋 Generation report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save generation report: {e}")

def main():
    """Main function to run batch video generation."""
    print("🎬 Drodeo Batch Video Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = BatchVideoGenerator(use_dev_videos=True)
    
    # Generate all videos
    generated_videos = generator.generate_all_videos(max_duration=60)
    
    # Save report
    if generated_videos:
        generator.save_generation_report(generated_videos)
        
        print(f"\n✅ Batch generation successful!")
        print(f"   Check the output/ folder for your videos")
    else:
        print(f"\n❌ No videos were generated")
        print(f"   Check that you have:")
        print(f"   - Music files in music_input/ folder")
        print(f"   - Video files in input/ or input_dev/ folder")

if __name__ == "__main__":
    main()
