# Drone Video Generator MVP

A command-line tool that processes drone videos, uses AI for intelligent clip detection, and outputs multiple themed videos with royalty-free music.

## Setup

1. **Install system dependencies:**
   ```bash
   brew install ffmpeg
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Usage

```bash
# Basic usage
python3 main.py uploads/*.mp4

# Test without processing
python3 main.py --dry-run uploads/*.mp4

# Force reprocessing (ignore cache)
python3 main.py --no-cache uploads/*.mp4

# Clear all cached results
python3 main.py --clear-cache uploads/*.mp4

# Select specific themes
python3 main.py --themes happy exciting uploads/*.mp4
```

## Current Status

**✅ Completed:**
- Environment setup and validation
- Real-time video processing with OpenCV
- Multi-video batch processing
- Smart caching system (25s → 1s processing time!)
- 4K drone video support
- Motion analysis and scene detection
- Quality scoring and clip extraction

**🚧 In Progress:**
- AI-powered clip enhancement with OpenAI GPT-4 Vision
- Theme-based video generation
- Music integration and synchronization

## Project Structure

```
├── main.py                 # Command-line entry point
├── video_processor.py      # Core video analysis
├── ai_analyzer.py          # OpenAI integration
├── video_editor.py         # Video editing and music overlay
├── music_downloader.py     # Music API integration
├── config.py               # Configuration and themes
├── requirements.txt        # Python dependencies
├── .env                    # API keys (create from .env.example)
├── music/                  # Downloaded music files
├── output/                 # Generated videos
├── uploads/                # Temporary uploads
└── tests/                  # Test files
```

## Features

- ✅ **Real Video Analysis** - Motion detection, scene changes, quality scoring
- ✅ **Multi-video Processing** - Process multiple drone videos simultaneously
- ✅ **Smart Caching** - Instant reprocessing with file-based cache system
- ✅ **4K Support** - Handles large drone video files (600MB-1GB+)
- ✅ **Progress Tracking** - Detailed feedback and progress bars
- 🚧 **AI Integration** - OpenAI GPT-4 Vision for intelligent clip detection (coming next)
- 🚧 **5 Themed Outputs** - Happy, Exciting, Peaceful, Adventure, Cinematic (coming next)
- 🚧 **Music Integration** - Automatic royalty-free music downloading (coming next)
