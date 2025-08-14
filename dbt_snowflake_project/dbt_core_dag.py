"""
Enhanced dbt Airflow DAG with comprehensive data pipeline orchestration.
Includes data quality checks, monitoring, and failure handling.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.exceptions import AirflowException

# Configuration
DBT_PROJECT_DIR = Variable.get("dbt_project_dir", "/opt/airflow/dbt")
DBT_PROFILES_DIR = Variable.get("dbt_profiles_dir", "/opt/airflow/.dbt")
SNOWFLAKE_CONN_ID = Variable.get("snowflake_conn_id", "snowflake_default")
SLACK_CONN_ID = Variable.get("slack_conn_id", "slack_default")
ENVIRONMENT = Variable.get("environment", "dev")

# Email configuration
ALERT_EMAIL_RECIPIENTS = Variable.get("alert_email_recipients", "data-team@company.com").split(",")

# Default arguments
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ALERT_EMAIL_RECIPIENTS,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(hours=1),
}

# DAG definition
dag = DAG(
    'finance_data_pipeline',
    default_args=default_args,
    description='Comprehensive finance data pipeline with dbt Core',
    schedule_interval='0 6 * * *',  # Run daily at 6 AM UTC
    catchup=False,
    max_active_runs=1,
    max_active_tasks=10,
    tags=['dbt', 'finance', 'data-pipeline'],
    doc_md=__doc__,
)

def check_data_freshness(**context) -> Dict[str, Any]:
    """Check source data freshness and quality."""
    snowflake_hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)
    
    # Check data freshness
    freshness_checks = {
        'customers': 24,  # hours
        'orders': 12,
        'order_items': 12,
        'products': 72,
    }
    
    results = {}
    for table, max_hours in freshness_checks.items():
        query = f"""
        SELECT 
            DATEDIFF('hour', MAX(_loaded_at), CURRENT_TIMESTAMP()) as hours_since_last_load
        FROM raw_data.{table}
        """
        
        result = snowflake_hook.get_first(query)
        hours_since_load = result[0] if result else float('inf')
        
        results[table] = {
            'hours_since_load': hours_since_load,
            'is_fresh': hours_since_load <= max_hours,
            'max_allowed_hours': max_hours
        }
        
        if not results[table]['is_fresh']:
            logging.warning(f"Data freshness issue: {table} last loaded {hours_since_load} hours ago")
    
    # Push results to XCom for downstream tasks
    context['task_instance'].xcom_push(key='freshness_results', value=results)
    
    # Raise exception if critical tables are stale
    critical_tables = ['orders', 'order_items']
    stale_critical_tables = [
        table for table in critical_tables 
        if not results[table]['is_fresh']
    ]
    
    if stale_critical_tables:
        raise AirflowException(f"Critical tables are stale: {stale_critical_tables}")
    
    return results

def validate_dbt_artifacts(**context) -> bool:
    """Validate dbt artifacts and configuration."""
    try:
        # Check if dbt_project.yml exists and is valid
        dbt_project_path = os.path.join(DBT_PROJECT_DIR, "dbt_project.yml")
        if not os.path.exists(dbt_project_path):
            raise AirflowException(f"dbt_project.yml not found at {dbt_project_path}")
        
        # Check if profiles.yml exists
        profiles_path = os.path.join(DBT_PROFILES_DIR, "profiles.yml")
        if not os.path.exists(profiles_path):
            raise AirflowException(f"profiles.yml not found at {profiles_path}")
        
        logging.info("dbt artifacts validation successful")
        return True
        
    except Exception as e:
        logging.error(f"dbt artifacts validation failed: {str(e)}")
        raise AirflowException(f"dbt artifacts validation failed: {str(e)}")

def send_success_notification(**context):
    """Send success notification with pipeline metrics."""
    # Get run statistics
    dag_run = context['dag_run']
    task_instances = dag_run.get_task_instances()
    
    success_count = len([ti for ti in task_instances if ti.state == 'success'])
    total_count = len(task_instances)
    duration = (datetime.now() - dag_run.start_date).total_seconds() / 60
    
    message = f"""
    ✅ Finance Data Pipeline Completed Successfully!
    
    📊 Pipeline Statistics:
    • Duration: {duration:.1f} minutes
    • Tasks: {success_count}/{total_count} successful
    • Environment: {ENVIRONMENT}
    • Execution Date: {context['ds']}
    
    🎯 Key Metrics:
    • All data quality tests passed
    • Models updated successfully
    • Documentation generated
    """
    
    context['task_instance'].xcom_push(key='success_message', value=message)
    logging.info(message)

# Start of DAG tasks
start = DummyOperator(
    task_id='start',
    dag=dag,
)

# Pre-processing task group
with TaskGroup('pre_processing', dag=dag) as pre_processing:
    
    data_freshness_check = PythonOperator(
        task_id='check_data_freshness',
        python_callable=check_data_freshness,
        provide_context=True,
    )
    
    dbt_artifacts_validation = PythonOperator(
        task_id='validate_dbt_artifacts',
        python_callable=validate_dbt_artifacts,
        provide_context=True,
    )
    
    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt deps --profiles-dir {DBT_PROFILES_DIR}',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    [data_freshness_check, dbt_artifacts_validation] >> dbt_deps

# Source freshness checks
source_freshness = BashOperator(
    task_id='source_freshness',
    bash_command=f'cd {DBT_PROJECT_DIR} && dbt source freshness --profiles-dir {DBT_PROFILES_DIR}',
    env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    dag=dag,
)

# Seed data
seed_data = BashOperator(
    task_id='seed_data',
    bash_command=f'cd {DBT_PROJECT_DIR} && dbt seed --profiles-dir {DBT_PROFILES_DIR} --full-refresh',
    env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    dag=dag,
)

# Snapshots
run_snapshots = BashOperator(
    task_id='run_snapshots',
    bash_command=f'cd {DBT_PROJECT_DIR} && dbt snapshot --profiles-dir {DBT_PROFILES_DIR}',
    env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    dag=dag,
)

# dbt model execution task group
with TaskGroup('dbt_models', dag=dag) as dbt_models:
    
    # Staging models
    dbt_run_staging = BashOperator(
        task_id='run_staging_models',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROFILES_DIR} --select staging',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    # Intermediate models
    dbt_run_intermediate = BashOperator(
        task_id='run_intermediate_models',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROFILES_DIR} --select intermediate',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    # Marts models
    dbt_run_marts = BashOperator(
        task_id='run_marts_models',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROFILES_DIR} --select marts',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    dbt_run_staging >> dbt_run_intermediate >> dbt_run_marts

# Testing task group
with TaskGroup('dbt_tests', dag=dag) as dbt_tests:
    
    # Data quality tests
    dbt_test_data_quality = BashOperator(
        task_id='test_data_quality',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROFILES_DIR} --select tag:data_quality',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    # Data integrity tests
    dbt_test_data_integrity = BashOperator(
        task_id='test_data_integrity',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROFILES_DIR} --select tag:data_integrity',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    # Business logic tests
    dbt_test_business_logic = BashOperator(
        task_id='test_business_logic',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROFILES_DIR} --select tag:business_logic',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    # All other tests
    dbt_test_all = BashOperator(
        task_id='test_all_remaining',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROFILES_DIR} --exclude tag:data_quality tag:data_integrity tag:business_logic',
        env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    )
    
    [dbt_test_data_quality, dbt_test_data_integrity] >> dbt_test_business_logic >> dbt_test_all

# Documentation generation
generate_docs = BashOperator(
    task_id='generate_docs',
    bash_command=f'cd {DBT_PROJECT_DIR} && dbt docs generate --profiles-dir {DBT_PROFILES_DIR}',
    env={'DBT_PROFILES_DIR': DBT_PROFILES_DIR},
    dag=dag,
)

# Post-processing tasks
with TaskGroup('post_processing', dag=dag) as post_processing:
    
    # Archive artifacts
    archive_artifacts = BashOperator(
        task_id='archive_artifacts',
        bash_command=f'''
        cd {DBT_PROJECT_DIR}
        DATE=$(date +%Y%m%d_%H%M%S)
        tar -czf /tmp/dbt_artifacts_$DATE.tar.gz target/
        # Upload to S3 or other storage
        echo "Artifacts archived successfully"
        ''',
    )
    
    # Send success notification
    success_notification = PythonOperator(
        task_id='send_success_notification',
        python_callable=send_success_notification,
        provide_context=True,
    )
    
    archive_artifacts >> success_notification

# Failure notification
failure_notification = SlackWebhookOperator(
    task_id='failure_notification',
    http_conn_id=SLACK_CONN_ID,
    message='''
    ❌ Finance Data Pipeline Failed!
    
    Pipeline: {{ dag.dag_id }}
    Execution Date: {{ ds }}
    Failed Task: {{ task_instance.task_id }}
    Log: {{ task_instance.log_url }}
    ''',
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag,
)

# End task
end = DummyOperator(
    task_id='end',
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    dag=dag,
)

# Define task dependencies
start >> pre_processing >> source_freshness
source_freshness >> [seed_data, run_snapshots]
[seed_data, run_snapshots] >> dbt_models
dbt_models >> dbt_tests
dbt_tests >> generate_docs
generate_docs >> post_processing >> end

# Failure handling
[pre_processing, source_freshness, seed_data, run_snapshots, 
 dbt_models, dbt_tests, generate_docs, post_processing] >> failure_notification
