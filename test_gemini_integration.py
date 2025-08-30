#!/usr/bin/env python3
"""
Test Gemini integration with development videos
"""

import sys
sys.path.append('src')
from core.llm_video_analyzer import GeminiVideoAnalyzer
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

print('=== GEMINI INTEGRATION TEST WITH DEV VIDEOS ===')
print()

# Initialize analyzer
analyzer = GeminiVideoAnalyzer()
print('✅ GeminiVideoAnalyzer initialized')

# Test with two different video formats
test_videos = [
    'input_dev/DJI_0108_dev.MP4',  # Drone footage
    'input_dev/IMG_7840_dev.mov'   # iPhone footage
]

for video_path in test_videos:
    if os.path.exists(video_path):
        print(f'\n📹 Testing with: {video_path}')
        
        # Get video info
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        print(f'   File size: {file_size:.2f} MB')
        
        try:
            start_time = time.time()
            
            # Test comprehensive analysis
            print('   🔍 Running analyze_video_comprehensive...')
            analysis = analyzer.analyze_video_comprehensive(video_path)
            
            processing_time = time.time() - start_time
            
            if analysis:
                print(f'   ✅ Analysis completed in {processing_time:.2f} seconds')
                print(f'   📊 Duration: {analysis.duration:.2f} seconds')
                print(f'   🎵 Music sync segments: {len(analysis.music_sync_segments)}')
                print(f'   ✂️  Beat aligned cuts: {len(analysis.beat_aligned_cuts)}')
                print(f'   🎯 Sync confidence: {analysis.sync_confidence:.2f}')
                print(f'   💰 API cost: ${analysis.api_cost:.4f}')
                
                # Show first music sync segment as example
                if analysis.music_sync_segments:
                    seg = analysis.music_sync_segments[0]
                    print(f'   📝 First segment: {seg.start_time:.1f}s-{seg.end_time:.1f}s, energy: {seg.energy_level}, BPM: {seg.recommended_bpm}')
                
                print(f'   🤖 Gemini reasoning (complete response):')
                print(f'   {"-" * 60}')
                print(f'   {analysis.gemini_reasoning}')
                print(f'   {"-" * 60}')
            else:
                print('   ❌ Analysis returned None')
                
        except Exception as e:
            print(f'   ❌ Error during analysis: {e}')
            import traceback
            traceback.print_exc()
    else:
        print(f'❌ Video not found: {video_path}')

print('\n🎉 Gemini integration test completed!')
