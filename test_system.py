#!/usr/bin/env python3
"""
System Testing and Validation for Drone Video Generator MVP

This module provides comprehensive testing and validation:
- End-to-end system testing
- Component integration testing
- Performance validation
- Output quality verification
- Error handling validation
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
import subprocess
import json

def test_environment_setup() -> Tuple[bool, List[str]]:
    """Test that the environment is properly set up."""
    print("🔧 Testing Environment Setup...")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check required modules
    required_modules = [
        'cv2', 'numpy', 'moviepy', 'openai', 'yt_dlp', 
        'scipy', 'tqdm', 'requests'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            issues.append(f"Missing required module: {module}")
    
    # Check ffmpeg availability
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        issues.append("ffmpeg not found or not working")
    
    # Check directory structure
    required_dirs = ['uploads', 'output', 'music', 'cache']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create directory {dir_name}: {e}")
    
    success = len(issues) == 0
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"   {status} - Environment setup")
    
    if issues:
        for issue in issues:
            print(f"      ⚠️  {issue}")
    
    return success, issues

def test_video_processing() -> Tuple[bool, List[str]]:
    """Test video processing components."""
    print("\n🎬 Testing Video Processing...")
    
    issues = []
    
    try:
        from video_processor import VideoProcessor, VideoClip
        
        # Check if test videos exist
        test_videos = ['uploads/DJI_0131.mp4', 'uploads/DJI_0141.mp4']
        available_videos = [v for v in test_videos if os.path.exists(v)]
        
        if not available_videos:
            issues.append("No test videos found in uploads directory")
            return False, issues
        
        # Test video processor
        processor = VideoProcessor()
        
        # Test basic video info extraction
        video_info = processor.get_video_info(available_videos[0])
        if not video_info or 'duration' not in video_info:
            issues.append("Failed to extract video information")
        
        # Test keyframe extraction
        keyframes = processor.extract_keyframes(available_videos[0], num_frames=3)
        if len(keyframes) == 0:
            issues.append("Failed to extract keyframes")
        
        print("   ✅ PASS - Video processing components")
        
    except Exception as e:
        issues.append(f"Video processing error: {str(e)}")
        print(f"   ❌ FAIL - Video processing: {e}")
    
    return len(issues) == 0, issues

def test_ai_integration() -> Tuple[bool, List[str]]:
    """Test AI integration components."""
    print("\n🤖 Testing AI Integration...")
    
    issues = []
    
    try:
        from ai_analyzer import AIAnalyzer
        
        # Test AI analyzer initialization
        analyzer = AIAnalyzer()
        
        # Test with a simple image (create a test image)
        import numpy as np
        test_image = np.random.randint(0, 255, (360, 640, 3), dtype=np.uint8)
        
        # This might fail if no OpenAI API key, which is expected
        try:
            analysis = analyzer.analyze_video_with_ai([test_image], "test_video.mp4")
            print("   ✅ PASS - AI integration working")
        except Exception as ai_error:
            if "API key" in str(ai_error) or "authentication" in str(ai_error).lower():
                print("   ⚠️  SKIP - AI integration (API key required)")
                issues.append("AI integration requires valid OpenAI API key")
            else:
                issues.append(f"AI integration error: {str(ai_error)}")
                print(f"   ❌ FAIL - AI integration: {ai_error}")
        
    except Exception as e:
        issues.append(f"AI analyzer initialization error: {str(e)}")
        print(f"   ❌ FAIL - AI analyzer: {e}")
    
    return len(issues) == 0, issues

def test_music_system() -> Tuple[bool, List[str]]:
    """Test music download and integration system."""
    print("\n🎵 Testing Music System...")
    
    issues = []
    
    try:
        from music_downloader import MusicDownloader
        
        # Test music downloader
        downloader = MusicDownloader()
        
        # Ensure sample music files exist
        downloader.ensure_music_library()
        
        # Test getting music for each theme
        themes = ['happy', 'exciting', 'peaceful', 'adventure', 'cinematic']
        for theme in themes:
            music_path = downloader.get_theme_music(theme)
            if not music_path or not os.path.exists(music_path):
                issues.append(f"No music available for {theme} theme")
        
        if len(issues) == 0:
            print("   ✅ PASS - Music system")
        else:
            print("   ⚠️  PARTIAL - Music system (some themes missing)")
        
    except Exception as e:
        issues.append(f"Music system error: {str(e)}")
        print(f"   ❌ FAIL - Music system: {e}")
    
    return len(issues) == 0, issues

def test_video_editing() -> Tuple[bool, List[str]]:
    """Test video editing and rendering."""
    print("\n✂️  Testing Video Editing...")
    
    issues = []
    
    try:
        from video_editor import VideoEditor
        from video_processor import VideoClip
        
        # Check if test videos exist
        test_videos = ['uploads/DJI_0131.mp4', 'uploads/DJI_0141.mp4']
        available_videos = [v for v in test_videos if os.path.exists(v)]
        
        if not available_videos:
            issues.append("No test videos available for editing test")
            return False, issues
        
        # Create a test clip
        test_clip = VideoClip(
            start_time=0,
            end_time=3,
            duration=3,
            quality_score=0.8,
            motion_score=50,
            brightness_score=0.7,
            file_path=available_videos[0],
            description='Test clip'
        )
        
        # Test video editor
        editor = VideoEditor(output_dir="test_output")
        
        # Create a short test video
        output_path = editor.create_themed_video([test_clip], 'peaceful', 3)
        
        if os.path.exists(output_path):
            # Verify the output video
            file_size = os.path.getsize(output_path)
            if file_size > 1000:  # At least 1KB
                print("   ✅ PASS - Video editing")
                # Clean up test file
                try:
                    os.remove(output_path)
                    if os.path.exists("test_output"):
                        os.rmdir("test_output")
                except:
                    pass
            else:
                issues.append("Generated video file is too small")
        else:
            issues.append("Failed to generate test video")
        
    except Exception as e:
        issues.append(f"Video editing error: {str(e)}")
        print(f"   ❌ FAIL - Video editing: {e}")
    
    return len(issues) == 0, issues

def test_end_to_end() -> Tuple[bool, List[str]]:
    """Test the complete end-to-end pipeline."""
    print("\n🚀 Testing End-to-End Pipeline...")
    
    issues = []
    
    try:
        # Check if test videos exist
        test_videos = ['uploads/DJI_0131.mp4', 'uploads/DJI_0141.mp4']
        available_videos = [v for v in test_videos if os.path.exists(v)]
        
        if not available_videos:
            issues.append("No test videos available for end-to-end test")
            return False, issues
        
        # Run the main pipeline with minimal settings
        cmd = [
            sys.executable, 'main.py',
            *available_videos,
            '--duration', '5',
            '--themes', 'peaceful',
            '--output-dir', 'test_e2e_output'
        ]
        
        print("   🔄 Running end-to-end test...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Check if output was generated
            output_dir = 'test_e2e_output'
            if os.path.exists(output_dir):
                output_files = os.listdir(output_dir)
                video_files = [f for f in output_files if f.endswith('.mp4')]
                
                if video_files:
                    print("   ✅ PASS - End-to-end pipeline")
                    # Clean up
                    try:
                        shutil.rmtree(output_dir)
                    except:
                        pass
                else:
                    issues.append("No video files generated in end-to-end test")
            else:
                issues.append("Output directory not created in end-to-end test")
        else:
            issues.append(f"End-to-end test failed with return code {result.returncode}")
            if result.stderr:
                issues.append(f"Error output: {result.stderr[:200]}")
        
    except subprocess.TimeoutExpired:
        issues.append("End-to-end test timed out (>5 minutes)")
    except Exception as e:
        issues.append(f"End-to-end test error: {str(e)}")
        print(f"   ❌ FAIL - End-to-end: {e}")
    
    return len(issues) == 0, issues

def test_performance() -> Tuple[bool, List[str]]:
    """Test system performance and resource usage."""
    print("\n⚡ Testing Performance...")
    
    issues = []
    warnings = []
    
    try:
        import psutil
        
        # Get initial system stats
        initial_memory = psutil.virtual_memory().percent
        initial_cpu = psutil.cpu_percent(interval=1)
        
        # Check available disk space
        disk_usage = psutil.disk_usage('.')
        free_gb = disk_usage.free / (1024**3)
        
        if free_gb < 1.0:
            issues.append(f"Low disk space: {free_gb:.1f}GB available")
        elif free_gb < 5.0:
            warnings.append(f"Limited disk space: {free_gb:.1f}GB available")
        
        # Check memory usage
        if initial_memory > 90:
            issues.append(f"High memory usage: {initial_memory:.1f}%")
        elif initial_memory > 80:
            warnings.append(f"High memory usage: {initial_memory:.1f}%")
        
        print(f"   📊 System stats:")
        print(f"      Memory usage: {initial_memory:.1f}%")
        print(f"      CPU usage: {initial_cpu:.1f}%")
        print(f"      Free disk space: {free_gb:.1f}GB")
        
        if len(issues) == 0:
            print("   ✅ PASS - Performance check")
        else:
            print("   ⚠️  WARN - Performance issues detected")
        
        if warnings:
            for warning in warnings:
                print(f"      ⚠️  {warning}")
        
    except ImportError:
        warnings.append("psutil not available for performance monitoring")
        print("   ⚠️  SKIP - Performance check (psutil required)")
    except Exception as e:
        issues.append(f"Performance check error: {str(e)}")
        print(f"   ❌ FAIL - Performance check: {e}")
    
    return len(issues) == 0, issues + warnings

def validate_output_quality() -> Tuple[bool, List[str]]:
    """Validate the quality of generated outputs."""
    print("\n🎯 Validating Output Quality...")
    
    issues = []
    
    try:
        output_dir = 'output'
        if not os.path.exists(output_dir):
            issues.append("Output directory does not exist")
            return False, issues
        
        # Find video files
        video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
        
        if not video_files:
            issues.append("No output videos found")
            return False, issues
        
        print(f"   📹 Found {len(video_files)} output videos")
        
        # Check each video file
        for video_file in video_files[:3]:  # Check first 3 videos
            video_path = os.path.join(output_dir, video_file)
            
            # Check file size
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if file_size_mb < 1:
                issues.append(f"{video_file}: File too small ({file_size_mb:.1f}MB)")
            elif file_size_mb > 100:
                issues.append(f"{video_file}: File too large ({file_size_mb:.1f}MB)")
            
            # Check video properties using ffprobe
            try:
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_format', '-show_streams', video_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    
                    # Check for video and audio streams
                    video_streams = [s for s in info['streams'] if s['codec_type'] == 'video']
                    audio_streams = [s for s in info['streams'] if s['codec_type'] == 'audio']
                    
                    if not video_streams:
                        issues.append(f"{video_file}: No video stream found")
                    if not audio_streams:
                        issues.append(f"{video_file}: No audio stream found")
                    
                    # Check duration
                    if 'format' in info and 'duration' in info['format']:
                        duration = float(info['format']['duration'])
                        if duration < 3:
                            issues.append(f"{video_file}: Duration too short ({duration:.1f}s)")
                        elif duration > 300:
                            issues.append(f"{video_file}: Duration too long ({duration:.1f}s)")
                
            except Exception as e:
                issues.append(f"{video_file}: Failed to analyze - {str(e)}")
        
        if len(issues) == 0:
            print("   ✅ PASS - Output quality validation")
        else:
            print("   ❌ FAIL - Output quality issues detected")
        
    except Exception as e:
        issues.append(f"Output validation error: {str(e)}")
        print(f"   ❌ FAIL - Output validation: {e}")
    
    return len(issues) == 0, issues

def run_all_tests() -> Dict[str, Any]:
    """Run all system tests and return comprehensive results."""
    print("🧪 DRONE VIDEO GENERATOR - SYSTEM TESTING")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all test suites
    test_results = {}
    
    test_suites = [
        ("Environment Setup", test_environment_setup),
        ("Video Processing", test_video_processing),
        ("AI Integration", test_ai_integration),
        ("Music System", test_music_system),
        ("Video Editing", test_video_editing),
        ("Performance", test_performance),
        ("Output Quality", validate_output_quality),
        ("End-to-End", test_end_to_end),
    ]
    
    total_passed = 0
    total_issues = []
    
    for test_name, test_func in test_suites:
        try:
            passed, issues = test_func()
            test_results[test_name] = {
                'passed': passed,
                'issues': issues
            }
            
            if passed:
                total_passed += 1
            
            total_issues.extend(issues)
            
        except Exception as e:
            test_results[test_name] = {
                'passed': False,
                'issues': [f"Test suite error: {str(e)}"]
            }
            total_issues.append(f"{test_name}: {str(e)}")
    
    # Calculate overall results
    total_tests = len(test_suites)
    success_rate = (total_passed / total_tests) * 100
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TESTING SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total time: {elapsed_time:.1f}s")
    print(f"📈 Success rate: {success_rate:.1f}% ({total_passed}/{total_tests})")
    print(f"❌ Total issues: {len(total_issues)}")
    
    # Print detailed results
    print(f"\n📋 Detailed Results:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"   {status} {test_name}")
        
        if result['issues']:
            for issue in result['issues'][:2]:  # Show first 2 issues
                print(f"      ⚠️  {issue}")
            if len(result['issues']) > 2:
                print(f"      ... and {len(result['issues']) - 2} more issues")
    
    # Overall assessment
    if success_rate >= 80:
        print(f"\n🎉 SYSTEM STATUS: READY FOR USE")
        print("   The drone video generator is working well!")
    elif success_rate >= 60:
        print(f"\n⚠️  SYSTEM STATUS: MOSTLY FUNCTIONAL")
        print("   Some issues detected but core functionality works.")
    else:
        print(f"\n❌ SYSTEM STATUS: NEEDS ATTENTION")
        print("   Multiple issues detected. Please review and fix.")
    
    print("=" * 60)
    
    return {
        'success_rate': success_rate,
        'total_passed': total_passed,
        'total_tests': total_tests,
        'total_issues': len(total_issues),
        'elapsed_time': elapsed_time,
        'test_results': test_results,
        'overall_status': 'ready' if success_rate >= 80 else 'needs_attention'
    }

if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Issues detected
