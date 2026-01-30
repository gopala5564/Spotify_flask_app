#!/usr/bin/env python
"""
Main script to fetch Spotify playlists and tracks
Usage: python fetch_playlists.py [num_playlists]
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spotify_scraper.config import (
    SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
    DEFAULT_NUM_PLAYLISTS, DATABASE_PATH, DATA_DIR,
    LOG_LEVEL, LOG_FILE, FETCH_AUDIO_FEATURES,
    SAVE_TO_DATABASE,
    validate_config, get_config_summary
)
from spotify_scraper.database import DatabaseManager
from spotify_scraper.api import SpotifyAPIClient

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main execution"""
    db_manager = None
    
    try:
        print("\n" + "="*100)
        print("SPOTIFY SCRAPER - Fetch Playlists and Tracks")
        print("="*100 + "\n")
        
        # Validate configuration
        validate_config()
        
        # Show configuration
        config_summary = get_config_summary()
        print("Configuration:")
        for key, value in config_summary.items():
            print(f"  {key:35} : {value}")
        print()
        
        # Get number of playlists from command line or use default
        num_playlists = DEFAULT_NUM_PLAYLISTS
        if len(sys.argv) > 1:
            try:
                num_playlists = int(sys.argv[1])
                logger.info(f"Using {num_playlists} playlists from command line argument")
            except ValueError:
                logger.warning(f"Invalid argument '{sys.argv[1]}', using default {DEFAULT_NUM_PLAYLISTS}")
        
        # Initialize database
        if SAVE_TO_DATABASE:
            db_manager = DatabaseManager(str(DATABASE_PATH))
            print()
        
        # Initialize API client
        api_client = SpotifyAPIClient()
        print()
        
        # Fetch playlists
        logger.info(f"Fetching {num_playlists} playlists...")
        playlists_result = api_client.fetch_playlists_with_tracks(num_playlists=num_playlists)
        playlists = playlists_result['playlists']
        
        if not playlists:
            logger.error("Failed to fetch playlists")
            return
        
        print()
        
        # Fetch tracks
        logger.info("Fetching tracks from all playlists...")
        tracks_result = api_client.fetch_tracks_from_playlists(playlists)
        all_tracks = tracks_result['all_tracks']
        all_track_ids = tracks_result['track_ids']
        
        print()
        
        # Fetch audio features
        features_dict = {}
        if FETCH_AUDIO_FEATURES and all_track_ids:
            logger.info("Fetching audio features...")
            features_dict = api_client.get_audio_features_batch(all_track_ids)
            print()
            
            # Add features to tracks
            for track in all_tracks:
                track_id = track['track_id']
                if track_id in features_dict:
                    track.update(features_dict[track_id])
                else:
                    track.update({
                        'danceability': None,
                        'energy': None,
                        'key': None,
                        'loudness': None,
                        'mode': None,
                        'speechiness': None,
                        'acousticness': None,
                        'instrumentalness': None,
                        'liveness': None,
                        'valence': None,
                        'tempo': None,
                        'time_signature': None
                    })
        else:
            logger.info("Skipping audio features (disabled in config)")
            # Add placeholder values
            for track in all_tracks:
                track.update({
                    'danceability': None,
                    'energy': None,
                    'key': None,
                    'loudness': None,
                    'mode': None,
                    'speechiness': None,
                    'acousticness': None,
                    'instrumentalness': None,
                    'liveness': None,
                    'valence': None,
                    'tempo': None,
                    'time_signature': None
                })
        
        data = {
            'playlists': playlists,
            'all_tracks': all_tracks
        }
        
        # Save to database
        if SAVE_TO_DATABASE and db_manager:
            logger.info("Saving data to database...")
            print("  Inserting playlists...", end='', flush=True)
            for playlist in playlists:
                db_manager.insert_playlist(playlist)
            print(" [OK]")
            
            print("  Inserting tracks...", end='', flush=True)
            for idx, track in enumerate(all_tracks):
                db_manager.insert_track(track)
                if (idx + 1) % 1000 == 0:
                    db_manager.commit()
            db_manager.commit()
            print(" [OK]")
            
            print("  Inserting audio features...", end='', flush=True)
            for track_id, features in features_dict.items():
                db_manager.insert_audio_features(track_id, features)
            
            for track in all_tracks:
                track_id = track.get('track_id')
                if track_id and track_id not in features_dict:
                    features = {
                        'danceability': track.get('danceability'),
                        'energy': track.get('energy'),
                        'key': track.get('key'),
                        'loudness': track.get('loudness'),
                        'mode': track.get('mode'),
                        'speechiness': track.get('speechiness'),
                        'acousticness': track.get('acousticness'),
                        'instrumentalness': track.get('instrumentalness'),
                        'liveness': track.get('liveness'),
                        'valence': track.get('valence'),
                        'tempo': track.get('tempo'),
                        'time_signature': track.get('time_signature')
                    }
                    db_manager.insert_audio_features(track_id, features)
            
            db_manager.commit()
            print(" [OK]")
            
            stats = db_manager.get_stats()
            print(f"\n  Database Statistics:")
            print(f"    - Playlists: {stats['playlists']}")
            print(f"    - Tracks: {stats['tracks']}")
            print(f"    - Tracks with Audio Features: {stats['audio_features']}")
            print()
        
        logger.info("[OK] Fetch completed successfully!")
        print("[OK] Fetch completed successfully!\n")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n[ERROR] Error: {e}\n")
        sys.exit(1)
    
    finally:
        if db_manager:
            db_manager.close()


if __name__ == "__main__":
    main()
