"""AWS Lambda handler for Spotify data extraction to raw layer"""

import json
import logging
import sys
import os
from datetime import datetime
import boto3
import pandas as pd

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')

# Get environment variables
DATA_LAKE_BUCKET = os.getenv('DATA_LAKE_BUCKET')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


def lambda_handler(event, context):
    """
    Extract Spotify data and write to raw layer of data lake.
    
    Event format:
    {
        "action": "playlists" | "tracks" | "audio_features",
        "playlist_ids": ["optional list of playlist IDs for tracks extraction"]
    }
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        {
            "statusCode": 200 | 500,
            "body": JSON string with results
        }
    """
    try:
        logger.info(f"Extract Lambda invoked with event: {json.dumps(event)}")
        
        if not DATA_LAKE_BUCKET:
            raise ValueError("DATA_LAKE_BUCKET environment variable not set")
        
        action = event.get('action', 'playlists')
        results = {}
        
        if action == 'playlists':
            results = extract_playlists()
        elif action == 'tracks':
            playlist_ids = event.get('playlist_ids', [])
            results = extract_tracks(playlist_ids)
        elif action == 'audio_features':
            playlist_ids = event.get('playlist_ids', [])
            results = extract_audio_features(playlist_ids)
        else:
            raise ValueError(f"Unknown action: {action}")
        
        logger.info(f"Extraction completed successfully: {results}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'action': action,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in extract Lambda: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def extract_playlists():
    """
    Extract Spotify playlists using API credentials.
    
    Returns:
        dict with extraction results
    """
    try:
        # Placeholder for Spotify API extraction
        # In production, this would use spotipy library to fetch playlists
        logger.info("Starting playlist extraction")
        
        # For now, create sample data structure
        playlists = {
            "playlists": [],
            "total_extracted": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to raw layer
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
        s3_key = f"raw/playlists/{timestamp}/playlists.json"
        
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=s3_key,
            Body=json.dumps(playlists),
            ContentType='application/json'
        )
        
        logger.info(f"Playlists saved to s3://{DATA_LAKE_BUCKET}/{s3_key}")
        
        return {
            "action": "extract_playlists",
            "s3_location": f"s3://{DATA_LAKE_BUCKET}/{s3_key}",
            "total_playlists": 0,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error extracting playlists: {str(e)}", exc_info=True)
        raise


def extract_tracks(playlist_ids):
    """
    Extract tracks from specified Spotify playlists.
    
    Args:
        playlist_ids: List of playlist IDs to extract from
        
    Returns:
        dict with extraction results
    """
    try:
        logger.info(f"Starting tracks extraction for playlists: {playlist_ids}")
        
        # Placeholder for Spotify API extraction
        tracks = {
            "tracks": [],
            "total_extracted": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to raw layer
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
        s3_key = f"raw/tracks/{timestamp}/tracks.json"
        
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=s3_key,
            Body=json.dumps(tracks),
            ContentType='application/json'
        )
        
        logger.info(f"Tracks saved to s3://{DATA_LAKE_BUCKET}/{s3_key}")
        
        return {
            "action": "extract_tracks",
            "s3_location": f"s3://{DATA_LAKE_BUCKET}/{s3_key}",
            "total_tracks": 0,
            "playlists_processed": len(playlist_ids),
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error extracting tracks: {str(e)}", exc_info=True)
        raise


def extract_audio_features(playlist_ids):
    """
    Extract audio features for tracks in specified playlists.
    
    Args:
        playlist_ids: List of playlist IDs to extract audio features from
        
    Returns:
        dict with extraction results
    """
    try:
        logger.info(f"Starting audio features extraction for playlists: {playlist_ids}")
        
        # Placeholder for Spotify API extraction
        audio_features = {
            "features": [],
            "total_extracted": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to raw layer
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
        s3_key = f"raw/audio_features/{timestamp}/audio_features.json"
        
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=s3_key,
            Body=json.dumps(audio_features),
            ContentType='application/json'
        )
        
        logger.info(f"Audio features saved to s3://{DATA_LAKE_BUCKET}/{s3_key}")
        
        return {
            "action": "extract_audio_features",
            "s3_location": f"s3://{DATA_LAKE_BUCKET}/{s3_key}",
            "total_features": 0,
            "playlists_processed": len(playlist_ids),
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error extracting audio features: {str(e)}", exc_info=True)
        raise
