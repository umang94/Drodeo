# 🎬 Drone Video Generator MVP

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: MVP Complete](https://img.shields.io/badge/Status-MVP%20Complete-green.svg)](https://github.com/your-username/drone-video-generator)

**Transform raw drone footage into polished, themed videos with AI-powered automation.**

The Drone Video Generator MVP is an intelligent video processing system that automatically analyzes drone footage, selects the best clips, and creates themed videos with appropriate background music. Perfect for content creators, drone enthusiasts, and anyone looking to quickly turn raw footage into engaging videos.

## ✨ Features

### 🎯 **Core Functionality**
- **🤖 AI-Powered Analysis**: Uses OpenAI GPT-4 Vision to understand scene content and quality
- **📹 Smart Clip Detection**: Automatically identifies the best segments using motion analysis and quality scoring
- **🎨 Theme Generation**: Creates 5 distinct themed videos (Happy, Exciting, Peaceful, Adventure, Cinematic)
- **🎵 Music Integration**: Adds theme-appropriate background music with proper audio mixing
- **⚡ Batch Processing**: Process multiple drone videos simultaneously
- **💾 Intelligent Caching**: Avoids reprocessing with smart caching system

### 🎬 **Video Processing**
- **Motion Analysis**: Detects dynamic scenes and camera movements
- **Scene Change Detection**: Identifies natural transition points
- **Quality Assessment**: Evaluates brightness, exposure, and visual appeal
- **4K Support**: Maintains original video quality (up to 4K resolution)
- **Multiple Formats**: Supports MP4, MOV, AVI, and MKV files

### 🎵 **Music & Audio**
- **Freesound Integration**: Downloads high-quality music previews from Freesound.org
- **Creative Commons Licensed**: All music uses proper CC licensing
- **Theme Matching**: Selects music that fits each video theme perfectly
- **Audio Mixing**: Balances original drone audio with background music
- **Volume Optimization**: Ensures clear, audible output
- **Smart Caching**: Avoids re-downloading music with intelligent storage
- **Fallback System**: Uses sample music when API is unavailable
- **Preview Quality**: Uses high-quality MP3 previews (no OAuth required)

### 🛠️ **System Features**
- **Progress Tracking**: Real-time progress updates with detailed logging
- **Error Handling**: Comprehensive error recovery with helpful suggestions
- **Testing Suite**: Built-in system validation (87.5% success rate)
- **Configuration**: Flexible settings for customization

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **ffmpeg** (for video processing)
- **OpenAI API Key** (optional, for enhanced AI analysis)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/drone-video-generator.git
   cd drone-video-generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install ffmpeg:**
   ```bash
   # macOS (using Homebrew)
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Windows (using Chocolatey)
   choco install ffmpeg
   ```

4. **Set up API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys:
   # - OpenAI API key (optional, for enhanced AI analysis)
   # - Freesound API key (optional, for music downloads)
   ```

5. **Get Freesound API key (optional):**
   - Visit [https://freesound.org/apiv2/apply/](https://freesound.org/apiv2/apply/)
   - Create account and apply for API access
   - Add your API key to `.env` file

### Basic Usage

1. **Place your drone videos in the `input/` directory**

2. **Run the generator:**
   ```bash
   python main.py input/your_video.mp4
   ```

3. **Find your themed videos in the `output/` directory!**

**Note**: The system now defaults to generating only the "happy" theme for faster processing. You can specify multiple themes using the `--themes` option.

## 📖 Usage Examples

### Basic Processing
```bash
# Process a single video (defaults to happy theme)
python main.py input/DJI_0131.mp4

# Process multiple videos
python main.py input/DJI_0131.mp4 input/DJI_0141.mp4

# Process all videos in input directory
python main.py input/*.mp4
```

### Advanced Options
```bash
# Create videos for specific themes
python main.py input/*.mp4 --themes peaceful exciting

# Create 60-second videos
python main.py input/*.mp4 --duration 60

# Generate all 5 themes
python main.py input/*.mp4 --themes happy exciting peaceful adventure cinematic

# Custom output directory
python main.py input/*.mp4 --output-dir my_videos

# Disable caching (force reprocessing)
python main.py input/*.mp4 --no-cache

# Dry run (validate inputs without processing)
python main.py input/*.mp4 --dry-run
```

### System Testing
```bash
# Run comprehensive system tests
python test_system.py

# Test individual components
python -m pytest tests/ -v
```

## 📁 Project Structure

```
drone-video-generator/
├── main.py                 # Command-line interface
├── video_processor.py      # Video analysis and clip extraction
├── ai_analyzer.py          # OpenAI integration for scene analysis
├── clip_selector.py        # Theme assignment logic
├── video_editor.py         # Video editing and rendering
├── music_downloader.py     # Music management and integration
├── cache_manager.py        # Caching system
├── progress_tracker.py     # Progress tracking and error handling
├── config.py              # Configuration management
├── test_system.py          # System validation suite
├── requirements.txt        # Python dependencies
├── setup.py               # Package installation
├── .env.example           # Environment variables template
├── input/                 # Input video directory
├── uploads/               # Legacy input directory (still supported)
├── output/                # Generated video directory
├── music/                 # Downloaded/generated music
└── cache/                 # Processing cache
```

## 🎨 Themes

The system generates 5 distinct themed videos:

| Theme | Description | Music Style | Pacing |
|-------|-------------|-------------|---------|
| **🌟 Happy** | Bright, uplifting scenes | Upbeat, cheerful | Medium |
| **⚡ Exciting** | High-energy, dynamic footage | Energetic, intense | Fast |
| **🌿 Peaceful** | Calm, serene landscapes | Ambient, relaxing | Slow |
| **🏔️ Adventure** | Epic, dramatic scenes | Cinematic, inspiring | Medium |
| **🎭 Cinematic** | Professional, artistic shots | Orchestral, dramatic | Variable |

## 🔧 Configuration

### Environment Variables (.env)
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-vision-preview

# Video Processing Settings
MAX_CLIPS_PER_THEME=5
DEFAULT_VIDEO_DURATION=180
CACHE_ENABLED=true

# Music Settings
MUSIC_VOLUME=0.6
ORIGINAL_AUDIO_BOOST=1.5
FINAL_AUDIO_BOOST=1.2
```

### Theme Customization (config.py)
```python
THEME_CONFIGS = {
    VideoTheme.HAPPY: ThemeConfig(
        name="Happy",
        target_duration=180,
        pacing="medium",
        music_keywords=["upbeat", "cheerful", "positive"],
        # ... more settings
    ),
    # ... other themes
}
```

## 📊 System Requirements

### Minimum Requirements
- **CPU**: Dual-core processor (2.0 GHz+)
- **RAM**: 8 GB
- **Storage**: 10 GB free space
- **GPU**: Not required (CPU processing)

### Recommended Requirements
- **CPU**: Quad-core processor (3.0 GHz+)
- **RAM**: 16 GB
- **Storage**: 50 GB free space (for large video files)
- **GPU**: Dedicated GPU (for faster processing)

### Performance Notes
- Processing time: ~2-5 minutes per minute of input video
- Output file sizes: ~20-30 MB per minute of generated video
- Memory usage: ~2-4 GB during processing

## 🧪 Testing & Validation

The system includes comprehensive testing with **87.5% success rate**:

```bash
# Run all tests
python test_system.py

# Expected output:
# 🎉 SYSTEM STATUS: READY FOR USE
# 📈 Success rate: 87.5% (7/8)
```

### Test Coverage
- ✅ Environment Setup
- ✅ Video Processing
- ✅ Music System
- ✅ Video Editing
- ✅ Output Quality
- ✅ End-to-End Pipeline
- ✅ Performance Validation
- ⚠️ AI Integration (requires API key)

## 🔍 Troubleshooting

### Common Issues

**1. "No valid video files found"**
```bash
# Ensure videos are in input/ directory
ls input/
# Supported formats: .mp4, .mov, .avi, .mkv
```

**2. "ffmpeg not found"**
```bash
# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

**3. "OpenAI API key required"**
```bash
# Set up API key in .env file
echo "OPENAI_API_KEY=your_key_here" > .env
```

**4. "Audio not audible in output"**
- Check that music files exist in `music/` directory
- Verify audio levels with: `ffmpeg -i output/video.mp4 -af volumedetect -f null -`

### Performance Optimization

**For faster processing:**
- Use SSD storage for video files
- Close other applications to free RAM
- Process shorter video segments
- Disable AI analysis if not needed

**For better quality:**
- Use high-quality source videos
- Ensure good lighting in original footage
- Provide OpenAI API key for better scene analysis

## 🛣️ Roadmap

### Current MVP (v1.0.0) ✅
- [x] Basic video processing and clip detection
- [x] 5 themed video generation (defaults to single theme for efficiency)
- [x] Freesound.org music integration with Creative Commons licensing
- [x] AI-powered scene analysis with OpenAI GPT-4 Vision
- [x] Comprehensive testing suite
- [x] Fixed authentication issues with music downloads
- [x] Optimized for single-theme generation workflow

### Future Enhancements (v2.0.0)
- [ ] **Human Prompt Integration**: Custom themes via text prompts
- [ ] **Web Interface**: Browser-based drag & drop interface
- [ ] **Advanced Transitions**: More sophisticated video effects
- [ ] **Custom Music Upload**: User-provided background music
- [ ] **Batch Export Options**: Multiple formats and resolutions
- [ ] **Cloud Processing**: Scalable cloud-based processing

### Long-term Vision (v3.0.0+)
- [ ] **Real-time Processing**: Live drone feed processing
- [ ] **Social Media Integration**: Direct upload to platforms
- [ ] **Collaborative Editing**: Multi-user project sharing
- [ ] **Mobile App**: iOS/Android companion app
- [ ] **Enterprise Features**: Team management and analytics

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone and install in development mode
git clone https://github.com/your-username/drone-video-generator.git
cd drone-video-generator
pip install -e ".[dev]"

# Run tests
python test_system.py
pytest tests/ -v

# Code formatting
black .
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 Vision API
- **MoviePy** for video editing capabilities
- **OpenCV** for computer vision processing
- **Freesound.org** for royalty-free music API
- **scipy** for audio processing
- The drone community for inspiration and feedback

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/drone-video-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/drone-video-generator/discussions)
- **Email**: contact@dronevideogenerator.com

---

**Made with ❤️ for the drone community**

*Transform your raw footage into cinematic masterpieces with the power of AI!*
