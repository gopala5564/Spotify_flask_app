# Spotify Scraper

A comprehensive Python tool for scraping Spotify data including playlists, tracks, and audio features. Data is automatically stored in a SQLite database and exported to CSV/JSON formats.

## Features

- 🎵 **Playlist Discovery** - Fetch 500+ playlists using 17 different search queries
- 📊 **Track Extraction** - Get all tracks from playlists with complete metadata
- 🎚️ **Audio Analysis** - Fetch 12 audio features (danceability, energy, tempo, etc.)
- 💾 **Database Storage** - Automatic SQLite database with relationships
- 📁 **Multi-format Export** - Save to CSV and JSON
- 🚀 **Rate Limiting** - Built-in retry logic and configurable delays
- 📈 **Concurrent Processing** - Multi-threaded playlist fetching
- 🔍 **Query Tools** - Interactive database querying interface

## Quick Start

### 1. Installation

```bash
# Clone or download the repository
cd spotify_scraper

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Get Spotify Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a free Spotify account (if you don't have one)
3. Create a new application
4. Copy your **Client ID** and **Client Secret**

### 3. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
# SPOTIFY_CLIENT_ID=your_client_id_here
# SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 4. Run the Scraper

```bash
# Fetch default 500 playlists
python scripts/fetch_playlists.py

# Or fetch a specific number of playlists
python scripts/fetch_playlists.py 200
```

## Project Structure

```
spotify_scraper/
├── src/spotify_scraper/          # Main package
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   └── manager.py            # Database operations
│   ├── api/
│   │   ├── __init__.py
│   │   └── client.py             # Spotify API client
│   └── utils/
│       ├── __init__.py
│       └── export.py             # Export utilities
├── scripts/
│   ├── fetch_playlists.py        # Main fetch script
│   └── query_database.py         # Query tool
├── config/                        # Configuration files
├── data/                          # Output data (created on first run)
├── logs/                          # Log files (created on first run)
├── pyproject.toml               # Project metadata
├── setup.py                      # Setup script
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

## Configuration

Edit `.env` file to customize behavior:

```env
# Required
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Optional - Rate Limiting (adjust if you get HTTP 403)
API_DELAY_BETWEEN_REQUESTS=1.5
API_DELAY_BETWEEN_BATCHES=2.0
AUDIO_FEATURES_BATCH_SIZE=50
PLAYLIST_FETCH_MAX_WORKERS=3

# Optional - Data Fetching
DEFAULT_NUM_PLAYLISTS=500
TRACKS_PER_PLAYLIST=100

# Optional - Features
LOG_LEVEL=INFO
```

## Rate Limiting

If you encounter HTTP 403 errors, try these adjustments in `.env`:

### Conservative Settings (Guaranteed to work)

```env
API_DELAY_BETWEEN_REQUESTS=3.0
API_DELAY_BETWEEN_BATCHES=4.0
AUDIO_FEATURES_BATCH_SIZE=20
PLAYLIST_FETCH_MAX_WORKERS=1
```

### Skip Audio Features (Fastest)

```env
# Edit src/spotify_scraper/config.py
FETCH_AUDIO_FEATURES=False
```

See [RATE_LIMITING_GUIDE.md](../RATE_LIMITING_GUIDE.md) for detailed troubleshooting.

## Usage Examples

### Fetch Data

```bash
# Fetch 500 playlists (default)
python scripts/fetch_playlists.py

# Fetch 100 playlists
python scripts/fetch_playlists.py 100

# Fetch 1000 playlists (takes longer)
python scripts/fetch_playlists.py 1000
```

### Query Database

```bash
# Interactive query tool
python scripts/query_database.py
```

Menu options:
1. Database Statistics
2. Top 20 Playlists by Followers
3. Top 20 Tracks by Popularity
4. Most Danceable Tracks
5. Highest Energy Tracks
6. Most Acoustic Tracks
7. Audio Features Statistics
8. Search Tracks
9. Export Playlists to CSV
10. Export Tracks to CSV

### Use as Library

