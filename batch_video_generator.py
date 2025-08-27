"""
Batch Video Generator

Creates one video for each music track using enhanced LLM-driven audio-visual
analysis and full-length beat-synchronized video generation.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json
from dataclasses import asdict
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (override existing ones)
load_dotenv(override=True)

# Add src to path for imports
sys.path.append('src')

from src.core.music_analyzer import MusicInputManager, AudioDrivenCreativeDirector
from src.core.llm_video_analyzer import LLMVideoAnalyzer
from src.editing.video_editor import VideoEditor
from src.core.video_processor import VideoProcessor
from src.utils.llm_logger import LLMResponseLogger, create_session_logger

logger = logging.getLogger(__name__)

class BatchVideoGenerator:
    """Generates videos for all music tracks using enhanced audio-visual analysis."""
    
    def __init__(self, use_dev_videos: bool = True, enable_logging: bool = True, 
                 use_cache: bool = True, enable_llm: bool = True, fast_test: bool = False):
        """Initialize batch video generator."""
        self.use_dev_videos = use_dev_videos
        self.enable_logging = enable_logging
        self.use_cache = use_cache
        self.enable_llm = enable_llm
        self.fast_test = fast_test
        
        # Initialize session logging
        if self.enable_logging:
            self.session_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.llm_logger = create_session_logger(self.session_id)
            print(f"📝 Session logging enabled: {self.session_id}")
        else:
            self.llm_logger = None
        
        # Initialize components with logging
        self.music_manager = MusicInputManager()
        
        # Initialize LLM analyzer only if enabled and API key available
        if self.enable_llm and os.getenv('OPENAI_API_KEY'):
            self.video_analyzer = LLMVideoAnalyzer(llm_logger=self.llm_logger)
            llm_status = "✅"
        else:
            self.video_analyzer = None
            llm_status = "❌ (No API key or disabled)"
            if self.enable_llm:
                print("⚠️  LLM analysis disabled: No OPENAI_API_KEY found")
        
        self.creative_director = AudioDrivenCreativeDirector()
        self.video_processor = VideoProcessor()
        self.video_editor = VideoEditor()
        
        print("🚀 Enhanced Batch Video Generator initialized")
        print(f"   Using development videos: {use_dev_videos}")
        print(f"   Cache enabled: {self.use_cache}")
        print(f"   LLM analysis: {llm_status}")
        print(f"   Fast test mode: {'✅ (3 videos max)' if fast_test else '❌'}")
        print(f"   Full-length video generation: ✅")
    
    def generate_all_videos(self) -> Dict[str, str]:
        """
        Generate FULL-LENGTH videos for all music tracks using enhanced audio-visual analysis.
        
        Returns:
            Dictionary mapping music filename to output video path
        """
        print("🎬 Starting ENHANCED batch video generation...")
        print("   🎵 Full-length videos (no duration limits)")
        print("   🎯 Beat-synchronized transitions")
        print(f"   🤖 LLM audio-visual analysis: {'✅' if self.video_analyzer else '❌'}")
        print(f"   💾 Cache: {'✅' if self.use_cache else '❌ (disabled)'}")
        
        # Step 1: Scan music tracks
        print("\n📊 Step 1: Scanning music tracks...")
        music_tracks = self.music_manager.scan_music_folder()
        
        if not music_tracks:
            print("❌ No music tracks found in music/ folder")
            return {}
        
        print(f"   Found {len(music_tracks)} music tracks")
        
        # Step 2: Get available videos
        print(f"\n📹 Step 2: Scanning video files...")
        video_dir = "input_dev" if self.use_dev_videos else "input"
        video_files = self._get_video_files(video_dir)
        
        if not video_files:
            print(f"❌ No video files found in {video_dir}/ folder")
            print(f"   Make sure downsampled videos exist in input_dev/ directory")
            return {}
        
        print(f"   Found {len(video_files)} video files ({'downsampled' if self.use_dev_videos else 'full resolution'})")
        
        # Verify we're using downsampled versions
        for video_file in video_files[:3]:  # Check first few files
            file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
            print(f"   📹 {Path(video_file).name}: {file_size_mb:.1f}MB")
        
        # Step 3: Generate videos for each music track
        print(f"\n🎵 Step 3: Creating full-length videos...")
        generated_videos = {}
        
        for i, music_track in enumerate(music_tracks, 1):
            print(f"\n[{i}/{len(music_tracks)}] Processing: {music_track.filename}")
            
            try:
                # Enhanced: Use unified audio-visual analysis
                output_path = self._create_enhanced_video(music_track, video_files)
                
                if output_path:
                    generated_videos[music_track.filename] = output_path
                    print(f"   ✅ Full-length video created: {Path(output_path).name}")
                    
                    # Log video generation result
                    if self.llm_logger:
                        self.llm_logger.log_video_generation_result(
                            music_track.filename, output_path, None, success=True
                        )
                else:
                    print(f"   ❌ Failed to create video for {music_track.filename}")
                    
                    # Log failure
                    if self.llm_logger:
                        self.llm_logger.log_video_generation_result(
                            music_track.filename, "", None, success=False, 
                            error_message="Video creation failed"
                        )
                    
            except Exception as e:
                logger.error(f"Error creating video for {music_track.filename}: {e}")
                print(f"   ❌ Error: {e}")
                
                # Log error
                if self.llm_logger:
                    self.llm_logger.log_video_generation_result(
                        music_track.filename, "", None, success=False, 
                        error_message=str(e)
                    )
            
        
        # Step 4: Generate session report
        if self.llm_logger:
            try:
                report_path = self.llm_logger.create_analysis_report(self.session_id)
                print(f"\n📋 LLM analysis report generated: {report_path}")
            except Exception as e:
                logger.warning(f"Failed to generate analysis report: {e}")
        
        # Step 5: Summary
        print(f"\n🎉 Enhanced batch generation complete!")
        print(f"   Music tracks processed: {len(music_tracks)}")
        print(f"   Full-length videos created: {len(generated_videos)}")
        
        if generated_videos:
            print(f"\n📊 Generated Full-Length Videos:")
            total_duration = 0
            for music_file, video_path in generated_videos.items():
                file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                
                # Get video duration
                try:
                    from moviepy.editor import VideoFileClip
                    clip = VideoFileClip(video_path)
                    duration = clip.duration
                    total_duration += duration
                    clip.close()
                    
                    print(f"   🎵 {music_file}")
                    print(f"      → {Path(video_path).name} ({duration:.1f}s, {file_size_mb:.1f}MB)")
                except:
                    print(f"   🎵 {music_file}")
                    print(f"      → {Path(video_path).name} ({file_size_mb:.1f}MB)")
            
            print(f"\n📈 Total video content: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        
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
    
    def _create_enhanced_video(self, music_track, video_files: List[str]) -> str:
        """Create enhanced full-length video using audio-visual analysis."""
        try:
            cache_status = "enabled" if self.use_cache else "disabled"
            print(f"   🎵🎬 Starting enhanced audio-visual analysis (cache {cache_status})...")
            
            # Step 1: Limit videos for fast testing
            test_video_files = video_files
            if self.fast_test:
                test_video_files = video_files[:3]  # Use only first 3 videos for fast testing
                print(f"      🚀 Fast test mode: Using only {len(test_video_files)} videos")
            
            # Step 2: Perform unified audio-visual analysis (if LLM available)
            sync_plan = None
            if self.video_analyzer:
                sync_plan = self.video_analyzer.analyze_audio_visual_unified(
                    audio_path=music_track.file_path,
                    video_paths=test_video_files,
                    use_dev_versions=self.use_dev_videos,
                    use_cache=self.use_cache
                )
                
                if sync_plan:
                    print(f"   ✅ Sync plan generated:")
                    print(f"      Duration: {sync_plan.music_duration:.1f}s")
                    print(f"      Transitions: {len(sync_plan.transition_points)}")
                    print(f"      Confidence: {sync_plan.sync_confidence:.2f}")
                else:
                    print(f"   ⚠️  LLM audio-visual analysis failed, using fallback method...")
            else:
                print(f"   ⚠️  LLM analysis not available, using fallback method...")
            
            # Step 2: Process videos to get clips
            cache_msg = "cached" if self.use_cache else "fresh analysis"
            print(f"   📹 Processing video clips ({cache_msg})...")
            all_clips = []
            
            for video_file in video_files[:6]:  # Use up to 6 videos
                try:
                    clips, keyframes = self.video_processor.process_video(
                        video_file, use_cache=self.use_cache, use_ai=self.enable_llm
                    )
                    all_clips.extend(clips[:3])  # Use up to 3 clips per video
                    print(f"      📹 {Path(video_file).name}: {len(clips)} clips ({cache_msg})")
                except Exception as e:
                    logger.warning(f"Failed to process {video_file}: {e}")
            
            if not all_clips:
                print(f"      ❌ No clips extracted from videos")
                return None
            
            print(f"      📊 Total clips available: {len(all_clips)}")
            
            # Step 3: Create full-length video using sync plan
            music_stem = Path(music_track.filename).stem
            
            final_video = self.video_editor.create_music_driven_video(
                clips=all_clips,
                music_name=music_stem,
                sync_plan=sync_plan,  # Use sync plan for full-length generation
                music_path=music_track.file_path
            )
            
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating enhanced video: {e}")
            print(f"   ⚠️  Enhanced creation failed, trying fallback...")
            return self._create_fallback_video(music_track, video_files)
    
    def _create_fallback_video(self, music_track, video_files: List[str]) -> str:
        """Create video using fallback method (traditional approach)."""
        try:
            cache_status = "enabled" if self.use_cache else "disabled"
            print(f"   📹 Creating fallback video (cache {cache_status})...")
            
            # Process videos to get clips
            all_clips = []
            cache_msg = "cached" if self.use_cache else "fresh analysis"
            
            for video_file in video_files[:6]:  # Use up to 6 videos
                try:
                    clips, keyframes = self.video_processor.process_video(
                        video_file, use_cache=self.use_cache, use_ai=self.enable_llm
                    )
                    all_clips.extend(clips[:3])  # Use up to 3 clips per video
                    print(f"      📹 {Path(video_file).name}: {len(clips)} clips ({cache_msg})")
                except Exception as e:
                    logger.warning(f"Failed to process {video_file}: {e}")
            
            if not all_clips:
                print(f"      ❌ No clips extracted from videos")
                return None
            
            print(f"      📊 Total clips available: {len(all_clips)}")
            
            # Create video using traditional method (no sync plan)
            music_stem = Path(music_track.filename).stem
            
            final_video = self.video_editor.create_music_driven_video(
                clips=all_clips,
                music_name=music_stem,
                sync_plan=None,  # No sync plan - will use fallback method
                music_path=music_track.file_path
            )
            
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating fallback video: {e}")
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
    """Main function to run enhanced batch video generation."""
    parser = argparse.ArgumentParser(description='Enhanced Drodeo Batch Video Generator')
    parser.add_argument('--no-cache', action='store_true', 
                       help='Disable video processing cache (force fresh analysis)')
    parser.add_argument('--use-full-res', action='store_true',
                       help='Use full resolution videos instead of downsampled versions')
    parser.add_argument('--no-logging', action='store_true',
                       help='Disable session logging')
    parser.add_argument('--fast-test', action='store_true',
                       help='Fast test mode: Use only 3 videos for quicker testing')
    
    args = parser.parse_args()
    
    print("🎬 Enhanced Drodeo Batch Video Generator")
    print("=" * 50)
    print("🎵 Full-length beat-synchronized videos")
    print("🤖 AI-powered audio-visual analysis (required)")
    print("📝 Comprehensive logging and reporting")
    print(f"📹 Using {'full resolution' if args.use_full_res else 'downsampled'} videos by default")
    
    # Initialize enhanced generator with command line options
    generator = BatchVideoGenerator(
        use_dev_videos=not args.use_full_res,  # Default to downsampled
        enable_logging=not args.no_logging,
        use_cache=not args.no_cache,
        enable_llm=True,  # Always use AI
        fast_test=args.fast_test
    )
    
    # Generate all full-length videos (no duration limits)
    generated_videos = generator.generate_all_videos()
    
    # Save report
    if generated_videos:
        generator.save_generation_report(generated_videos)
        
        print(f"\n✅ Enhanced batch generation successful!")
        print(f"   Check the output/ folder for your full-length videos")
        if not args.no_logging:
            print(f"   Check the logs/openai_responses/ folder for analysis logs")
    else:
        print(f"\n❌ No videos were generated")
        print(f"   Check that you have:")
        print(f"   - Music files in music/ folder")
        print(f"   - Video files in input_dev/ folder (or input/ with --use-full-res)")
        print(f"   - Valid OpenAI API key in environment")

if __name__ == "__main__":
    main()
