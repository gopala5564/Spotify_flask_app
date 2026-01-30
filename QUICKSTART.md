# Quick Start Guide - Spotify Scraper

## 5-Minute Setup

### Step 1: Navigate to Project

```bash
cd d:\Python_projects\spotify_scraper
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Expected time: 2-3 minutes

### Step 3: Get Spotify Credentials

1. Go to https://developer.spotify.com/dashboard
2. Create a free account or log in
3. Create a new application
4. Copy your **Client ID** and **Client Secret**

### Step 4: Configure Credentials

```bash
# Copy the example env file
copy .env.example .env

# Edit .env with your credentials
# Open in your favorite editor and add:
# SPOTIFY_CLIENT_ID=your_client_id_here
# SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### Step 5: Test the Installation

```bash
# Run with a small sample (10 playlists)
python scripts/fetch_playlists.py 10
```

Expected time: 5-10 minutes
This will create:
- `data/spotify_data.db` (database)
- `data/spotify_data_playlists.csv`
- `data/spotify_data_tracks.csv`
- `data/spotify_data_playlists.json`
- `data/spotify_data_tracks.json`

## Common Commands

### Fetch Default 500 Playlists

```bash
python scripts/fetch_playlists.py
```

### Fetch Custom Number

```bash
python scripts/fetch_playlists.py 100    # 100 playlists
python scripts/fetch_playlists.py 1000   # 1000 playlists
```

### Query Database

```bash
python scripts/query_database.py
```

Interactive menu:
1. View database statistics
2. See top playlists
3. Find popular tracks
4. Audio analysis
5. Search tracks
6. Export data

### Check Status

```bash
# View log file
tail -f logs/spotify_scraper.log

# Check output files
dir data/

# View configuration
python -c "from spotify_scraper.config import get_config_summary; import json; print(json.dumps(get_config_summary(), indent=2))"
```

## Troubleshooting

### "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"

```bash
# Check .env file exists
dir .env

# Check format (no spaces around =)
type .env
```

Should show:
```
SPOTIFY_CLIENT_ID=abc123...
SPOTIFY_CLIENT_SECRET=xyz789...
```

### HTTP 403 Errors (Rate Limited)

Edit `.env`:
```bash
# Original
API_DELAY_BETWEEN_REQUESTS=1.5
AUDIO_FEATURES_BATCH_SIZE=50

# Conservative (slower but safer)
API_DELAY_BETWEEN_REQUESTS=3.0
AUDIO_FEATURES_BATCH_SIZE=30
```

Then try again. See `docs/RATE_LIMITING.md` for more options.

### Database Already Exists

```bash
# Delete old database (optional)
del data/spotify_data.db

# Run again - it will create a fresh database
python scripts/fetch_playlists.py
```

## Performance Tips

- **Faster**: Skip audio features by setting `FETCH_AUDIO_FEATURES=False` in `.env`
- **Safer**: Use conservative rate limiting
- **Smarter**: Run during off-peak hours (2-6 AM)
- **Efficient**: Reduce workers: `PLAYLIST_FETCH_MAX_WORKERS=1`

## What Gets Downloaded?

### Database (`spotify_data.db`)
- All playlists (name, owner, followers, etc.)
- All tracks (name, artist, album, popularity)
- Audio features (danceability, energy, tempo, etc.)

### CSV Files
- `spotify_data_playlists.csv` - Playlist metadata
- `spotify_data_tracks.csv` - Track details with playlist info

### JSON Files
- `spotify_data_playlists.json` - Playlists in JSON
- `spotify_data_tracks.json` - Tracks in JSON

## Example Workflows

### Workflow 1: Quick Sample

```bash
# Small test run
python scripts/fetch_playlists.py 50

# Takes ~5 minutes
# Creates sample database with 500-1000 tracks
```

### Workflow 2: Full Dataset

```bash
# Get all available data
python scripts/fetch_playlists.py 500

# Takes ~1-2 hours
# Creates database with 5000+ tracks
```

### Workflow 3: Analysis

```bash
# After fetching, query the data
python scripts/query_database.py

# Menu options:
# - Top playlists by followers
# - Most popular tracks
# - Most danceable songs
# - Audio feature statistics
# - Search for specific tracks
```

### Workflow 4: Export to Excel

```bash
# After fetching, get CSV files
# Open in Excel: data/spotify_data_tracks.csv
# Sort, filter, analyze
```

## Project Layout After First Run

```
spotify_scraper/
├── data/                          # ← Generated after first run
│   ├── spotify_data.db            #   SQLite database
│   ├── spotify_data_playlists.csv
│   ├── spotify_data_playlists.json
│   ├── spotify_data_tracks.csv
│   └── spotify_data_tracks.json
│
├── logs/                          # ← Generated after first run
│   └── spotify_scraper.log
│
├── src/spotify_scraper/           # ← Source code
├── scripts/                       # ← Executable scripts
├── docs/                          # ← Documentation
├── .env                           # ← Your credentials (create from .env.example)
└── README.md
```

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main documentation and reference |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical design and structure |
| [RATE_LIMITING.md](docs/RATE_LIMITING.md) | Troubleshooting rate limits |
| [UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md) | Changes from old version |

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure credentials
3. ✅ Run test with `python scripts/fetch_playlists.py 10`
4. ✅ Run full fetch with `python scripts/fetch_playlists.py`
5. ✅ Explore data with `python scripts/query_database.py`
6. ✅ Analyze results in `data/` folder

## Support

- Check logs: `tail logs/spotify_scraper.log`
- Read docs: See files in `docs/` folder
- Adjust config: Edit `.env` file
- Review README: [README.md](README.md)

---

**Total Setup Time**: 5-10 minutes ⏱️
**Total Data Collection**: 1-2 hours ⏳
**Result**: 5000+ tracks from 500+ playlists ready for analysis! 📊
