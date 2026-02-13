"""AWS Lambda handler for loading transformed data to processed layer"""

import json
import logging
import os
from datetime import datetime
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')

# Environment variables
DATA_LAKE_BUCKET = os.getenv('DATA_LAKE_BUCKET')


def lambda_handler(event, context):
    """
    Load transformed data from processed folder into final destination.
    
    Event format:
    {
        "processed_key": "processed/playlists/2026/02/14/120000/playlists_processed.json",
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
        logger.info(f"Load Lambda invoked with event: {json.dumps(event)}")
        
        if not DATA_LAKE_BUCKET:
            raise ValueError("DATA_LAKE_BUCKET environment variable not set")
        
        processed_key = event.get('processed_key')
        data_type = event.get('data_type', 'playlists')
        
        if not processed_key:
            raise ValueError("processed_key is required in event")
        
        # Read processed data
        logger.info(f"Reading processed data from s3://{DATA_LAKE_BUCKET}/{processed_key}")
        response = s3_client.get_object(Bucket=DATA_LAKE_BUCKET, Key=processed_key)
        processed_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Load to final destination
        timestamp = datetime.utcnow().strftime('%Y/%m/%d')
        final_key = f"final/{data_type}/{timestamp}/{data_type}_final.json"
        
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=final_key,
            Body=json.dumps(processed_data),
            ContentType='application/json'
        )
        
        logger.info(f"Data loaded to s3://{DATA_LAKE_BUCKET}/{final_key}")
        
        # Create a manifest file
        manifest = {
            'data_type': data_type,
            'source_key': processed_key,
            'final_key': final_key,
            'record_count': processed_data.get('record_count', 0),
            'loaded_at': datetime.utcnow().isoformat()
        }
        
        manifest_key = f"manifests/{data_type}/{timestamp}/manifest_{datetime.utcnow().strftime('%H%M%S')}.json"
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=manifest_key,
            Body=json.dumps(manifest),
            ContentType='application/json'
        )
        
        logger.info(f"Manifest saved to s3://{DATA_LAKE_BUCKET}/{manifest_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'data_type': data_type,
                'source': f"s3://{DATA_LAKE_BUCKET}/{processed_key}",
                'destination': f"s3://{DATA_LAKE_BUCKET}/{final_key}",
                'manifest': f"s3://{DATA_LAKE_BUCKET}/{manifest_key}",
                'records_loaded': processed_data.get('record_count', 0),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in load Lambda: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def create_data_lake_folders():
    """Create folder structure in data lake bucket."""
    try:
        logger.info("Creating data lake folder structure")
        
        folders = [
            'raw/playlists/',
            'raw/tracks/',
            'raw/audio_features/',
            'processed/playlists/',
            'processed/tracks/',
            'processed/audio_features/',
            'final/playlists/',
            'final/tracks/',
            'final/audio_features/',
            'manifests/',
            'metadata/',
        ]
        
        for folder in folders:
            key = folder + '.keep'
            s3_client.put_object(
                Bucket=DATA_LAKE_BUCKET,
                Key=key,
                Body=b''
            )
            logger.info(f"Created folder structure: {folder}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating data lake folders: {str(e)}", exc_info=True)
        raise
