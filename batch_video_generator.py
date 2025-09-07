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

from src.core.gemini_multimodal_analyzer import GeminiMultimodalAnalyzer
from src.core.gemini_self_translator import GeminiSelfTranslator
from src.editing.video_editor import VideoEditor
from src.utils.llm_logger import create_session_logger

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
        
        # Initialize Gemini multimodal analyzer only if enabled and API key available
        if self.enable_llm and os.getenv('GEMINI_API_KEY'):
            self.multimodal_analyzer = GeminiMultimodalAnalyzer()
            llm_status = "✅ Gemini Multimodal"
        else:
            self.multimodal_analyzer = None
            llm_status = "❌ (No Gemini API key or disabled)"
            if self.enable_llm:
                print("⚠️  Gemini multimodal analysis disabled: No GEMINI_API_KEY found")
        
        self.video_editor = VideoEditor()
        
        # Initialize Gemini model for video selection
        if self.multimodal_analyzer and hasattr(self.multimodal_analyzer, 'model'):
            self.model = self.multimodal_analyzer.model
        else:
            self.model = None
        
        print("🚀 Enhanced Batch Video Generator initialized")
        print(f"   Using development videos: {use_dev_videos}")
        print(f"   Cache enabled: {self.use_cache}")
        print(f"   LLM analysis: {llm_status}")
        print(f"   Fast test mode: {'✅ (3 videos max)' if fast_test else '❌'}")
        print(f"   Full-length video generation: ✅")
        print(f"   Video orchestration: {'✅ (unlimited videos)' if self.model else '❌'}")
    
    def generate_all_videos(self) -> Dict[str, str]:
        """
        Generate FULL-LENGTH videos for all music tracks using enhanced audio-visual analysis.
        
        Returns:
            Dictionary mapping music filename to output video path
        """
        print("🎬 Starting ENHANCED batch video generation...")
        print("   🎵 Full-length videos (no duration limits)")
        print("   🎯 Beat-synchronized transitions")
        print(f"   🤖 Gemini multimodal analysis: {'✅' if self.multimodal_analyzer else '❌'}")
        print(f"   💾 Cache: {'✅' if self.use_cache else '❌ (disabled)'}")
        
        # Step 1: Scan music tracks
        print("\n📊 Step 1: Scanning music tracks...")
        music_tracks = self._get_music_files("music")
        
        if not music_tracks:
            print("❌ No music tracks found in music_input/ folder")
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
            print(f"\n[{i}/{len(music_tracks)}] Processing: {music_track['filename']}")
            
            try:
                # Enhanced: Use unified audio-visual analysis
                output_path = self._create_enhanced_video(music_track, video_files)
                
                if output_path:
                    generated_videos[music_track['filename']] = output_path
                    print(f"   ✅ Full-length video created: {Path(output_path).name}")
                    
                    # Log video generation result
                    if self.llm_logger:
                        self.llm_logger.log_video_generation_result(
                            music_track['filename'], output_path, None, success=True
                        )
                else:
                    print(f"   ❌ Failed to create video for {music_track['filename']}")
                    
                    # Log failure
                    if self.llm_logger:
                        self.llm_logger.log_video_generation_result(
                            music_track['filename'], "", None, success=False, 
                            error_message="Video creation failed"
                        )
                    
            except Exception as e:
                logger.error(f"Error creating video for {music_track['filename']}: {e}")
                print(f"   ❌ Error: {e}")
                
                # Log error
                if self.llm_logger:
                    self.llm_logger.log_video_generation_result(
                        music_track['filename'], "", None, success=False, 
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
    
    def _get_music_files(self, music_dir: str) -> List[Dict[str, str]]:
        """Get list of music files from directory - simple version like test script."""
        if not os.path.exists(music_dir):
            return []
        
        music_extensions = ['.mp3', '.m4a', '.wav', '.flac', '.ogg', '.MP3', '.M4A', '.WAV']
        music_files = []
        
        for file_path in Path(music_dir).iterdir():
            if file_path.is_file() and file_path.suffix in music_extensions:
                music_files.append({
                    'filename': file_path.name,
                    'file_path': str(file_path)
                })
        
        return music_files
    
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
    
    def select_best_videos(self, music_path: str, video_paths: List[str]) -> List[str]:
        """If >10 videos, ask Gemini to pick the best 10"""
        
        if len(video_paths) <= 10:
            return video_paths
        
        if not self.model:
            print(f"      ⚠️  No Gemini model available, using first 10 videos")
            return video_paths[:10]
        
        print(f"      🎯 Orchestrating: Selecting best 10 from {len(video_paths)} videos...")
        
        try:
            # Upload audio for analysis
            import google.generativeai as genai
            uploaded_audio = genai.upload_file(path=music_path)
            
            # Wait for processing
            import time
            max_wait = 30
            elapsed = 0
            while uploaded_audio.state.name == "PROCESSING" and elapsed < max_wait:
                time.sleep(1)
                elapsed += 1
                uploaded_audio = genai.get_file(uploaded_audio.name)
            
            if uploaded_audio.state.name != "ACTIVE":
                print(f"         ⚠️  Audio upload failed, using first 10 videos")
                return video_paths[:10]
            
            # Simple prompt to Gemini
            video_list = "\n".join([f"- {os.path.basename(path)}" for path in video_paths])
            
            prompt = f"""
            I have {len(video_paths)} videos and need to pick the best 10 for a music video.
            
            Music: {os.path.basename(music_path)}
            
            Available videos:
            {video_list}
            
            Pick the 10 best video filenames for this music. Just list the filenames, one per line.
            """
            
            response = self.model.generate_content([prompt, uploaded_audio])
            selected_names = response.text.strip().split('\n')
            
            # Match back to full paths
            selected_paths = []
            for name in selected_names:
                name_clean = name.strip().replace('-', '').replace('*', '').strip()
                for path in video_paths:
                    if name_clean in os.path.basename(path):
                        selected_paths.append(path)
                        break
            
            # Ensure we have exactly 10 or fewer
            final_selection = selected_paths[:10]
            
            # If we didn't get enough matches, fill with remaining videos
            if len(final_selection) < 10:
                remaining_videos = [v for v in video_paths if v not in final_selection]
                final_selection.extend(remaining_videos[:10-len(final_selection)])
            
            print(f"         ✅ Selected {len(final_selection)} videos for analysis")
            for i, path in enumerate(final_selection, 1):
                print(f"            {i}. {os.path.basename(path)}")
            
            return final_selection
            
        except Exception as e:
            print(f"         ⚠️  Video selection failed ({e}), using first 10 videos")
            return video_paths[:10]

    def _create_enhanced_video(self, music_track, video_files: List[str]) -> str:
        """Create enhanced full-length video using two-step Gemini pipeline."""
        try:
            print(f"   🎵🎬 Starting TWO-STEP GEMINI PIPELINE...")
            
            # NEW: Smart video selection if >10 videos
            if len(video_files) > 10 and not self.fast_test:
                print(f"      🎯 {len(video_files)} videos detected - using orchestration...")
                selected_videos = self.select_best_videos(music_track['file_path'], video_files)
                test_video_files = selected_videos
            else:
                # Original logic for ≤10 videos or fast test mode
                test_video_files = video_files
                if self.fast_test:
                    test_video_files = video_files[:3]  # Use only first 3 videos for fast testing
                    print(f"      🚀 Fast test mode: Using only {len(test_video_files)} videos")
            
            # Check if two-step pipeline is available
            if not self.multimodal_analyzer:
                raise ValueError("Two-step pipeline not available: No GEMINI_API_KEY found")
            
            # STEP 1: Multimodal Analysis
            print(f"   📊 Step 1: Multimodal Analysis...")
            multimodal_result = self.multimodal_analyzer.analyze_batch(
                audio_path=music_track['file_path'],
                video_paths=test_video_files,
                test_name=f"Music Video: {music_track['filename']}"
            )
            
            if not multimodal_result:
                raise ValueError("Multimodal analysis failed - no result returned")
            
            print(f"   ✅ Step 1 complete:")
            print(f"      Duration: {multimodal_result.audio_duration:.1f}s")
            print(f"      Tempo: {multimodal_result.audio_tempo:.1f} BPM")
            print(f"      Sync confidence: {multimodal_result.sync_confidence:.2f}")
            
            # STEP 2: Self-Translation with Video Duration Information
            print(f"   🤖 Step 2: Self-Translation with video duration validation...")
            translator = GeminiSelfTranslator()
            
            # CRITICAL FIX: Get actual video durations for validation
            video_durations = {}
            for video_path in test_video_files:
                try:
                    from moviepy.editor import VideoFileClip
                    temp_clip = VideoFileClip(video_path)
                    video_durations[os.path.basename(video_path)] = temp_clip.duration
                    temp_clip.close()
                    print(f"      📹 {os.path.basename(video_path)}: {video_durations[os.path.basename(video_path)]:.1f}s")
                except Exception as e:
                    logger.warning(f"Failed to get duration for {video_path}: {e}")
                    video_durations[os.path.basename(video_path)] = 60.0  # Fallback duration
            
            available_video_names = [os.path.basename(path) for path in test_video_files]
            editing_instructions = translator.translate_timeline(
                gemini_reasoning=multimodal_result.gemini_reasoning,
                audio_duration=None,  # Let self-translator extract from natural language
                available_videos=available_video_names,
                video_durations=video_durations  # Pass actual durations
            )
            
            print(f"   ✅ Step 2 complete:")
            print(f"      Clips generated: {len(editing_instructions.clips)}")
            print(f"      Transitions: {len(editing_instructions.transitions)}")
            print(f"      Translation confidence: {editing_instructions.metadata.get('confidence', 'N/A')}")
            
            # STEP 3: Direct Video Creation
            print(f"   🎬 Step 3: Direct Video Creation...")
            
            # Update video paths in instructions to full paths
            for clip_data in editing_instructions.clips:
                video_name = clip_data['video_path']
                # Find full path for this video name
                for full_path in test_video_files:
                    if os.path.basename(full_path) == video_name:
                        clip_data['video_path'] = full_path
                        break
            
            # Create video using two-step pipeline method
            music_stem = Path(music_track['filename']).stem
            final_video = self.video_editor.create_from_instructions(
                instructions=editing_instructions,
                music_name=music_stem,
                music_path=music_track['file_path']
            )
            
            print(f"   ✅ Step 3 complete: Two-step pipeline video created!")
            return final_video
            
        except Exception as e:
            logger.error(f"Error in two-step pipeline: {e}")
            raise
    
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
