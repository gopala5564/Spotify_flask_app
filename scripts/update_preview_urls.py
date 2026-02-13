#!/usr/bin/env python
"""
Script to update existing tracks in the database with preview URLs from Spotify API
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spotify_scraper.config import DATABASE_PATH, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from spotify_scraper.database import DatabaseManager
from spotify_scraper.api import SpotifyAPIClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Update preview URLs for existing tracks"""
    try:
        print("\n" + "="*80)
        print("UPDATE PREVIEW URLS - Fetching preview URLs from Spotify API")
        print("="*80 + "\n")
        
        # Initialize database
        db_manager = DatabaseManager(str(DATABASE_PATH))
        api_client = SpotifyAPIClient()
        
        # Get all tracks that have no preview URL
        tracks_without_preview = db_manager.execute_query(
            "SELECT track_id, name FROM tracks WHERE preview_url IS NULL OR preview_url = '' LIMIT 100"
        )
        
        if not tracks_without_preview:
            print("✓ All tracks already have preview URLs!")
            return
        
        print(f"Found {len(tracks_without_preview)} tracks without preview URLs")
        print("Fetching preview URLs from Spotify API...\n")
        
        # Get track IDs
        track_ids = [track['track_id'] for track in tracks_without_preview]
        
        # Fetch track details from Spotify API to get preview URLs
        updated_count = 0
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            try:
                results = api_client.sp.tracks(batch)
                
                for track in results['tracks']:
                    if track:
                        preview_url = track.get('preview_url')
                        if preview_url:
                            # Update the database
                            db_manager.execute_query(
                                "UPDATE tracks SET preview_url = ? WHERE track_id = ?",
                                (preview_url, track['id'])
                            )
                            updated_count += 1
                            track_name = next((t['name'] for t in tracks_without_preview if t['track_id'] == track['id']), 'Unknown')
                            print(f"  ✓ Updated: {track_name}")
                
                db_manager.commit()
            except Exception as e:
                logger.error(f"Error updating batch: {e}")
                continue
        
        print(f"\n✓ Successfully updated {updated_count} tracks with preview URLs!")
        print("\nNow you should be able to play the tracks in your Flask app.\n")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if db_manager:
            db_manager.close()


if __name__ == '__main__':
    main()
