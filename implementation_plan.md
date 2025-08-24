# Implementation Plan

Create a simplified command-line drone video generation MVP that processes MP4 files, uses AI for intelligent clip detection, and outputs multiple themed videos with progress tracking.

This implementation focuses on a streamlined command-line interface with essential AI integration and progress feedback. The system processes large drone video files locally while using OpenAI API for smart clip selection, outputting 5 themed videos with different music and pacing.

## [Types]

Define minimal data structures for command-line video processing.

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class VideoTheme(Enum):
    HAPPY = "happy"
    EXCITING = "exciting"
    PEACEFUL = "peaceful"
    ADVENTURE = "adventure"
    CINEMATIC = "cinematic"

@dataclass
class VideoClip:
    start_time: float
    end_time: float
    quality_score: float
    ai_description: str

@dataclass
class ThemeConfig:
    name: str
    music_file: str
    target_duration: int = 180
    pacing: str = "medium"
```

## [Files]

Create minimal file structure for command-line MVP.

**New files to be created:**
- `main.py` - Command-line entry point with argument parsing
- `video_processor.py` - Core video analysis and processing
- `ai_analyzer.py` - OpenAI GPT-4 Vision integration
- `video_editor.py` - MoviePy-based editing and music overlay
- `music_downloader.py` - API integration for downloading royalty-free music
- `config.py` - Theme configurations and settings
- `requirements.txt` - Python dependencies
- `music/` - Directory for downloaded theme music files (auto-populated)
- `output/` - Video output directory
- `.env` - OpenAI API key and music API keys

## [Functions]

Implement essential functions for command-line processing.

**New functions in main.py:**
- `main()` - Command-line interface and argument parsing
- `process_videos(input_paths: List[str]) -> None`
- `display_progress(current: int, total: int, step: str) -> None`

**New functions in video_processor.py:**
- `extract_keyframes(video_path: str) -> List[np.ndarray]`
- `analyze_motion(video_path: str) -> List[float]`
- `select_best_clips(video_path: str, ai_data: List[Dict]) -> List[VideoClip]`

**New functions in ai_analyzer.py:**
- `analyze_keyframes(keyframes: List[np.ndarray]) -> List[Dict]`
- `get_quality_scores(ai_responses: List[Dict]) -> List[float]`

**New functions in video_editor.py:**
- `create_themed_video(clips: List[VideoClip], theme: VideoTheme) -> str`
- `add_music_overlay(video_path: str, music_path: str) -> str`

**New functions in music_downloader.py:**
- `download_theme_music(theme: VideoTheme) -> str`
- `search_royalty_free_music(theme: str, duration: int) -> List[Dict]`
- `download_audio_file(url: str, filename: str) -> str`
- `ensure_music_library() -> None`

## [Classes]

Simple class structure for command-line tool.

**New classes in video_processor.py:**
- `VideoProcessor` - Main processing coordinator
  - Methods: `__init__()`, `process()`, `get_clips()`
  - Purpose: Handle video analysis and clip extraction

## [Dependencies]

Essential dependencies for command-line MVP.

```
moviepy==1.0.3
opencv-python==4.8.1.78
numpy==1.24.3
openai==1.3.0
python-dotenv==1.0.0
tqdm==4.66.1
requests==2.31.0
yt-dlp==2023.10.13
argparse
```

**System Dependencies:**
- FFmpeg (brew install ffmpeg)

**Music API Options:**
- YouTube Audio Library (via yt-dlp for royalty-free tracks)
- Freesound API (for ambient/nature sounds)
- Pixabay API (royalty-free music)
- No API key required for YouTube Audio Library

## [Testing]

Basic testing for core functionality.

**Test files:**
- `test_video_processor.py` - Core logic tests
- `test_ai_analyzer.py` - API integration tests with mocks

## [Implementation Order]

**✅ COMPLETED STEPS:**

0. **Environment Setup & Validation** - ✅ COMPLETE
   - Python 3.12.3 validation, FFmpeg installation check
   - Virtual environment setup, dependency installation
   - API key configuration with .env file
   - Comprehensive setup.py script with validation

1. **Basic Functionality Test** - ✅ COMPLETE
   - All imports verified (MoviePy, OpenCV, OpenAI, etc.)
   - CLI help and argument parsing working
   - Environment validation passing all checks

2. **Project Structure Validation** - ✅ COMPLETE
   - Directory creation (uploads/, output/, cache/, tests/)
   - File organization and .gitignore setup
   - Git repository initialization and first commit

3. **Configuration Testing** - ✅ COMPLETE
   - Theme configurations loaded (5 themes: Happy, Exciting, Peaceful, Adventure, Cinematic)
   - Video processing parameters configured
   - API settings and file paths established

4. **Command-line Interface Enhancement** - ✅ COMPLETE
   - Multi-video support with argument parsing
   - Cache management options (--no-cache, --clear-cache)
   - Dry-run mode and theme selection
   - Progress tracking and error handling

5. **Video Processing Core** - ✅ COMPLETE
   - Real-time video analysis with OpenCV
   - Motion detection and scene change analysis
   - Quality scoring (brightness, focus, motion)
   - Keyframe extraction for AI analysis
   - 4K drone video support (3840x2160)

5.5. **Performance Optimization** - ✅ COMPLETE
   - Smart caching system with file-based storage
   - 25-second → 1-second processing time improvement
   - Cache invalidation based on file changes
   - Keyframe storage as JPEG files

**🚧 REMAINING STEPS:**

6. **AI Integration** - Add OpenAI GPT-4 Vision for intelligent clip detection
7. **Clip Selection Logic** - Combine motion analysis with AI insights for theme-based selection
8. **Video Editing Pipeline** - Implement MoviePy-based editing and rendering
9. **Music Integration** - Add dynamic music downloading and overlay
10. **Theme Generation** - Create multiple themed outputs with different styles
11. **Progress & Error Handling** - Enhanced feedback and error management
12. **Testing & Validation** - End-to-end testing with real drone videos

**📊 CURRENT STATUS: 6/12 steps completed (50%)**
