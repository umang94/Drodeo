#!/usr/bin/env python3
"""
Drodeo Main Entry Point

Simplified, reliable entry point with built-in validation and smart caching.
Integrates the two-step Gemini pipeline directly with robust setup checks.

Usage:
    python main.py                 # Normal operation with cached videos
    python main.py --fast-test     # Fast testing with limited videos
    python main.py --force-setup   # Force recreation of development videos
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST to ensure config modules work correctly
load_dotenv(override=False)

# Import validation and pipeline functions
from src.utils.validation import validate_environment, validate_directories, setup_development_videos
from src.core.pipeline import run_two_step_pipeline

def main():
    """Main function handling validation and pipeline execution."""
    parser = argparse.ArgumentParser(description='Drodeo Two-Step Pipeline with Validation')
    parser.add_argument('--fast-test', action='store_true', 
                       help='Fast test mode with limited videos (3 videos max)')
    parser.add_argument('--force-setup', action='store_true',
                       help='Force recreation of development videos (ignore cache)')
    
    args = parser.parse_args()
    
    print("🎬 Drodeo Main - Simplified & Reliable")
    print("=" * 50)
    print("🤖 Two-Step Gemini Pipeline Integration")
    print("📊 Built-in Validation & Smart Caching")
    print(f"🚀 Fast test mode: {'✅ Enabled' if args.fast_test else '❌ Disabled'}")
    print(f"🔄 Force setup: {'✅ Enabled' if args.force_setup else '❌ Disabled'}")
    
    # Step 1: Environment Validation
    print("\n🔍 Step 1: Environment Validation...")
    if not validate_environment():
        print("❌ Environment validation failed. Please fix the issues above.")
        sys.exit(1)
    print("   ✅ Environment validation passed")
    
    # Step 2: Directory Structure Validation
    print("\n📂 Step 2: Directory Validation...")
    if not validate_directories():
        print("❌ Directory validation failed. Please fix the issues above.")
        sys.exit(1)
    print("   ✅ Directory validation passed")
    
    # Step 3: Smart Video Setup (cached by default)
    print("\n🎥 Step 3: Video Setup (smart caching)...")
    if not setup_development_videos(force=args.force_setup):
        print("❌ Video setup failed. Please check input/ directory and FFmpeg installation.")
        sys.exit(1)
    print("   ✅ Video setup completed")
    
    # Step 4: Run Two-Step Pipeline
    print("\n🚀 Step 4: Starting Two-Step Gemini Pipeline...")
    success = run_two_step_pipeline(fast_test=args.fast_test)
    
    if success:
        print("\n✅ Pipeline completed successfully!")
        print("   Check output/ directory for generated videos")
        print("   🎉 Ready for your next creative project!")
    else:
        print("\n❌ Pipeline failed. Check the error messages above for details.")
        print("   Common issues:")
        print("   - Missing or invalid Gemini API key")
        print("   - Network connectivity issues")
        print("   - Insufficient video files in input_dev/")
        print("   - FFmpeg not installed or not in PATH")
        sys.exit(1)

if __name__ == "__main__":
    main()
