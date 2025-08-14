"""
Modern Stock Market Data Transformation Pipeline
================================================

A refactored PySpark job using modern software engineering practices.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_path = current_dir.parent / "src"
sys.path.append(str(src_path))

from config.settings import SparkConfig
from transformers.spark_transformer import SparkTransformer


def setup_logging() -> logging.Logger:
    """Configure the logging system."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Stock market data transformation pipeline"
    )
    parser.add_argument(
        "--bucket", 
        required=True, 
        help="GCS bucket name"
    )
    parser.add_argument(
        "--previous_day", 
        required=True, 
        help="Previous day in YYYY-MM-DD format"
    )
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate input arguments."""
    if not args.bucket:
        raise ValueError("Bucket name is required")
    if not args.previous_day:
        raise ValueError("Previous day is required")


def main() -> None:
    """Main pipeline function."""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting stock market data transformation pipeline")
    
    try:
        # Parse and validate arguments
        args = parse_arguments()
        validate_arguments(args)
        
        # Define paths
        input_api_path = f"gs://{args.bucket}/raw/yahoo/*_{args.previous_day}.json"
        input_erp_path = f"gs://{args.bucket}/raw/ERP/erp_companies.csv"
        output_fact_path = f"gs://{args.bucket}/processed/fact_stock_price.parquet"
        output_dim_company_path = f"gs://{args.bucket}/processed/dim_company.parquet"
        output_dim_exchange_path = f"gs://{args.bucket}/processed/dim_exchange.parquet"
        
        # Initialize Spark configuration
        spark_config = SparkConfig()
        
        # Use context manager for Spark session
        with SparkTransformer(spark_config) as transformer:
            logger.info("Spark session initialized successfully")
            
            # Read input data
            df_api = transformer.read_json_data(input_api_path)
            df_erp = transformer.read_csv_data(input_erp_path)
            
            if df_api is None or df_erp is None:
                logger.error("Failed to load input data")
                sys.exit(1)
            
            # Check data quality
            transformer.check_data_quality(df_api, "Yahoo Finance API")
            transformer.check_data_quality(df_erp, "ERP")
            
            # Transform data
            logger.info("Starting data transformations")
            df_stock_price = transformer.transform_stock_data(df_api)
            df_dim_company = transformer.create_company_dimension(df_erp)
            df_dim_exchange = transformer.create_exchange_dimension(df_erp)
            
            # Write output data
            logger.info("Writing transformed data")
            success_results = [
                transformer.write_parquet_data(
                    df_stock_price, output_fact_path, "Stock Price Fact Table"
                ),
                transformer.write_parquet_data(
                    df_dim_company, output_dim_company_path, "Company Dimension"
                ),
                transformer.write_parquet_data(
                    df_dim_exchange, output_dim_exchange_path, "Exchange Dimension"
                ),
            ]
            
            if all(success_results):
                logger.info("Pipeline completed successfully!")
            else:
                logger.error("Pipeline completed with errors")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Critical error in pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
