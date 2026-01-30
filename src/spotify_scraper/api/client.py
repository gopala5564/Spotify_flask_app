"""
Spotify API Client
Handles all interactions with the Spotify Web API
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config import (
    SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
    API_DELAY_BETWEEN_REQUESTS, API_DELAY_BETWEEN_BATCHES,
    AUDIO_FEATURES_BATCH_SIZE, PLAYLIST_FETCH_MAX_WORKERS,
    MAX_RETRIES, RETRY_BACKOFF_FACTOR, PLAYLIST_SEARCH_QUERIES
)

logger = logging.getLogger(__name__)


class SpotifyAPIClient:
    """Client for interacting with Spotify Web API"""
    
    def __init__(self):
        """Initialize Spotify API client with credentials"""
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Connected to Spotify API")
        except Exception as e:
            logger.error(f"Failed to connect to Spotify API: {e}")
            raise
    
    def search_playlists(self, query='', limit=50, offset=0):
        """
        Search for playlists
        
        Args:
            query: Search query
            limit: Number of results to return (max 50)
            offset: Offset for pagination
            
        Returns:
            List of playlist dictionaries
        """
        playlists = []
        try:
            search_query = query if query else 'playlist'
            results = self.sp.search(q=search_query, type='playlist', limit=limit, offset=offset)
            
            if not results or not results.get('playlists'):
                logger.warning(f"No results returned for query '{search_query}'")
                return []
            
            playlist_items = results['playlists'].get('items', [])
            
            for playlist in playlist_items:
                if not playlist:
                    continue
                    
                playlist_info = {
                    'playlist_id': playlist['id'],
                    'name': playlist['name'],
                    'description': playlist.get('description', 'N/A'),
                    'owner': playlist['owner']['display_name'],
                    'owner_id': playlist['owner']['id'],
                    'total_tracks': playlist['tracks']['total'],
                    'followers': playlist.get('followers', {}).get('total', 0),
                    'public': playlist.get('public', True),
                    'collaborative': playlist.get('collaborative', False),
                    'external_url': playlist['external_urls']['spotify'],
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None
                }
                playlists.append(playlist_info)
            
            logger.debug(f"Found {len(playlists)} playlists for query '{query}'")
            return playlists
        
        except Exception as e:
            logger.error(f"Error searching playlists: {e}", exc_info=True)
            return []
    
    def get_playlist_tracks(self, playlist_id, limit=100):
        """
        Get all tracks from a playlist with pagination
        
        Args:
            playlist_id: Spotify playlist ID
            limit: Max tracks per request (max 100)
            
        Returns:
            List of track dictionaries
        """
        tracks = []
        offset = 0
        
        try:
            while True:
                results = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
                
                for item in results['items']:
                    if item['track'] is None:
                        continue
                    
                    track = item['track']
                    track_info = {
                        'track_id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'artist_id': track['artists'][0]['id'] if track['artists'] else None,
                        'album': track['album']['name'],
                        'album_id': track['album']['id'],
                        'release_date': track['album']['release_date'],
                        'duration_ms': track['duration_ms'],
                        'duration_minutes': round(track['duration_ms'] / 60000, 2),
                        'popularity': track['popularity'],
                        'explicit': track['explicit'],
                        'isrc': track.get('external_ids', {}).get('isrc', 'N/A'),
                        'spotify_url': track['external_urls']['spotify'],
                        'added_at': item['added_at'],
                        'added_by': item.get('added_by', {}).get('display_name', 'N/A')
                    }
                    tracks.append(track_info)
                
                # Check if there are more tracks
                if results['next'] is None:
                    break
                offset += limit
            
            logger.debug(f"Retrieved {len(tracks)} tracks from playlist {playlist_id}")
            return tracks
        
        except Exception as e:
            logger.error(f"Error fetching tracks for playlist {playlist_id}: {e}")
            return []
    
    def get_audio_features_batch(self, track_ids):
        """
        Get audio features for multiple tracks with retry logic
        
        Args:
            track_ids: List of track IDs
            
        Returns:
            Dictionary mapping track_id to audio features
        """
        features_dict = {}
        
        # Remove duplicates and filter empty
        track_ids = list(set([tid for tid in track_ids if tid]))
        
        if not track_ids:
            return features_dict
        
        batch_size = AUDIO_FEATURES_BATCH_SIZE
        failed_batches = []
        
        logger.info(f"Fetching audio features for {len(track_ids)} tracks in batches of {batch_size}")
        
        for i in range(0, len(track_ids), batch_size):
            batch_num = i // batch_size + 1
            total_batches = (len(track_ids) + batch_size - 1) // batch_size
            batch_ids = track_ids[i:i+batch_size]
            
            retry_count = 0
            success = False
            
            while retry_count < MAX_RETRIES and not success:
                try:
                    features_list = self.sp.audio_features(batch_ids)
                    
                    if features_list:
                        for features in features_list:
                            if features:
                                features_dict[features['id']] = {
                                    'danceability': features.get('danceability'),
                                    'energy': features.get('energy'),
                                    'key': features.get('key'),
                                    'loudness': features.get('loudness'),
                                    'mode': features.get('mode'),
                                    'speechiness': features.get('speechiness'),
                                    'acousticness': features.get('acousticness'),
                                    'instrumentalness': features.get('instrumentalness'),
                                    'liveness': features.get('liveness'),
                                    'valence': features.get('valence'),
                                    'tempo': features.get('tempo'),
                                    'time_signature': features.get('time_signature')
                                }
                        success = True
                        logger.debug(f"[{batch_num}/{total_batches}] [OK] Audio features fetched")
                    else:
                        success = True
                    
                    time.sleep(API_DELAY_BETWEEN_REQUESTS)
                
                except Exception as e:
                    retry_count += 1
                    if retry_count < MAX_RETRIES:
                        wait_time = RETRY_BACKOFF_FACTOR ** retry_count
                        logger.warning(f"[{batch_num}/{total_batches}] Retrying in {wait_time}s (attempt {retry_count}/{MAX_RETRIES}): {str(e)[:60]}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"[{batch_num}/{total_batches}] Failed after {MAX_RETRIES} retries")
                        failed_batches.append((i, batch_ids))
            
            time.sleep(API_DELAY_BETWEEN_BATCHES)
        
        # Retry failed batches with smaller size
        if failed_batches:
            logger.info(f"Retrying {len(failed_batches)} failed batches with smaller size")
            for batch_idx, failed_ids in failed_batches:
                for j in range(0, len(failed_ids), 20):
                    small_batch = failed_ids[j:j+20]
                    try:
                        features_list = self.sp.audio_features(small_batch)
                        for features in features_list:
                            if features:
                                features_dict[features['id']] = {
                                    'danceability': features.get('danceability'),
                                    'energy': features.get('energy'),
                                    'key': features.get('key'),
                                    'loudness': features.get('loudness'),
                                    'mode': features.get('mode'),
                                    'speechiness': features.get('speechiness'),
                                    'acousticness': features.get('acousticness'),
                                    'instrumentalness': features.get('instrumentalness'),
                                    'liveness': features.get('liveness'),
                                    'valence': features.get('valence'),
                                    'tempo': features.get('tempo'),
                                    'time_signature': features.get('time_signature')
                                }
                        logger.info(f"Recovered {len([f for f in features_list if f])} features")
                        time.sleep(API_DELAY_BETWEEN_BATCHES)
                    except Exception as e:
                        logger.error(f"Unable to fetch features: {str(e)[:80]}")
                        time.sleep(API_DELAY_BETWEEN_BATCHES)
        
        logger.info(f"Successfully fetched {len(features_dict)} audio feature sets")
        return features_dict
    
    def fetch_playlists_with_tracks(self, num_playlists=500):
        """
        Fetch playlists and their tracks
        
        Args:
            num_playlists: Number of playlists to fetch
            
        Returns:
            Dictionary with playlists and tracks
        """
        playlists = []
        seen_playlist_ids = set()
        
        logger.info(f"Searching for {num_playlists} playlists with {len(PLAYLIST_SEARCH_QUERIES)} search queries")
        
        playlists_per_query = max(50, num_playlists // len(PLAYLIST_SEARCH_QUERIES))
        
        for query_idx, query in enumerate(PLAYLIST_SEARCH_QUERIES, 1):
            fetched_count = 0
            offset = 0
            query_label = f"'{query}'" if query else "(trending)"
            
            logger.info(f"[{query_idx}/{len(PLAYLIST_SEARCH_QUERIES)}] Fetching playlists {query_label}")
            
            while fetched_count < playlists_per_query and len(playlists) < num_playlists:
                batch_playlists = self.search_playlists(query=query, limit=50, offset=offset)
                
                if not batch_playlists:
                    break
                
                for playlist in batch_playlists:
                    if playlist['playlist_id'] not in seen_playlist_ids and len(playlists) < num_playlists:
                        playlists.append(playlist)
                        seen_playlist_ids.add(playlist['playlist_id'])
                        fetched_count += 1
                
                offset += 50
                time.sleep(API_DELAY_BETWEEN_REQUESTS)
            
            logger.info(f"  -> Retrieved {fetched_count} playlists")
            
            if len(playlists) >= num_playlists:
                break
        
        playlists = playlists[:num_playlists]
        logger.info(f"Total playlists retrieved: {len(playlists)}")
        
        return {
            'playlists': playlists,
            'total': len(playlists)
        }
    
    def fetch_tracks_from_playlists(self, playlists):
        """
        Fetch tracks from multiple playlists concurrently
        
        Args:
            playlists: List of playlist dictionaries
            
        Returns:
            Dictionary with all tracks and their IDs
        """
        all_tracks = []
        all_track_ids = []
        
        logger.info(f"Fetching tracks from {len(playlists)} playlists")
        
        def fetch_and_process_playlist(playlist):
            """Fetch tracks for a playlist"""
            tracks = self.get_playlist_tracks(playlist['playlist_id'], limit=100)
            
            for track in tracks:
                track['playlist_id'] = playlist['playlist_id']
                track['playlist_name'] = playlist['name']
                track['playlist_owner'] = playlist['owner']
                track['playlist_followers'] = playlist['followers']
            
            return playlist, tracks
        
        with ThreadPoolExecutor(max_workers=PLAYLIST_FETCH_MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_and_process_playlist, playlist): idx 
                      for idx, playlist in enumerate(playlists, 1)}
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    playlist, tracks = future.result()
                    all_tracks.extend(tracks)
                    all_track_ids.extend([t['track_id'] for t in tracks])
                    logger.info(f"  [{idx}/{len(playlists)}] {playlist['name']} ({len(tracks)} tracks)")
                except Exception as e:
                    logger.error(f"  [{idx}/{len(playlists)}] Error: {e}")
        
        logger.info(f"Total tracks fetched: {len(all_tracks)}")
        
        return {
            'all_tracks': all_tracks,
            'track_ids': all_track_ids
        }
