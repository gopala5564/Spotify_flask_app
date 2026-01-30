#!/usr/bin/env python
"""
Setup script for Spotify Scraper
"""

from setuptools import setup, find_packages

setup(
    name="spotify-scraper",
    version="1.0.0",
    description="A comprehensive tool for scraping Spotify data",
    long_description=open("README.md").read() if __name__ != "__main__" else "",
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/spotify-scraper",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "spotipy>=2.22.0",
        "python-dotenv>=0.19.0",
        "pandas>=1.3.0",
        "requests>=2.25.0",
        "tabulate>=0.8.9",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "spotify-scraper=spotify_scraper.cli:main",
        ],
    },
)
