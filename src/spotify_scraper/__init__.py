"""
Spotify Scraper Package
A comprehensive tool for scraping Spotify data including playlists, tracks, and audio features
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Spotify API data scraper with database storage"

from .config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    DATABASE_PATH,
    get_config_summary,
    validate_config
)
from .database.manager import DatabaseManager
from .api.client import SpotifyAPIClient

__all__ = [
    'DatabaseManager',
    'SpotifyAPIClient',
    'SPOTIFY_CLIENT_ID',
    'SPOTIFY_CLIENT_SECRET',
    'DATABASE_PATH',
    'get_config_summary',
    'validate_config'
]
