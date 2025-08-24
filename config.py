from dataclasses import dataclass
from typing import Dict, List
from enum import Enum
import os

class VideoTheme(Enum):
    HAPPY = "happy"
    EXCITING = "exciting"
    PEACEFUL = "peaceful"
    ADVENTURE = "adventure"
    CINEMATIC = "cinematic"

@dataclass
class ThemeConfig:
    name: str
    music_keywords: List[str]
    target_duration: int = 180  # 3 minutes
    pacing: str = "medium"  # "slow", "medium", "fast"
    description: str = ""

# Theme configurations for music search and video pacing
THEME_CONFIGS = {
    VideoTheme.HAPPY: ThemeConfig(
        name="Happy",
        music_keywords=["upbeat", "cheerful", "positive", "joyful", "bright"],
        pacing="medium",
        description="Upbeat and cheerful with positive energy"
    ),
    VideoTheme.EXCITING: ThemeConfig(
        name="Exciting",
        music_keywords=["energetic", "dynamic", "action", "intense", "powerful"],
        pacing="fast",
        description="High energy and dynamic with intense moments"
    ),
    VideoTheme.PEACEFUL: ThemeConfig(
        name="Peaceful",
        music_keywords=["calm", "relaxing", "ambient", "peaceful", "serene"],
        pacing="slow",
        description="Calm and relaxing with serene atmosphere"
    ),
    VideoTheme.ADVENTURE: ThemeConfig(
        name="Adventure",
        music_keywords=["epic", "adventure", "cinematic", "inspiring", "heroic"],
        pacing="medium",
        description="Epic and inspiring with adventurous spirit"
    ),
    VideoTheme.CINEMATIC: ThemeConfig(
        name="Cinematic",
        music_keywords=["orchestral", "dramatic", "cinematic", "emotional", "epic"],
        pacing="medium",
        description="Dramatic and emotional with cinematic quality"
    )
}

# Video processing settings
VIDEO_CONFIG = {
    "output_resolution": (1920, 1080),
    "frame_sample_rate": 30,  # analyze every 30th frame
    "min_clip_duration": 2.0,  # minimum clip length in seconds
    "max_clip_duration": 15.0,  # maximum clip length in seconds
    "keyframes_per_video": 8,  # number of keyframes to analyze with AI
    "target_clips_per_theme": 10,  # target number of clips per themed video
}

# API settings
API_CONFIG = {
    "openai_model": "gpt-4-vision-preview",
    "max_tokens": 300,
    "temperature": 0.3,
}

# File paths
PATHS = {
    "music_dir": "music",
    "output_dir": "output",
    "uploads_dir": "uploads",
    "temp_dir": "temp",
}

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)
    
    # Create temp directory
    os.makedirs("temp", exist_ok=True)

# Music search settings
MUSIC_CONFIG = {
    "youtube_audio_library_playlists": {
        "happy": "PLrAl6rYgs4IvGFUh8N60K4AyNUBUGf_CE",
        "exciting": "PLrAl6rYgs4IuO4o7tKJeP0NKPP6dAYBa8", 
        "peaceful": "PLrAl6rYgs4IsB0909ZlK9f4wNRVaWFhpF",
        "adventure": "PLrAl6rYgs4IvGFUh8N60K4AyNUBUGf_CE",
        "cinematic": "PLrAl6rYgs4IuO4o7tKJeP0NKPP6dAYBa8"
    },
    "fallback_search_terms": {
        "happy": "royalty free upbeat music",
        "exciting": "royalty free energetic music", 
        "peaceful": "royalty free calm ambient music",
        "adventure": "royalty free epic adventure music",
        "cinematic": "royalty free cinematic orchestral music"
    }
}

def get_theme_config(theme: VideoTheme) -> ThemeConfig:
    """Get configuration for a specific theme."""
    return THEME_CONFIGS[theme]

def get_all_themes() -> List[VideoTheme]:
    """Get list of all available themes."""
    return list(VideoTheme)

if __name__ == "__main__":
    # Test configuration loading
    ensure_directories()
    print("Configuration loaded successfully!")
    print(f"Available themes: {[theme.value for theme in get_all_themes()]}")
    
    for theme in get_all_themes():
        config = get_theme_config(theme)
        print(f"{config.name}: {config.description}")
