# Enhanced Terraform variables for stock market pipeline

# Project Configuration
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  validation {
    condition     = length(var.project_id) > 0
    error_message = "Project ID cannot be empty."
  }
}

variable "project_name" {
  description = "Name of the project for resource naming"
  type        = string
  default     = "stock-market-pipeline"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "team" {
  description = "Team responsible for the project"
  type        = string
  default     = "data-engineering"
}

# Service Account Configuration
variable "service_account_email" {
  description = "Service account email for the pipeline"
  type        = string
  validation {
    condition     = can(regex(".*@.*\\.iam\\.gserviceaccount\\.com$", var.service_account_email))
    error_message = "Service account email must be in the format: name@project.iam.gserviceaccount.com"
  }
}

# Geographic Configuration
variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for resources"
  type        = string
  default     = "us-central1-a"
}

# Network Configuration
variable "subnet_name" {
  description = "Subnet for Composer environment"
  type        = string
  default     = "default"
}

variable "enable_private_ip" {
  description = "Enable private IP for Composer environment"
  type        = bool
  default     = false
}

variable "enable_private_endpoint" {
  description = "Enable private endpoint for Composer environment"
  type        = bool
  default     = false
}

# Storage Configuration
variable "storage_class" {
  description = "Storage class for the data lake bucket"
  type        = string
  default     = "STANDARD"
  validation {
    condition = contains([
      "STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"
    ], var.storage_class)
    error_message = "Storage class must be one of: STANDARD, NEARLINE, COLDLINE, ARCHIVE."
  }
}

variable "enable_versioning" {
  description = "Enable versioning for the storage bucket"
  type        = bool
  default     = true
}

variable "raw_data_retention_days" {
  description = "Number of days to retain raw data before deletion"
  type        = number
  default     = 90
}

variable "processed_data_transition_days" {
  description = "Number of days before transitioning processed data to cheaper storage"
  type        = number
  default     = 30
}

variable "force_destroy_bucket" {
  description = "Allow Terraform to destroy the bucket even if it contains objects"
  type        = bool
  default     = false
}

# BigQuery Configuration
variable "bigquery_tables" {
  description = "BigQuery tables to create"
  type = map(object({
    type = string
  }))
  default = {
    fact_stock_price = { type = "fact" }
    dim_company      = { type = "dimension" }
    dim_exchange     = { type = "dimension" }
    dim_date         = { type = "dimension" }
  }
}

variable "bigquery_dataset_access" {
  description = "Access control for BigQuery dataset"
  type = list(object({
    role           = string
    user_by_email  = optional(string)
    group_by_email = optional(string)
    domain         = optional(string)
    special_group  = optional(string)
  }))
  default = []
}

variable "force_destroy_bigquery" {
  description = "Allow Terraform to destroy BigQuery dataset and tables"
  type        = bool
  default     = false
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for BigQuery tables"
  type        = bool
  default     = true
}

# Composer Configuration
variable "composer_image_version" {
  description = "Composer image version"
  type        = string
  default     = "composer-3-airflow-2.10.5-build.6"
}

variable "composer_python_version" {
  description = "Python version for Composer"
  type        = string
  default     = "3"
}

variable "composer_machine_type" {
  description = "Machine type for Composer nodes"
  type        = string
  default     = "n1-standard-1"
}

variable "composer_disk_size" {
  description = "Disk size in GB for Composer nodes"
  type        = number
  default     = 100
}

# Composer Workloads Configuration
variable "composer_scheduler_cpu" {
  description = "CPU allocation for Composer scheduler"
  type        = number
  default     = 0.5
}

variable "composer_scheduler_memory" {
  description = "Memory allocation in GB for Composer scheduler"
  type        = number
  default     = 1.875
}

variable "composer_scheduler_storage" {
  description = "Storage allocation in GB for Composer scheduler"
  type        = number
  default     = 1
}

variable "composer_scheduler_count" {
  description = "Number of Composer scheduler instances"
  type        = number
  default     = 1
}

variable "composer_webserver_cpu" {
  description = "CPU allocation for Composer web server"
  type        = number
  default     = 0.5
}

variable "composer_webserver_memory" {
  description = "Memory allocation in GB for Composer web server"
  type        = number
  default     = 1.875
}

variable "composer_webserver_storage" {
  description = "Storage allocation in GB for Composer web server"
  type        = number
  default     = 1
}

variable "composer_worker_cpu" {
  description = "CPU allocation for Composer workers"
  type        = number
  default     = 0.5
}

variable "composer_worker_memory" {
  description = "Memory allocation in GB for Composer workers"
  type        = number
  default     = 1.875
}

variable "composer_worker_storage" {
  description = "Storage allocation in GB for Composer workers"
  type        = number
  default     = 1
}

variable "composer_worker_min_count" {
  description = "Minimum number of Composer workers"
  type        = number
  default     = 1
}

variable "composer_worker_max_count" {
  description = "Maximum number of Composer workers"
  type        = number
  default     = 3
}

variable "composer_env_variables" {
  description = "Additional environment variables for Composer"
  type        = map(string)
  default     = {}
}

# Security Configuration
variable "kms_key_name" {
  description = "KMS key for encryption (optional)"
  type        = string
  default     = null
}

# Monitoring Configuration
variable "notification_email" {
  description = "Email for monitoring notifications"
  type        = string
  default     = null
}

# Stock Market Specific Configuration
variable "stock_symbols" {
  description = "Stock symbols to track"
  type        = list(string)
  default     = ["META", "AAPL", "AMZN", "NFLX", "GOOGL"]
}

variable "pipeline_schedule" {
  description = "Cron schedule for the pipeline"
  type        = string
  default     = "@daily"
}
