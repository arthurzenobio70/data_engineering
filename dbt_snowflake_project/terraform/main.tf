terraform {
  required_version = ">= 1.0"
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.94"
    }
  }

  # Configure remote state backend (recommended for production)
  # Comment out for local testing
  # backend "s3" {
  #   bucket = var.terraform_state_bucket
  #   key    = "snowflake-data-platform/terraform.tfstate"
  #   region = var.aws_region
  #   
  #   # Enable state locking via DynamoDB
  #   dynamodb_table = var.terraform_state_lock_table
  #   encrypt        = true
  # }
}

provider "snowflake" {
  account  = var.snowflake_account
  username = var.snowflake_username
  password = var.snowflake_password
  role     = var.snowflake_role
}

# Data sources for existing resources
data "snowflake_current_account" "this" {}

# Local values for resource naming and tagging
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Owner       = var.owner
    ManagedBy   = "terraform"
    CreatedAt   = timestamp()
  }
  
  resource_prefix = "${var.project_name}-${var.environment}"
}
