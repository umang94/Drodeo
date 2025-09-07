# Drodeo - AI-Powered Music Video Generator

An intelligent music-driven video generation system that creates beat-synchronized videos using Gemini's multimodal analysis.

## Overview

Drodeo uses a two-step Gemini pipeline to analyze audio and video content, then generates synchronized music videos through intelligent clip selection and editing.

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
# Create development videos (recommended for testing)
python create_dev_videos.py

# Generate videos
python batch_video_generator.py

# Generate music prompts from video content
python generate_music_prompt.py input_dev/*.mp4

# Test the system
python test_two_step_pipeline.py
```

## Input Requirements

- **Music**: Place audio files (MP3, M4A, WAV) in `music/` directory
- **Videos**: Place video files (MP4, MOV) in `input/` directory
- **Development**: Use `input_dev/` for faster testing (created by `create_dev_videos.py`)

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

For detailed technical information, architecture details, and development guidelines, see:

- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Complete system documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Recent changes and bug fixes

## Development

- Use `input_dev/` videos for development (35-70x faster processing)
- Run `python test_two_step_pipeline.py` to test changes
- See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) for detailed development guidelines

## License

MIT License - see LICENSE file for details.
