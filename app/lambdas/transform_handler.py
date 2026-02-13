"""AWS Lambda handler for data transformation"""

import json
import logging
import os
from datetime import datetime
import boto3
import pandas as pd

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')

# Environment variables
DATA_LAKE_BUCKET = os.getenv('DATA_LAKE_BUCKET')


def lambda_handler(event, context):
    """
    Transform raw Spotify data into processed format.
    
    Event format:
    {
        "raw_key": "raw/playlists/2026/02/14/120000/playlists.json",
        "data_type": "playlists" | "tracks" | "audio_features"
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
        logger.info(f"Transform Lambda invoked with event: {json.dumps(event)}")
        
        if not DATA_LAKE_BUCKET:
            raise ValueError("DATA_LAKE_BUCKET environment variable not set")
        
        raw_key = event.get('raw_key')
        data_type = event.get('data_type', 'playlists')
        
        if not raw_key:
            raise ValueError("raw_key is required in event")
        
        # Read raw data from S3
        logger.info(f"Reading raw data from s3://{DATA_LAKE_BUCKET}/{raw_key}")
        response = s3_client.get_object(Bucket=DATA_LAKE_BUCKET, Key=raw_key)
        raw_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Transform based on data type
        if data_type == 'playlists':
            transformed_data = transform_playlists(raw_data)
        elif data_type == 'tracks':
            transformed_data = transform_tracks(raw_data)
        elif data_type == 'audio_features':
            transformed_data = transform_audio_features(raw_data)
        else:
            raise ValueError(f"Unknown data_type: {data_type}")
        
        # Save transformed data
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
        processed_key = f"processed/{data_type}/{timestamp}/{data_type}_processed.json"
        
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=processed_key,
            Body=json.dumps(transformed_data),
            ContentType='application/json'
        )
        
        logger.info(f"Transformed data saved to s3://{DATA_LAKE_BUCKET}/{processed_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'data_type': data_type,
                'source': f"s3://{DATA_LAKE_BUCKET}/{raw_key}",
                'destination': f"s3://{DATA_LAKE_BUCKET}/{processed_key}",
                'records_processed': len(transformed_data.get('data', [])),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in transform Lambda: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def transform_playlists(raw_data):
    """
    Transform raw playlist data.
    
    Args:
        raw_data: Raw playlist data
        
    Returns:
        Transformed playlist data
    """
    try:
        logger.info("Transforming playlists data")
        
        # Placeholder transformation logic
        playlists = raw_data.get('playlists', [])
        
        # Remove duplicates and clean data
        seen = set()
        cleaned_playlists = []
        
        for playlist in playlists:
            playlist_id = playlist.get('id')
            if playlist_id and playlist_id not in seen:
                seen.add(playlist_id)
                cleaned_playlists.append(playlist)
        
        return {
            'data_type': 'playlists',
            'data': cleaned_playlists,
            'record_count': len(cleaned_playlists),
            'duplicates_removed': len(playlists) - len(cleaned_playlists),
            'transformed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error transforming playlists: {str(e)}", exc_info=True)
        raise


def transform_tracks(raw_data):
    """
    Transform raw track data.
    
    Args:
        raw_data: Raw track data
        
    Returns:
        Transformed track data
    """
    try:
        logger.info("Transforming tracks data")
        
        # Placeholder transformation logic
        tracks = raw_data.get('tracks', [])
        
        # Remove duplicates and add processing metadata
        seen = set()
        cleaned_tracks = []
        
        for track in tracks:
            track_id = track.get('id')
            if track_id and track_id not in seen:
                seen.add(track_id)
                track['processed_at'] = datetime.utcnow().isoformat()
                cleaned_tracks.append(track)
        
        return {
            'data_type': 'tracks',
            'data': cleaned_tracks,
            'record_count': len(cleaned_tracks),
            'duplicates_removed': len(tracks) - len(cleaned_tracks),
            'transformed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error transforming tracks: {str(e)}", exc_info=True)
        raise


def transform_audio_features(raw_data):
    """
    Transform raw audio features data.
    
    Args:
        raw_data: Raw audio features data
        
    Returns:
        Transformed audio features data
    """
    try:
        logger.info("Transforming audio features data")
        
        # Placeholder transformation logic
        features = raw_data.get('features', [])
        
        # Remove duplicates and add processing metadata
        seen = set()
        cleaned_features = []
        
        for feature in features:
            track_id = feature.get('id')
            if track_id and track_id not in seen:
                seen.add(track_id)
                feature['processed_at'] = datetime.utcnow().isoformat()
                cleaned_features.append(feature)
        
        return {
            'data_type': 'audio_features',
            'data': cleaned_features,
            'record_count': len(cleaned_features),
            'duplicates_removed': len(features) - len(cleaned_features),
            'transformed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error transforming audio features: {str(e)}", exc_info=True)
        raise
