"""
GPU-Accelerated Video Processing

This module provides GPU-accelerated versions of video processing operations
with automatic fallback to CPU processing when GPU is not available.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Union
import logging
import time
from dataclasses import dataclass

from .gpu_detector import get_gpu_detector, GPUCapabilities

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Statistics for processing performance."""
    frames_processed: int = 0
    gpu_time_ms: float = 0.0
    cpu_time_ms: float = 0.0
    memory_used_mb: float = 0.0
    batch_size: int = 1
    
    @property
    def total_time_ms(self) -> float:
        return self.gpu_time_ms + self.cpu_time_ms
    
    @property
    def fps(self) -> float:
        if self.total_time_ms > 0:
            return (self.frames_processed * 1000.0) / self.total_time_ms
        return 0.0

class GPUVideoProcessor:
    """GPU-accelerated video processing operations."""
    
    def __init__(self, force_cpu: bool = False):
        """
        Initialize GPU video processor.
        
        Args:
            force_cpu: Force CPU processing even if GPU is available
        """
        self.detector = get_gpu_detector()
        self.capabilities = self.detector.get_capabilities()
        self.force_cpu = force_cpu
        self.use_gpu = self.capabilities.is_gpu_ready and not force_cpu
        
        # Initialize GPU libraries if available
        self.cupy = None
        self.cv2_cuda = None
        
        if self.use_gpu:
            self._initialize_gpu_libraries()
        
        # Processing statistics
        self.stats = ProcessingStats()
        
        logger.info(f"GPUVideoProcessor initialized - GPU: {'✅' if self.use_gpu else '❌'}")
    
    def _initialize_gpu_libraries(self):
        """Initialize GPU libraries."""
        self.torch = None
        self.device = None
        
        # Initialize PyTorch for MPS or CUDA
        if self.capabilities.has_mps or self.capabilities.has_cuda:
            try:
                import torch
                self.torch = torch
                
                if self.capabilities.has_mps:
                    self.device = torch.device("mps")
                    logger.debug("PyTorch MPS initialized successfully")
                elif self.capabilities.has_cuda:
                    self.device = torch.device("cuda:0")
                    logger.debug("PyTorch CUDA initialized successfully")
                    
            except ImportError:
                logger.warning("PyTorch not available - GPU operations will be disabled")
                self.use_gpu = False
                return
        
        # Try to initialize CuPy for CUDA-specific operations
        if self.capabilities.has_cuda:
            try:
                import cupy as cp
                self.cupy = cp
                logger.debug("CuPy initialized successfully")
            except ImportError:
                logger.debug("CuPy not available - using PyTorch for GPU operations")
                self.cupy = None
        
        # Check OpenCV CUDA support
        if self.capabilities.can_accelerate_opencv:
            self.cv2_cuda = cv2.cuda
            logger.debug("OpenCV CUDA support detected")
        else:
            logger.debug("OpenCV CUDA not available")
    
    def extract_frames_batch(self, video_path: str, frame_indices: List[int], 
                           target_size: Tuple[int, int] = (640, 360)) -> List[np.ndarray]:
        """
        Extract multiple frames from video with GPU acceleration.
        
        Args:
            video_path: Path to video file
            frame_indices: List of frame indices to extract
            target_size: Target size for resized frames (width, height)
            
        Returns:
            List of extracted and resized frames
        """
        start_time = time.time()
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        frames = []
        
        if self.use_gpu and (self.torch is not None):
            frames = self._extract_frames_gpu(cap, frame_indices, target_size)
        else:
            frames = self._extract_frames_cpu(cap, frame_indices, target_size)
        
        cap.release()
        
        # Update statistics
        processing_time = (time.time() - start_time) * 1000
        self.stats.frames_processed += len(frames)
        if self.use_gpu:
            self.stats.gpu_time_ms += processing_time
        else:
            self.stats.cpu_time_ms += processing_time
        
        return frames
    
    def _extract_frames_gpu(self, cap: cv2.VideoCapture, frame_indices: List[int], 
                           target_size: Tuple[int, int]) -> List[np.ndarray]:
        """Extract frames using GPU acceleration."""
        frames = []
        
        # Process frames in batches for better GPU utilization
        batch_size = self.detector.get_recommended_batch_size()
        
        for i in range(0, len(frame_indices), batch_size):
            batch_indices = frame_indices[i:i + batch_size]
            batch_frames = []
            
            # Extract frames to CPU first
            for frame_idx in batch_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    batch_frames.append(frame)
            
            if batch_frames:
                # Process batch on GPU
                processed_batch = self._process_frame_batch_gpu(batch_frames, target_size)
                frames.extend(processed_batch)
        
        return frames
    
    def _extract_frames_cpu(self, cap: cv2.VideoCapture, frame_indices: List[int], 
                           target_size: Tuple[int, int]) -> List[np.ndarray]:
        """Extract frames using CPU processing."""
        frames = []
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                # Resize frame
                resized_frame = cv2.resize(frame, target_size)
                frames.append(resized_frame)
        
        return frames
    
    def _process_frame_batch_gpu(self, frames: List[np.ndarray], 
                                target_size: Tuple[int, int]) -> List[np.ndarray]:
        """Process a batch of frames on GPU."""
        processed_frames = []
        
        try:
            if self.cupy and self.capabilities.has_cuda:
                # Use CuPy for CUDA
                processed_frames = self._process_frames_cupy(frames, target_size)
            elif self.torch and self.device:
                # Use PyTorch for MPS or CUDA
                processed_frames = self._process_frames_torch(frames, target_size)
            else:
                # Fallback to CPU
                processed_frames = [cv2.resize(frame, target_size) for frame in frames]
            
        except Exception as e:
            logger.warning(f"GPU batch processing failed: {e}, falling back to CPU")
            # Fallback to CPU processing
            processed_frames = [cv2.resize(frame, target_size) for frame in frames]
        
        return processed_frames
    
    def _process_frames_torch(self, frames: List[np.ndarray], 
                             target_size: Tuple[int, int]) -> List[np.ndarray]:
        """Process frames using PyTorch tensors (MPS/CUDA)."""
        processed_frames = []
        
        for frame in frames:
            # Convert numpy array to PyTorch tensor
            # OpenCV uses BGR, PyTorch expects RGB, but for resizing it doesn't matter
            tensor = self.torch.from_numpy(frame).float()
            
            # Move to GPU device (MPS or CUDA)
            tensor = tensor.to(self.device)
            
            # Reshape for interpolation: (H, W, C) -> (1, C, H, W)
            if len(tensor.shape) == 3:
                tensor = tensor.permute(2, 0, 1).unsqueeze(0)  # (C, H, W) -> (1, C, H, W)
            else:
                tensor = tensor.unsqueeze(0).unsqueeze(0)  # (H, W) -> (1, 1, H, W)
            
            # Resize using PyTorch interpolation
            resized_tensor = self.torch.nn.functional.interpolate(
                tensor, 
                size=target_size[::-1],  # PyTorch expects (H, W), we have (W, H)
                mode='bilinear', 
                align_corners=False
            )
            
            # Convert back to numpy: (1, C, H, W) -> (H, W, C)
            if len(frame.shape) == 3:
                resized_tensor = resized_tensor.squeeze(0).permute(1, 2, 0)
            else:
                resized_tensor = resized_tensor.squeeze(0).squeeze(0)
            
            # Move back to CPU and convert to numpy
            resized_frame = resized_tensor.cpu().numpy().astype(np.uint8)
            processed_frames.append(resized_frame)
        
        return processed_frames
    
    def _process_frames_cupy(self, frames: List[np.ndarray], 
                            target_size: Tuple[int, int]) -> List[np.ndarray]:
        """Process frames using CuPy (CUDA only)."""
        processed_frames = []
        
        # Convert frames to GPU arrays
        gpu_frames = []
        for frame in frames:
            gpu_frame = self.cupy.asarray(frame)
            gpu_frames.append(gpu_frame)
        
        # Process each frame (resize operation)
        for gpu_frame in gpu_frames:
            # Use OpenCV CUDA if available, otherwise use CuPy interpolation
            if self.cv2_cuda and hasattr(self.cv2_cuda, 'resize'):
                # Upload to GPU memory for OpenCV CUDA
                gpu_mat = self.cv2_cuda.GpuMat()
                gpu_mat.upload(self.cupy.asnumpy(gpu_frame))
                
                # Resize on GPU
                resized_gpu = self.cv2_cuda.resize(gpu_mat, target_size)
                
                # Download result
                result = resized_gpu.download()
                processed_frames.append(result)
            else:
                # Fallback to CuPy-based resizing
                resized_frame = self._resize_frame_cupy(gpu_frame, target_size)
                processed_frames.append(self.cupy.asnumpy(resized_frame))
        
        return processed_frames
    
    def _resize_frame_cupy(self, gpu_frame, target_size: Tuple[int, int]):
        """Resize frame using CuPy (basic bilinear interpolation)."""
        # This is a simplified resize - for production, consider using
        # more sophisticated interpolation methods
        h, w = gpu_frame.shape[:2]
        target_w, target_h = target_size
        
        # Create coordinate grids
        y_coords = self.cupy.linspace(0, h - 1, target_h)
        x_coords = self.cupy.linspace(0, w - 1, target_w)
        
        # Simple nearest neighbor for now (can be improved)
        y_indices = self.cupy.round(y_coords).astype(self.cupy.int32)
        x_indices = self.cupy.round(x_coords).astype(self.cupy.int32)
        
        # Clamp indices
        y_indices = self.cupy.clip(y_indices, 0, h - 1)
        x_indices = self.cupy.clip(x_indices, 0, w - 1)
        
        # Sample the image
        if len(gpu_frame.shape) == 3:  # Color image
            resized = gpu_frame[y_indices[:, None], x_indices[None, :], :]
        else:  # Grayscale
            resized = gpu_frame[y_indices[:, None], x_indices[None, :]]
        
        return resized
    
    def analyze_motion_batch(self, frames: List[np.ndarray]) -> List[float]:
        """
        Analyze motion in a batch of frames with GPU acceleration.
        
        Args:
            frames: List of consecutive frames
            
        Returns:
            List of motion scores for each frame pair
        """
        if len(frames) < 2:
            return []
        
        start_time = time.time()
        
        if self.use_gpu and self.cupy is not None:
            motion_scores = self._analyze_motion_gpu(frames)
        else:
            motion_scores = self._analyze_motion_cpu(frames)
        
        # Update statistics
        processing_time = (time.time() - start_time) * 1000
        if self.use_gpu:
            self.stats.gpu_time_ms += processing_time
        else:
            self.stats.cpu_time_ms += processing_time
        
        return motion_scores
    
    def _analyze_motion_gpu(self, frames: List[np.ndarray]) -> List[float]:
        """Analyze motion using GPU acceleration."""
        if not self.cupy:
            return self._analyze_motion_cpu(frames)
        
        motion_scores = []
        
        try:
            # Convert frames to grayscale and upload to GPU
            prev_frame_gpu = None
            
            for frame in frames:
                # Convert to grayscale
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame
                
                # Upload to GPU
                current_frame_gpu = self.cupy.asarray(gray, dtype=self.cupy.float32)
                
                if prev_frame_gpu is not None:
                    # Calculate frame difference on GPU
                    diff = self.cupy.abs(current_frame_gpu - prev_frame_gpu)
                    motion_score = float(self.cupy.mean(diff))
                    motion_scores.append(motion_score)
                
                prev_frame_gpu = current_frame_gpu
            
        except Exception as e:
            logger.warning(f"GPU motion analysis failed: {e}, falling back to CPU")
            return self._analyze_motion_cpu(frames)
        
        return motion_scores
    
    def _analyze_motion_cpu(self, frames: List[np.ndarray]) -> List[float]:
        """Analyze motion using CPU processing."""
        motion_scores = []
        prev_frame = None
        
        for frame in frames:
            # Convert to grayscale
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Apply Gaussian blur
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_frame is not None:
                # Calculate frame difference
                frame_diff = cv2.absdiff(prev_frame, gray)
                motion_score = np.mean(frame_diff)
                motion_scores.append(motion_score)
            
            prev_frame = gray
        
        return motion_scores
    
    def calculate_brightness_batch(self, frames: List[np.ndarray]) -> List[float]:
        """
        Calculate brightness scores for a batch of frames.
        
        Args:
            frames: List of frames to analyze
            
        Returns:
            List of brightness scores (0.0 to 1.0)
        """
        start_time = time.time()
        
        if self.use_gpu and self.cupy is not None:
            brightness_scores = self._calculate_brightness_gpu(frames)
        else:
            brightness_scores = self._calculate_brightness_cpu(frames)
        
        # Update statistics
        processing_time = (time.time() - start_time) * 1000
        if self.use_gpu:
            self.stats.gpu_time_ms += processing_time
        else:
            self.stats.cpu_time_ms += processing_time
        
        return brightness_scores
    
    def _calculate_brightness_gpu(self, frames: List[np.ndarray]) -> List[float]:
        """Calculate brightness using GPU acceleration."""
        if not self.cupy:
            return self._calculate_brightness_cpu(frames)
        
        brightness_scores = []
        
        try:
            for frame in frames:
                # Convert to grayscale if needed
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame
                
                # Upload to GPU and calculate mean brightness
                gpu_frame = self.cupy.asarray(gray, dtype=self.cupy.float32)
                brightness = float(self.cupy.mean(gpu_frame))
                
                # Calculate quality score based on brightness
                if brightness < 50:  # too dark
                    score = brightness / 50.0
                elif brightness > 200:  # too bright
                    score = (255 - brightness) / 55.0
                else:  # good range
                    score = 1.0
                
                brightness_scores.append(max(0.0, min(1.0, score)))
            
        except Exception as e:
            logger.warning(f"GPU brightness calculation failed: {e}, falling back to CPU")
            return self._calculate_brightness_cpu(frames)
        
        return brightness_scores
    
    def _calculate_brightness_cpu(self, frames: List[np.ndarray]) -> List[float]:
        """Calculate brightness using CPU processing."""
        brightness_scores = []
        
        for frame in frames:
            # Convert to grayscale if needed
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Calculate mean brightness
            brightness = np.mean(gray)
            
            # Calculate quality score based on brightness
            if brightness < 50:  # too dark
                score = brightness / 50.0
            elif brightness > 200:  # too bright
                score = (255 - brightness) / 55.0
            else:  # good range
                score = 1.0
            
            brightness_scores.append(max(0.0, min(1.0, score)))
        
        return brightness_scores
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get processing performance statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = ProcessingStats()
    
    def print_performance_summary(self):
        """Print performance summary."""
        stats = self.stats
        print(f"\n📊 GPU Processing Performance Summary:")
        print(f"   Frames Processed: {stats.frames_processed}")
        print(f"   Total Time: {stats.total_time_ms:.1f}ms")
        print(f"   Average FPS: {stats.fps:.1f}")
        print(f"   GPU Time: {stats.gpu_time_ms:.1f}ms ({stats.gpu_time_ms/stats.total_time_ms*100:.1f}%)")
        print(f"   CPU Time: {stats.cpu_time_ms:.1f}ms ({stats.cpu_time_ms/stats.total_time_ms*100:.1f}%)")
        print(f"   Processing Mode: {'🚀 GPU' if self.use_gpu else '💻 CPU'}")

