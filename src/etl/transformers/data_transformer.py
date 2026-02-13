"""Data transformation for ETL pipeline using PySpark"""

import logging
from typing import List, Dict, Any
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit, current_timestamp

logger = logging.getLogger(__name__)

class DataTransformer:
    """Transforms raw Spotify data into clean, structured formats using PySpark"""

    @staticmethod
    def transform_playlists(raw_playlists: List[Dict[str, Any]], spark: SparkSession) -> DataFrame:
        """
        Transform raw playlist data into normalized DataFrame

        Args:
            raw_playlists: Raw playlist dictionaries from API
            spark: SparkSession instance

        Returns:
            PySpark DataFrame with cleaned playlist data
        """
        if not raw_playlists:
            logger.warning("No playlists to transform")
            return spark.createDataFrame([], schema=None)

        try:
            df = spark.createDataFrame(raw_playlists)

            # Standardize column names
            for col_name in df.columns:
                df = df.withColumnRenamed(col_name, col_name.lower().replace(' ', '_'))

            # Add load timestamp
            df = df.withColumn("loaded_at", current_timestamp())

            # Ensure key columns exist
            required_cols = ['playlist_id', 'name', 'owner', 'total_tracks']
            for col_name in required_cols:
                if col_name not in df.columns:
                    logger.warning(f"Missing column: {col_name}")

            logger.info(f"Transformed {df.count()} playlists")
            return df

        except Exception as e:
            logger.error(f"Error transforming playlists: {e}")
            return spark.createDataFrame([], schema=None)

    @staticmethod
    def transform_tracks(raw_tracks: List[Dict[str, Any]], spark: SparkSession) -> DataFrame:
        """
        Transform raw track data into normalized DataFrame

        Args:
            raw_tracks: Raw track dictionaries from API
            spark: SparkSession instance

        Returns:
            PySpark DataFrame with cleaned track data
        """
        if not raw_tracks:
            logger.warning("No tracks to transform")
            return spark.createDataFrame([], schema=None)

        try:
            df = spark.createDataFrame(raw_tracks)

            # Standardize column names
            for col_name in df.columns:
                df = df.withColumnRenamed(col_name, col_name.lower().replace(' ', '_'))

            # Add load timestamp
            df = df.withColumn("loaded_at", current_timestamp())

            # Handle missing preview URLs
            if 'preview_url' in df.columns:
                df = df.withColumn("has_preview", col("preview_url").isNotNull())

            # Ensure numeric columns are typed correctly
            numeric_cols = ['popularity', 'duration_ms']
            for col_name in numeric_cols:
                if col_name in df.columns:
                    df = df.withColumn(col_name, col(col_name).cast("double"))

            logger.info(f"Transformed {df.count()} tracks")
            return df

        except Exception as e:
            logger.error(f"Error transforming tracks: {e}")
            return spark.createDataFrame([], schema=None)

    @staticmethod
    def transform_audio_features(raw_features: List[Dict[str, Any]], spark: SparkSession) -> DataFrame:
        """
        Transform raw audio features into normalized DataFrame

        Args:
            raw_features: Raw audio feature dictionaries from API
            spark: SparkSession instance

        Returns:
            PySpark DataFrame with cleaned audio features
        """
        if not raw_features:
            logger.warning("No audio features to transform")
            return spark.createDataFrame([], schema=None)

        try:
            df = spark.createDataFrame(raw_features)

            # Standardize column names
            for col_name in df.columns:
                df = df.withColumnRenamed(col_name, col_name.lower().replace(' ', '_'))

            # Add load timestamp
            df = df.withColumn("loaded_at", current_timestamp())

            # Ensure numeric columns
            numeric_cols = [
                'danceability', 'energy', 'key', 'loudness', 'mode',
                'speechiness', 'acousticness', 'instrumentalness',
                'liveness', 'valence', 'tempo', 'duration_ms'
            ]
            for col_name in numeric_cols:
                if col_name in df.columns:
                    df = df.withColumn(col_name, col(col_name).cast("double"))

            logger.info(f"Transformed {df.count()} audio features")
            return df

        except Exception as e:
            logger.error(f"Error transforming audio features: {e}")
            return spark.createDataFrame([], schema=None)

    @staticmethod
    def deduplicate(df: DataFrame, id_column: str = 'id') -> DataFrame:
        """
        Remove duplicate records based on ID

        Args:
            df: DataFrame to deduplicate
            id_column: Column name to use for deduplication

        Returns:
            Deduplicated DataFrame
        """
        if id_column not in df.columns:
            logger.warning(f"Column {id_column} not found in DataFrame")
            return df

        original_count = df.count()
        df = df.dropDuplicates([id_column])

        logger.info(f"Removed {original_count - df.count()} duplicate records")
        return df
