# 🏗️ Drodeo System Architecture

**Version:** 3.3.0  
**Last Updated:** August 30, 2025  
**Status:** Production Ready with Gemini API Integration Complete (Phase 1)

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [API Integration Strategy](#api-integration-strategy)
6. [Configuration Management](#configuration-management)
7. [Performance & Scalability](#performance--scalability)
8. [Future Enhancements](#future-enhancements)

---

## 🎯 System Overview

Drodeo is an intelligent music-driven video generation system that analyzes audio and video content to create compelling, beat-synchronized videos. The system uses AI-powered analysis, GPU acceleration, and advanced video processing to eliminate repetition and enhance engagement.

### Core Capabilities
- **Music-Driven Video Generation** - Creates videos synchronized to music beats and energy
- **AI-Powered Analysis** - Uses LLM and computer vision for content understanding
- **GPU Acceleration** - CUDA and Apple Silicon MPS support for fast processing
- **Intelligent Clip Sequencing** - Prevents repetition through smart content selection
- **Batch Processing** - Processes multiple music tracks efficiently

---

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DRODEO v3.3.0 SYSTEM ARCHITECTURE                 │
└─────────────────────────────────────────────────────────────────────────────────┘

INPUT LAYER
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   music_input/  │    │     input/      │    │   input_dev/    │
│                 │    │                 │    │                 │
│ ♪ song1.mp3     │    │ 📹 video1.mp4   │    │ 📹 video1_dev   │
│ ♪ song2.m4a     │    │ 📹 video2.mov   │    │ 📹 video2_dev   │
│ ♪ song3.wav     │    │ 📹 video3.mp4   │    │ 📹 video3_dev   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼

ANALYSIS LAYER
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─────────────────────┐              ┌─────────────────────────────────────┐   │
│  │   AUDIO ANALYSIS    │              │        VIDEO ANALYSIS               │   │
│  │                     │              │                                     │   │
│  │ src/audio/          │              │ src/core/llm_video_analyzer.py      │   │
│  │ audio_analyzer.py   │              │                                     │   │
│  │                     │              │ ┌─────────────────────────────────┐ │   │
│  │ 🎵 Beat Detection   │              │ │      GEMINI API VIDEO ANALYSIS  │ │   │
│  │ 🎵 Tempo Analysis   │              │ │         (IMPLEMENTED)           │ │   │
│  │ 🎵 Energy Profile   │              │ │                                 │ │   │
│  │ 🎵 Music Structure  │              │ │ 🎬 Music-Aware Analysis         │ │   │
│  │                     │              │ │ 🎬 Beat-Aligned Segments        │ │   │
│  │ Libraries:          │              │ │ 🎬 Energy Level Matching        │ │   │
│  │ • librosa           │              │ │ 🎬 Visual Rhythm Analysis       │ │   │
│  │ • numpy             │              │ │ 🎬 Temporal Understanding       │ │   │
│  │ • scipy             │              │ │                                 │ │   │
│  └─────────────────────┘              │ └─────────────────────────────────┘ │   │
│           │                           │                 │                   │   │
│           │                           │                 ▼                   │   │
│           │                           │ ┌─────────────────────────────────┐ │   │
│           │                           │ │     FALLBACK: GPT-4 VISION      │ │   │
│           │                           │ │                                 │ │   │
│           │                           │ │ 🤖 Keyframe Analysis            │ │   │
│           │                           │ │ 🤖 Content Understanding       │ │   │
│           │                           │ │ 🤖 Mood Detection              │ │   │
│           │                           │ │ 🤖 Quality Assessment          │ │   │
│           │                           │ └─────────────────────────────────┘ │   │
│           │                           └─────────────────────────────────────┘   │
└───────────┼─────────────────────────────────────────┼───────────────────────────┘
            │                                         │
            ▼                                         ▼

PROCESSING LAYER
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      STREAMLINED WITH GEMINI API INTEGRATION                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    DIRECT MUSIC-AWARE VIDEO PROCESSING                 │   │
│  │                                                                         │   │
│  │ 🎬 Gemini Music Sync Segments → Beat-Aligned Cut Points               │   │
│  │ 🎬 Energy Level Analysis → Music Energy Matching                       │   │
│  │ 🎬 Visual Rhythm Detection → Tempo Synchronization                     │   │
│  │ 🎬 Narrative Flow Understanding → Natural Transitions                  │   │
│  │ 💾 Smart Caching → Gemini API Response Optimization                    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼

EDITING LAYER
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           src/editing/video_editor.py                          │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    GEMINI-OPTIMIZED VIDEO CREATION                     │   │
│  │                                                                         │   │
│  │ 🎬 Music Sync Segments → Precise Beat-Aligned Cuts                     │   │
│  │ 🎬 Energy-Based Transitions → Dynamic Music Matching                   │   │
│  │ 🎬 Visual Rhythm Flow → Professional Video Sequencing                  │   │
│  │ 🎬 Beat Synchronization → Music-Driven Timing                          │   │
│  │ 🎬 No Repetition → Comprehensive Temporal Understanding                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼

RENDERING LAYER
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MoviePy + GPU Acceleration                        │
│                                                                                 │
│  ┌─────────────────────┐              ┌─────────────────────────────────────┐   │
│  │   VIDEO RENDERING   │              │         AUDIO OVERLAY               │   │
│  │                     │              │                                     │   │
│  │ 🚀 CUDA/MPS Support │              │ 🎵 Music Synchronization           │   │
│  │ 🚀 Batch Processing │              │ 🎵 Volume Balancing                │   │
│  │ 🚀 H.264 Encoding   │              │ 🎵 Audio Mixing                    │   │
│  │ 🚀 Progress Tracking│              │ 🎵 Fade Transitions                │   │
│  │ 🚀 Memory Mgmt      │              │                                     │   │
│  └─────────────────────┘              └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼

OUTPUT LAYER
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  output/                                        │
│                                                                                 │
│  📹 song1_7clips_180s.mp4     📹 song2_5clips_120s.mp4     📹 song3_9clips_200s.mp4 │
│                                                                                 │
│  ✅ Beat-synchronized         ✅ No repetition              ✅ Professional quality │
│  ✅ Activity-matched          ✅ Natural transitions        ✅ GPU-accelerated     │
│  ✅ Intelligent sequencing    ✅ Dynamic duration           ✅ High engagement     │
└─────────────────────────────────────────────────────────────────────────────────┘

CONTROL FLOW & ORCHESTRATION
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            batch_video_generator.py                            │
│                                                                                 │
│  1. 📂 Scan music_input/ and input/ directories                                │
│  2. 🔄 For each music file:                                                    │
│     a. 🎵 Analyze audio (beats, energy, tempo, structure)                      │
│     b. 📹 Analyze videos (Gemini API → GPT-4 Vision → Basic fallback)          │
│     c. 🧠 Create intelligent sync plan with anti-repetition                    │
│     d. 🎬 Render final video with music overlay and GPU acceleration           │
│     e. 💾 Cache results for future processing                                  │
│  3. 📤 Save to output/ directory with descriptive filenames                    │
└─────────────────────────────────────────────────────────────────────────────────┘

CONFIGURATION & SUPPORT SYSTEMS
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │      .env       │  │     cache/      │  │ src/utils/      │  │    logs/    │ │
│  │                 │  │                 │  │                 │  │             │ │
│  │ 🔑 API Keys     │  │ 💾 Video Cache  │  │ ⚙️  config.py   │  │ 📊 Analysis │ │
│  │ 🔑 Gemini API   │  │ 💾 Audio Cache  │  │ ⚙️  cache_mgr   │  │ 📊 Progress │ │
│  │ 🔑 OpenAI       │  │ 💾 LLM Cache    │  │ ⚙️  progress    │  │ 📊 Errors   │ │
│  │ ⚙️  GPU Config  │  │ 💾 Keyframes    │  │ ⚙️  llm_logger  │  │ 📊 Reports  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Component Details

### Input Layer

#### Music Input (`music_input/`)
- **Supported Formats:** MP3, M4A, WAV, FLAC, OGG
- **Processing:** Automatic format detection and conversion
- **Quality:** Preserves original audio quality in final output

#### Video Input (`input/` & `input_dev/`)
- **Primary:** `input/` - Full quality videos (4K, 1080p, etc.)
- **Development:** `input_dev/` - Downsampled 360p versions for fast iteration
- **Supported Formats:** MP4, MOV, AVI, MKV
- **Auto-generation:** Development videos created automatically when needed

### Analysis Layer

#### Audio Analysis (`src/audio/audio_analyzer.py`)
```python
class AudioFeatures:
    tempo: float                    # BPM detection
    beats: List[float]             # Beat timestamps
    energy_profile: List[float]    # Energy over time
    duration: float                # Total duration
    spectral_features: np.ndarray  # Frequency analysis
```

**Key Capabilities:**
- **Beat Detection:** Uses librosa for precise beat timing
- **Energy Profiling:** Calculates energy levels over time windows
- **Tempo Analysis:** BPM detection with fallback mechanisms
- **Music Structure:** Identifies intro, build, climax, outro sections

#### Video Analysis (`src/core/llm_video_analyzer.py`)

**Current Implementation: GPT-4 Vision**
```python
class VideoAnalysis:
    content_summary: str           # What happens in the video
    shot_types: List[str]         # Wide, medium, close-up shots
    mood_energy: str              # Peaceful, exciting, dramatic
    quality_score: float          # Technical quality assessment
    transition_points: List[float] # Optimal cut points
```

**Planned Enhancement: Google Video Intelligence API**
```python
class GoogleVideoAnalysis:
    shots: List[VideoSegment]      # Natural shot boundaries
    activities: List[Dict]         # Detected activities with timestamps
    labels: List[Dict]            # Scene/object labels with confidence
    recommended_segments: List[VideoSegment]  # Best segments for sync
```

### Processing Layer

#### Video Processing (`src/core/video_processor.py`)
```python
class VideoProcessor:
    def process_videos(self, video_paths: List[str]) -> List[VideoClip]:
        # 1. Quality assessment and scoring
        # 2. Content analysis and categorization
        # 3. Duration calculation and optimization
        # 4. GPU-accelerated processing when available
        # 5. Cache management for processed results
```

**Key Features:**
- **Dynamic Keyframe Extraction:** 1 frame per 2 seconds of video duration
- **Quality Scoring:** Assesses technical quality, composition, lighting
- **Content Matching:** Matches video content to music characteristics
- **GPU Optimization:** Leverages CUDA/MPS for faster processing
- **Intelligent Caching:** Avoids reprocessing with smart cache keys

#### Clip Selection & Sequencing
```python
class ClipSequencer:
    def create_intelligent_sequence(self, clips: List[VideoClip], 
                                  audio_features: AudioFeatures) -> List[VideoClip]:
        # 1. Analyze music structure (intro, build, climax, outro)
        # 2. Match video content to music energy levels
        # 3. Prevent repetition through smart scheduling
        # 4. Optimize for beat synchronization
        # 5. Ensure visual variety and engagement
```

### Editing Layer

#### Video Editor (`src/editing/video_editor.py`)

**Sync Plan Video Creation:**
```python
def _create_sync_plan_video(self, clips: List[VideoClip], 
                           sync_plan: AudioVisualSyncPlan) -> VideoFileClip:
    # 1. Load clips based on sync plan
    # 2. Create beat-aligned segments
    # 3. Apply intelligent clip extension (5 strategies)
    # 4. Add smooth transitions with fade effects
    # 5. Concatenate with precise timing
```

**Intelligent Clip Extension Strategies:**
1. **Extend from same source** - Use content before/after original clip
2. **Find longer clip** - Use different segment from same video
3. **Combine with variety** - Mix with different clip for diversity
4. **Speed adjustment** - Slow down clip slightly (max 30%)
5. **Freeze frame padding** - Last resort fallback

### Rendering Layer

#### GPU Acceleration
```python
class GPUVideoProcessor:
    def __init__(self):
        self.device = self._detect_gpu()  # CUDA, MPS, or CPU
        
    def process_batch(self, clips: List[VideoClip]) -> List[VideoClip]:
        # Optimized batch processing for GPU memory efficiency
```

**Supported Platforms:**
- **NVIDIA CUDA:** GeForce RTX, Quadro, Tesla series
- **Apple Silicon MPS:** M1, M2, M3 chips with Metal Performance Shaders
- **CPU Fallback:** Automatic fallback when GPU unavailable

#### Audio Processing
```python
class AudioProcessor:
    def add_music_overlay(self, video: VideoFileClip, 
                         music_path: str) -> VideoFileClip:
        # 1. Load and loop audio to match video duration
        # 2. Apply volume balancing (music 60%, original audio 150%)
        # 3. Mix audio tracks with proper levels
        # 4. Apply fade in/out effects
        # 5. Ensure audio quality preservation
```

---

## 🔄 Data Flow

### Primary Processing Pipeline

```
1. INPUT SCANNING
   music_input/*.{mp3,m4a,wav} + input/*.{mp4,mov,avi}
   ↓
2. AUDIO ANALYSIS
   librosa → beats, tempo, energy_profile, duration
   ↓
3. VIDEO ANALYSIS
   GPT-4 Vision → content, mood, quality, transitions
   (Future: Google Video Intelligence → shots, activities, labels)
   ↓
4. INTELLIGENT MATCHING
   Match video segments to music structure and energy
   ↓
5. SYNC PLAN CREATION
   Create beat-aligned video sequence with anti-repetition
   ↓
6. VIDEO RENDERING
   MoviePy + GPU → final MP4 with music overlay
   ↓
7. OUTPUT
   output/musicname_Nclips_Nseconds.mp4
```

### Caching Strategy

```
CACHE HIERARCHY:
├── Audio Analysis Cache
│   ├── beats_tempo_energy.json
│   └── spectral_features.npy
├── Video Analysis Cache
│   ├── llm_analysis.json
│   ├── keyframes/
│   └── quality_scores.json
├── Processing Cache
│   ├── clip_selections.json
│   └── sync_plans.json
└── Rendered Output Cache
    └── final_videos.mp4
```

**Cache Invalidation:**
- Audio files: Based on file modification time and size
- Video files: Based on content hash and analysis parameters
- LLM responses: Based on model version and prompt changes
- Processing results: Based on algorithm version and parameters

---

## 🔌 API Integration Strategy

### Current: OpenAI GPT-4 Vision

**Integration Points:**
- `src/core/llm_video_analyzer.py` - Main analysis engine
- `src/utils/llm_logger.py` - Request/response logging
- Rate limiting and error handling built-in

**API Usage:**
```python
# Keyframe analysis with GPT-4 Vision
response = self.client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Expert video editor..."},
        {"role": "user", "content": [
            {"type": "text", "text": analysis_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}"}}
        ]}
    ],
    max_tokens=1500,
    temperature=0.3
)
```

### Planned: Google Video Intelligence API

**Integration Architecture:**
```python
# Enhanced video analysis with Google API
class GoogleVideoAnalyzer:
    def analyze_video_comprehensive(self, video_path: str) -> GoogleVideoAnalysis:
        # 1. Upload to Google Cloud Storage
        # 2. Request shot detection, activity recognition, label detection
        # 3. Process results into structured format
        # 4. Create music synchronization recommendations
        # 5. Cleanup temporary files
```

**API Features to Leverage:**
- **Shot Change Detection:** Natural cut points for transitions
- **Activity Recognition:** Match high-energy music to action scenes
- **Label Detection:** Scene classification for content matching
- **Object Tracking:** Temporal understanding of video content

**Cost Comparison:**
- **Current (GPT-4 Vision):** ~$0.08 per video (8 frames)
- **Planned (Google Video Intelligence):** ~$0.20 per video (full analysis)
- **Benefit:** 2.5x cost increase for significantly better temporal understanding

---

## ⚙️ Configuration Management

### Environment Variables (`.env`)
```bash
# API Configuration
OPENAI_API_KEY=your_openai_key_here
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_CLOUD_STORAGE_BUCKET=drodeo-video-analysis
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Processing Configuration
MAX_CLIPS_PER_VIDEO=10
DEFAULT_VIDEO_DURATION=180
MIN_CLIP_DURATION=4.0
MAX_CLIP_DURATION=40.0

# GPU Configuration
ENABLE_GPU_ACCELERATION=true
GPU_MEMORY_LIMIT=8192  # MB

# Development Configuration
USE_DEV_VIDEOS=true
ENABLE_CACHE=true
FAST_TEST_MODE=false

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_LLM_LOGGING=true
```

### Runtime Configuration (`src/utils/config.py`)
```python
class VideoConfig:
    # Clip duration settings (enhanced in v3.2.0)
    MIN_CLIP_DURATION = 4.0    # Increased from 1.0
    MAX_CLIP_DURATION = 40.0   # Increased from 25.0
    
    # Keyframe extraction (dynamic in v3.2.0)
    KEYFRAMES_PER_SECOND = 0.5  # 1 frame per 2 seconds
    
    # Quality thresholds
    MIN_QUALITY_SCORE = 0.3
    PREFERRED_QUALITY_SCORE = 0.7

class AudioConfig:
    SAMPLE_RATE = 22050
    HOP_LENGTH = 512
    BEAT_DETECTION_SENSITIVITY = 0.7
    ENERGY_WINDOW_SIZE = 1.0  # seconds

class GPUConfig:
    CUDA_ENABLED = torch.cuda.is_available()
    MPS_ENABLED = torch.backends.mps.is_available()
    BATCH_SIZE = 4  # Clips processed simultaneously
    MEMORY_FRACTION = 0.8  # GPU memory usage limit
```

---

## 🚀 Performance & Scalability

### Current Performance Metrics

**Processing Speed (v3.2.0):**
- **Development Mode:** 35-70x faster with 360p videos
- **GPU Acceleration:** 2-5x faster video processing
- **Caching:** 90%+ cache hit rate for repeated processing
- **Batch Processing:** Linear scaling with number of music tracks

**Video Quality Improvements:**
- **Frame Repetition:** Eliminated through intelligent extension
- **Clip Variety:** 7 clips vs previous 13+ repetitive clips
- **Duration Range:** 4-40s clips vs previous 1-25s
- **Engagement:** Significantly improved through better sequencing

**Resource Usage:**
- **Memory:** 2-8GB RAM depending on video resolution and batch size
- **GPU Memory:** 2-6GB VRAM for GPU-accelerated processing
- **Storage:** ~100MB cache per hour of video content
- **Network:** Minimal (only for API calls)

### Scalability Considerations

**Horizontal Scaling:**
- **Multi-processing:** Can process multiple music tracks simultaneously
- **Cloud Deployment:** Google Cloud integration ready for cloud scaling
- **Distributed Processing:** Architecture supports distributed video analysis

**Vertical Scaling:**
- **GPU Scaling:** Supports multiple GPUs for parallel processing
- **Memory Optimization:** Efficient memory management for large video files
- **Storage Scaling:** Configurable cache management and cleanup

### Performance Optimization Strategies

1. **Video Preprocessing:**
   - Use development videos (360p) for rapid iteration
   - Implement progressive quality scaling
   - Smart keyframe extraction reduces API calls

2. **Caching Strategy:**
   - Multi-layer caching (audio, video, LLM responses)
   - Intelligent cache invalidation
   - Persistent cache across sessions

3. **GPU Utilization:**
   - Batch processing for optimal GPU memory usage
   - Automatic device detection and selection
   - Memory-aware processing limits

---

## 🚀 Future Enhancements

### Phase 1: Google Video Intelligence Integration
- **Timeline:** Next 2-4 weeks
- **Goal:** Replace keyframe-based analysis with full temporal understanding
- **Benefits:** Eliminate repetition, improve sync quality, better engagement

**Implementation Steps:**
1. Google Cloud setup and authentication
2. Modify `src/core/llm_video_analyzer.py` to integrate Google API
3. Enhance `src/editing/video_editor.py` with shot boundary data
4. Implement fallback system: Google API → GPT-4 Vision → Basic
5. Cost optimization and caching strategy

### Phase 2: Advanced Content Understanding
- **Timeline:** 1-2 months
- **Features:**
  - Multi-modal analysis (audio + video together)
  - Advanced story arc algorithms
  - Real-time preview capabilities
  - Custom transition effects library

### Phase 3: User Experience Enhancements
- **Timeline:** 2-3 months
- **Features:**
  - Web interface for content management
  - Real-time processing status
  - Advanced configuration options
  - Cloud processing support

### Phase 4: AI-Driven Creativity
- **Timeline:** 3-6 months
- **Features:**
  - Custom music genre classification
  - AI-generated visual effects
  - Multi-track audio mixing
  - Automated color grading
  - Style transfer capabilities

---

## 🔧 Technical Debt & Maintenance

### Current Technical Debt
1. **Legacy AI Analyzer:** `src/core/ai_analyzer.py` needs deprecation
2. **Code Duplication:** Some analysis logic duplicated across modules
3. **Error Handling:** Inconsistent error handling patterns
4. **Testing Coverage:** Need more comprehensive integration tests

### Maintenance Priorities
1. **Deprecate Legacy Components:** Phase out old analysis methods
2. **Standardize Error Handling:** Implement consistent error patterns
3. **Improve Test Coverage:** Add integration and performance tests
4. **Documentation Updates:** Keep documentation in sync with code changes

---

## 📊 Monitoring & Observability

### Logging Strategy
```python
# Structured logging with different levels
logs/
├── analysis/           # LLM and video analysis logs
├── processing/         # Video processing and rendering logs
├── errors/            # Error logs and stack traces
└── performance/       # Performance metrics and timing
```

### Metrics Collection
- **Processing Times:** Track analysis and rendering performance
- **API Usage:** Monitor OpenAI and Google API consumption
- **Cache Performance:** Track cache hit rates and storage usage
- **GPU Utilization:** Monitor GPU memory and processing efficiency
- **Quality Metrics:** Track video quality scores and user engagement

### Health Monitoring
- **System Resources:** Memory, CPU, GPU, and storage usage
- **API Status:** Monitor external API availability and response times
- **Processing Queue:** Track batch processing status and bottlenecks
- **Error Rates:** Monitor failure rates and automatic recovery

---

## 🔒 Security & Privacy

### Data Security
- **API Keys:** Secure storage in environment variables
- **Temporary Files:** Automatic cleanup of processing artifacts
- **Cloud Storage:** Encrypted transmission and storage
- **Local Processing:** Most processing happens locally

### Privacy Considerations
- **User Content:** Videos processed locally when possible
- **API Data:** Minimal data sent to external APIs
- **Cache Management:** Automatic cleanup of sensitive cached data
- **Audit Trail:** Logging of all external API interactions

---

## 📚 Development Guidelines

### Code Structure
```
src/
├── core/           # Core business logic
├── editing/        # Video editing and rendering
├── audio/          # Audio analysis and processing
├── utils/          # Shared utilities and configuration
├── gpu/           # GPU acceleration modules
└── tests/         # Test suites and validation
```

### Coding Standards
- **Python Style:** Follow PEP 8 with Black formatting
- **Type Hints:** Use type annotations for all public functions
- **Documentation:** Comprehensive docstrings for all modules
- **Error Handling:** Consistent exception handling patterns

### Testing Strategy
- **Unit Tests:** Individual component testing
- **Integration Tests:** End-to-end workflow testing
- **Performance Tests:** GPU and processing speed validation
- **Regression Tests:** Ensure quality improvements maintain

---

*This document serves as the definitive technical reference for the Drodeo system architecture. Keep it updated as the system evolves.*
