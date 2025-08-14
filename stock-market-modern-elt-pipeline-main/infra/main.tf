terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}


# Google Cloud Storage - GCS
resource "google_storage_bucket" "datalake_stock_market_bucket" {
  name                        = var.bucket_name
  location                    = var.region
  storage_class               = "STANDARD"
  force_destroy               = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Fazer upload do arquivo dim_date.csv para o bucket GCS recém-criado
resource "google_storage_bucket_object" "dim_date_csv" {
  name         = "dates/dates.csv"
  bucket       = var.bucket_name
  source       = "../data/dates.csv"
  content_type = "text/csv"
  depends_on   = [google_storage_bucket.datalake_stock_market_bucket]
}
# Fazer upload do script dataproc transform_stock_data_pipeline.py para o bucket GCS recém-criado
resource "google_storage_bucket_object" "upload_dataproc_script" {
  name         = "dataproc_jobs/transform_stock_data.py"
  bucket       = var.bucket_name
  source       = "../dataproc_jobs/transform_stock_data_pipeline.py"
  content_type = "text/x-python"
  depends_on   = [google_storage_bucket.datalake_stock_market_bucket]
}

# Dar permissões de criação de batch dataproc para sua conta de serviço
resource "google_project_iam_member" "composer_dataproc_permissions" {
  project = var.project_id
  role    = "roles/dataproc.admin"
  member  = "serviceAccount:${var.service_account}"
}

# Google Composer - Airflow
resource "google_composer_environment" "google_composer" {
  name   = var.composer_name
  region = var.region

  config {
    software_config {
      image_version = "composer-3-airflow-2.10.5-build.6" # Versões do Composer e Airflow
      env_variables = {
        "SERVICE_ACCOUNT" = var.service_account
        "REGION"          = var.region
        "BUCKET_NAME"     = var.bucket_name
        "DATASET_ID"      = var.dataset_id
      }
    }
    node_config {
      service_account = var.service_account
    }
    ## workloads_config {} -> Valores padrão
  }
}

# Dar permissões de administrador de objetos do storage ao Composer
resource "google_project_iam_member" "composer_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${var.service_account}"
}

# Dar permissões de logging ao Composer
resource "google_project_iam_member" "composer_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${var.service_account}"
}

# Dar permissões de edição do BigQuery ao Composer para etapas posteriores
resource "google_project_iam_member" "composer_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${var.service_account}"
}


# Necessário para ler dag_gcs_prefix mais tarde após a criação do ambiente composer
data "google_composer_environment" "google_composer" {
  name       = var.composer_name
  region     = var.region
  depends_on = [google_composer_environment.google_composer]
}

# Definir variável local para gerar o nome do bucket do Composer
locals {
  composer_bucket_name = replace(replace(data.google_composer_environment.google_composer.config[0].dag_gcs_prefix, "gs://", ""), "/dags", "")
}

# Fazer upload do dag para o Google Composer
resource "google_storage_bucket_object" "upload_dag" {
  name       = "dags/stock_market_dag.py"
  bucket     = local.composer_bucket_name
  source     = "../dags/stock_market_dag.py"
  depends_on = [google_composer_environment.google_composer]
}


# Dataset do BigQuery
resource "google_bigquery_dataset" "stock_market_dw" {
  dataset_id                 = var.dataset_id
  project                    = var.project_id
  location                   = var.region
  delete_contents_on_destroy = true
}

# Tabela BigQuery dim_company
resource "google_bigquery_table" "dim_company" {
  dataset_id          = var.dataset_id
  table_id            = "dim_company"
  schema              = file("./schemas/dim_company_schema.json")
  deletion_protection = false
  depends_on          = [google_bigquery_dataset.stock_market_dw]
}

# Tabela BigQuery dim_date
resource "google_bigquery_table" "dim_date" {
  dataset_id          = var.dataset_id
  table_id            = "dim_date"
  schema              = file("./schemas/dim_date_schema.json")
  deletion_protection = false
  depends_on          = [google_bigquery_dataset.stock_market_dw]
}

# Tabela BigQuery dim_exchange
resource "google_bigquery_table" "dim_exchange" {
  dataset_id          = var.dataset_id
  table_id            = "dim_exchange"
  schema              = file("./schemas/dim_exchange_schema.json")
  deletion_protection = false
  depends_on          = [google_bigquery_dataset.stock_market_dw]
}

# Tabela BigQuery fact_stock_price
resource "google_bigquery_table" "fact_stock_price" {
  dataset_id          = var.dataset_id
  table_id            = "fact_stock_price"
  schema              = file("./schemas/fact_stock_price_schema.json")
  deletion_protection = false
  depends_on          = [google_bigquery_dataset.stock_market_dw]
}

