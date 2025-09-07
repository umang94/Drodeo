#!/usr/bin/env python3
"""
Music Prompt Generator for Drodeo

Standalone script that analyzes video content and generates descriptive prompts
for music generation APIs like Udio. Uses Step 1 of the Gemini multimodal analysis
pipeline to extract visual characteristics and create music prompts.

Usage:
    python generate_music_prompt.py input_dev/video1.mp4 input_dev/video2.mov
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path to import core modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.gemini_multimodal_analyzer import GeminiMultimodalAnalyzer

def generate_music_prompt_from_videos(video_paths):
    """
    Generate a music prompt based on video content analysis.
    
    Args:
        video_paths: List of paths to video files
        
    Returns:
        str: Formatted music generation prompt
    """
    # Initialize the analyzer
    analyzer = GeminiMultimodalAnalyzer()
    
    if not analyzer.is_available():
        print("❌ Gemini API not available. Please check your GEMINI_API_KEY environment variable.")
        sys.exit(1)
    
    print(f"🎬 Analyzing {len(video_paths)} video(s) for music prompt generation...")
    
    # Use an existing audio file from the music directory
    # The analyzer expects both audio and video, so we'll use a real audio file
    music_files = [f for f in os.listdir("music") if f.endswith(('.mp3', '.m4a', '.wav'))]
    if not music_files:
        print("❌ No audio files found in music/ directory. Please add some music files.")
        sys.exit(1)
    
    audio_path = os.path.join("music", music_files[0])
    print(f"   🎵 Using audio file: {music_files[0]}")
    
    # Run Step 1 multimodal analysis
    result = analyzer.analyze_batch(audio_path, video_paths, "Music Prompt Analysis")
    
    if not result:
        print("❌ Video analysis failed. Please check your video files and try again.")
        sys.exit(1)
    
    # Generate music prompt from the analysis
    prompt = create_music_prompt(result.gemini_reasoning, video_paths)
    return prompt

def create_music_prompt(gemini_reasoning, video_paths):
    """
    Create a concise music generation prompt from Gemini's natural language analysis.
    Uses Gemini to generate a Udio-friendly prompt without video references.
    
    Args:
        gemini_reasoning: Natural language analysis from Gemini
        video_paths: List of video file paths for context
        
    Returns:
        str: Concise music prompt ready for Udio
    """
    # Use Gemini to generate a concise, Udio-friendly prompt
    from core.gemini_multimodal_analyzer import GeminiMultimodalAnalyzer
    
    analyzer = GeminiMultimodalAnalyzer()
    
    # Create a specialized prompt for Gemini to generate concise music description
    music_prompt_request = f"""
Based on this video content analysis:
{gemini_reasoning}

Generate a concise music prompt suitable for Udio music generation. Include only:
- Duration in seconds
- BPM/tempo
- Genre/style  
- Instrumentation
- Mood/energy profile
- Musical structure (intro, verse, chorus, etc.)

Output ONLY the music prompt text itself, without any additional explanations, video references, or file names.
Keep it under 200 characters and make it ready to copy-paste into Udio.
"""
    
    try:
        # Use Gemini to generate the concise prompt
        response = analyzer.model.generate_content(music_prompt_request)
        concise_prompt = response.text.strip()
        
        # Ensure it's properly formatted and concise
        if len(concise_prompt) > 250:
            # If too long, create a simple fallback
            concise_prompt = "Create atmospheric instrumental music suitable for aerial landscape videos"
        
        return concise_prompt
        
    except Exception as e:
        # Fallback to a simple prompt if Gemini fails
        return "Create atmospheric instrumental music with moderate tempo for video background"

def main():
    """Main function to handle command-line arguments and generate music prompt."""
    parser = argparse.ArgumentParser(description='Generate music prompts from video content analysis')
    parser.add_argument('videos', nargs='+', help='Video files to analyze for music prompt generation')
    
    args = parser.parse_args()
    
    # Check if video files exist
    existing_videos = []
    for video_path in args.videos:
        if os.path.exists(video_path):
            existing_videos.append(video_path)
        else:
            print(f"⚠️  Video file not found: {video_path}")
    
    if not existing_videos:
        print("❌ No valid video files provided. Please check your file paths.")
        sys.exit(1)
    
    # Generate and display the music prompt
    try:
        music_prompt = generate_music_prompt_from_videos(existing_videos)
        print("\n" + "="*80)
        print("🎵 MUSIC GENERATION PROMPT READY FOR UDIO/OTHER SERVICES")
        print("="*80)
        print(music_prompt)
        print("="*80)
        print("\n📋 Copy the prompt above and use it with your preferred music generation service.")
        
    except Exception as e:
        print(f"❌ Error generating music prompt: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
