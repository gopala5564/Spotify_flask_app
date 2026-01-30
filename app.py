"""
Flask Web Application for Spotify Scraper
Provides dashboard, web UI, and REST API for browsing scraped data
"""

import logging
from pathlib import Path
import sys

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from spotify_scraper.database import DatabaseManager
from spotify_scraper.config import DATABASE_PATH, DATA_DIR, LOGS_DIR

# Setup logging
LOG_FILE = LOGS_DIR / 'flask_app.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize database manager
db_manager = None

def get_db():
    """Get or create database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(str(DATABASE_PATH))
    return db_manager


@app.before_request
def before_request():
    """Initialize database connection before each request"""
    get_db()


@app.teardown_appcontext
def teardown_db(exception):
    """Close database connection after request"""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None


# ============================================================================
# ROUTES - WEB INTERFACE
# ============================================================================

@app.route('/')
def dashboard():
    """Dashboard with statistics"""
    try:
        db = get_db()
        stats = db.get_stats()
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return f"Error: {e}", 500


@app.route('/playlists')
def playlists():
    """Browse playlists"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        per_page = 20
        
        db = get_db()
        
        if search:
            # Search playlists by name
            playlists_data = db.execute_query(
                "SELECT * FROM playlists WHERE name LIKE ? ORDER BY followers DESC LIMIT ? OFFSET ?",
                (f"%{search}%", per_page, (page - 1) * per_page)
            )
            total = db.execute_query(
                "SELECT COUNT(*) as count FROM playlists WHERE name LIKE ?",
                (f"%{search}%",)
            )[0]['count']
        else:
            playlists_data = db.execute_query(
                "SELECT * FROM playlists ORDER BY followers DESC LIMIT ? OFFSET ?",
                (per_page, (page - 1) * per_page)
            )
            total = db.execute_query("SELECT COUNT(*) as count FROM playlists")[0]['count']
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template(
            'playlists.html',
            playlists=playlists_data,
            page=page,
            total_pages=total_pages,
            search=search,
            total=total
        )
    except Exception as e:
        logger.error(f"Error loading playlists: {e}")
        return f"Error: {e}", 500


@app.route('/playlists/<playlist_id>')
def playlist_detail(playlist_id):
    """View playlist details and tracks"""
    try:
        db = get_db()
        
        # Get playlist info
        playlist = db.execute_query(
            "SELECT * FROM playlists WHERE playlist_id = ?",
            (playlist_id,)
        )
        
        if not playlist:
            return "Playlist not found", 404
        
        playlist = playlist[0]
        
        # Get tracks in this playlist
        tracks = db.execute_query(
            """
            SELECT t.* FROM tracks t
            WHERE t.playlist_id = ?
            ORDER BY t.added_at DESC
            """,
            (playlist_id,)
        )
        
        return render_template(
            'playlist_detail.html',
            playlist=playlist,
            tracks=tracks
        )
    except Exception as e:
        logger.error(f"Error loading playlist detail: {e}")
        return f"Error: {e}", 500


