from datetime import datetime, timedelta
import os
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

from google.cloud import storage
import yfinance as yf


# Parameters
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
SERVICE_ACCOUNT = os.environ.get("SERVICE_ACCOUNT")
REGION = os.environ.get("REGION")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
PYTHON_FILE_URI = f"gs://{BUCKET_NAME}/scripts/transform_stock_data_pipeline.py"
DATASET_ID = os.environ.get("DATASET_ID")

if not all([PROJECT_ID, SERVICE_ACCOUNT, REGION, BUCKET_NAME]):
    raise ValueError("Missing one or more required environment variables.")

SYMBOLS = ["META", "AAPL", "AMZN", "NFLX", "GOOGL"]


# Python Functions
def yahoo_finance_to_gcs(ds, **kwargs):
    # Get previous day
    previous_day = datetime.strptime(ds, "%Y-%m-%d") - timedelta(days=1)
    previous_day_str = previous_day.strftime("%Y-%m-%d")

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    for symbol in SYMBOLS:
        try:
            # Create Yahoo Finance ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data from previous day
            data = ticker.history(
                start=previous_day, 
                end=previous_day + timedelta(days=1),
                interval="1d"
            )
            
            if not data.empty:
                # Prepare data in JSON format
                stock_data = {
                    "ticker": symbol,
                    "date": previous_day_str,
                    "open": float(data['Open'].iloc[0]),
                    "high": float(data['High'].iloc[0]),
                    "low": float(data['Low'].iloc[0]),
                    "close": float(data['Close'].iloc[0]),
                    "volume": int(data['Volume'].iloc[0]),
                    "timestamp": int(previous_day.timestamp() * 1000)  # For compatibility
                }
                
                # Upload to GCS
                blob = bucket.blob(
                    f"raw/yahoo/yahoo_{symbol}_{previous_day_str}.json"
                )
                blob.upload_from_string(
                    json.dumps(stock_data), 
                    content_type="application/json"
                )
                print(f"Successfully uploaded data for {symbol}")
            else:
                print(f"No data available for {symbol} on {previous_day_str}")
                
        except Exception as e:
            print(f"Error processing symbol {symbol}: {e}")


# DAG
default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

with DAG(
    dag_id="stock_market_dag",
    description='Daily data pipeline to generate dims and facts for stock market analysis',
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False
) as dag:

    fetch_and_upload_raw = PythonOperator(
        task_id="fetch_and_upload",
        python_callable=yahoo_finance_to_gcs,
    )

    # Wait for files to be loaded in raw/ERP in GCS bucket
    wait_for_erp_companies_file = GCSObjectExistenceSensor(
        task_id="wait_for_erp_companies_file",
        bucket=BUCKET_NAME,
        object="raw/ERP/erp_companies.csv",
        timeout=600,  # 10 minutes
        poke_interval=30,
    )

    # Set up Dataproc serverless and execute transformation job
    run_dataproc_job = DataprocCreateBatchOperator(
        task_id="run_transform_stock_data_pipeline",
        project_id=PROJECT_ID,
        region=REGION,
        batch_id="dataproc-batch-{{ ds_nodash }}",
        batch={
            "pyspark_batch": {
                "main_python_file_uri": PYTHON_FILE_URI,
                "args": [
                    "--bucket", BUCKET_NAME,
                    "--previous_day", "{{ macros.ds_add(ds, -1) }}"
                ]
            },
            "environment_config": {
                "execution_config": {
                    "service_account": SERVICE_ACCOUNT,
                }
            }
        }
    )

    # Add stock price data to BigQuery with append
    load_fact_stock_price = GCSToBigQueryOperator(
        task_id="load_fact_stock_price",
        bucket=BUCKET_NAME,
        source_objects=["processed/fact_stock_price.parquet"],
        destination_project_dataset_table=f"{PROJECT_ID}.{DATASET_ID}.fact_stock_price",
        source_format="PARQUET",
        write_disposition="WRITE_APPEND",
        location=REGION,
    )

    # Load dimension tables
    load_dim_company = GCSToBigQueryOperator(
        task_id="load_dim_company",
        bucket=BUCKET_NAME,
        source_objects=["processed/dim_company.parquet"],
        destination_project_dataset_table=f"{PROJECT_ID}.{DATASET_ID}.dim_company",
        source_format="PARQUET",
        write_disposition="WRITE_TRUNCATE",
        location=REGION,
    )

    load_dim_exchange = GCSToBigQueryOperator(
        task_id="load_dim_exchange",
        bucket=BUCKET_NAME,
        source_objects=["processed/dim_exchange.parquet"],
        destination_project_dataset_table=f"{PROJECT_ID}.{DATASET_ID}.dim_exchange",
        source_format="PARQUET",
        write_disposition="WRITE_TRUNCATE",
        location=REGION,
    )

    # Define dependencies
    fetch_and_upload_raw >> wait_for_erp_companies_file >> run_dataproc_job
    run_dataproc_job >> [load_fact_stock_price, load_dim_company, load_dim_exchange]
