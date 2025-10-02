# Drodeo - Video Content Generation System

A system for generating videos using Gemini's multimodal analysis with optional music overlay. Supports both standard 1080p and high-resolution 4K output modes.

## Overview

Drodeo processes video content through a two-step Gemini pipeline to create videos with optional music synchronization. The system intelligently handles large video collections by automatically batching and concatenating videos when more than 10 videos are provided.

**Key Features:**
- Two-step Gemini pipeline for intelligent video analysis and editing
- High-resolution 4K output support via `--high-res` flag
- Automatic video batching for large collections
- Smart caching of development videos for cost-effective processing
- Audio-free mode for silent video generation

## Quick Start

### Prerequisites
- Python 3.8+
- Gemini API key
- FFmpeg installed

### Installation
```bash
git clone https://github.com/umang94/Drodeo.git
cd Drodeo

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Usage
```bash
# Primary interface with built-in validation (processes 30 videos by default)
python main.py

# Process videos from a custom directory
python main.py --input-dir my_videos

# Process videos from an absolute path
python main.py --input-dir /path/to/videos

# Force recreation of development videos
python main.py --input-dir my_videos --force-setup

# Limit number of videos processed (default: 30)
python main.py --max-videos 50

# Enable high-resolution 4K output mode
python main.py --high-res

# Create development videos (moved to scripts/)
python scripts/create_dev_videos.py
```

## Input Requirements

- **Music (Optional)**: Audio files (MP3, M4A, WAV) in `music/` directory for background music overlay
- **Videos**: Video files (MP4, MOV) in `input/` directory or any custom directory specified via `--input-dir`
- **Development**: Low-resolution versions are automatically created in `input_dev/{folder_name}/` for custom directories, maintaining isolated caching

## Configuration

Set up your `.env` file (if it doesn't already exist):
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

**Note**: If you already have a `.env` file configured with your API keys, do not overwrite it. The system will use your existing configuration.

## Project Structure

```
src/
├── core/                    # Core analysis components
│   ├── gemini_multimodal_analyzer.py
│   ├── gemini_self_translator.py
│   └── video_mapping.py     # Timestamp translation system
├── editing/                 # Video editing
│   └── video_editor.py
└── utils/                   # Configuration and logging
    ├── config.py
    └── llm_logger.py
```

## Documentation

For technical information and development guidelines, see:

- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - System documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Recent changes

## Development

- Use `input_dev/` videos for development
- Run `python main.py` for standard testing (processes 30 videos by default)

## License

MIT License - see LICENSE file for details.
