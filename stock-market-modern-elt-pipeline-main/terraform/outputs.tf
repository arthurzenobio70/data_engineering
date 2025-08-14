# Terraform outputs for stock market pipeline

# Project Information
output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

# Storage Outputs
output "data_lake_bucket_name" {
  description = "Name of the data lake bucket"
  value       = google_storage_bucket.data_lake.name
}

output "data_lake_bucket_url" {
  description = "URL of the data lake bucket"
  value       = google_storage_bucket.data_lake.url
}

output "data_lake_bucket_self_link" {
  description = "Self link of the data lake bucket"
  value       = google_storage_bucket.data_lake.self_link
}

# BigQuery Outputs
output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.data_warehouse.dataset_id
}

output "bigquery_dataset_location" {
  description = "BigQuery dataset location"
  value       = google_bigquery_dataset.data_warehouse.location
}

output "bigquery_tables" {
  description = "Map of BigQuery table IDs"
  value = {
    for table_name, table in google_bigquery_table.tables :
    table_name => table.table_id
  }
}

# Composer Outputs
output "composer_environment_name" {
  description = "Name of the Composer environment"
  value       = google_composer_environment.pipeline_orchestrator.name
}

output "composer_environment_region" {
  description = "Region of the Composer environment"
  value       = google_composer_environment.pipeline_orchestrator.region
}

output "composer_airflow_uri" {
  description = "URI of the Airflow web server"
  value       = google_composer_environment.pipeline_orchestrator.config[0].airflow_uri
}

output "composer_dag_gcs_prefix" {
  description = "GCS prefix for DAG files"
  value       = google_composer_environment.pipeline_orchestrator.config[0].dag_gcs_prefix
}

output "composer_gcs_bucket" {
  description = "GCS bucket used by Composer"
  value       = local.composer_bucket_name
}

# Network Information
output "composer_node_config" {
  description = "Composer node configuration"
  value = {
    zone         = google_composer_environment.pipeline_orchestrator.config[0].node_config[0].zone
    machine_type = google_composer_environment.pipeline_orchestrator.config[0].node_config[0].machine_type
    disk_size_gb = google_composer_environment.pipeline_orchestrator.config[0].node_config[0].disk_size_gb
  }
}

# Service Account
output "service_account_email" {
  description = "Service account email used by the pipeline"
  value       = var.service_account_email
}

# Pipeline Configuration
output "pipeline_configuration" {
  description = "Pipeline configuration summary"
  value = {
    stock_symbols    = var.stock_symbols
    schedule         = var.pipeline_schedule
    retention_days   = var.raw_data_retention_days
    storage_class    = var.storage_class
  }
}

# Connection Strings
output "bigquery_connection_string" {
  description = "BigQuery connection string for external tools"
  value       = "bigquery://${var.project_id}/${google_bigquery_dataset.data_warehouse.dataset_id}"
}

output "gcs_data_paths" {
  description = "Important GCS paths for the pipeline"
  value = {
    raw_yahoo_data    = "gs://${google_storage_bucket.data_lake.name}/raw/yahoo/"
    raw_erp_data      = "gs://${google_storage_bucket.data_lake.name}/raw/erp/"
    processed_data    = "gs://${google_storage_bucket.data_lake.name}/processed/"
    dataproc_scripts  = "gs://${google_storage_bucket.data_lake.name}/scripts/"
    temp_data         = "gs://${google_storage_bucket.data_lake.name}/temp/"
  }
}

# Monitoring
output "monitoring_enabled" {
  description = "Whether monitoring and alerting is enabled"
  value       = var.notification_email != null
}

output "notification_email" {
  description = "Email address for notifications (if configured)"
  value       = var.notification_email
  sensitive   = true
}

# Resource Labels
output "resource_labels" {
  description = "Common labels applied to resources"
  value = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    team        = var.team
  }
}

# Deployment Information
output "terraform_workspace" {
  description = "Terraform workspace used for deployment"
  value       = terraform.workspace
}

output "deployment_timestamp" {
  description = "Timestamp of the deployment"
  value       = timestamp()
}
