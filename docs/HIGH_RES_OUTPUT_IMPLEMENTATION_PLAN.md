# High-Resolution Output Implementation Plan

**Version:** 1.0.0
**Last Updated:** September 21, 2025
**Status:** Planning

## Overview
This document outlines the implementation plan for adding high-resolution output capability to Drodeo via a new `--high-res` command-line flag. The feature will enable 4K UHD output while maintaining the current efficient low-resolution analysis workflow.

## Problem Statement
The current system outputs videos at 1080p resolution using downsampled development videos from `input_dev/`. Users need the ability to produce higher quality outputs (up to 4K) using original source files while preserving the cost-effective Gemini analysis on low-resolution versions.

## Solution Architecture
### Modified Workflow
1. **Input Setup**: Always create low-res videos in `input_dev/` for analysis
2. **Analysis**: Gemini analyzes low-res videos (cost-effective)
3. **Editing**: Use original high-res files when `--high-res` flag is enabled
4. **Output**: Render at 4K resolution for high-res mode, 1080p for normal mode

### Key Components
- **CLI Flag**: `--high-res` to enable high-resolution output
- **Filename Mapping**: Convert `_dev` suffixes to original filenames
- **Resolution Presets**: Configurable output resolutions (1080p, 1440p, 4K)
- **Backward Compatibility**: Normal operation unchanged

## Technical Specifications
### Resolution Presets
```python
RESOLUTION_PRESETS = {
    "standard": (1920, 1080),  # Current default
    "high": (2560, 1440),      # 1440p QHD
    "ultra": (3840, 2160),     # 4K UHD
}
```

### Filename Mapping Function
```python
def map_to_high_res_filename(low_res_name: str) -> str:
    """Convert low-res filename (_dev) to original high-res filename"""
    if low_res_name.endswith('_dev.mp4'):
        return low_res_name.replace('_dev.mp4', '.mp4')
    if low_res_name.endswith('_dev.mov'):
        return low_res_name.replace('_dev.mov', '.mov')
    return low_res_name
```

## Implementation Phases
### Phase 1: CLI and Configuration
- [ ] Add `--high-res` flag to `main.py` argument parser
- [ ] Add resolution presets to `src/utils/config.py`
- [ ] Update pipeline to accept high-res parameter

### Phase 2: Filename Mapping and Source Selection
- [ ] Implement filename mapping function in `src/core/pipeline.py`
- [ ] Modify `_get_development_videos()` to support original file access
- [ ] Update video path resolution logic for high-res mode

### Phase 3: Video Editor Integration
- [ ] Modify `VideoEditor` to support configurable resolution
- [ ] Update rendering to use appropriate source files
- [ ] Ensure proper scaling from original resolution to target output

### Phase 4: Testing and Validation
- [ ] Test high-res mode with various input resolutions
- [ ] Verify filename mapping accuracy
- [ ] Ensure backward compatibility
- [ ] Performance testing for 4K rendering

## Files to Modify
1. `main.py` - Add CLI flag
2. `src/utils/config.py` - Add resolution presets
3. `src/core/pipeline.py` - Implement high-res logic and filename mapping
4. `src/editing/video_editor.py` - Support configurable resolution output

## Dependencies
- Original high-resolution source files must be available in `input/` directory
- Low-resolution versions will still be required for Gemini analysis
- Adequate system resources for 4K video processing

## Risk Assessment
- **Performance Impact**: 4K rendering will require more resources
- **Input Quality**: Original files must support the target output resolution
- **Memory Usage**: Higher resolutions may increase memory requirements during editing

## Success Metrics
- High-resolution mode produces 4K output from original source files
- Normal mode continues to output 1080p unchanged
- Filename mapping accurately converts `_dev` names to original names
- No regression in processing time or reliability

## Documentation Updates
- Update `SYSTEM_ARCHITECTURE.md` with high-res workflow
- Update `README.md` with `--high-res` flag documentation
- Add entry to `CHANGELOG.md` for the new feature

## Implementation Status
- [x] Planning Phase Complete
- [x] Feature plan document created (docs/HIGH_RES_OUTPUT_IMPLEMENTATION_PLAN.md)
- [x] Phase 1: CLI and Configuration
  - [x] Added `--high-res` flag to `main.py` argument parser
  - [x] Added resolution presets to `src/utils/config.py`
  - [x] Updated pipeline to accept high-res parameter
- [x] Phase 2: Filename Mapping
  - [x] Implemented `map_to_high_res_filename()` function in `src/core/pipeline.py`
  - [x] Added filename mapping logic for high-res mode in video path resolution
  - [x] Supports all video extensions (mp4, mov, avi, mkv) with case sensitivity
- [x] Phase 3: Video Editor Integration
  - [x] Modified `VideoEditor` to accept `resolution_preset` parameter
  - [x] Updated `_render_video()` to apply target resolution based on preset
  - [x] Added automatic resizing from original to target resolution
  - [x] Integrated resolution preset selection in pipeline based on high-res flag
- [x] Phase 4: Testing and Validation
  - [x] Tested high-res mode with 3 videos - successful source file selection and filename mapping
  - [x] Tested normal mode with 3 videos - successful operation (backward compatibility confirmed)
  - [x] Verified resolution scaling: 640x360 → 1920x1080 (normal) and original 4K → 3840x2160 (high-res)
  - [x] Confirmed proper video rendering with appropriate target resolutions
- [ ] Documentation Updated

---

*This document will be updated throughout implementation to track progress and record decisions.*
