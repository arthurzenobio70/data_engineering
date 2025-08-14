"""
Modern Stock Market Data Pipeline DAG
=====================================

A refactored version of the stock market data pipeline using modern software engineering practices.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config.settings import get_config
from extractors.yahoo_finance import YahooFinanceExtractor


# Configuration
gcp_config, pipeline_config, spark_config = get_config()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_yahoo_finance_data(ds: str, **kwargs) -> None:
    """
    Extract stock data from Yahoo Finance and upload to GCS.
    
    Args:
        ds: Execution date as string
        **kwargs: Additional context from Airflow
    """
    # Get previous day
    execution_date = datetime.strptime(ds, "%Y-%m-%d")
    previous_day = execution_date - timedelta(days=1)
    
    # Initialize extractor
    extractor = YahooFinanceExtractor(gcp_config.bucket_name)
    
    # Extract data
    results = extractor.extract_stock_data(pipeline_config.symbols, previous_day)
    
    # Log results
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    logger.info(f"Extraction completed: {successful}/{total} symbols successful")
    
    if successful == 0:
        raise ValueError("No stock data was successfully extracted")


# DAG definition
default_args = {
    "owner": "data-engineering-team",
    "start_date": datetime(2024, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
    "depends_on_past": False,
}

with DAG(
    dag_id="stock_market_pipeline_v2",
    description="Modern stock market data pipeline with improved architecture",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["stock-market", "finance", "etl", "bigquery"],
) as dag:

    # Task 1: Extract data from Yahoo Finance
    extract_stock_data = PythonOperator(
        task_id="extract_yahoo_finance_data",
        python_callable=extract_yahoo_finance_data,
        doc_md="""
        ### Extract Stock Data
        
        Extracts daily stock price data from Yahoo Finance for configured symbols.
        Data is stored in GCS in JSON format for further processing.
        """,
    )

    # Task 2: Wait for ERP companies file
    wait_for_erp_file = GCSObjectExistenceSensor(
        task_id="wait_for_erp_companies_file",
        bucket=gcp_config.bucket_name,
        object="raw/ERP/erp_companies.csv",
        timeout=600,  # 10 minutes
        poke_interval=30,
        doc_md="""
        ### Wait for ERP File
        
        Waits for the ERP companies file to be available in GCS.
        This file contains company and exchange dimension data.
        """,
    )

    # Task 3: Run Dataproc transformation job
    run_transformation = DataprocCreateBatchOperator(
        task_id="run_spark_transformation",
        project_id=gcp_config.project_id,
        region=gcp_config.region,
        batch_id="stock-pipeline-{{ ds_nodash }}-{{ run_id }}",
        batch={
            "pyspark_batch": {
                "main_python_file_uri": pipeline_config.python_file_uri,
                "args": [
                    "--bucket", gcp_config.bucket_name,
                    "--previous_day", "{{ macros.ds_add(ds, -1) }}"
                ]
            },
            "environment_config": {
                "execution_config": {
                    "service_account": gcp_config.service_account,
                }
            }
        },
        doc_md="""
        ### Spark Transformation
        
        Runs PySpark job on Dataproc Serverless to transform raw data
        into dimensional model (fact and dimension tables).
        """,
    )

    # Task 4: Load fact table to BigQuery
    load_fact_table = GCSToBigQueryOperator(
        task_id="load_fact_stock_price",
        bucket=gcp_config.bucket_name,
        source_objects=["processed/fact_stock_price.parquet"],
        destination_project_dataset_table=f"{gcp_config.project_id}.{gcp_config.dataset_id}.fact_stock_price",
        source_format="PARQUET",
        write_disposition="WRITE_APPEND",
        location=gcp_config.region,
        doc_md="""
        ### Load Fact Table
        
        Loads the transformed stock price fact table from GCS to BigQuery.
        Uses APPEND mode to add new daily data.
        """,
    )

    # Task 5: Load company dimension
    load_company_dimension = GCSToBigQueryOperator(
        task_id="load_dim_company",
        bucket=gcp_config.bucket_name,
        source_objects=["processed/dim_company.parquet"],
        destination_project_dataset_table=f"{gcp_config.project_id}.{gcp_config.dataset_id}.dim_company",
        source_format="PARQUET",
        write_disposition="WRITE_TRUNCATE",
        location=gcp_config.region,
        doc_md="""
        ### Load Company Dimension
        
        Loads the company dimension table from GCS to BigQuery.
        Uses TRUNCATE mode to replace all data.
        """,
    )

    # Task 6: Load exchange dimension
    load_exchange_dimension = GCSToBigQueryOperator(
        task_id="load_dim_exchange",
        bucket=gcp_config.bucket_name,
        source_objects=["processed/dim_exchange.parquet"],
        destination_project_dataset_table=f"{gcp_config.project_id}.{gcp_config.dataset_id}.dim_exchange",
        source_format="PARQUET",
        write_disposition="WRITE_TRUNCATE",
        location=gcp_config.region,
        doc_md="""
        ### Load Exchange Dimension
        
        Loads the exchange dimension table from GCS to BigQuery.
        Uses TRUNCATE mode to replace all data.
        """,
    )

    # Define task dependencies
    extract_stock_data >> wait_for_erp_file >> run_transformation
    run_transformation >> [load_fact_table, load_company_dimension, load_exchange_dimension]
