# Drodeo System Architecture

**Version:** 4.2.0  
**Last Updated:** September 7, 2025  
**Status:** Production Ready

## System Overview

Drodeo is a video content generation system that uses a two-step Gemini pipeline to analyze video content with optional music overlay for video creation.

### System Design Diagram
```
┌─────────────────────────────────────────────────┐
│                   INPUT LAYER                   │
│  music/ (audio)      input/ (videos)            │
│  input_dev/ (dev videos)                        │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                ANALYSIS LAYER                   │
│  Gemini Multimodal Analysis → Self-Translation  │
│  (Natural Language → Structured JSON)           │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                EDITING LAYER                    │
│  Video Editor: JSON → Video Segments            │
│  Simplified Audio Processing                    │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                OUTPUT LAYER                     │
│  output/ (generated videos)                     │
└─────────────────────────────────────────────────┘
```

### Core Components
- **Two-Step Gemini Pipeline**: Multimodal analysis followed by self-translation
- **Video Processing**: MoviePy-based video editing and rendering
- **Validation System**: Environment and directory validation
- **Batch Processing**: Support for multiple music tracks

## Architecture

### Input Layer
- **Music Input**: Audio files in `music/` directory (MP3, M4A, WAV formats)
- **Video Input**: Video files in `input/` directory or any custom directory specified via the `--input-dir` command-line option (MP4, MOV formats)  
- **Development Videos**: Downsampled versions in `input_dev/` for default input, or `input_dev/{source_folder_name}/` for custom directories

### Analysis Layer
#### Gemini Multimodal Analyzer (`src/core/gemini_multimodal_analyzer.py`)
- Analyzes video content and scene characteristics (video-only analysis)
- Generates UDIO prompts for music generation based on video content
- Provides natural language analysis output focused on visual elements

#### Gemini Self-Translator (`src/core/gemini_self_translator.py`)
- Converts natural language analysis into structured JSON
- Provides MoviePy-compatible editing instructions
- Includes timestamp validation and error handling

### Editing Layer
#### Video Editor (`src/editing/video_editor.py`)
- Processes JSON instructions from Gemini analysis
- Loads and validates video clips with timestamp checking
- Implements basic music overlay functionality (optional)
- Handles video concatenation and rendering
- Gracefully handles music loading failures

### Output Layer
- Generated videos saved to `output/` directory
- Filename format: `{music_name}_twostep_{duration}s.mp4`
- Standard H.264 video encoding with AAC audio

## Component Details

### Main Interface (`main.py`)
- Primary entry point with built-in validation
- Command-line arguments for testing modes
- Orchestrates the complete two-step pipeline
- Provides user feedback and error handling

### Validation Utilities (`src/utils/validation.py`)
- `validate_environment()`: Checks .env configuration and dependencies
- `validate_directories()`: Ensures required directory structure exists
- `setup_development_videos()`: Manages development video caching

### Pipeline Module (`src/core/pipeline.py`)
- `run_two_step_pipeline()`: Integrated pipeline execution
- Reusable functions for analysis and translation steps
- Error handling and progress reporting

### Batch Processing (`batch_video_generator.py`)
- Processes multiple music tracks sequentially
- Maintains session logging and reporting
- Supports both development and production video modes

## Data Flow

1. **Input Scanning**: Video files are scanned from input directories, music files are optionally discovered
2. **Multimodal Analysis**: Gemini performs video-only analysis and generates UDIO prompts
3. **Self-Translation**: Gemini converts analysis into structured JSON format
4. **Video Editing**: JSON instructions are processed to create video segments
5. **Music Overlay**: Optional background music is added using basic overlay functionality
6. **Rendering**: Final video is rendered with or without audio
7. **Output**: Completed video is saved to output directory

## Configuration

### Environment Variables (`.env`)
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Command-Line Options
- `--fast-test`: Enable fast testing mode with limited videos
- `--force-setup`: Force recreation of development videos
- `--input-dir PATH`: Specify a custom directory containing video files for processing. Development videos are cached in `input_dev/{dirname}/`

### Runtime Configuration (`src/utils/config.py`)
- Video processing settings (resolution, frame rates, durations)
- Gemini API configuration (timeouts, retries, model selection)
- Development settings (caching, video quality)

## Development Guidelines

### Code Structure
```
src/
├── core/           # Core analysis components
│   ├── gemini_multimodal_analyzer.py
│   └── gemini_self_translator.py
├── editing/        # Video editing components
│   └── video_editor.py
└── utils/          # Shared utilities
    ├── config.py
    └── llm_logger.py
```

### Development Practices
- Use `input_dev/` videos for all development and testing
- Run `python main.py --fast-test` for quick validation
- Use `python main.py --input-dir my_videos` to test with videos from custom directories
- Test individual components before full pipeline execution
- Maintain documentation consistency with code changes

### Testing
- Environment validation: `python -c "from src.utils.validation import validate_environment; validate_environment()"`
- Component testing: Import and test individual modules
- Integration testing: Use `main.py --fast-test`
- Batch testing: Use `batch_video_generator.py` for multiple tracks

## Performance Considerations

### Development Mode
- Use `input_dev/` videos (360p) for faster processing
- Enable `--fast-test` mode to limit video count
- Utilize caching for repeated analysis

### Production Mode
- Use full-resolution videos from `input/` directory
- Monitor system resources during batch processing
- Consider API rate limits for Gemini analysis

## Error Handling

- Comprehensive validation at each pipeline stage
- Graceful degradation for missing components
- Detailed logging for troubleshooting
- Clear user feedback for common issues

## Maintenance

- Keep documentation updated with architectural changes
- Maintain consistency between code and documentation
- Review and update configuration settings as needed
- Monitor system performance and resource usage

---

## Documentation Guidelines

### Writing Standards
- **Technical Tone Only**: Use factual, objective language without emotional adjectives
- **No Hyperbolic Claims**: Avoid words like "revolutionary", "perfect", "superior", "best"
- **No Emojis or Decorative Formatting**: Use standard technical documentation formatting
- **Factual Descriptions**: Describe functionality without subjective quality claims
- **Clear and Concise**: Focus on essential information without unnecessary elaboration

### Content Standards
- Document actual implemented functionality, not aspirational features
- Avoid marketing language and focus on technical specifications
- Maintain consistency with current codebase implementation
- Update documentation when architecture changes

*This document provides technical documentation for the Drodeo system architecture. Maintain factual accuracy and avoid subjective language when updating.*
