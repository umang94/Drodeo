"""
GPU Acceleration Module for Drone Video Generator

This module provides GPU-accelerated video processing capabilities using CUDA,
with automatic fallback to CPU processing when GPU is not available.
"""

from .gpu_detector import GPUDetector, GPUCapabilities
from .gpu_video_processor import GPUVideoProcessor

__all__ = [
    'GPUDetector',
    'GPUCapabilities', 
    'GPUVideoProcessor'
]

# Initialize GPU detector on module import
gpu_detector = GPUDetector()
gpu_available = gpu_detector.is_gpu_available()

def get_gpu_info():
    """Get GPU information and capabilities."""
    return gpu_detector.get_capabilities()

def is_gpu_available():
    """Check if GPU acceleration is available."""
    return gpu_available
