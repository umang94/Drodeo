# Drodeo - Video Content Generation System

A system for generating videos using Gemini's multimodal analysis with optional music overlay.

## Overview

Drodeo processes video content through a two-step Gemini pipeline to create videos with optional music synchronization.

## Quick Start

### Prerequisites
- Python 3.8+
- Gemini API key
- FFmpeg installed

### Installation
```bash
git clone https://github.com/umang94/Drodeo.git
cd Drodeo
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Usage
```bash
# Primary interface with built-in validation
python main.py

# Process videos from a custom directory
python main.py --input-dir my_videos

# Process videos from an absolute path
python main.py --input-dir /path/to/videos

# Fast testing with custom directory
python main.py --input-dir my_videos --fast-test

# Force recreation of development videos
python main.py --input-dir my_videos --force-setup

# Batch processing for multiple tracks
python batch_video_generator.py

# Generate music prompts from video content
python generate_music_prompt.py input_dev/*.mp4

# Create development videos (moved to scripts/)
python scripts/create_dev_videos.py
```

## Input Requirements

- **Music (Optional)**: Audio files (MP3, M4A, WAV) in `music/` directory for background music overlay
- **Videos**: Video files (MP4, MOV) in `input/` directory or any custom directory specified via `--input-dir`
- **Development**: Low-resolution versions are automatically created in `input_dev/{folder_name}/` for custom directories, maintaining isolated caching

## Configuration

Set up your `.env` file:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## Project Structure

```
src/
├── core/                    # Core analysis components
│   ├── gemini_multimodal_analyzer.py
│   └── gemini_self_translator.py
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
- Run `python main.py --fast-test` for quick testing
- Use `python batch_video_generator.py` for batch processing

## License

MIT License - see LICENSE file for details.