@app.route('/tracks')
def tracks():
    """Browse all tracks"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        per_page = 50
        
        db = get_db()
        
        if search:
            # Search tracks by name or artist
            tracks_data = db.execute_query(
                """
                SELECT * FROM tracks
                WHERE name LIKE ? OR artist LIKE ?
                ORDER BY popularity DESC
                LIMIT ? OFFSET ?
                """,
                (f"%{search}%", f"%{search}%", per_page, (page - 1) * per_page)
            )
            total = db.execute_query(
                """
                SELECT COUNT(*) as count FROM tracks
                WHERE name LIKE ? OR artist LIKE ?
                """,
                (f"%{search}%", f"%{search}%")
            )[0]['count']
        else:
            tracks_data = db.execute_query(
                "SELECT * FROM tracks ORDER BY popularity DESC LIMIT ? OFFSET ?",
                (per_page, (page - 1) * per_page)
            )
            total = db.execute_query("SELECT COUNT(*) as count FROM tracks")[0]['count']
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template(
            'tracks.html',
            tracks=tracks_data,
            page=page,
            total_pages=total_pages,
            search=search,
            total=total
        )
    except Exception as e:
        logger.error(f"Error loading tracks: {e}")
        return f"Error: {e}", 500


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/stats')
def api_stats():
    """Get database statistics"""
    try:
        db = get_db()
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlists')
def api_playlists():
    """API endpoint to get playlists"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        sort_by = request.args.get('sort_by', 'followers', type=str)
        
        # Validate sort_by
        valid_sorts = ['followers', 'tracks', 'name']
        if sort_by not in valid_sorts:
            sort_by = 'followers'
        
        db = get_db()
        
        if search:
            playlists_data = db.execute_query(
                f"""
                SELECT * FROM playlists
                WHERE name LIKE ? OR owner LIKE ?
                ORDER BY {sort_by} DESC
                LIMIT ? OFFSET ?
                """,
                (f"%{search}%", f"%{search}%", per_page, (page - 1) * per_page)
            )
            total = db.execute_query(
                "SELECT COUNT(*) as count FROM playlists WHERE name LIKE ? OR owner LIKE ?",
                (f"%{search}%", f"%{search}%")
            )[0]['count']
        else:
            playlists_data = db.execute_query(
                f"SELECT * FROM playlists ORDER BY {sort_by} DESC LIMIT ? OFFSET ?",
                (per_page, (page - 1) * per_page)
            )
            total = db.execute_query("SELECT COUNT(*) as count FROM playlists")[0]['count']
        
        return jsonify({
            'data': playlists_data,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Error getting playlists API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlists/<playlist_id>')
def api_playlist_detail(playlist_id):
    """API endpoint to get playlist details"""
    try:
        db = get_db()
        
        playlist = db.execute_query(
            "SELECT * FROM playlists WHERE playlist_id = ?",
            (playlist_id,)
        )
        
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        tracks = db.execute_query(
            "SELECT * FROM tracks WHERE playlist_id = ? ORDER BY added_at DESC",
            (playlist_id,)
        )
        
        return jsonify({
            'playlist': playlist[0],
            'tracks': tracks,
            'track_count': len(tracks)
        })
    except Exception as e:
        logger.error(f"Error getting playlist detail API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tracks')
def api_tracks():
    """API endpoint to get tracks"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        sort_by = request.args.get('sort_by', 'popularity', type=str)
        
        # Validate sort_by
        valid_sorts = ['popularity', 'name', 'artist', 'release_date']
        if sort_by not in valid_sorts:
            sort_by = 'popularity'
        
        db = get_db()
        
        if search:
            tracks_data = db.execute_query(
                f"""
                SELECT * FROM tracks
                WHERE name LIKE ? OR artist LIKE ? OR album LIKE ?
                ORDER BY {sort_by} DESC
                LIMIT ? OFFSET ?
                """,
                (f"%{search}%", f"%{search}%", f"%{search}%", per_page, (page - 1) * per_page)
            )
            total = db.execute_query(
                """
                SELECT COUNT(*) as count FROM tracks
                WHERE name LIKE ? OR artist LIKE ? OR album LIKE ?
                """,
                (f"%{search}%", f"%{search}%", f"%{search}%")
            )[0]['count']
        else:
            tracks_data = db.execute_query(
                f"SELECT * FROM tracks ORDER BY {sort_by} DESC LIMIT ? OFFSET ?",
                (per_page, (page - 1) * per_page)
            )
            total = db.execute_query("SELECT COUNT(*) as count FROM tracks")[0]['count']
        
        return jsonify({
            'data': tracks_data,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Error getting tracks API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tracks/<track_id>')
def api_track_detail(track_id):
    """API endpoint to get track details"""
    try:
        db = get_db()
        
        track = db.execute_query(
            "SELECT * FROM tracks WHERE track_id = ?",
            (track_id,)
        )
        
        if not track:
            return jsonify({'error': 'Track not found'}), 404
        
        return jsonify(track[0])
    except Exception as e:
        logger.error(f"Error getting track detail API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search')
def api_search():
    """Combined search across playlists and tracks"""
    try:
        query = request.args.get('q', '', type=str)
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Query too short'}), 400
        
        db = get_db()
        
        playlists = db.execute_query(
            "SELECT * FROM playlists WHERE name LIKE ? OR owner LIKE ? LIMIT 10",
            (f"%{query}%", f"%{query}%")
        )
        
        tracks = db.execute_query(
            "SELECT * FROM tracks WHERE name LIKE ? OR artist LIKE ? LIMIT 10",
            (f"%{query}%", f"%{query}%")
        )
        
        return jsonify({
            'query': query,
            'playlists': playlists,
            'tracks': tracks,
            'playlist_count': len(playlists),
            'track_count': len(tracks)
        })
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500


if __name__ == '__main__':
    logger.info("Starting Flask app...")
    app.run(debug=True, host='127.0.0.1', port=5000)
