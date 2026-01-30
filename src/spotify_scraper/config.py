"""
Configuration Management for Spotify Scraper
Centralized settings for API rate limiting, database, and behavior
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_NAME = os.getenv('SPOTIFY_DB_NAME', 'spotify_data.db')
DATABASE_PATH = DATA_DIR / DATABASE_NAME
DATABASE_TIMEOUT = 30.0  # Connection timeout in seconds

# ============================================================================
# SPOTIFY API CONFIGURATION
# ============================================================================
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError(
        "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file. "
        "Get credentials from https://developer.spotify.com/dashboard"
    )

# ============================================================================
# API RATE LIMITING CONFIGURATION
# ============================================================================
# Adjust these values if you experience rate limiting issues (HTTP 403)
API_DELAY_BETWEEN_REQUESTS = float(os.getenv('API_DELAY_BETWEEN_REQUESTS', '1.5'))
API_DELAY_BETWEEN_BATCHES = float(os.getenv('API_DELAY_BETWEEN_BATCHES', '2.0'))
AUDIO_FEATURES_BATCH_SIZE = int(os.getenv('AUDIO_FEATURES_BATCH_SIZE', '50'))
PLAYLIST_FETCH_MAX_WORKERS = int(os.getenv('PLAYLIST_FETCH_MAX_WORKERS', '3'))

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 2s, 4s, 8s

# ============================================================================
# DATA FETCHING CONFIGURATION
# ============================================================================
DEFAULT_NUM_PLAYLISTS = int(os.getenv('DEFAULT_NUM_PLAYLISTS', '500'))
TRACKS_PER_PLAYLIST = int(os.getenv('TRACKS_PER_PLAYLIST', '100'))

# Search queries for discovering playlists
PLAYLIST_SEARCH_QUERIES = [
    '',  # Empty query for trending
    'pop',
    'hip hop',
    'rock',
    'jazz',
    'electronic',
    'indie',
    'workout',
    'relax',
    'party',
    'love',
    'sleep',
    'focus',
    'discover',
    'new',
    'viral',
    'trending'
]

# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================
EXPORT_FORMATS = ['csv', 'json']  # Supported export formats
OUTPUT_PREFIX = 'spotify_data'

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOGS_DIR / 'spotify_scraper.log'

# ============================================================================
# FEATURE FLAGS
# ============================================================================
FETCH_AUDIO_FEATURES = False  # Set to False to skip audio features (faster)
SAVE_TO_DATABASE = True      # Save to SQLite database
EXPORT_TO_CSV = True         # Export to CSV files
EXPORT_TO_JSON = True        # Export to JSON files

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================
def get_config_summary():
    """Get a summary of current configuration"""
    return {
        'database': str(DATABASE_PATH),
        'api_delay_between_requests': API_DELAY_BETWEEN_REQUESTS,
        'api_delay_between_batches': API_DELAY_BETWEEN_BATCHES,
        'audio_features_batch_size': AUDIO_FEATURES_BATCH_SIZE,
        'playlist_fetch_workers': PLAYLIST_FETCH_MAX_WORKERS,
        'default_num_playlists': DEFAULT_NUM_PLAYLISTS,
        'fetch_audio_features': FETCH_AUDIO_FEATURES,
        'export_formats': EXPORT_FORMATS,
    }

def validate_config():
    """Validate configuration and raise errors if needed"""
    errors = []
    
    if not SPOTIFY_CLIENT_ID:
        errors.append("SPOTIFY_CLIENT_ID not set")
    if not SPOTIFY_CLIENT_SECRET:
        errors.append("SPOTIFY_CLIENT_SECRET not set")
    
    if AUDIO_FEATURES_BATCH_SIZE > 100:
        errors.append("AUDIO_FEATURES_BATCH_SIZE cannot exceed 100")
    if AUDIO_FEATURES_BATCH_SIZE < 1:
        errors.append("AUDIO_FEATURES_BATCH_SIZE must be at least 1")
    
    if API_DELAY_BETWEEN_REQUESTS < 0:
        errors.append("API_DELAY_BETWEEN_REQUESTS cannot be negative")
    if API_DELAY_BETWEEN_BATCHES < 0:
        errors.append("API_DELAY_BETWEEN_BATCHES cannot be negative")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SPOTIFY SCRAPER CONFIGURATION")
    print("="*80)
    for key, value in get_config_summary().items():
        print(f"{key:35} : {value}")
    print("="*80 + "\n")
