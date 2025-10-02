import os

# Resolution presets for output quality
RESOLUTION_PRESETS = {
    "standard": (1920, 1080),  # 1080p Full HD (current default)
    "high": (2560, 1440),      # 1440p QHD
    "ultra": (3840, 2160),     # 4K UHD
}

# Video processing settings
VIDEO_CONFIG = {
    "output_resolution_preset": "standard",  # Default to standard resolution
    "output_resolution": (1920, 1080),       # Backward compatibility
    "frame_sample_rate": 30,  # analyze every 30th frame
    "min_clip_duration": 2.0,  # minimum clip length in seconds
    "max_clip_duration": 15.0,  # maximum clip length in seconds
    "keyframes_per_video": 8,  # number of keyframes to analyze with AI
    "target_clips_per_video": 10,  # target number of clips per video
}

# API settings
API_CONFIG = {
    "openai_model": "gpt-4-vision-preview",
    "max_tokens": 300,
    "temperature": 0.3,
}

# File paths
PATHS = {
    "music_input_dir": "music_input",
    "video_input_dir": "input",
    "video_input_dev_dir": "input_dev", 
    "output_dir": "output",
    "cache_dir": "cache",
    "temp_dir": "temp",
}

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

def get_resolution_from_preset(preset_name: str) -> tuple:
    """Get resolution tuple from preset name."""
    return RESOLUTION_PRESETS.get(preset_name, RESOLUTION_PRESETS["standard"])

# Audio analysis settings
AUDIO_CONFIG = {
    "sample_rate": 22050,
    "hop_length": 512,
    "frame_length": 2048,
    "energy_window_size": 1.0,  # seconds
    "beat_detection_threshold": 0.3,
}

# Gemini API Video Analysis settings
GEMINI_VIDEO_CONFIG = {
    # Gemini API Configuration
    "api_key": os.getenv('GEMINI_API_KEY'),
    "model_name": 'gemini-2.5-flash',  # Latest model with video support
    
    # Video Processing Configuration
    "max_inline_video_size_mb": 20,    # Direct upload limit
    "use_file_api_for_large": True,    # Use File API for >20MB videos
    "custom_frame_rate": 1,            # 1 FPS sampling rate
    
    # Music-Aware Analysis Configuration
    "enable_music_sync_analysis": True,
    "enable_beat_alignment": True,
    "enable_energy_matching": True,
    "enable_visual_rhythm_analysis": True,
    
    # Performance Configuration
    "api_timeout_seconds": 120,        # Faster than Google Video Intelligence
    "cache_responses": True,
    "max_retries": 3,
    
    # Cost Management
    "monthly_budget_limit": 50.0,      # USD
    "cost_alert_threshold": 0.8,
}

# Development settings
DEV_CONFIG = {
    "downsample_resolution": (640, 360),  # 360p for fast development
    "use_dev_videos": True,  # Use downsampled videos by default
    "enable_cache": True,  # Enable caching by default
}

if __name__ == "__main__":
    # Test configuration loading
    ensure_directories()
    print("Configuration loaded successfully!")
    print(f"Available paths: {list(PATHS.keys())}")