# Convenience functions for easy integration
def create_gpu_processor(force_cpu: bool = False) -> GPUVideoProcessor:
    """Create a GPU video processor instance."""
    return GPUVideoProcessor(force_cpu=force_cpu)

def extract_keyframes_gpu(video_path: str, num_frames: int = 8, 
                         target_size: Tuple[int, int] = (640, 360)) -> List[np.ndarray]:
    """
    Extract keyframes using GPU acceleration.
    
    Args:
        video_path: Path to video file
        num_frames: Number of keyframes to extract
        target_size: Target size for frames
        
    Returns:
        List of extracted keyframes
    """
    processor = create_gpu_processor()
    
    # Get video info to calculate frame indices
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    # Calculate evenly distributed frame indices
    if frame_count <= num_frames:
        frame_indices = list(range(frame_count))
    else:
        frame_indices = np.linspace(0, frame_count - 1, num_frames, dtype=int).tolist()
    
    # Extract frames
    keyframes = processor.extract_frames_batch(video_path, frame_indices, target_size)
    
    return keyframes

if __name__ == "__main__":
    # Test GPU video processor
    processor = create_gpu_processor()
    print(f"GPU Processor initialized - GPU available: {processor.use_gpu}")
    
    # Print GPU info
    from .gpu_detector import print_gpu_info
    print_gpu_info()
