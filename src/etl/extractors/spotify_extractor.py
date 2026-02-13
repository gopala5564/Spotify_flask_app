"""Spotify API Extractor for ETL pipeline"""

import logging
from typing import List, Dict, Any
from spotify_scraper.api.client import SpotifyAPIClient

logger = logging.getLogger(__name__)


class SpotifyExtractor:
    """Extracts data from Spotify API"""
    
    def __init__(self):
        """Initialize Spotify API client"""
        self.client = SpotifyAPIClient()
        logger.info("SpotifyExtractor initialized")
    
    def extract_playlists(self, search_queries: List[str] = None) -> List[Dict[str, Any]]:
        """
        Extract playlists from Spotify
        
        Args:
            search_queries: List of search queries (uses defaults if None)
            
        Returns:
            List of playlist dictionaries with metadata
        """
        if search_queries is None:
            # Default search queries
            search_queries = [
                'indie', 'rock', 'pop', 'hip hop', 'electronic',
                'jazz', 'classical', 'r&b', 'soul', 'country'
            ]
        
        all_playlists = []
        
        for query in search_queries:
            try:
                logger.info(f"Extracting playlists for query: {query}")
                playlists = self.client.search_playlists(query=query, limit=50)
                all_playlists.extend(playlists)
                logger.info(f"Extracted {len(playlists)} playlists for query '{query}'")
            except Exception as e:
                logger.error(f"Error extracting playlists for query '{query}': {e}")
                continue
        
        logger.info(f"Total playlists extracted: {len(all_playlists)}")
        return all_playlists
    
    def extract_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """
        Extract all tracks from a specific playlist
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            List of track dictionaries
        """
        try:
            logger.info(f"Extracting tracks from playlist: {playlist_id}")
            tracks = self.client.get_playlist_tracks(playlist_id)
            logger.info(f"Extracted {len(tracks)} tracks from playlist {playlist_id}")
            return tracks
        except Exception as e:
            logger.error(f"Error extracting tracks from playlist {playlist_id}: {e}")
            return []
    
    def extract_audio_features(self, track_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Extract audio features for tracks
        
        Args:
            track_ids: List of Spotify track IDs
            
        Returns:
            List of audio feature dictionaries
        """
        try:
            logger.info(f"Extracting audio features for {len(track_ids)} tracks")
            features = self.client.get_audio_features_batch(track_ids)
            logger.info(f"Extracted audio features for {len(features)} tracks")
            return features
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            return []
