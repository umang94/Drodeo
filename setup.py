#!/usr/bin/env python3
"""
Environment Setup and Validation Script
Checks and installs all dependencies for the Drone Video Generator MVP
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    print("\n🎬 Checking FFmpeg...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ FFmpeg not found")
    system = platform.system().lower()
    if system == "darwin":  # macOS
        print("   Install with: brew install ffmpeg")
    elif system == "linux":
        print("   Install with: sudo apt install ffmpeg  (Ubuntu/Debian)")
        print("                 sudo yum install ffmpeg  (CentOS/RHEL)")
    elif system == "windows":
        print("   Download from: https://ffmpeg.org/download.html")
    return False

def check_virtual_environment():
    """Check if we're in a virtual environment."""
    print("\n🏠 Checking virtual environment...")
    in_venv = (hasattr(sys, 'real_prefix') or 
               (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    
    if in_venv:
        print("✅ Running in virtual environment")
        return True
    else:
        print("⚠️  Not in virtual environment")
        print("   Recommended: python -m venv venv && source venv/bin/activate")
        return False

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("\n📦 Installing Python dependencies...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def test_imports():
    """Test importing key dependencies."""
    print("\n🧪 Testing imports...")
    
    imports_to_test = [
        ('moviepy', 'moviepy.editor'),
        ('opencv', 'cv2'),
        ('numpy', 'numpy'),
        ('openai', 'openai'),
        ('tqdm', 'tqdm'),
        ('requests', 'requests'),
        ('yt-dlp', 'yt_dlp'),
    ]
    
    all_good = True
    for name, module in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name} - {e}")
            all_good = False
    
    return all_good

def check_api_keys():
    """Check if API keys are configured."""
    print("\n🔑 Checking API configuration...")
    
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env file not found")
            print("   Copy .env.example to .env and add your OpenAI API key")
            print("   Command: cp .env.example .env")
        else:
            print("❌ No .env.example file found")
        return False
    
    # Check if .env has OpenAI key
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY=your_openai_api_key_here' in content:
                print("⚠️  OpenAI API key not configured in .env")
                print("   Edit .env and replace 'your_openai_api_key_here' with your actual key")
                return False
            elif 'OPENAI_API_KEY=' in content:
                print("✅ OpenAI API key configured")
                return True
            else:
                print("⚠️  OPENAI_API_KEY not found in .env")
                return False
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return False

def test_cli():
    """Test the command-line interface."""
    print("\n🖥️  Testing CLI...")
    
    if not os.path.exists('main.py'):
        print("❌ main.py not found")
        return False
    
    try:
        result = subprocess.run([sys.executable, 'main.py', '--help'],
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ CLI working")
            return True
        else:
            print(f"❌ CLI error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def main():
    """Run all setup and validation checks."""
    print("🚀 Drone Video Generator - Environment Setup\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("FFmpeg", check_ffmpeg),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Import Tests", test_imports),
        ("API Keys", check_api_keys),
        ("CLI Test", test_cli),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    # Summary
    print("\n" + "="*50)
    print("📋 SETUP SUMMARY")
    print("="*50)
    
    passed = 0
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(checks)} checks")
    
    if passed == len(checks):
        print("\n🎉 All checks passed! Ready to process drone videos.")
        print("\nNext steps:")
        print("1. Add a drone video to test: python main.py --dry-run your_video.mp4")
        print("2. Run actual processing: python main.py your_video.mp4")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above before proceeding.")
        
        # Provide specific next steps
        if not results["FFmpeg"]:
            print("\n🔧 To install FFmpeg:")
            if platform.system().lower() == "darwin":
                print("   brew install ffmpeg")
        
        if not results["Virtual Environment"]:
            print("\n🔧 To create virtual environment:")
            print("   python -m venv venv")
            print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        
        if not results["API Keys"]:
            print("\n🔧 To configure API keys:")
            print("   cp .env.example .env")
            print("   # Edit .env and add your OpenAI API key")

if __name__ == "__main__":
    main()
