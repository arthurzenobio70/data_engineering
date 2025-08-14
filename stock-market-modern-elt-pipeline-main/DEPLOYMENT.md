# Deployment Guide

This guide provides step-by-step instructions for deploying the Stock Market Data Pipeline to Google Cloud Platform.

## Prerequisites

### Required Tools
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
- [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) (>= 1.0)
- [Docker](https://docs.docker.com/get-docker/)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Make](https://www.gnu.org/software/make/) (optional but recommended)

### GCP Setup
1. Create or select a GCP project
2. Enable billing for the project
3. Set up authentication (see [GCP Setup Guide](setup/gcp_setup.md))

## Environment Configuration

### 1. Clone and Setup Repository

```bash
git clone <repository-url>
cd stock-market-modern-elt-pipeline-main

# Setup development environment
make dev-setup
```

### 2. Configure Environment Variables

Create a `.env` file (copy from `.env.example` if available):

```bash
# GCP Configuration
export GOOGLE_CLOUD_PROJECT="your-project-id"
export SERVICE_ACCOUNT="your-service-account@your-project.iam.gserviceaccount.com"
export REGION="us-central1"
export ZONE="us-central1-a"

# Pipeline Configuration
export BUCKET_NAME="your-datalake-bucket"
export DATASET_ID="stock_market_dw"
export COMPOSER_NAME="stock-market-composer"

# Optional: Custom stock symbols
export STOCK_SYMBOLS="META,AAPL,AMZN,NFLX,GOOGL"
```

### 3. Authenticate with GCP

```bash
# Authenticate with your user account
gcloud auth login

# Set application default credentials
gcloud auth application-default login

# Set the project
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

## Infrastructure Deployment

### 1. Initialize Terraform

```bash
make tf-init
```

### 2. Configure Terraform Variables

Create `terraform/terraform.tfvars`:

```hcl
# Required variables
project_id           = "your-project-id"
service_account_email = "your-service-account@your-project.iam.gserviceaccount.com"

# Optional customizations
environment          = "prod"
region              = "us-central1"
zone                = "us-central1-a"
storage_class       = "STANDARD"
notification_email  = "your-email@example.com"

# Resource sizing (adjust based on needs)
composer_machine_type    = "n1-standard-2"
composer_disk_size      = 100
raw_data_retention_days = 90
```

### 3. Review Infrastructure Plan

```bash
make tf-plan
```

Review the planned changes carefully before proceeding.

### 4. Deploy Infrastructure

```bash
make tf-apply
```

This will create:
- GCS bucket for data lake
- BigQuery dataset and tables
- Cloud Composer environment
- IAM roles and permissions
- Monitoring and alerting (if configured)

**Note**: Deployment typically takes 20-25 minutes due to Composer environment setup.

## Application Deployment

### 1. Upload DAG Files

DAG files are automatically uploaded during Terraform deployment. To manually update:

```bash
# Upload specific DAG
gsutil cp dags/stock_market_dag_v2.py gs://your-composer-bucket/dags/

# Upload all DAGs
gsutil -m cp dags/*.py gs://your-composer-bucket/dags/
```

### 2. Upload Dataproc Scripts

```bash
# Scripts are uploaded during Terraform deployment
# To manually update:
gsutil cp dataproc_jobs/transform_stock_data_v2.py gs://your-datalake-bucket/scripts/
```

### 3. Upload ERP Data

```bash
make upload-erp
# Or manually:
gsutil cp data/erp_companies.csv gs://your-datalake-bucket/raw/erp/
```

## Verification and Testing

### 1. Check Composer Environment

```bash
# Get Composer environment details
gcloud composer environments describe $COMPOSER_NAME --location=$REGION
```

Access the Airflow UI through the GCP Console:
1. Go to Cloud Composer in GCP Console
2. Click on your environment
3. Click "Open Airflow UI"

### 2. Verify DAG Deployment

In the Airflow UI:
1. Check that DAGs are visible and parsed correctly
2. Ensure no import errors
3. Verify DAG is not paused

### 3. Test Pipeline Execution

1. Manually trigger the DAG from Airflow UI
2. Monitor task execution
3. Check logs for any errors
4. Verify data in BigQuery

### 4. Validate Data Quality

```sql
-- Check fact table data
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT Ticker) as unique_tickers,
    MIN(DateKey) as earliest_date,
    MAX(DateKey) as latest_date
FROM `your-project.stock_market_dw.fact_stock_price`;

-- Check dimension tables
SELECT COUNT(*) FROM `your-project.stock_market_dw.dim_company`;
SELECT COUNT(*) FROM `your-project.stock_market_dw.dim_exchange`;
```

## Configuration Management

### Environment-Specific Deployments

For multiple environments (dev, staging, prod):

1. Create environment-specific tfvars files:
   ```
   terraform/environments/
   ├── dev.tfvars
   ├── staging.tfvars
   └── prod.tfvars
   ```

2. Deploy with environment-specific variables:
   ```bash
   terraform plan -var-file="environments/dev.tfvars"
   terraform apply -var-file="environments/dev.tfvars"
   ```

### Terraform Workspaces

For complete environment isolation:

```bash
# Create workspace
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select dev

# Deploy to current workspace
make tf-plan
make tf-apply
```

## Monitoring Setup

### 1. Configure Alerts

Update `terraform/terraform.tfvars`:

```hcl
notification_email = "your-team@example.com"
```

### 2. Access Monitoring

- **Cloud Monitoring**: GCP Console > Monitoring
- **Cloud Logging**: GCP Console > Logging
- **Airflow Logs**: Available in Airflow UI

### 3. Custom Dashboards

Create custom dashboards in Cloud Monitoring for:
- Pipeline execution metrics
- Data freshness
- Error rates
- Cost tracking

## Backup and Recovery

### 1. Terraform State Backup

Configure remote state backend in `terraform/main.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket = "your-terraform-state-bucket"
    prefix = "stock-market-pipeline"
  }
}
```

### 2. Data Backup

The pipeline includes automatic backup features:
- GCS bucket versioning
- BigQuery dataset backup (configure separately)
- Cross-region replication (optional)

## Troubleshooting

### Common Issues

1. **Composer Environment Creation Fails**
   - Check IAM permissions
   - Verify network configuration
   - Check quota limits

2. **DAG Import Errors**
   - Verify Python dependencies
   - Check file paths in DAGs
   - Review Airflow logs

3. **Dataproc Job Failures**
   - Check service account permissions
   - Verify Spark configuration
   - Review job logs in GCP Console

4. **BigQuery Load Failures**
   - Check schema compatibility
   - Verify file formats
   - Review IAM permissions

### Debug Commands

```bash
# Check Terraform state
terraform state list
terraform state show <resource>

# View Composer logs
gcloud logging read "resource.type=composer_environment"

# Check service account permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# Validate DAG syntax locally
python -m py_compile dags/stock_market_dag_v2.py
```

## Cleanup

### Destroy Infrastructure

⚠️ **Warning**: This will permanently delete all resources and data.

```bash
make tf-destroy
```

### Selective Cleanup

To remove specific resources:

```bash
# Remove specific resource
terraform destroy -target=google_composer_environment.pipeline_orchestrator

# Remove with confirmation
terraform destroy -auto-approve
```

## Security Considerations

### 1. Least Privilege Access
- Use dedicated service accounts
- Assign minimal required permissions
- Regular permission audits

### 2. Data Protection
- Enable encryption at rest
- Use private IP ranges
- Implement VPC security controls

### 3. Secrets Management
- Store sensitive data in Secret Manager
- Avoid hardcoding credentials
- Use IAM for authentication

### 4. Network Security
- Configure firewall rules
- Use private Google Access
- Implement VPC peering if needed

## Cost Optimization

### 1. Resource Optimization
- Use appropriate machine types
- Enable autoscaling
- Schedule non-production environments

### 2. Storage Optimization
- Configure lifecycle policies
- Use appropriate storage classes
- Compress data files

### 3. Monitoring Costs
- Set up billing alerts
- Regular cost reviews
- Optimize query patterns

## Next Steps

After successful deployment:

1. Set up monitoring dashboards
2. Configure backup procedures
3. Implement CI/CD pipeline
4. Train team on operations
5. Plan for scaling requirements
6. Schedule regular maintenance
