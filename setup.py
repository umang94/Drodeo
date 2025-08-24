#!/usr/bin/env python3
"""
Setup script for Drone Video Generator MVP
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Drone Video Generator MVP - Transform raw drone footage into themed videos"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="drone-video-generator",
    version="1.0.0",
    description="AI-powered drone video generator that creates themed videos from raw footage",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Drone Video Generator Team",
    author_email="contact@dronevideogenerator.com",
    url="https://github.com/your-username/drone-video-generator",
    
    # Package configuration
    packages=find_packages(where='.', include=['src*']),
    package_dir={'': '.'},
    py_modules=[
        'main',
        'src.core.video_processor',
        'src.core.ai_analyzer', 
        'src.core.clip_selector',
        'src.editing.video_editor',
        'src.editing.music_downloader',
        'src.utils.cache_manager',
        'src.utils.progress_tracker',
        'src.utils.config',
        'src.tests.test_system'
    ],
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points for command-line usage
    entry_points={
        'console_scripts': [
            'drone-video-generator=main:main',
            'dvg=main:main',
            'dvg-test=test_system:run_all_tests',
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.json', '*.yaml', '*.yml'],
    },
    
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Content Creators",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    
    # Keywords for discoverability
    keywords=[
        "drone", "video", "editing", "ai", "automation", 
        "opencv", "moviepy", "openai", "content-creation",
        "video-processing", "theme-generation", "music-integration"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/your-username/drone-video-generator/issues",
        "Source": "https://github.com/your-username/drone-video-generator",
        "Documentation": "https://github.com/your-username/drone-video-generator/blob/main/README.md",
    },
    
    # Additional metadata
    license="MIT",
    platforms=["any"],
    
    # Optional dependencies for advanced features
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "performance": [
            "psutil>=5.8.0",
        ],
        "full": [
            "pytest>=6.0",
            "pytest-cov>=2.0", 
            "psutil>=5.8.0",
        ]
    },
    
    # Zip safety
    zip_safe=False,
)
