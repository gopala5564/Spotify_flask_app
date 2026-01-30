"""
Utility functions for data export
"""

import pandas as pd
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def export_to_csv(data, output_dir, prefix='spotify_data'):
    """
    Export data to CSV files
    
    Args:
        data: Dictionary with 'playlists' and 'all_tracks' keys
        output_dir: Directory to save CSV files
        prefix: Filename prefix
        
    Returns:
        Tuple of (playlists_file, tracks_file)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    try:
        playlists = data.get('playlists', [])
        all_tracks = data.get('all_tracks', [])
        
        # Save playlists
        if playlists:
            playlists_file = output_dir / f"{prefix}_playlists.csv"
            df_playlists = pd.DataFrame(playlists)
            df_playlists.to_csv(playlists_file, index=False)
            logger.info(f"Exported {len(playlists)} playlists to {playlists_file}")
        
        # Save tracks
        if all_tracks:
            tracks_file = output_dir / f"{prefix}_tracks.csv"
            df_tracks = pd.DataFrame(all_tracks)
            
            # Reorder columns
            columns_order = [
                'playlist_name', 'playlist_owner', 'name', 'artist', 'album', 'release_date',
                'duration_minutes', 'popularity', 'explicit', 'added_at', 'added_by',
                'danceability', 'energy', 'tempo', 'valence', 'acousticness',
                'instrumentalness', 'liveness', 'speechiness', 'loudness', 'key', 'mode',
                'track_id', 'artist_id', 'album_id', 'playlist_id', 'playlist_followers',
                'isrc', 'spotify_url', 'duration_ms', 'time_signature'
            ]
            
            for col in columns_order:
                if col not in df_tracks.columns:
                    df_tracks[col] = None
            
            df_tracks = df_tracks[columns_order]
            df_tracks.to_csv(tracks_file, index=False)
            logger.info(f"Exported {len(all_tracks)} tracks to {tracks_file}")
            
            return playlists_file, tracks_file
        
        return None, None
    
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise


def export_to_json(data, output_dir, prefix='spotify_data'):
    """
    Export data to JSON files
    
    Args:
        data: Dictionary with 'playlists' and 'all_tracks' keys
        output_dir: Directory to save JSON files
        prefix: Filename prefix
        
    Returns:
        Tuple of (playlists_file, tracks_file)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    try:
        playlists = data.get('playlists', [])
        all_tracks = data.get('all_tracks', [])
        
        # Save playlists
        if playlists:
            playlists_file = output_dir / f"{prefix}_playlists.json"
            with open(playlists_file, 'w', encoding='utf-8') as f:
                json.dump(playlists, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(playlists)} playlists to {playlists_file}")
        
        # Save tracks
        if all_tracks:
            tracks_file = output_dir / f"{prefix}_tracks.json"
            with open(tracks_file, 'w', encoding='utf-8') as f:
                json.dump(all_tracks, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(all_tracks)} tracks to {tracks_file}")
            
            return playlists_file, tracks_file
        
        return None, None
    
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        raise
