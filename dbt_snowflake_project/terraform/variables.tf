# Environment Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "finance-data-platform"
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "data-engineering-team"
}

# Snowflake Configuration
variable "snowflake_account" {
  description = "Snowflake account identifier"
  type        = string
}

variable "snowflake_username" {
  description = "Snowflake username"
  type        = string
}

variable "snowflake_password" {
  description = "Snowflake password"
  type        = string
  sensitive   = true
}

variable "snowflake_role" {
  description = "Snowflake role to use"
  type        = string
  default     = "ACCOUNTADMIN"
}

# Database Configuration
variable "databases" {
  description = "List of databases to create"
  type = list(object({
    name    = string
    comment = string
  }))
  default = [
    {
      name    = "FINANCE_DB"
      comment = "Primary finance data warehouse"
    },
    {
      name    = "FINANCE_DB_DEV"
      comment = "Development environment for finance data"
    }
  ]
}

# Warehouse Configuration
variable "warehouses" {
  description = "List of warehouses to create"
  type = list(object({
    name                         = string
    comment                      = string
    warehouse_size               = string
    auto_suspend                 = number
    auto_resume                  = bool
    initially_suspended          = bool
    resource_monitor             = optional(string)
    max_cluster_count            = optional(number)
    min_cluster_count            = optional(number)
    scaling_policy               = optional(string)
  }))
  default = [
    {
      name                = "FINANCE_WH"
      comment             = "Primary warehouse for finance operations"
      warehouse_size      = "X-SMALL"
      auto_suspend        = 300
      auto_resume         = true
      initially_suspended = true
      max_cluster_count   = 3
      min_cluster_count   = 1
      scaling_policy      = "STANDARD"
    },
    {
      name                = "FINANCE_WH_DEV"
      comment             = "Development warehouse"
      warehouse_size      = "X-SMALL"
      auto_suspend        = 60
      auto_resume         = true
      initially_suspended = true
    }
  ]
}

# Schema Configuration
variable "schemas" {
  description = "List of schemas to create"
  type = list(object({
    database = string
    name     = string
    comment  = string
  }))
  default = [
    {
      database = "FINANCE_DB"
      name     = "RAW"
      comment  = "Raw data ingestion layer"
    },
    {
      database = "FINANCE_DB"
      name     = "STAGING"
      comment  = "Staging layer for data transformation"
    },
    {
      database = "FINANCE_DB"
      name     = "MARTS"
      comment  = "Data marts for analytics"
    },
    {
      database = "FINANCE_DB"
      name     = "UTILS"
      comment  = "Utility objects and functions"
    }
  ]
}

# User Configuration
variable "users" {
  description = "List of users to create"
  type = list(object({
    name              = string
    comment           = string
    default_warehouse = string
    default_role      = string
    default_namespace = string
    email             = optional(string)
    first_name        = optional(string)
    last_name         = optional(string)
  }))
  default = [
    {
      name              = "DBT_USER"
      comment           = "Service user for dbt transformations"
      default_warehouse = "FINANCE_WH"
      default_role      = "DBT_ROLE"
      default_namespace = "FINANCE_DB.RAW"
    },
    {
      name              = "AIRFLOW_USER"
      comment           = "Service user for Airflow orchestration"
      default_warehouse = "FINANCE_WH"
      default_role      = "AIRFLOW_ROLE"
      default_namespace = "FINANCE_DB.RAW"
    }
  ]
}

# Role Configuration
variable "roles" {
  description = "List of roles to create"
  type = list(object({
    name    = string
    comment = string
  }))
  default = [
    {
      name    = "DBT_ROLE"
      comment = "Role for dbt service user with transformation permissions"
    },
    {
      name    = "AIRFLOW_ROLE"
      comment = "Role for Airflow service user with orchestration permissions"
    },
    {
      name    = "ANALYST_ROLE"
      comment = "Role for data analysts with read access to marts"
    },
    {
      name    = "DATA_ENGINEER_ROLE"
      comment = "Role for data engineers with full development access"
    }
  ]
}

# AWS Configuration (for Terraform state backend)
variable "aws_region" {
  description = "AWS region for Terraform state backend"
  type        = string
  default     = "us-east-1"
}

variable "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  type        = string
}

variable "terraform_state_lock_table" {
  description = "DynamoDB table for Terraform state locking"
  type        = string
}

# Resource Monitor Configuration
variable "resource_monitors" {
  description = "List of resource monitors to create"
  type = list(object({
    name              = string
    credit_quota      = number
    frequency         = string
    start_timestamp   = optional(string)
    end_timestamp     = optional(string)
    notify_triggers   = optional(list(number))
    suspend_triggers  = optional(list(number))
    suspend_immediate_triggers = optional(list(number))
  }))
  default = [
    {
      name          = "FINANCE_MONITOR"
      credit_quota  = 1000
      frequency     = "MONTHLY"
      notify_triggers = [80, 90]
      suspend_triggers = [95]
      suspend_immediate_triggers = [100]
    }
  ]
}
