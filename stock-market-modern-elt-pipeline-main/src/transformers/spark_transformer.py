"""
Spark-based data transformations for stock market data.
"""

import logging
from typing import Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, count, isnan, isnull, to_date, when
from pyspark.sql.types import DateType, FloatType, LongType, StringType

from ..config.settings import SparkConfig


class SparkTransformer:
    """Handles Spark-based data transformations."""
    
    def __init__(self, spark_config: SparkConfig) -> None:
        """
        Initialize the Spark transformer.
        
        Args:
            spark_config: Spark configuration settings
        """
        self.spark_config = spark_config
        self.spark: Optional[SparkSession] = None
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self) -> "SparkTransformer":
        """Enter context manager and create Spark session."""
        self.spark = self._create_spark_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and stop Spark session."""
        if self.spark:
            self.spark.stop()
            self.logger.info("Spark session stopped")
    
    def _create_spark_session(self) -> SparkSession:
        """Create an optimized Spark session."""
        builder = SparkSession.builder.appName(self.spark_config.app_name)
        
        # Apply configuration
        for key, value in self.spark_config.get_config_dict().items():
            builder = builder.config(key, value)
        
        session = builder.getOrCreate()
        self.logger.info("Spark session created successfully")
        return session
    
    def read_json_data(self, input_path: str) -> Optional[DataFrame]:
        """
        Read JSON data from GCS with error handling.
        
        Args:
            input_path: Path to JSON files
            
        Returns:
            DataFrame or None if error
        """
        try:
            self.logger.info(f"Reading JSON data from: {input_path}")
            df = self.spark.read.option("multiline", "true").json(input_path)
            
            if not self._validate_dataframe(df, "Yahoo Finance API"):
                return None
            
            return df
        except Exception as e:
            self.logger.error(f"Error reading JSON data: {str(e)}")
            return None
    
    def read_csv_data(self, input_path: str) -> Optional[DataFrame]:
        """
        Read CSV data from GCS with error handling.
        
        Args:
            input_path: Path to CSV file
            
        Returns:
            DataFrame or None if error
        """
        try:
            self.logger.info(f"Reading CSV data from: {input_path}")
            df = self.spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)
            
            if not self._validate_dataframe(df, "ERP"):
                return None
            
            return df
        except Exception as e:
            self.logger.error(f"Error reading CSV data: {str(e)}")
            return None
    
    def transform_stock_data(self, df_api: DataFrame) -> DataFrame:
        """
        Transform stock data from Yahoo Finance format.
        
        Args:
            df_api: DataFrame with API data
            
        Returns:
            Transformed DataFrame
        """
        self.logger.info("Starting stock data transformation")
        
        # Extract data from Yahoo Finance format
        df_stock_price = df_api.selectExpr(
            "ticker as Ticker",
            "open as Open",
            "high as High",
            "low as Low",
            "close as Close",
            "volume as Volume",
            "date as DateKey"
        )
        
        # Convert string DateKey to date format
        df_stock_price = df_stock_price.withColumn(
            "DateKey",
            to_date(col("DateKey"), "yyyy-MM-dd")
        )
        
        # Ensure data types and order columns
        df_stock_price = df_stock_price.select(
            col("DateKey").cast(DateType()),
            col("Ticker").cast(StringType()),
            col("Open").cast(FloatType()),
            col("High").cast(FloatType()),
            col("Low").cast(FloatType()),
            col("Close").cast(FloatType()),
            col("Volume").cast(LongType())
        )
        
        # Filter records with required values
        df_stock_price = df_stock_price.filter(
            col("DateKey").isNotNull() &
            col("Ticker").isNotNull() &
            col("Open").isNotNull() &
            col("Close").isNotNull()
        )
        
        # Remove duplicates
        df_stock_price = df_stock_price.dropDuplicates(["DateKey", "Ticker"])
        
        # Cache for performance
        df_stock_price.cache()
        
        record_count = df_stock_price.count()
        self.logger.info(f"Transformation completed: {record_count} records processed")
        return df_stock_price
    
    def create_company_dimension(self, df_erp: DataFrame) -> DataFrame:
        """
        Create company dimension from ERP data.
        
        Args:
            df_erp: ERP DataFrame
            
        Returns:
            Company dimension DataFrame
        """
        self.logger.info("Creating company dimension")
        
        df_dim_company = df_erp.selectExpr(
            "Symbol as Symbol",
            "CompanyName as CompanyName"
        ).filter(
            col("Symbol").isNotNull() &
            col("CompanyName").isNotNull()
        ).distinct()
        
        record_count = df_dim_company.count()
        self.logger.info(f"Company dimension created: {record_count} records")
        return df_dim_company
    
    def create_exchange_dimension(self, df_erp: DataFrame) -> DataFrame:
        """
        Create exchange dimension from ERP data.
        
        Args:
            df_erp: ERP DataFrame
            
        Returns:
            Exchange dimension DataFrame
        """
        self.logger.info("Creating exchange dimension")
        
        df_dim_exchange = df_erp.selectExpr(
            "Exchange as ExchangeCode",
            "ExchangeName as ExchangeName"
        ).filter(
            col("Exchange").isNotNull() &
            col("ExchangeName").isNotNull()
        ).distinct()
        
        record_count = df_dim_exchange.count()
        self.logger.info(f"Exchange dimension created: {record_count} records")
        return df_dim_exchange
    
    def write_parquet_data(self, df: DataFrame, output_path: str, df_name: str) -> bool:
        """
        Write DataFrame to Parquet format with error handling.
        
        Args:
            df: DataFrame to write
            output_path: Output path
            df_name: DataFrame name for logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Writing {df_name} to: {output_path}")
            
            df.write \
                .mode("overwrite") \
                .option("compression", "snappy") \
                .parquet(output_path)
            
            self.logger.info(f"{df_name} written successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error writing {df_name}: {str(e)}")
            return False
    
    def _validate_dataframe(self, df: DataFrame, df_name: str) -> bool:
        """
        Validate if DataFrame is not empty and log basic statistics.
        
        Args:
            df: DataFrame to validate
            df_name: DataFrame name for logging
            
        Returns:
            True if valid, False otherwise
        """
        count_rows = df.count()
        
        if count_rows == 0:
            self.logger.error(f"DataFrame {df_name} is empty")
            return False
        
        self.logger.info(f"DataFrame {df_name}: {count_rows} rows loaded")
        return True
    
    def check_data_quality(self, df: DataFrame, df_name: str) -> None:
        """
        Check data quality and log statistics.
        
        Args:
            df: DataFrame to check
            df_name: DataFrame name
        """
        total_rows = df.count()
        
        # Check null values in all columns
        null_counts = df.select([
            count(when(isnan(c) | isnull(c), c)).alias(c)
            for c in df.columns
        ]).collect()[0]
        
        self.logger.info(f"Data quality for {df_name}:")
        self.logger.info(f"  Total rows: {total_rows}")
        
        for col_name, null_count in null_counts.asDict().items():
            if null_count > 0:
                percentage = (null_count / total_rows) * 100
                self.logger.warning(
                    f"  Column '{col_name}': {null_count} null values ({percentage:.2f}%)"
                )
