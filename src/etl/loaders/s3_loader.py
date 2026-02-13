"""AWS S3 Data Lake loader for ETL pipeline"""

import logging
import os
from typing import Optional
from datetime import datetime
import pandas as pd
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3DataLake:
    """Manages data lake operations in AWS S3"""
    
    def __init__(self, bucket_name: Optional[str] = None, region: str = 'us-east-1'):
        """
        Initialize S3 data lake client
        
        Args:
            bucket_name: S3 bucket name (uses env var if not provided)
            region: AWS region
        """
        self.bucket_name = bucket_name or os.getenv('DATA_LAKE_BUCKET')
        self.region = region
        
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided or set in DATA_LAKE_BUCKET env var")
        
        self.s3_client = boto3.client('s3', region_name=region)
        logger.info(f"S3DataLake initialized for bucket: {self.bucket_name}")
    
    def write_parquet(
        self,
        dataframe: pd.DataFrame,
        s3_path: str,
        partition_cols: Optional[list] = None
    ) -> bool:
        """
        Write DataFrame to S3 as Parquet file
        
        Args:
            dataframe: Pandas DataFrame to write
            s3_path: S3 path (e.g., 's3://bucket/playlists/data.parquet')
            partition_cols: Columns to partition by (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if dataframe.empty:
                logger.warning(f"Skipping write for empty DataFrame to {s3_path}")
                return False
            
            # Extract key from full S3 path
            if s3_path.startswith('s3://'):
                key = s3_path.replace(f's3://{self.bucket_name}/', '')
            else:
                key = s3_path
            
            # Convert to Parquet in memory
            parquet_buffer = dataframe.to_parquet()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=parquet_buffer,
                ContentType='application/octet-stream'
            )
            
            logger.info(f"Successfully wrote {len(dataframe)} records to {s3_path}")
            return True
        
        except ClientError as e:
            logger.error(f"AWS error writing to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing Parquet to S3: {e}")
            return False
    
    def read_parquet(self, s3_path: str) -> Optional[pd.DataFrame]:
        """
        Read Parquet file from S3
        
        Args:
            s3_path: S3 path to Parquet file
            
        Returns:
            Pandas DataFrame or None if error
        """
        try:
            if s3_path.startswith('s3://'):
                key = s3_path.replace(f's3://{self.bucket_name}/', '')
            else:
                key = s3_path
            
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            df = pd.read_parquet(obj['Body'])
            
            logger.info(f"Successfully read {len(df)} records from {s3_path}")
            return df
        
        except ClientError as e:
            logger.error(f"AWS error reading from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading Parquet from S3: {e}")
            return None
    
    def list_objects(self, prefix: str = '') -> list:
        """
        List objects in S3 bucket by prefix
        
        Args:
            prefix: S3 prefix to filter by
            
        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            logger.info(f"Found {len(objects)} objects with prefix '{prefix}'")
            return objects
        
        except Exception as e:
            logger.error(f"Error listing S3 objects: {e}")
            return []
    
    def get_last_modified(self, s3_path: str) -> Optional[datetime]:
        """
        Get last modified timestamp for S3 object
        
        Args:
            s3_path: S3 path to object
            
        Returns:
            datetime of last modification or None
        """
        try:
            if s3_path.startswith('s3://'):
                key = s3_path.replace(f's3://{self.bucket_name}/', '')
            else:
                key = s3_path
            
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return response['LastModified']
        
        except Exception as e:
            logger.warning(f"Could not get last modified for {s3_path}: {e}")
            return None
    
    def create_data_lake_structure(self) -> bool:
        """
        Create standard data lake folder structure
        
        Returns:
            True if successful
        """
        try:
            folders = [
                'raw/playlists/',
                'raw/tracks/',
                'raw/audio_features/',
                'processed/playlists/',
                'processed/tracks/',
                'processed/audio_features/',
                'metadata/',
            ]
            
            for folder in folders:
                # Create marker objects for folders
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder + '.gitkeep'
                )
            
            logger.info(f"Created data lake structure in {self.bucket_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating data lake structure: {e}")
            return False
