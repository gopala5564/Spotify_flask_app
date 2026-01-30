# Spotify Scraper - Architecture Documentation

## Overview

Spotify Scraper is a modular Python application for collecting and analyzing Spotify data. It follows best practices for Python project organization with separated concerns, configuration management, and extensibility.

## Design Principles

1. **Modularity** - Core functionality is separated into focused modules
2. **Configuration Management** - All settings are centralized and environment-driven
3. **Logging** - Comprehensive logging for debugging and monitoring
4. **Error Handling** - Graceful error handling with retry logic
5. **Extensibility** - Easy to add new features and export formats

## Project Structure

```
spotify_scraper/
├── src/spotify_scraper/          # Main package (installed as library)
│   ├── __init__.py              # Package initialization and exports
│   ├── config.py                # Configuration management
│   │
│   ├── database/                # Database module
│   │   ├── __init__.py
│   │   └── manager.py           # SQLite database operations
│   │
│   ├── api/                     # Spotify API module
│   │   ├── __init__.py
│   │   └── client.py            # Spotify API client
│   │
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       └── export.py            # Data export functions
│
├── scripts/                      # Executable scripts
│   ├── fetch_playlists.py       # Main fetch script
│   └── query_database.py        # Database query interface
│
├── tests/                        # Unit tests (for future)
│
├── docs/                         # Documentation
│   └── RATE_LIMITING.md
│
├── config/                       # Configuration files
│
├── data/                         # Output data (generated)
│   ├── spotify_data.db
│   ├── spotify_data_playlists.csv
│   ├── spotify_data_playlists.json
│   ├── spotify_data_tracks.csv
│   └── spotify_data_tracks.json
│
├── logs/                         # Log files (generated)
│   └── spotify_scraper.log
│
├── pyproject.toml              # Project metadata (modern approach)
├── setup.py                     # Setup script (legacy compatibility)
├── requirements.txt             # Dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # Main documentation
```

## Module Architecture

### 1. Configuration Module (`config.py`)

**Responsibility**: Centralized configuration management

**Key Features**:
- Environment variable loading via `.env`
- Path management
- Validation of configuration
- Rate limiting settings
- Feature flags

**Usage**:
```python
from spotify_scraper.config import (
    DATABASE_PATH,
    SPOTIFY_CLIENT_ID,
    API_DELAY_BETWEEN_REQUESTS
)
```

### 2. Database Module (`database/manager.py`)

**Responsibility**: SQLite database operations

**Key Components**:
- `DatabaseManager` - Main class for database operations

**Capabilities**:
- Table creation with proper schema
- Insert operations (playlists, tracks, audio features)
- Transaction management (commit/rollback)
- Statistics queries
- Custom query execution

**Design Pattern**: Single Responsibility Principle
- Each insert method handles one entity type
- Connection management is encapsulated
- Foreign keys enforce data integrity

**Usage**:
```python
from spotify_scraper.database import DatabaseManager

db = DatabaseManager(db_path)
db.insert_playlist(playlist_data)
db.insert_track(track_data)
db.insert_audio_features(track_id, features)
db.commit()
db.close()
```

### 3. API Module (`api/client.py`)

**Responsibility**: Spotify Web API interactions

**Key Components**:
- `SpotifyAPIClient` - Main API client class

**Methods**:
- `search_playlists()` - Search for playlists
- `get_playlist_tracks()` - Fetch all tracks from a playlist
- `get_audio_features_batch()` - Fetch audio features with retry logic
- `fetch_playlists_with_tracks()` - High-level orchestration
- `fetch_tracks_from_playlists()` - Concurrent track fetching

**Features**:
- Automatic rate limiting
- Exponential backoff retry logic
- Concurrent processing with ThreadPoolExecutor
- Pagination for large result sets
- Batch processing for efficiency

**Error Handling**:
- Try-catch blocks with logging
- Graceful degradation on failures
- Automatic retry with exponential backoff

**Usage**:
```python
from spotify_scraper.api import SpotifyAPIClient

api = SpotifyAPIClient()
playlists = api.fetch_playlists_with_tracks(num_playlists=500)
tracks_result = api.fetch_tracks_from_playlists(playlists)
features = api.get_audio_features_batch(track_ids)
```

### 4. Utils Module (`utils/export.py`)

**Responsibility**: Data export functionality

**Functions**:
- `export_to_csv()` - Export to CSV format
- `export_to_json()` - Export to JSON format

**Features**:
- Column reordering for readability
- Directory creation
- Multiple file output
- Error handling

**Usage**:
```python
from spotify_scraper.utils import export_to_csv, export_to_json

export_to_csv(data, output_dir)
export_to_json(data, output_dir)
```

## Data Flow

```
┌─────────────────────────┐
│   Spotify API           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  SpotifyAPIClient       │
│  - search_playlists()   │
│  - get_playlist_tracks()│
│  - get_audio_features() │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Data Processing        │
│  - Deduplicate          │
│  - Transform            │
│  - Enrich with features │
└────────────┬────────────┘
             │
       ┌─────┴─────┐
       ▼           ▼
   ┌──────┐    ┌──────────────┐
   │ CSV  │    │ JSON         │
   └──────┘    └──────────────┘
       │           │
       └─────┬─────┘
             ▼
        ┌─────────────┐
        │  Database   │
        │  (SQLite)   │
        └─────────────┘
```

