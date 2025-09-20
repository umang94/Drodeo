# Changelog

All notable changes to the Drodeo video generation system will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Blank-Frame-Free Architecture**: Implemented seamless video concatenation without blank frames
  - Created `_concatenate_video_batch_no_blanks()` function for direct video joining
  - Updated `create_mapping_from_concatenation()` to handle zero blank frame duration
  - Enhanced timestamp translation to work with accurate video durations
  - Modified multimodal analyzer prompt for single concatenated video analysis

- **Timestamp Mapping System**: Implemented comprehensive timestamp translation between concatenated and original videos
  - Created `src/core/video_mapping.py` with `VideoBatchMapping` class and utility functions
  - Added `translate_gemini_timestamps()` to convert concatenated video timestamps to original video references
  - Implemented `extract_timestamps_from_reasoning()` for parsing Gemini response timestamps
  - Enhanced self-translation prompt with explicit timestamp interpretation instructions

- **Large-Scale Batch Processing**: Enhanced pipeline to handle 30-50+ videos efficiently
  - Added `--max-videos` parameter to control processing limits
  - Improved video discovery with efficient `os.walk()` and early termination
  - Enhanced error handling for API quota limits with graceful fallback
  - Added robust video duration validation and clamping

- **Batch Video Processing**: Implemented support for processing more than 10 input videos
  - Added intelligent video batching with concatenation (now blank-frame-free)
  - Created `_create_video_batches()`, `_concatenate_video_batch_no_blanks()`, and `_process_video_batches()` functions in `src/core/pipeline.py`
  - Removed `create_blank_clip()` method from `src/editing/video_editor.py` as it's no longer needed
  - Implemented automatic temporary file cleanup with `_cleanup_temporary_files()`
  - Created comprehensive implementation plan in `docs/BATCH_VIDEO_PROCESSING_IMPLEMENTATION_PLAN.md`

- **Audio-Free Pipeline**: Implemented complete audio-free operation while preserving music overlay capability
  - Modified `src/core/gemini_multimodal_analyzer.py` to remove audio processing from Gemini analysis
  - Enhanced multimodal prompt with UDIO prompt generation and longer video duration preference
  - Updated `src/core/pipeline.py` to enable automatic music file discovery
  - Simplified music overlay in `src/editing/video_editor.py` to basic functionality
  - Created comprehensive implementation plan in `docs/AUDIO_FREE_PIPELINE_IMPLEMENTATION_PLAN.md`

- **Simplified Main Interface**: Created `main.py` with built-in validation and smart caching
  - Environment validation (API keys, dependencies)
  - Directory structure validation
  - Smart video caching for development videos
  - Command-line arguments for fast-test and force-setup modes
  - Clear user feedback and error handling

- **Robust Validation Utilities**: Created `src/utils/validation.py`
  - `validate_environment()`: Checks .env, API keys, dependencies
  - `validate_directories()`: Ensures required directories exist
  - `setup_development_videos()`: Smart caching for low-res videos

- **Reusable Pipeline Module**: Created `src/core/pipeline.py`
  - `run_two_step_pipeline()`: Integrated two-step Gemini pipeline
  - Replaces functionality from `test_two_step_pipeline.py`

### Changed
- **Audio-Free Architecture**: Transformed Drodeo to remove audio processing from Gemini analysis
  - Updated `SYSTEM_ARCHITECTURE.md` to version 4.2.0 with audio-free documentation
  - Modified `README.md` to reflect video-only analysis with optional music overlay
  - Moved `create_dev_videos.py` to `scripts/` directory for better organization
  - Removed optional audio-related API keys from configuration documentation

- **Simplified Video Editor**: Refactored `src/editing/video_editor.py`
  - Reduced from ~1200 to ~250 lines (79% reduction)
  - Removed legacy methods: `create_from_multimodal_analysis()`, `create_music_driven_video()`, `_create_sync_plan_video()`, `_create_traditional_video()`
  - Eliminated complex clip extension logic
  - Cleaned up unused imports and dependencies
  - Maintained full functionality for two-step pipeline

- **File Cleanup**: Removed redundant `test_two_step_pipeline.py`
  - Functionality integrated into `src/core/pipeline.py`
  - Preserved `batch_video_generator.py` for unique batch processing features

### Fixed
- **Timestamp Interpretation Bug**: Fixed critical issue where Gemini's creative timeline timestamps were incorrectly interpreted as concatenated video positions instead of original video positions
  - Root cause: Self-translation was applying concatenated video timestamps to individual source videos, causing all clips to reference the same video with invalid timestamps
  - Solution: Enhanced self-translation prompt with explicit timestamp interpretation instructions and implemented comprehensive timestamp mapping system
  - Added timestamp validation and clamping to prevent "End time > video duration" warnings
  - Files modified: `src/core/gemini_self_translator.py`, `src/core/video_mapping.py`, `src/editing/video_editor.py`

- **Critical Audio Bug**: Fixed issue where generated videos were missing audio tracks in the end-to-end pipeline
  - Root cause: MoviePy's complex audio processing pipeline was failing with FFmpeg subprocess errors when using `volumex()`, `CompositeAudioClip`, and fade effects
  - Solution: Implemented simplified audio overlay approach in `VideoEditor._add_music_overlay()` that uses raw audio files directly without complex processing
  - Fixed secondary issue in `GeminiSelfTranslator._create_self_translation_prompt()` where `None` audio duration values caused string formatting errors
  - All generated videos now successfully include audio tracks with proper AAC encoding at 44.1kHz stereo
  - Files modified: `src/editing/video_editor.py`, `src/core/gemini_self_translator.py`

### Technical Details
- **Timestamp Mapping**: Implemented global-to-local timestamp conversion to properly interpret Gemini's creative timeline
- **Video Duration Validation**: Added robust timestamp clamping to respect individual video durations
- **API Quota Handling**: Enhanced graceful fallback for Gemini API quota limits
- Removed complex audio processing that was causing `'NoneType' object has no attribute 'stdout'` FFmpeg errors
- Simplified audio overlay to use `video.without_audio().set_audio(audio)` approach
- Added proper None handling for audio duration in self-translation prompts
- Maintained audio quality while eliminating processing failures

## [Previous Versions]
- Initial implementation of two-step Gemini pipeline
- Multimodal video analysis and generation
- Beat-synchronized video editing
