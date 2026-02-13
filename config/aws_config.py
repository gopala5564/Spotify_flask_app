"""AWS configuration for Spotify ETL"""

import os
from dotenv import load_dotenv

load_dotenv()

# AWS Settings
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
DATA_LAKE_BUCKET = os.getenv('DATA_LAKE_BUCKET')

# Lambda Settings
LAMBDA_TIMEOUT = int(os.getenv('LAMBDA_TIMEOUT', '300'))
LAMBDA_MEMORY = int(os.getenv('LAMBDA_MEMORY', '3008'))

# Spotify Settings (shared with Spotipy client)
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# ETL Settings
ETL_BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', '100'))
ETL_SCHEDULE_CRON = os.getenv('ETL_SCHEDULE_CRON', 'cron(0 2 * * ? *)')  # Daily at 2 AM UTC

# Validation
if not DATA_LAKE_BUCKET:
    raise ValueError("DATA_LAKE_BUCKET environment variable is required")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("Spotify credentials (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET) are required")