```python
from spotify_scraper import SpotifyAPIClient, DatabaseManager
from spotify_scraper.config import DATABASE_PATH

# Initialize API client
api = SpotifyAPIClient()

# Fetch playlists
result = api.fetch_playlists_with_tracks(num_playlists=100)
playlists = result['playlists']

# Fetch tracks
tracks_result = api.fetch_tracks_from_playlists(playlists)
all_tracks = tracks_result['all_tracks']

# Get audio features
audio_features = api.get_audio_features_batch(
    [t['track_id'] for t in all_tracks]
)

# Save to database
db = DatabaseManager(DATABASE_PATH)
for playlist in playlists:
    db.insert_playlist(playlist)
for track in all_tracks:
    db.insert_track(track)
db.commit()
```

## Output Files

After running the script, you'll find:

```
data/
├── spotify_data_playlists.csv
├── spotify_data_playlists.json
├── spotify_data_tracks.csv
├── spotify_data_tracks.json
└── spotify_data.db                 # SQLite database
```

## Database Schema

### playlists table
- `playlist_id` (PRIMARY KEY)
- `name`, `description`
- `owner`, `owner_id`
- `total_tracks`, `followers`
- `public`, `collaborative`
- `external_url`, `image_url`
- `created_at`, `updated_at`

### tracks table
- `track_id` (PRIMARY KEY)
- `playlist_id` (FOREIGN KEY)
- `name`, `artist`, `artist_id`
- `album`, `album_id`
- `release_date`, `duration_ms`, `duration_minutes`
- `popularity`, `explicit`
- `isrc`, `spotify_url`
- `added_at`, `added_by`
- `created_at`

### audio_features table
- `track_id` (PRIMARY KEY, FOREIGN KEY)
- `danceability`, `energy`, `acousticness`
- `instrumentalness`, `liveness`, `valence`
- `tempo`, `loudness`, `key`, `mode`
- `speechiness`, `time_signature`
- `created_at`

## Audio Features Explained

- **Danceability** (0-1): How suitable for dancing (rhythm)
- **Energy** (0-1): Intensity and activity level
- **Acousticness** (0-1): Likelihood the track is acoustic
- **Instrumentalness** (0-1): Probability track has no vocals
- **Liveness** (0-1): Presence of audience/live performance
- **Valence** (0-1): Musical positivity/happiness
- **Tempo** (BPM): Beats per minute
- **Loudness** (dB): Overall loudness level
- **Key** (0-11): Pitch class (C to B)
- **Mode** (0-1): Major (1) or minor (0)
- **Speechiness** (0-1): Presence of spoken words

## Performance

With default settings (500 playlists):
- **Playlist fetch**: 5-10 minutes
- **Track fetch**: 15-20 minutes
- **Audio features**: 30-60 minutes
- **Total**: ~50-90 minutes

## Troubleshooting

### "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
- Check that `.env` file exists in project root
- Verify credentials are correctly copied from Dashboard
- Make sure they're in the correct order

### HTTP 403 "Forbidden" Errors
- See [RATE_LIMITING_GUIDE.md](../RATE_LIMITING_GUIDE.md)
- Increase `API_DELAY_BETWEEN_REQUESTS`
- Reduce `AUDIO_FEATURES_BATCH_SIZE`
- Run during off-peak hours

### Database locked errors
- Ensure only one instance of the script is running
- Wait for current run to complete before starting new one

### Database recovery
- Data is saved to `data/spotify_data.db`
- You can query existing data while script runs
- Re-running will skip duplicate playlists

## Contributing

Contributions welcome! Areas for improvement:
- Additional search queries
- Advanced filtering options
- Data visualization
- Performance optimizations
- Test coverage

## License

MIT License - See LICENSE file for details

## Resources

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotipy Documentation](https://spotipy.readthedocs.io/)
- [Audio Features Guide](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)

## Support

For issues, questions, or suggestions:
1. Check the [RATE_LIMITING_GUIDE.md](../RATE_LIMITING_GUIDE.md)
2. Review logs in `logs/spotify_scraper.log`
3. Check Spotify API status at [developer.spotify.com](https://developer.spotify.com/status)
