"""
Database Manager for Spotify Scraper
Handles all SQLite database operations
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage SQLite database operations for Spotify data"""
    
    def __init__(self, db_path):
        """
        Initialize database connection and create tables
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Create database connection"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def create_tables(self):
        """Create necessary tables for storing playlist and track data"""
        try:
            # Create playlists table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    playlist_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner TEXT NOT NULL,
                    owner_id TEXT,
                    total_tracks INTEGER,
                    followers INTEGER DEFAULT 0,
                    public BOOLEAN DEFAULT 1,
                    collaborative BOOLEAN DEFAULT 0,
                    external_url TEXT,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create tracks table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    track_id TEXT PRIMARY KEY,
                    playlist_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    artist_id TEXT,
                    album TEXT,
                    album_id TEXT,
                    release_date TEXT,
                    duration_ms INTEGER,
                    duration_minutes REAL,
                    popularity INTEGER,
                    explicit BOOLEAN,
                    isrc TEXT,
                    spotify_url TEXT,
                    added_at TIMESTAMP,
                    added_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id)
                )
            ''')
            
            # Create audio_features table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_features (
                    track_id TEXT PRIMARY KEY,
                    danceability REAL,
                    energy REAL,
                    key INTEGER,
                    loudness REAL,
                    mode INTEGER,
                    speechiness REAL,
                    acousticness REAL,
                    instrumentalness REAL,
                    liveness REAL,
                    valence REAL,
                    tempo REAL,
                    time_signature INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
                )
            ''')
            
            self.connection.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def insert_playlist(self, playlist_data):
        """
        Insert a playlist into the database
        
        Args:
            playlist_data: Dictionary with playlist information
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO playlists 
                (playlist_id, name, description, owner, owner_id, total_tracks, 
                 followers, public, collaborative, external_url, image_url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                playlist_data.get('playlist_id'),
                playlist_data.get('name'),
                playlist_data.get('description'),
                playlist_data.get('owner'),
                playlist_data.get('owner_id'),
                playlist_data.get('total_tracks'),
                playlist_data.get('followers', 0),
                playlist_data.get('public', True),
                playlist_data.get('collaborative', False),
                playlist_data.get('external_url'),
                playlist_data.get('image_url'),
                datetime.now()
            ))
        except Exception as e:
            logger.error(f"Error inserting playlist: {e}")
            raise
    
    def insert_track(self, track_data):
        """
        Insert a track into the database
        
        Args:
            track_data: Dictionary with track information
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO tracks 
                (track_id, playlist_id, name, artist, artist_id, album, album_id, 
                 release_date, duration_ms, duration_minutes, popularity, explicit, 
                 isrc, spotify_url, added_at, added_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                track_data.get('track_id'),
                track_data.get('playlist_id'),
                track_data.get('name'),
                track_data.get('artist'),
                track_data.get('artist_id'),
                track_data.get('album'),
                track_data.get('album_id'),
                track_data.get('release_date'),
                track_data.get('duration_ms'),
                track_data.get('duration_minutes'),
                track_data.get('popularity'),
                track_data.get('explicit'),
                track_data.get('isrc'),
                track_data.get('spotify_url'),
                track_data.get('added_at'),
                track_data.get('added_by')
            ))
        except Exception as e:
            logger.error(f"Error inserting track: {e}")
            raise
    
    def insert_audio_features(self, track_id, features):
        """
        Insert audio features for a track
        
        Args:
            track_id: Spotify track ID
            features: Dictionary with audio feature values
        """
        try:
            if not features or not any(features.values()):
                return
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO audio_features 
                (track_id, danceability, energy, key, loudness, mode, speechiness, 
                 acousticness, instrumentalness, liveness, valence, tempo, time_signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                track_id,
                features.get('danceability'),
                features.get('energy'),
                features.get('key'),
                features.get('loudness'),
                features.get('mode'),
                features.get('speechiness'),
                features.get('acousticness'),
                features.get('instrumentalness'),
                features.get('liveness'),
                features.get('valence'),
                features.get('tempo'),
                features.get('time_signature')
            ))
        except Exception as e:
            logger.error(f"Error inserting audio features: {e}")
            raise
    
    def commit(self):
        """Commit changes to database"""
        try:
            if self.connection:
                self.connection.commit()
        except Exception as e:
            logger.error(f"Error committing to database: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        try:
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
    
    def get_stats(self):
        """
        Get database statistics
        
        Returns:
            Dictionary with counts of playlists, tracks, and audio features
        """
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM playlists")
            playlist_count = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM tracks")
            track_count = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM audio_features WHERE danceability IS NOT NULL")
            features_count = self.cursor.fetchone()['count']
            
            return {
                'playlists': playlist_count,
                'tracks': track_count,
                'audio_features': features_count
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'playlists': 0, 'tracks': 0, 'audio_features': 0}
    
    def execute_query(self, query, params=None):
        """
        Execute a custom SQL query
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            List of rows
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
