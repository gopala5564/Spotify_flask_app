# Spotify Scraper - Flask Web Application

A complete Flask web application for browsing and querying Spotify playlist and track data collected by the scraper.

## Features

### Web Interface
- **Dashboard** - View database statistics and quick links
- **Playlists** - Browse all playlists with search and pagination
- **Playlist Details** - View playlist information and all tracks
- **Tracks** - Browse all tracks with search and pagination

### REST API
- `GET /api/stats` - Database statistics
- `GET /api/playlists` - List playlists with pagination and sorting
- `GET /api/playlists/<id>` - Get playlist details and tracks
- `GET /api/tracks` - List tracks with pagination and sorting
- `GET /api/tracks/<id>` - Get track details
- `GET /api/search?q=query` - Search playlists and tracks

## Installation

1. Install Flask dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install Flask Flask-CORS
```

## Running the Application

From the project root directory:

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000`

## Usage

### Web Interface
- Open your browser and navigate to `http://localhost:5000`
- Use the navigation menu to browse playlists and tracks
- Use search boxes to find specific playlists or tracks
- Click on playlists to view their details and tracks

### API Usage

#### Get Database Statistics
```bash
curl http://localhost:5000/api/stats
```

Response:
```json
{
  "playlists": 500,
  "tracks": 25000,
  "audio_features": 0
}
```

#### List Playlists
```bash
curl "http://localhost:5000/api/playlists?page=1&per_page=20&sort_by=followers"
```

Query Parameters:
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)
- `search` - Search query
- `sort_by` - Sort field: `followers`, `tracks`, `name` (default: followers)

#### List Tracks
```bash
curl "http://localhost:5000/api/tracks?page=1&per_page=50&sort_by=popularity"
```

Query Parameters:
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 50)
- `search` - Search query
- `sort_by` - Sort field: `popularity`, `name`, `artist`, `release_date` (default: popularity)

#### Search Across Data
```bash
curl "http://localhost:5000/api/search?q=drake"
```

Returns matching playlists and tracks.

## Architecture

```
spotify_scraper/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── dashboard.html    # Dashboard page
│   ├── playlists.html    # Playlists list page
│   ├── playlist_detail.html  # Playlist details page
│   ├── tracks.html       # Tracks list page
│   ├── 404.html          # 404 error page
│   └── 500.html          # 500 error page
├── static/               # Static files
│   ├── style.css         # Custom CSS (Spotify theme)
│   └── script.js         # JavaScript utilities
└── requirements.txt      # Python dependencies
```

## Features

### Dashboard
- Quick overview of database statistics
- Number of playlists, tracks, and audio features
- Coverage percentage of audio features
- Quick links to browse data

### Playlists
- Paginated list of all playlists
- Sort by followers, tracks, or name
- Search by playlist name or owner
- View playlist details including all tracks

### Tracks
- Paginated list of all tracks
- View by popularity
- Search by track name, artist, or album
- Track metadata including release date and explicit content indicator

### Responsive Design
- Mobile-friendly interface using Bootstrap 5
- Works on desktop, tablet, and mobile devices
- Spotify-themed styling with green accent colors

## Customization

### Styling
Edit `static/style.css` to customize the appearance. The theme uses:
- Primary color: `#1DB954` (Spotify green)
- Dark background: `#191414`

### Database Queries
Edit `app.py` to modify database queries or add new endpoints.

### Templates
Edit files in `templates/` to change page layouts and content.

## Logging

Application logs are saved to `logs/flask_app.log`

## Performance Tips

- Use pagination when browsing large datasets
- Use the API for programmatic access
- Consider adding caching for frequently accessed data
- API responses are JSON for easy integration with other applications

## Development

### Enable Debug Mode
The app runs with `debug=True` by default. For production, change this in `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Adding New Routes
1. Add a new route function with `@app.route()` decorator
2. Create a template in `templates/` if needed
3. Add navigation link to `templates/base.html`

### Adding New API Endpoints
1. Add a new route with `@app.route('/api/...')` decorator
2. Return JSON response with `jsonify()`
3. Document the endpoint in this README

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, change it in `app.py`:
```python
app.run(debug=True, host='127.0.0.1', port=5001)
```

### Database Connection Error
Ensure the database file exists at `data/spotify_data.db`
Run the scraper first: `python scripts/fetch_playlists.py`

### Template Not Found
Ensure all template files are in the `templates/` directory

## Future Enhancements

- [ ] Authentication and user accounts
- [ ] Favorites/bookmarks
- [ ] Export functionality
- [ ] Advanced filtering and analytics
- [ ] Real-time data updates
- [ ] WebSocket support for live search
