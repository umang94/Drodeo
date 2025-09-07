# Drodeo - Music Video Generation System

A system for generating music-synchronized videos using Gemini's multimodal analysis capabilities.

## Overview

Drodeo processes audio and video content through a two-step Gemini pipeline to create synchronized music videos.

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

# Fast testing with limited videos
python main.py --fast-test

# Force recreation of development videos
python main.py --force-setup

# Batch processing for multiple tracks
python batch_video_generator.py

# Generate music prompts from video content
python generate_music_prompt.py input_dev/*.mp4
```

## Input Requirements

- **Music**: Audio files (MP3, M4A, WAV) in `music/` directory
- **Videos**: Video files (MP4, MOV) in `input/` directory
- **Development**: Use `input_dev/` for testing (created by `create_dev_videos.py`)

## Configuration

Set up your `.env` file:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
FREESOUND_API_KEY=your_freesound_api_key_here  # Optional
OPENAI_API_KEY=your_openai_api_key_here        # Optional
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
