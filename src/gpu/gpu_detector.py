"""
GPU Detection and Capability Management

This module handles detection of GPU capabilities and manages fallback to CPU processing.
"""

import os
import sys
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
import warnings

# Suppress warnings during GPU detection
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)

@dataclass
class GPUCapabilities:
    """Container for GPU capability information."""
    has_cuda: bool = False
    has_mps: bool = False  # Apple Silicon Metal Performance Shaders
    has_cupy: bool = False
    has_opencv_cuda: bool = False
    cuda_version: Optional[str] = None
    gpu_count: int = 0
    gpu_memory_mb: int = 0
    gpu_name: str = ""
    compute_capability: Optional[str] = None
    gpu_type: str = "unknown"  # "cuda", "mps", "cpu"
    
    @property
    def is_gpu_ready(self) -> bool:
        """Check if GPU is ready for acceleration."""
        return (self.has_cuda or self.has_mps) and self.gpu_count > 0
    
    @property
    def can_accelerate_opencv(self) -> bool:
        """Check if OpenCV CUDA acceleration is available."""
        return self.has_opencv_cuda and self.has_cuda
    
    @property
    def can_accelerate_torch(self) -> bool:
        """Check if PyTorch GPU acceleration is available."""
        return self.has_cuda or self.has_mps

