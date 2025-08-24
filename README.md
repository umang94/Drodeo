# 🎬 Drone Video Generator MVP

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: MVP Complete](https://img.shields.io/badge/Status-MVP%20Complete-green.svg)](https://github.com/your-username/drone-video-generator)

**Transform raw drone footage into polished, themed videos with AI-powered automation.**

An intelligent video processing system that automatically analyzes drone footage, selects the best clips, and creates themed videos with appropriate background music. Perfect for content creators, drone enthusiasts, and anyone looking to quickly turn raw footage into engaging videos.

## ✨ Features

### 🎯 Core Functionality
1. **AI-Powered Analysis** - OpenAI GPT-4 Vision for scene understanding and quality assessment
2. **Smart Clip Detection** - Automatic identification of best segments using motion analysis and quality scoring
3. **Multi-Theme Generation** - Creates 5 distinct themes (Happy, Exciting, Peaceful, Adventure, Cinematic), defaults to single theme for efficiency
4. **Automated Music Integration** - Freesound.org integration with theme-appropriate background music and proper audio mixing

### 🎬 Video Processing
1. **Motion & Scene Analysis** - Detects dynamic scenes, camera movements, and natural transition points
2. **Quality Assessment** - Evaluates brightness, exposure, and visual appeal with intelligent caching
3. **4K Support** - Maintains original video quality with multiple format support (MP4, MOV, AVI, MKV)

### 🎵 Music & Audio
1. **Freesound Integration** - Downloads high-quality music previews with Creative Commons licensing
2. **Theme Matching** - Intelligent music selection based on video content and theme
3. **Audio Mixing** - Balances original drone audio with background music and volume optimization

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **ffmpeg** (for video processing)
- **OpenAI API Key** (optional, for enhanced AI analysis)

### Installation

**Method 1: Using setup.py (Recommended)**
```bash
git clone https://github.com/your-username/drone-video-generator.git
cd drone-video-generator
python setup.py install
```

**Method 2: Development Installation**
```bash
pip install -e .
# With optional dependencies
pip install -e ".[dev,performance]"
```

**Method 3: Manual Installation**
```bash
pip install -r requirements.txt
# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

### Configuration
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY=your_key_here (optional)
# - FREESOUND_API_KEY=your_key_here (optional)
```

### Basic Usage
1. Place drone videos in `input/` directory
2. Run: `python main.py input/your_video.mp4`
3. Find themed videos in `output/` directory

**Note**: Defaults to "happy" theme. Use `--themes` for multiple themes.

## 📖 Usage Examples

```bash
# Single video (happy theme)
python main.py input/DJI_0131.mp4

# Multiple themes
python main.py input/*.mp4 --themes peaceful exciting

# Custom duration and output
python main.py input/*.mp4 --duration 60 --output-dir my_videos

# All themes
python main.py input/*.mp4 --themes happy exciting peaceful adventure cinematic
```

## 📁 Project Structure

```
drone-video-generator/
├── main.py                 # CLI entry point
├── setup.py               # Package installation
├── requirements.txt        # Dependencies
├── src/
│   ├── core/              # Core processing
│   │   ├── video_processor.py
│   │   ├── ai_analyzer.py
│   │   └── clip_selector.py
│   ├── editing/           # Video editing
│   │   ├── video_editor.py
│   │   └── music_downloader.py
│   ├── utils/             # Utilities
│   │   ├── cache_manager.py
│   │   ├── progress_tracker.py
│   │   └── config.py
│   └── tests/             # Test modules
│       ├── test_system.py
│       └── test_freesound_integration.py
├── input/                 # Input videos
├── output/                # Generated videos
├── music/                 # Downloaded music
└── cache/                 # Processing cache
```

## 🎨 Themes

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
OPENAI_API_KEY=your_api_key_here
FREESOUND_API_KEY=your_api_key_here
MAX_CLIPS_PER_THEME=5
DEFAULT_VIDEO_DURATION=180
```

### API Keys
- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Freesound**: [https://freesound.org/apiv2/apply/](https://freesound.org/apiv2/apply/)

## 🧪 Testing

```bash
# Run system tests
python src/tests/test_system.py

# Test Freesound integration
python src/tests/test_freesound_integration.py
```

**Success Rate**: 87.5% (7/8 test suites pass)

## 🔍 Troubleshooting

**Common Issues:**
1. **"No valid video files found"** - Ensure videos are in `input/` directory
2. **"ffmpeg not found"** - Install ffmpeg: `brew install ffmpeg` (macOS)
3. **"OpenAI API key required"** - Add key to `.env` file
4. **Audio not audible** - Check music files exist in `music/` directory

## 📊 System Requirements

**Minimum**: Dual-core 2.0GHz, 8GB RAM, 10GB storage  
**Recommended**: Quad-core 3.0GHz, 16GB RAM, 50GB storage  
**Performance**: ~2-5 minutes processing per minute of input video

## 🛣️ Roadmap

### Current MVP (v1.0.0) ✅
- [x] AI-powered video processing and clip detection
- [x] 5 themed video generation (optimized for single theme)
- [x] Freesound.org music integration
- [x] Comprehensive testing suite

### Future Enhancements (v2.0.0)
- [ ] Human prompt integration for custom themes
- [ ] Web interface with drag & drop
- [ ] Advanced transitions and effects
- [ ] Cloud processing capabilities

## 🤝 Contributing

```bash
# Development setup
git clone https://github.com/your-username/drone-video-generator.git
cd drone-video-generator
pip install -e ".[dev]"

# Run tests
python src/tests/test_system.py
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 Vision API
- **MoviePy** for video editing capabilities  
- **OpenCV** for computer vision processing
- **Freesound.org** for royalty-free music API

---

**Made with ❤️ for the drone community**

*Transform your raw footage into cinematic masterpieces with AI!*
