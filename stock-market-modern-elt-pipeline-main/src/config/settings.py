"""
Configuration settings for the stock market data pipeline.
"""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GCPConfig:
    """Google Cloud Platform configuration settings."""
    
    project_id: str
    service_account: str
    region: str
    zone: str
    bucket_name: str
    dataset_id: str
    
    @classmethod
    def from_env(cls) -> "GCPConfig":
        """Create GCP configuration from environment variables."""
        return cls(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            service_account=os.environ.get("SERVICE_ACCOUNT", ""),
            region=os.environ.get("REGION", "us-central1"),
            zone=os.environ.get("ZONE", "us-central1-a"),
            bucket_name=os.environ.get("BUCKET_NAME", "datalake-stock-market-bucket"),
            dataset_id=os.environ.get("DATASET_ID", "stock_market_dw"),
        )
    
    def validate(self) -> None:
        """Validate that all required configuration values are present."""
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        if not self.service_account:
            raise ValueError("SERVICE_ACCOUNT environment variable is required")


@dataclass
class PipelineConfig:
    """Pipeline-specific configuration settings."""
    
    symbols: List[str]
    composer_name: str
    python_file_uri: str
    
    @classmethod
    def from_env(cls, gcp_config: GCPConfig) -> "PipelineConfig":
        """Create pipeline configuration from environment variables."""
        symbols_str = os.environ.get("STOCK_SYMBOLS", "META,AAPL,AMZN,NFLX,GOOGL")
        symbols = [symbol.strip() for symbol in symbols_str.split(",")]
        
        return cls(
            symbols=symbols,
            composer_name=os.environ.get("COMPOSER_NAME", "stock-market-composer"),
            python_file_uri=f"gs://{gcp_config.bucket_name}/scripts/transform_stock_data_pipeline.py"
        )


@dataclass
class SparkConfig:
    """Spark configuration settings."""
    
    app_name: str = "transform-stock-market-data-pipeline"
    adaptive_enabled: bool = True
    coalesce_partitions_enabled: bool = True
    compression_codec: str = "snappy"
    serializer: str = "org.apache.spark.serializer.KryoSerializer"
    
    def get_config_dict(self) -> dict:
        """Get Spark configuration as dictionary."""
        return {
            "spark.sql.adaptive.enabled": str(self.adaptive_enabled).lower(),
            "spark.sql.adaptive.coalescePartitions.enabled": str(self.coalesce_partitions_enabled).lower(),
            "spark.sql.parquet.compression.codec": self.compression_codec,
            "spark.serializer": self.serializer,
        }


def get_config() -> tuple[GCPConfig, PipelineConfig, SparkConfig]:
    """Get all configuration objects."""
    gcp_config = GCPConfig.from_env()
    gcp_config.validate()
    
    pipeline_config = PipelineConfig.from_env(gcp_config)
    spark_config = SparkConfig()
    
    return gcp_config, pipeline_config, spark_config
