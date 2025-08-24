#!/usr/bin/env python3
"""
Test script for Freesound integration

This script tests the Freesound API integration without requiring an actual API key.
It validates the integration logic and fallback behavior.
"""

import os
import sys
from music_downloader import MusicDownloader

def test_freesound_integration():
    """Test Freesound integration functionality"""
    print("🎵 Testing Freesound Integration")
    print("=" * 50)
    
    # Initialize music downloader
    downloader = MusicDownloader()
    
    # Test 1: Check search terms mapping
    print("\n1. Testing theme search terms mapping:")
    themes = ['happy', 'exciting', 'peaceful', 'adventure', 'cinematic']
    for theme in themes:
        search_terms = downloader._get_freesound_search_terms(theme)
        print(f"   {theme}: {search_terms[:3]}")  # Show first 3 terms
    
    # Test 2: Test API integration (without actual API key)
    print("\n2. Testing API integration (no API key):")
    api_key = os.getenv('FREESOUND_API_KEY')
    if api_key:
        print(f"   ✅ Freesound API key found: {api_key[:10]}...")
        
        # Test actual API call
        try:
            result = downloader._download_from_freesound('happy', 60)
            if result:
                print(f"   ✅ Successfully downloaded: {os.path.basename(result)}")
            else:
                print("   ⚠️  No suitable tracks found")
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
    else:
        print("   ⚠️  No Freesound API key found (expected for testing)")
        print("   ℹ️  To test with real API:")
        print("      1. Get API key from https://freesound.org/apiv2/apply/")
        print("      2. Add FREESOUND_API_KEY=your_key to .env file")
    
    # Test 3: Test fallback behavior
    print("\n3. Testing fallback behavior:")
    for theme in ['happy', 'peaceful']:
        music_path = downloader.get_theme_music(theme, 60)
        if music_path:
            filename = os.path.basename(music_path)
            print(f"   {theme}: ✅ {filename}")
        else:
            print(f"   {theme}: ❌ No music available")
    
    # Test 4: Test music library
    print("\n4. Testing music library:")
    music_library = downloader.list_available_music()
    total_files = sum(len(files) for files in music_library.values())
    print(f"   Total music files: {total_files}")
    
    for theme, files in music_library.items():
        status = "✅" if files else "❌"
        count = len(files)
        print(f"   {theme}: {status} {count} file(s)")
    
    # Test 5: Test music info
    print("\n5. Testing music info:")
    sample_music = downloader._get_fallback_music()
    if sample_music:
        info = downloader.get_music_info(sample_music)
        print(f"   Sample file: {info['filename']}")
        print(f"   Size: {info['size_mb']:.2f} MB")
        print(f"   Exists: {info['exists']}")
    
    print("\n" + "=" * 50)
    print("🎉 Freesound integration test completed!")
    
    # Summary
    has_api_key = bool(os.getenv('FREESOUND_API_KEY'))
    has_fallback = bool(downloader._get_fallback_music())
    
    print(f"\n📊 Integration Status:")
    print(f"   API Key Available: {'✅' if has_api_key else '⚠️'}")
    print(f"   Fallback Music: {'✅' if has_fallback else '❌'}")
    print(f"   System Ready: {'✅' if has_fallback else '❌'}")
    
    if not has_api_key:
        print(f"\n💡 To enable Freesound downloads:")
        print(f"   1. Visit: https://freesound.org/apiv2/apply/")
        print(f"   2. Create account and apply for API access")
        print(f"   3. Add FREESOUND_API_KEY=your_key to .env file")
    
    return has_fallback

if __name__ == "__main__":
    success = test_freesound_integration()
    sys.exit(0 if success else 1)
