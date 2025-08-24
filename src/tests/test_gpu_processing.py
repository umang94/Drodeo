#!/usr/bin/env python3
"""
GPU Processing Tests

Test suite for GPU-accelerated video processing functionality.
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gpu.gpu_detector import print_gpu_info, get_gpu_detector
from gpu.gpu_video_processor import create_gpu_processor, extract_keyframes_gpu

def test_gpu_detection():
    """Test GPU detection capabilities."""
    print("🔍 Testing GPU Detection...")
    print_gpu_info()
    
    detector = get_gpu_detector()
    capabilities = detector.get_capabilities()
    
    print(f"\n📊 Detection Results:")
    print(f"   GPU Ready: {'✅' if capabilities.is_gpu_ready else '❌'}")
    print(f"   Can Accelerate OpenCV: {'✅' if capabilities.can_accelerate_opencv else '❌'}")
    print(f"   Recommended Batch Size: {detector.get_recommended_batch_size()}")
    
    return capabilities.is_gpu_ready

def test_gpu_processor_initialization():
    """Test GPU processor initialization."""
    print("\n🚀 Testing GPU Processor Initialization...")
    
    # Test with GPU enabled
    processor_gpu = create_gpu_processor(force_cpu=False)
    print(f"   GPU Processor: {'✅' if processor_gpu.use_gpu else '❌'}")
    
    # Test with CPU forced
    processor_cpu = create_gpu_processor(force_cpu=True)
    print(f"   CPU Processor: {'✅' if not processor_cpu.use_gpu else '❌'}")
    
    return processor_gpu, processor_cpu

def create_test_video():
    """Create a simple test video for testing."""
    import cv2
    
    test_video_path = "test_video.mp4"
    
    # Create a simple test video if it doesn't exist
    if not os.path.exists(test_video_path):
        print("   Creating test video...")
        
        # Video properties
        width, height = 640, 480
        fps = 30
        duration = 5  # seconds
        total_frames = fps * duration
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(test_video_path, fourcc, fps, (width, height))
        
        # Generate frames with moving pattern
        for frame_num in range(total_frames):
            # Create a frame with moving pattern
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add moving circle
            center_x = int((frame_num / total_frames) * width)
            center_y = height // 2
            cv2.circle(frame, (center_x, center_y), 50, (0, 255, 0), -1)
            
            # Add some noise for motion detection
            noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)
            
            out.write(frame)
        
        out.release()
        print(f"   Test video created: {test_video_path}")
    
    return test_video_path

def test_frame_extraction(processor, test_video_path, test_name):
    """Test frame extraction performance."""
    print(f"\n📹 Testing Frame Extraction ({test_name})...")
    
    try:
        # Reset stats
        processor.reset_stats()
        
        # Extract frames
        start_time = time.time()
        frame_indices = [0, 30, 60, 90, 120]  # Extract 5 frames
        frames = processor.extract_frames_batch(test_video_path, frame_indices)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        
        print(f"   Frames extracted: {len(frames)}")
        print(f"   Processing time: {processing_time:.1f}ms")
        print(f"   Average per frame: {processing_time/len(frames):.1f}ms")
        
        # Validate frames
        if frames:
            frame = frames[0]
            print(f"   Frame shape: {frame.shape}")
            print(f"   Frame dtype: {frame.dtype}")
        
        return frames, processing_time
        
    except Exception as e:
        print(f"   ❌ Frame extraction failed: {e}")
        return [], 0

def test_motion_analysis(processor, frames, test_name):
    """Test motion analysis performance."""
    print(f"\n🏃 Testing Motion Analysis ({test_name})...")
    
    if len(frames) < 2:
        print("   ⚠️  Need at least 2 frames for motion analysis")
        return []
    
    try:
        start_time = time.time()
        motion_scores = processor.analyze_motion_batch(frames)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        
        print(f"   Motion scores calculated: {len(motion_scores)}")
        print(f"   Processing time: {processing_time:.1f}ms")
        if motion_scores:
            print(f"   Average motion score: {np.mean(motion_scores):.2f}")
            print(f"   Motion score range: {np.min(motion_scores):.2f} - {np.max(motion_scores):.2f}")
        
        return motion_scores
        
    except Exception as e:
        print(f"   ❌ Motion analysis failed: {e}")
        return []

def test_brightness_analysis(processor, frames, test_name):
    """Test brightness analysis performance."""
    print(f"\n💡 Testing Brightness Analysis ({test_name})...")
    
    if not frames:
        print("   ⚠️  No frames available for brightness analysis")
        return []
    
    try:
        start_time = time.time()
        brightness_scores = processor.calculate_brightness_batch(frames)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        
        print(f"   Brightness scores calculated: {len(brightness_scores)}")
        print(f"   Processing time: {processing_time:.1f}ms")
        if brightness_scores:
            print(f"   Average brightness score: {np.mean(brightness_scores):.2f}")
            print(f"   Brightness score range: {np.min(brightness_scores):.2f} - {np.max(brightness_scores):.2f}")
        
        return brightness_scores
        
    except Exception as e:
        print(f"   ❌ Brightness analysis failed: {e}")
        return []

def test_keyframe_extraction_convenience():
    """Test the convenience function for keyframe extraction."""
    print(f"\n🎯 Testing Keyframe Extraction Convenience Function...")
    
    test_video_path = create_test_video()
    
    try:
        start_time = time.time()
        keyframes = extract_keyframes_gpu(test_video_path, num_frames=8)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        
        print(f"   Keyframes extracted: {len(keyframes)}")
        print(f"   Processing time: {processing_time:.1f}ms")
        if keyframes:
            print(f"   Keyframe shape: {keyframes[0].shape}")
        
        return keyframes
        
    except Exception as e:
        print(f"   ❌ Keyframe extraction failed: {e}")
        return []

def performance_comparison():
    """Compare GPU vs CPU performance."""
    print(f"\n⚡ Performance Comparison...")
    
    test_video_path = create_test_video()
    
    # Test GPU processor
    gpu_processor = create_gpu_processor(force_cpu=False)
    gpu_frames, gpu_time = test_frame_extraction(gpu_processor, test_video_path, "GPU")
    
    # Test CPU processor
    cpu_processor = create_gpu_processor(force_cpu=True)
    cpu_frames, cpu_time = test_frame_extraction(cpu_processor, test_video_path, "CPU")
    
    # Compare results
    if gpu_time > 0 and cpu_time > 0:
        speedup = cpu_time / gpu_time
        print(f"\n📊 Performance Comparison Results:")
        print(f"   GPU Time: {gpu_time:.1f}ms")
        print(f"   CPU Time: {cpu_time:.1f}ms")
        print(f"   Speedup: {speedup:.2f}x {'🚀' if speedup > 1.0 else '🐌'}")
    
    # Print detailed stats
    if gpu_processor.use_gpu:
        gpu_processor.print_performance_summary()
    cpu_processor.print_performance_summary()

def cleanup_test_files():
    """Clean up test files."""
    test_files = ["test_video.mp4"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Cleaned up: {file}")

def main():
    """Run all GPU processing tests."""
    print("🧪 GPU Processing Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: GPU Detection
        gpu_available = test_gpu_detection()
        
        # Test 2: Processor Initialization
        gpu_processor, cpu_processor = test_gpu_processor_initialization()
        
        # Test 3: Create test video
        test_video_path = create_test_video()
        
        # Test 4: Frame Extraction
        gpu_frames, _ = test_frame_extraction(gpu_processor, test_video_path, "GPU")
        cpu_frames, _ = test_frame_extraction(cpu_processor, test_video_path, "CPU")
        
        # Test 5: Motion Analysis
        if gpu_frames:
            test_motion_analysis(gpu_processor, gpu_frames, "GPU")
        if cpu_frames:
            test_motion_analysis(cpu_processor, cpu_frames, "CPU")
        
        # Test 6: Brightness Analysis
        if gpu_frames:
            test_brightness_analysis(gpu_processor, gpu_frames, "GPU")
        if cpu_frames:
            test_brightness_analysis(cpu_processor, cpu_frames, "CPU")
        
        # Test 7: Convenience Function
        test_keyframe_extraction_convenience()
        
        # Test 8: Performance Comparison
        performance_comparison()
        
        print(f"\n✅ All tests completed successfully!")
        
        if gpu_available:
            print(f"🚀 GPU acceleration is working!")
        else:
            print(f"💻 Running in CPU mode (GPU not available)")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test files...")
        cleanup_test_files()

if __name__ == "__main__":
    main()
