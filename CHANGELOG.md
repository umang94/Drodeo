# Changelog

All notable changes to the Drodeo video generation system will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Critical Audio Bug**: Fixed issue where generated videos were missing audio tracks in the end-to-end pipeline
  - Root cause: MoviePy's complex audio processing pipeline was failing with FFmpeg subprocess errors when using `volumex()`, `CompositeAudioClip`, and fade effects
  - Solution: Implemented simplified audio overlay approach in `VideoEditor._add_music_overlay()` that uses raw audio files directly without complex processing
  - Fixed secondary issue in `GeminiSelfTranslator._create_self_translation_prompt()` where `None` audio duration values caused string formatting errors
  - All generated videos now successfully include audio tracks with proper AAC encoding at 44.1kHz stereo
  - Files modified: `src/editing/video_editor.py`, `src/core/gemini_self_translator.py`

### Technical Details
- Removed complex audio processing that was causing `'NoneType' object has no attribute 'stdout'` FFmpeg errors
- Simplified audio overlay to use `video.without_audio().set_audio(audio)` approach
- Added proper None handling for audio duration in self-translation prompts
- Maintained audio quality while eliminating processing failures

## [Previous Versions]
- Initial implementation of two-step Gemini pipeline
- Multimodal video analysis and generation
- Beat-synchronized video editing