## Configuration Priority

1. **Environment Variables** (`.env` file)
2. **Default Values** (in `config.py`)

Example `config.py` defaults:
```python
API_DELAY_BETWEEN_REQUESTS = float(os.getenv('API_DELAY_BETWEEN_REQUESTS', '1.5'))
```

## Rate Limiting Strategy

### Default Behavior

1. **Batch Size**: 50 tracks per request
2. **Delay Between Requests**: 1.5 seconds
3. **Delay Between Batches**: 2.0 seconds
4. **Max Retries**: 3 attempts with exponential backoff

### Exponential Backoff

On failure:
- Attempt 1: Wait 2 seconds (2^1)
- Attempt 2: Wait 4 seconds (2^2)
- Attempt 3: Wait 8 seconds (2^3)
- Fallback: Retry with batch size 20

### Configuration

Adjust in `.env`:
```env
# More conservative (slower, safer)
API_DELAY_BETWEEN_REQUESTS=3.0
AUDIO_FEATURES_BATCH_SIZE=30

# More aggressive (faster, riskier)
API_DELAY_BETWEEN_REQUESTS=1.0
AUDIO_FEATURES_BATCH_SIZE=100
```

## Logging

- **File**: `logs/spotify_scraper.log`
- **Level**: Configurable via `LOG_LEVEL` env variable
- **Format**: `timestamp - module - level - message`
- **Handlers**: File + Console

## Database Schema

### Relationships

```
playlists (1) ──┬─── (∞) tracks
                │
                └─── (?:1) audio_features
                    │
                    └─── [join via track_id]
```

### Key Constraints

- **Primary Keys**: Spotify IDs (unique identifiers)
- **Foreign Keys**: Maintain referential integrity
- **Not Null**: Essential fields like name, artist
- **Defaults**: Created timestamps, boolean flags

## Extensibility Points

### Add New Export Format

1. Create new export function in `utils/export.py`:
```python
def export_to_parquet(data, output_dir):
    # Implementation
    pass
```

2. Update config to include format in `EXPORT_FORMATS`

### Add New API Endpoint

1. Add method to `SpotifyAPIClient`:
```python
def get_artist_info(self, artist_id):
    return self.sp.artist(artist_id)
```

2. Call from main script

### Add Database Entity

1. Add table creation in `DatabaseManager.create_tables()`
2. Add insert method to `DatabaseManager`
3. Call from main script

## Performance Considerations

### Memory

- Playlists: ~100 KB each
- Tracks: ~5 KB each
- Audio Features: ~1 KB each
- 500 playlists × 2000 tracks: ~10 GB peak RAM (with CSV in memory)

### Time

- Playlist search: 5-10 min
- Track fetching: 15-20 min
- Audio features: 30-60 min
- Export: 1-2 min
- Total: 50-90 min

### Optimization Tips

1. **Reduce batch size** if rate limited
2. **Skip audio features** for faster initial run
3. **Run during off-peak hours**
4. **Use conservative rate limits**

## Testing Strategy (Future)

```
tests/
├── test_config.py
├── test_database.py
├── test_api.py
└── test_utils.py
```

## Deployment Options

### Local Development

```bash
pip install -e .
python scripts/fetch_playlists.py
```

### Production (Docker)

```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "scripts/fetch_playlists.py"]
```

### Scheduled Execution (Cron)

```bash
0 2 * * * cd /path/to/spotify_scraper && python scripts/fetch_playlists.py >> logs/cron.log 2>&1
```

## Future Enhancements

1. **Caching** - Cache API responses to reduce requests
2. **Incremental Updates** - Only fetch new/changed playlists
3. **Web UI** - Flask/Django interface for querying
4. **Advanced Analytics** - Genre detection, trend analysis
5. **Real-time Updates** - WebSocket for live data
6. **Multi-format Support** - Parquet, HDF5, PostgreSQL

## Dependencies

- **spotipy**: Spotify API client
- **python-dotenv**: Environment variable management
- **pandas**: Data manipulation
- **requests**: HTTP library
- **tabulate**: Pretty table formatting

## Code Quality

- **Logging**: All operations logged for debugging
- **Error Handling**: Comprehensive try-catch blocks
- **Type Hints**: (Future) Add type annotations
- **Documentation**: Docstrings for all public methods
- **Testing**: Unit tests (future)

## API Interaction Details

### Authentication

- OAuth 2.0 Client Credentials flow
- Credentials stored in `.env`
- Token managed by Spotipy library

### Rate Limits

- Spotify applies rate limiting (429 status)
- Our implementation catches and retries
- Configurable delays respect rate limits

### Data Freshness

- Spotify data updated in real-time
- Playlists refresh frequently (minutes)
- Popularity scores update hourly
- Audio features static per track

## Conclusion

The Spotify Scraper is designed for reliability, maintainability, and extensibility. Its modular architecture allows for easy enhancement while maintaining code quality and separation of concerns.
