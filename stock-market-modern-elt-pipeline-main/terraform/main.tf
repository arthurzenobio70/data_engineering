# Enhanced Terraform configuration for stock market pipeline
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Uncomment and configure for remote state storage
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "stock-market-pipeline"
  # }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Local values for resource naming
locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  
  common_labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    team        = var.team
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "composer.googleapis.com",
    "dataproc.googleapis.com",
    "iam.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Data Lake - Google Cloud Storage
resource "google_storage_bucket" "data_lake" {
  name          = "${local.resource_prefix}-datalake"
  location      = var.region
  storage_class = var.storage_class
  
  uniform_bucket_level_access = true
  force_destroy              = var.force_destroy_bucket

  labels = local.common_labels

  # Lifecycle management
  lifecycle_rule {
    condition {
      age = var.raw_data_retention_days
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age                   = var.processed_data_transition_days
      matches_storage_class = ["STANDARD"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  # Versioning
  versioning {
    enabled = var.enable_versioning
  }

  # Encryption
  dynamic "encryption" {
    for_each = var.kms_key_name != null ? [1] : []
    content {
      default_kms_key_name = var.kms_key_name
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Create bucket folders structure
resource "google_storage_bucket_object" "data_lake_folders" {
  for_each = toset([
    "raw/yahoo/",
    "raw/erp/",
    "processed/",
    "scripts/",
    "temp/"
  ])

  name    = each.value
  bucket  = google_storage_bucket.data_lake.name
  content = " "
}

# Upload initial data files
resource "google_storage_bucket_object" "dates_csv" {
  name         = "data/dates.csv"
  bucket       = google_storage_bucket.data_lake.name
  source       = "../data/dates.csv"
  content_type = "text/csv"
}

resource "google_storage_bucket_object" "erp_companies_csv" {
  name         = "raw/erp/erp_companies.csv"
  bucket       = google_storage_bucket.data_lake.name
  source       = "../data/erp_companies.csv"
  content_type = "text/csv"
}

# Upload Dataproc scripts
resource "google_storage_bucket_object" "dataproc_scripts" {
  for_each = {
    "transform_stock_data_pipeline.py" = "../dataproc_jobs/transform_stock_data_pipeline.py"
    "transform_stock_data_v2.py"       = "../dataproc_jobs/transform_stock_data_v2.py"
  }

  name         = "scripts/${each.key}"
  bucket       = google_storage_bucket.data_lake.name
  source       = each.value
  content_type = "text/x-python"
}

# Data Warehouse - BigQuery Dataset
resource "google_bigquery_dataset" "data_warehouse" {
  dataset_id    = "${local.resource_prefix}_dw"
  friendly_name = "Stock Market Data Warehouse"
  description   = "Data warehouse for stock market analysis"
  location      = var.region

  labels = local.common_labels

  # Access controls
  dynamic "access" {
    for_each = var.bigquery_dataset_access
    content {
      role          = access.value.role
      user_by_email = lookup(access.value, "user_by_email", null)
      group_by_email = lookup(access.value, "group_by_email", null)
      domain        = lookup(access.value, "domain", null)
      special_group = lookup(access.value, "special_group", null)
    }
  }

  # Default encryption
  dynamic "default_encryption_configuration" {
    for_each = var.kms_key_name != null ? [1] : []
    content {
      kms_key_name = var.kms_key_name
    }
  }

  delete_contents_on_destroy = var.force_destroy_bigquery

  depends_on = [google_project_service.required_apis]
}

# BigQuery Tables
resource "google_bigquery_table" "tables" {
  for_each = var.bigquery_tables

  dataset_id = google_bigquery_dataset.data_warehouse.dataset_id
  table_id   = each.key

  deletion_protection = var.enable_deletion_protection

  dynamic "schema" {
    for_each = fileexists("${path.module}/schemas/${each.key}_schema.json") ? [1] : []
    content {
      schema = file("${path.module}/schemas/${each.key}_schema.json")
    }
  }

  labels = merge(local.common_labels, {
    table_type = each.value.type
  })
}

# Cloud Composer Environment
resource "google_composer_environment" "pipeline_orchestrator" {
  name   = "${local.resource_prefix}-composer"
  region = var.region

  config {
    software_config {
      image_version = var.composer_image_version
      
      env_variables = merge(var.composer_env_variables, {
        GOOGLE_CLOUD_PROJECT = var.project_id
        SERVICE_ACCOUNT      = var.service_account_email
        REGION              = var.region
        BUCKET_NAME         = google_storage_bucket.data_lake.name
        DATASET_ID          = google_bigquery_dataset.data_warehouse.dataset_id
        ENVIRONMENT         = var.environment
      })

      python_version = var.composer_python_version
    }

    node_config {
      zone         = var.zone
      machine_type = var.composer_machine_type
      disk_size_gb = var.composer_disk_size
      
      service_account = var.service_account_email
      
      # Network configuration
      subnetwork = var.subnet_name
      
      # Tags for firewall rules
      tags = ["composer-worker"]
    }

    # Workloads configuration for better resource management
    workloads_config {
      scheduler {
        cpu        = var.composer_scheduler_cpu
        memory_gb  = var.composer_scheduler_memory
        storage_gb = var.composer_scheduler_storage
        count      = var.composer_scheduler_count
      }
      
      web_server {
        cpu       = var.composer_webserver_cpu
        memory_gb = var.composer_webserver_memory
        storage_gb = var.composer_webserver_storage
      }
      
      worker {
        cpu        = var.composer_worker_cpu
        memory_gb  = var.composer_worker_memory
        storage_gb = var.composer_worker_storage
        min_count  = var.composer_worker_min_count
        max_count  = var.composer_worker_max_count
      }
    }

    # Enable private IP
    dynamic "private_environment_config" {
      for_each = var.enable_private_ip ? [1] : []
      content {
        enable_private_endpoint = var.enable_private_endpoint
      }
    }
  }

  labels = local.common_labels

  depends_on = [
    google_project_service.required_apis,
    google_storage_bucket.data_lake
  ]
}

# Upload DAGs to Composer
data "google_composer_environment" "pipeline_orchestrator" {
  name   = google_composer_environment.pipeline_orchestrator.name
  region = var.region
}

locals {
  composer_bucket_name = regex("gs://([^/]+)", data.google_composer_environment.pipeline_orchestrator.config[0].dag_gcs_prefix)[0]
}

resource "google_storage_bucket_object" "dag_files" {
  for_each = fileset("${path.module}/../dags", "*.py")
  
  name   = "dags/${each.value}"
  bucket = local.composer_bucket_name
  source = "${path.module}/../dags/${each.value}"
  
  depends_on = [google_composer_environment.pipeline_orchestrator]
}

# IAM bindings for service account
resource "google_project_iam_member" "service_account_roles" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/dataproc.admin",
    "roles/composer.worker",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${var.service_account_email}"
}

# Cloud Monitoring for pipeline health
resource "google_monitoring_notification_channel" "email" {
  count = var.notification_email != null ? 1 : 0
  
  display_name = "Email Notification Channel"
  type         = "email"
  
  labels = {
    email_address = var.notification_email
  }
}

# Alerting policy for failed DAG runs
resource "google_monitoring_alert_policy" "dag_failure_alert" {
  count = var.notification_email != null ? 1 : 0
  
  display_name = "Stock Market Pipeline DAG Failure"
  combiner     = "OR"
  
  conditions {
    display_name = "DAG Failure Condition"
    
    condition_threshold {
      filter         = "resource.type=\"composer_environment\""
      duration       = "300s"
      comparison     = "COMPARISON_GT"
      threshold_value = 0
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email[0].id]
  
  alert_strategy {
    auto_close = "1800s"
  }
}
