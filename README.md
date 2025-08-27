# 🎵 Drodeo - Music-Driven Video Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Music-Driven](https://img.shields.io/badge/Status-Music%20Driven-brightgreen.svg)](https://github.com/umang94/Drodeo)
[![GPU Support](https://img.shields.io/badge/GPU-CUDA%20%7C%20MPS-orange.svg)](https://github.com/umang94/Drodeo)

**Transform your videos into music-driven masterpieces with AI-powered analysis and GPU acceleration.**

An intelligent video processing system that analyzes your music and video content to create compelling, beat-synchronized videos. Uses LLM-powered video analysis and music-driven creative direction for professional-quality results.

## 🔧 Current Development Status (v3.2.0)

**✅ Video Quality Enhancement Complete**

Major video quality improvements have been successfully implemented to eliminate frame repetition and enhance visual diversity:

### Phase 1 & 2 Complete ✅
- ✅ **Frame Repetition Eliminated** - Intelligent clip extension system with 5 progressive strategies
- ✅ **Dynamic Keyframe Extraction** - 1 frame per 2 seconds instead of fixed count
- ✅ **Enhanced Clip Duration** - 4-40s clips (vs previous 1-25s) for better variety
- ✅ **Fresh Analysis Pipeline** - Proper cache invalidation and regeneration
- ✅ **Intelligent Extension** - Smart content-aware clip extension vs simple looping
- ✅ **Robust Error Handling** - Comprehensive validation and graceful fallbacks

### Key Improvements
- **Better Video Variety** - 7 clips from 6 videos vs previous 13 repetitive clips
- **Reduced Repetition** - 34 clips needed vs previous 44 clips after extension
- **Fresh AI Analysis** - 96+ API calls ensuring quality-based clip selection
- **Fast Testing** - `--fast-test` flag for 3-video rapid iteration
- **Cache Control** - `--no-cache` flag for fresh analysis when needed

**Status:** Production ready with significantly improved video quality and variety.

## ✨ Features

### 🎵 Music-Driven Approach
- **User Music Input** - Use your own music files from `music_input/` folder
- **Audio Analysis** - Advanced beat detection and energy profiling with librosa
- **Creative Direction** - LLM generates video concepts based on music characteristics
- **Beat Synchronization** - Video transitions aligned with musical beats and energy
- **Genre Detection** - Automatic music genre and mood analysis

### 🚀 GPU Acceleration
- **CUDA Support** - NVIDIA GPU acceleration for video processing
- **Apple Silicon MPS** - Native Apple M1/M2 GPU acceleration
- **Automatic Fallback** - Seamless CPU processing when GPU unavailable
- **Batch Processing** - Process multiple music tracks with all videos efficiently

### 🎬 Advanced Video Processing
- **LLM Video Analysis** - GPT-4 Vision for comprehensive scene understanding
- **Smart Content Detection** - Identifies landscapes, action, people, objects
- **Quality Assessment** - Analyzes composition, lighting, and visual appeal
- **Mixed Content Support** - Works with drone footage, iPhone videos, and more
- **Development Mode** - Fast iteration with downsampled videos (360p)

### 🎯 Core Functionality
- **Batch Processing** - One video per music track automatically
- **Intelligent Caching** - Avoids reprocessing with smart cache management
- **4K Support** - Maintains original video quality with GPU-optimized processing
- **Flexible Input** - Supports various video and audio formats

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **ffmpeg** (for video processing)
- **GPU Drivers** (optional, for acceleration)
  - NVIDIA: CUDA 11.0+ and cuDNN
  - Apple Silicon: macOS 12.0+ (automatic)
- **OpenAI API Key** (required for LLM video analysis)

### Installation

```bash
git clone https://github.com/umang94/Drodeo.git
cd Drodeo
pip install -r requirements.txt
```

### Configuration
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your_key_here
```

### Basic Usage

**1. Add Your Content:**
```bash
# Add your music files
cp your_music.mp3 music_input/
cp your_music.m4a music_input/

# Add your video files
cp your_videos.mp4 input/
```

**2. Run Batch Processing (Recommended):**
```bash
# Process all music with all videos
python batch_video_generator.py

# Fast testing mode (recommended for development)
python batch_video_generator.py --fast-test

# Use development videos for faster processing
python batch_video_generator.py --use-dev-videos

# Combine flags for fastest testing
python batch_video_generator.py --fast-test --use-dev-videos
```

**3. Alternative: Process Specific Files:**
```bash
# Process specific music and videos
python main.py --music music_input/song.mp3 --videos input/video1.mp4 input/video2.mp4

# Use development mode for faster iteration
python main.py --use-dev-videos
```

## 📁 Project Structure

```
Drodeo/
├── batch_video_generator.py         # 🎵 Main batch processor
├── main.py                          # CLI entry point
├── setup.py                         # Package installation
├── requirements.txt                 # Dependencies
├── src/
│   ├── core/                        # Core processing
│   │   ├── llm_video_analyzer.py    # 🤖 GPT-4 Vision analysis
│   │   ├── music_analyzer.py        # 🎵 Music analysis & creative direction
│   │   ├── video_processor.py       # Video processing with GPU support
│   │   ├── ai_analyzer.py           # Legacy AI analysis
│   │   └── clip_selector.py         # Clip selection algorithms
│   ├── audio/                       # 🎵 Audio Analysis
│   │   └── audio_analyzer.py        # Beat detection and energy analysis
│   ├── editing/                     # Video editing
│   │   └── video_editor.py          # Video editing and composition
│   ├── utils/                       # Utilities
│   │   ├── video_preprocessor.py    # 🚀 Development video downsampling
│   │   ├── cache_manager.py         # Intelligent caching
│   │   ├── progress_tracker.py      # Progress monitoring
│   │   └── config.py                # Configuration management
│   └── tests/                       # Test modules
├── music_input/                     # 🎵 Your music files
├── input/                           # 🎬 Your video files (full quality)
├── input_dev/                       # 🎬 Downsampled videos (360p, auto-generated)
├── output/                          # 📹 Generated videos
└── cache/                           # Processing cache
```

## 🚀 GPU Acceleration

### Supported Platforms
- **NVIDIA GPUs** - CUDA 11.0+ with cuDNN
- **Apple Silicon** - M1/M2 with Metal Performance Shaders (MPS)
- **Automatic Detection** - Seamless fallback to CPU processing

### Performance Benefits
- **2-5x faster** video processing on supported GPUs
- **Batch processing** for optimal GPU memory utilization
- **Parallel analysis** for large video files
- **Development mode** with 35-70x smaller file sizes for fast iteration

### GPU Status Check
```bash
# Check GPU capabilities
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, MPS: {torch.backends.mps.is_available()}')"
```

## 🎬 Development Mode

For faster development and testing:

```bash
# Create downsampled development videos (360p)
python src/utils/video_preprocessor.py

# Use development videos for processing
python batch_video_generator.py --use-dev-videos

# Benefits: 35-70x smaller files, much faster processing
```

## 🔧 Advanced Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_api_key_here
MAX_CLIPS_PER_VIDEO=10
DEFAULT_VIDEO_DURATION=180
ENABLE_GPU_ACCELERATION=true
USE_DEV_VIDEOS=true
ENABLE_CACHE=true
```

### Command Line Options
```bash
# Disable caching (force reprocessing)
python batch_video_generator.py --no-cache

# Clear cache and test
python main.py --clear-cache

# Use specific output directory
python batch_video_generator.py --output-dir custom_output/

# Process with specific music and videos
python main.py --music song.mp3 --videos video1.mp4 video2.mp4
```

## 🧪 Testing & Validation

```bash
# Test system integration
python src/tests/test_system.py

# Test audio analysis
python src/tests/test_audio_debug.py

# Clear cache and test with fresh processing
python main.py --clear-cache
python batch_video_generator.py --no-cache --use-dev-videos
```

## 📊 Performance Metrics

### Processing Speed
- **Development Mode**: 35-70x faster with 360p videos
- **GPU Acceleration**: 2-5x faster video processing
- **Caching**: Avoids reprocessing analyzed content
- **Batch Processing**: Efficient handling of multiple music tracks

### Video Quality
- **4K Resolution**: Maintained in final output
- **Audio Quality**: Original music quality preserved
- **Compression**: Optimized H.264 encoding

## 🔍 Troubleshooting

**Common Issues:**
1. **"No music files found"** - Add music files to `music_input/` directory
2. **"No video files found"** - Add videos to `input/` directory
3. **"OpenAI API key required"** - Add `OPENAI_API_KEY` to `.env` file
4. **"ffmpeg not found"** - Install ffmpeg: `brew install ffmpeg` (macOS)

**GPU Issues:**
1. **"GPU not detected"** - Install CUDA drivers or update macOS
2. **"Out of GPU memory"** - Use development mode or reduce batch size

**Audio Issues:**
1. **"No beats detected"** - Music may be ambient/beatless, system will use fallback
2. **"Audio analysis failed"** - Check librosa installation

## 🛣️ Roadmap

### Current Version (v3.0.0) ✅
- [x] Music-driven video generation
- [x] LLM-powered video analysis with GPT-4 Vision
- [x] User input workflow (music_input/ and input/ folders)
- [x] Development mode with video downsampling
- [x] Batch processing (one video per music track)
- [x] GPU acceleration (CUDA + Apple Silicon MPS)
- [x] Advanced audio analysis and beat detection

### Future Enhancements (v4.0.0)
- [ ] Real-time preview during processing
- [ ] Web interface for easier content management
- [ ] Advanced music genre classification
- [ ] Custom transition effects library
- [ ] Multi-track audio mixing
- [ ] Cloud processing support
