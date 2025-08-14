"""Tests for configuration module."""

import os
import pytest
from unittest.mock import patch

from src.config.settings import GCPConfig, PipelineConfig, SparkConfig, get_config


class TestGCPConfig:
    """Test GCP configuration."""
    
    def test_from_env_with_all_vars(self):
        """Test creating GCPConfig from environment variables."""
        env_vars = {
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "SERVICE_ACCOUNT": "test@test.iam.gserviceaccount.com",
            "REGION": "us-west1",
            "ZONE": "us-west1-a",
            "BUCKET_NAME": "test-bucket",
            "DATASET_ID": "test_dataset",
        }
        
        with patch.dict(os.environ, env_vars):
            config = GCPConfig.from_env()
            
        assert config.project_id == "test-project"
        assert config.service_account == "test@test.iam.gserviceaccount.com"
        assert config.region == "us-west1"
        assert config.zone == "us-west1-a"
        assert config.bucket_name == "test-bucket"
        assert config.dataset_id == "test_dataset"
    
    def test_from_env_with_defaults(self):
        """Test creating GCPConfig with default values."""
        env_vars = {
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "SERVICE_ACCOUNT": "test@test.iam.gserviceaccount.com",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = GCPConfig.from_env()
            
        assert config.project_id == "test-project"
        assert config.region == "us-central1"
        assert config.zone == "us-central1-a"
        assert config.bucket_name == "datalake-stock-market-bucket"
        assert config.dataset_id == "stock_market_dw"
    
    def test_validate_success(self):
        """Test successful validation."""
        config = GCPConfig(
            project_id="test-project",
            service_account="test@test.iam.gserviceaccount.com",
            region="us-central1",
            zone="us-central1-a",
            bucket_name="test-bucket",
            dataset_id="test_dataset",
        )
        
        # Should not raise an exception
        config.validate()
    
    def test_validate_missing_project_id(self):
        """Test validation with missing project ID."""
        config = GCPConfig(
            project_id="",
            service_account="test@test.iam.gserviceaccount.com",
            region="us-central1",
            zone="us-central1-a",
            bucket_name="test-bucket",
            dataset_id="test_dataset",
        )
        
        with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT"):
            config.validate()
    
    def test_validate_missing_service_account(self):
        """Test validation with missing service account."""
        config = GCPConfig(
            project_id="test-project",
            service_account="",
            region="us-central1",
            zone="us-central1-a",
            bucket_name="test-bucket",
            dataset_id="test_dataset",
        )
        
        with pytest.raises(ValueError, match="SERVICE_ACCOUNT"):
            config.validate()


class TestPipelineConfig:
    """Test pipeline configuration."""
    
    def test_from_env_default_symbols(self):
        """Test creating PipelineConfig with default symbols."""
        gcp_config = GCPConfig(
            project_id="test-project",
            service_account="test@test.iam.gserviceaccount.com",
            region="us-central1",
            zone="us-central1-a",
            bucket_name="test-bucket",
            dataset_id="test_dataset",
        )
        
        with patch.dict(os.environ, {}, clear=True):
            config = PipelineConfig.from_env(gcp_config)
            
        assert config.symbols == ["META", "AAPL", "AMZN", "NFLX", "GOOGL"]
        assert config.composer_name == "stock-market-composer"
        assert "test-bucket" in config.python_file_uri
    
    def test_from_env_custom_symbols(self):
        """Test creating PipelineConfig with custom symbols."""
        gcp_config = GCPConfig(
            project_id="test-project",
            service_account="test@test.iam.gserviceaccount.com",
            region="us-central1",
            zone="us-central1-a",
            bucket_name="test-bucket",
            dataset_id="test_dataset",
        )
        
        env_vars = {
            "STOCK_SYMBOLS": "TSLA,NVDA,AMD",
            "COMPOSER_NAME": "custom-composer",
        }
        
        with patch.dict(os.environ, env_vars):
            config = PipelineConfig.from_env(gcp_config)
            
        assert config.symbols == ["TSLA", "NVDA", "AMD"]
        assert config.composer_name == "custom-composer"


class TestSparkConfig:
    """Test Spark configuration."""
    
    def test_default_config(self):
        """Test default Spark configuration."""
        config = SparkConfig()
        
        assert config.app_name == "transform-stock-market-data-pipeline"
        assert config.adaptive_enabled is True
        assert config.coalesce_partitions_enabled is True
        assert config.compression_codec == "snappy"
        
    def test_get_config_dict(self):
        """Test getting configuration as dictionary."""
        config = SparkConfig()
        config_dict = config.get_config_dict()
        
        expected_keys = {
            "spark.sql.adaptive.enabled",
            "spark.sql.adaptive.coalescePartitions.enabled",
            "spark.sql.parquet.compression.codec",
            "spark.serializer",
        }
        
        assert set(config_dict.keys()) == expected_keys
        assert config_dict["spark.sql.adaptive.enabled"] == "true"
        assert config_dict["spark.sql.adaptive.coalescePartitions.enabled"] == "true"


class TestGetConfig:
    """Test the get_config function."""
    
    def test_get_config_success(self):
        """Test successful configuration loading."""
        env_vars = {
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "SERVICE_ACCOUNT": "test@test.iam.gserviceaccount.com",
        }
        
        with patch.dict(os.environ, env_vars):
            gcp_config, pipeline_config, spark_config = get_config()
            
        assert isinstance(gcp_config, GCPConfig)
        assert isinstance(pipeline_config, PipelineConfig)
        assert isinstance(spark_config, SparkConfig)
        
        assert gcp_config.project_id == "test-project"
        assert gcp_config.service_account == "test@test.iam.gserviceaccount.com"