class GPUDetector:
    """Detects and manages GPU capabilities."""
    
    def __init__(self):
        self._capabilities = None
        self._detection_complete = False
        
    def detect_capabilities(self) -> GPUCapabilities:
        """Detect all GPU capabilities."""
        if self._detection_complete:
            return self._capabilities
            
        capabilities = GPUCapabilities()
        
        # Check for different GPU types
        capabilities.has_mps = self._check_mps()
        capabilities.has_cuda = self._check_cuda()
        
        # Check CuPy availability (CUDA only)
        capabilities.has_cupy = self._check_cupy()
        
        # Check OpenCV CUDA support
        capabilities.has_opencv_cuda = self._check_opencv_cuda()
        
        # Get detailed GPU information
        if capabilities.has_mps:
            self._get_mps_details(capabilities)
        elif capabilities.has_cuda:
            self._get_cuda_details(capabilities)
        
        self._capabilities = capabilities
        self._detection_complete = True
        
        # Log detection results
        self._log_detection_results(capabilities)
        
        return capabilities
    
    def _check_mps(self) -> bool:
        """Check if Apple Silicon MPS is available."""
        try:
            import torch
            return torch.backends.mps.is_available()
        except ImportError:
            return False
        except Exception:
            return False
    
    def _check_cuda(self) -> bool:
        """Check if NVIDIA CUDA is available."""
        try:
            import torch
            if torch.cuda.is_available():
                return True
        except ImportError:
            pass
        
        try:
            import pycuda.driver as cuda
            cuda.init()
            return cuda.Device.count() > 0
        except ImportError:
            pass
        except Exception:
            pass
        
        # Check for nvidia-smi as fallback
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return False
    
    def _check_cupy(self) -> bool:
        """Check if CuPy is available and working."""
        try:
            import cupy as cp
            # Try a simple operation to verify it works
            test_array = cp.array([1, 2, 3])
            _ = cp.sum(test_array)
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.debug(f"CuPy test failed: {e}")
            return False
    
    def _check_opencv_cuda(self) -> bool:
        """Check if OpenCV was compiled with CUDA support."""
        try:
            import cv2
            build_info = cv2.getBuildInformation()
            return 'CUDA:' in build_info and 'YES' in build_info.split('CUDA:')[1].split('\n')[0]
        except ImportError:
            return False
        except Exception:
            return False
    
    def _get_mps_details(self, capabilities: GPUCapabilities):
        """Get detailed Apple Silicon MPS information."""
        try:
            import torch
            import platform
            import subprocess
            
            capabilities.gpu_type = "mps"
            capabilities.gpu_count = 1  # Apple Silicon has integrated GPU
            
            # Get system information
            system_info = platform.uname()
            if "arm64" in system_info.machine.lower():
                # Try to get more specific chip information
                try:
                    result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        capabilities.gpu_name = f"Apple {result.stdout.strip()} GPU"
                    else:
                        capabilities.gpu_name = "Apple Silicon GPU"
                except:
                    capabilities.gpu_name = "Apple Silicon GPU"
            else:
                capabilities.gpu_name = "Apple Silicon GPU"
            
            # Estimate GPU memory (Apple Silicon uses unified memory)
            try:
                result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    total_memory_bytes = int(result.stdout.strip())
                    # Estimate GPU gets about 60% of system memory on Apple Silicon
                    capabilities.gpu_memory_mb = int((total_memory_bytes * 0.6) // (1024 * 1024))
                else:
                    capabilities.gpu_memory_mb = 8192  # Default estimate
            except:
                capabilities.gpu_memory_mb = 8192  # Default estimate
            
            capabilities.compute_capability = "MPS"
            capabilities.cuda_version = "N/A (MPS)"
            
        except Exception as e:
            logger.debug(f"Failed to get MPS details: {e}")
            capabilities.gpu_name = "Apple Silicon GPU"
            capabilities.gpu_memory_mb = 8192
            capabilities.gpu_count = 1
            capabilities.gpu_type = "mps"
    
    def _get_cuda_details(self, capabilities: GPUCapabilities):
        """Get detailed CUDA information."""
        capabilities.gpu_type = "cuda"
        
        # Try with PyTorch first
        try:
            import torch
            if torch.cuda.is_available():
                capabilities.gpu_count = torch.cuda.device_count()
                capabilities.gpu_name = torch.cuda.get_device_name(0)
                capabilities.gpu_memory_mb = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
                capabilities.compute_capability = f"{torch.cuda.get_device_properties(0).major}.{torch.cuda.get_device_properties(0).minor}"
                capabilities.cuda_version = torch.version.cuda
                return
        except ImportError:
            pass
        
        # Try with CuPy
        try:
            import cupy as cp
            capabilities.gpu_count = cp.cuda.runtime.getDeviceCount()
            if capabilities.gpu_count > 0:
                device = cp.cuda.Device(0)
                capabilities.gpu_memory_mb = device.mem_info[1] // (1024 * 1024)
                capabilities.gpu_name = device.attributes.get('Name', 'Unknown GPU')
                major = device.attributes.get('ComputeCapabilityMajor', 0)
                minor = device.attributes.get('ComputeCapabilityMinor', 0)
                capabilities.compute_capability = f"{major}.{minor}"
                capabilities.cuda_version = str(cp.cuda.runtime.runtimeGetVersion())
                return
        except ImportError:
            pass
        
        # Try with PyCUDA
        try:
            import pycuda.driver as cuda
            cuda.init()
            capabilities.gpu_count = cuda.Device.count()
            if capabilities.gpu_count > 0:
                device = cuda.Device(0)
                capabilities.gpu_name = device.name()
                capabilities.gpu_memory_mb = device.total_memory() // (1024 * 1024)
                major, minor = device.compute_capability()
                capabilities.compute_capability = f"{major}.{minor}"
                return
        except ImportError:
            pass
    
    def _log_detection_results(self, capabilities: GPUCapabilities):
        """Log GPU detection results."""
        if capabilities.is_gpu_ready:
            logger.info(f"🚀 GPU acceleration available!")
            logger.info(f"   GPU: {capabilities.gpu_name}")
            logger.info(f"   Memory: {capabilities.gpu_memory_mb}MB")
            logger.info(f"   CUDA Version: {capabilities.cuda_version}")
            logger.info(f"   Compute Capability: {capabilities.compute_capability}")
            logger.info(f"   OpenCV CUDA: {'✅' if capabilities.can_accelerate_opencv else '❌'}")
        else:
            logger.info("💻 GPU acceleration not available - using CPU processing")
            if not capabilities.has_cuda:
                logger.debug("   CUDA not detected")
            if not capabilities.has_cupy:
                logger.debug("   CuPy not available")
            if capabilities.gpu_count == 0:
                logger.debug("   No CUDA devices found")
    
    def get_capabilities(self) -> GPUCapabilities:
        """Get GPU capabilities (cached after first detection)."""
        if not self._detection_complete:
            return self.detect_capabilities()
        return self._capabilities
    
    def is_gpu_available(self) -> bool:
        """Check if GPU acceleration is available."""
        return self.get_capabilities().is_gpu_ready
    
    def get_recommended_batch_size(self, frame_size_mb: float = 2.0) -> int:
        """Get recommended batch size based on GPU memory."""
        capabilities = self.get_capabilities()
        
        if not capabilities.is_gpu_ready:
            return 1  # CPU fallback
        
        # Reserve 20% of GPU memory for other operations
        available_memory_mb = capabilities.gpu_memory_mb * 0.8
        
        # Estimate frames that can fit in memory
        # Account for intermediate processing buffers (3x frame size)
        memory_per_frame = frame_size_mb * 3
        max_batch_size = int(available_memory_mb / memory_per_frame)
        
        # Clamp to reasonable range
        return max(1, min(max_batch_size, 32))
    
    def get_processing_device(self) -> str:
        """Get the recommended processing device string."""
        capabilities = self.get_capabilities()
        if capabilities.has_mps:
            return "mps"
        elif capabilities.has_cuda:
            return "cuda:0"
        return "cpu"

# Global instance for easy access
_detector_instance = None

def get_gpu_detector() -> GPUDetector:
    """Get the global GPU detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = GPUDetector()
    return _detector_instance

def print_gpu_info():
    """Print detailed GPU information."""
    detector = get_gpu_detector()
    capabilities = detector.get_capabilities()
    
    print("🔍 GPU Detection Results:")
    print(f"   CUDA Available: {'✅' if capabilities.has_cuda else '❌'}")
    print(f"   MPS Available: {'✅' if capabilities.has_mps else '❌'}")
    print(f"   CuPy Available: {'✅' if capabilities.has_cupy else '❌'}")
    print(f"   OpenCV CUDA: {'✅' if capabilities.has_opencv_cuda else '❌'}")
    
    if capabilities.is_gpu_ready:
        print(f"   GPU Type: {capabilities.gpu_type.upper()}")
        print(f"   GPU Count: {capabilities.gpu_count}")
        print(f"   GPU Name: {capabilities.gpu_name}")
        print(f"   GPU Memory: {capabilities.gpu_memory_mb}MB")
        print(f"   Version: {capabilities.cuda_version}")
        print(f"   Compute Capability: {capabilities.compute_capability}")
        print(f"   Recommended Batch Size: {detector.get_recommended_batch_size()}")
        print(f"   Processing Device: {detector.get_processing_device()}")
    else:
        print("   Status: CPU processing only")

if __name__ == "__main__":
    # Test GPU detection
    print_gpu_info()
