# Finance Data Platform - Deployment Guide

This guide provides step-by-step instructions for deploying the Finance Data Platform in a production environment.

## 📋 Prerequisites Checklist

### Infrastructure Requirements
- [ ] Snowflake account with admin privileges
- [ ] AWS account for Terraform state backend
- [ ] GitHub repository with Actions enabled
- [ ] SMTP server for email alerts (optional)
- [ ] Slack workspace for notifications (optional)

### Access Requirements
- [ ] Snowflake ACCOUNTADMIN role
- [ ] AWS S3 and DynamoDB permissions
- [ ] GitHub repository admin access
- [ ] Domain/subdomain for documentation (optional)

## 🏗️ Infrastructure Deployment

### Step 1: Set Up Terraform Backend

1. **Create S3 Bucket for State**
   ```bash
   aws s3 mb s3://your-terraform-state-bucket
   aws s3api put-bucket-versioning --bucket your-terraform-state-bucket --versioning-configuration Status=Enabled
   ```

2. **Create DynamoDB Table for Locking**
   ```bash
   aws dynamodb create-table \
     --table-name terraform-lock-table \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
   ```

### Step 2: Configure Terraform Variables

1. **Copy Example Variables**
   ```bash
   cd terraform/
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit Variables**
   ```hcl
   # terraform.tfvars
   environment                  = "prod"
   project_name                = "finance-data-platform"
   owner                       = "data-engineering-team"
   
   snowflake_account           = "your-account.snowflakecomputing.com"
   snowflake_username          = "terraform_user"
   snowflake_password          = "secure_password"
   snowflake_role             = "ACCOUNTADMIN"
   
   aws_region                 = "us-east-1"
   terraform_state_bucket     = "your-terraform-state-bucket"
   terraform_state_lock_table = "terraform-lock-table"
   ```

### Step 3: Deploy Infrastructure

1. **Initialize Terraform**
   ```bash
   terraform init
   ```

2. **Plan Deployment**
   ```bash
   terraform plan -var-file="terraform.tfvars"
   ```

3. **Apply Infrastructure**
   ```bash
   terraform apply -var-file="terraform.tfvars"
   ```

4. **Save Outputs**
   ```bash
   terraform output -json > terraform-outputs.json
   ```

## 🔐 Secrets Configuration

### GitHub Secrets

Configure the following secrets in your GitHub repository:

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=dbt_user
SNOWFLAKE_PASSWORD=secure_password
SNOWFLAKE_ROLE=DBT_ROLE

# Environment-specific users
SNOWFLAKE_USER_DEV=dbt_user_dev
SNOWFLAKE_PASSWORD_DEV=dev_password
SNOWFLAKE_USER_STAGING=dbt_user_staging
SNOWFLAKE_PASSWORD_STAGING=staging_password
SNOWFLAKE_USER_PROD=dbt_user_prod
SNOWFLAKE_PASSWORD_PROD=prod_password

# Terraform Backend
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
TERRAFORM_STATE_BUCKET=your-terraform-state-bucket
TERRAFORM_STATE_LOCK_TABLE=terraform-lock-table

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ALERT_EMAIL_RECIPIENTS=data-team@company.com,alerts@company.com
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=alerts@company.com
SMTP_PASSWORD=app_password
```

### Environment Files

Create environment-specific configuration files:

```bash
# environments/dev.tfvars
environment = "dev"
warehouses = [
  {
    name                = "FINANCE_WH_DEV"
    warehouse_size      = "X-SMALL"
    auto_suspend        = 60
    initially_suspended = true
  }
]

# environments/staging.tfvars
environment = "staging"
warehouses = [
  {
    name                = "FINANCE_WH_STAGING"
    warehouse_size      = "SMALL"
    auto_suspend        = 300
    initially_suspended = true
  }
]

# environments/prod.tfvars
environment = "prod"
warehouses = [
  {
    name                = "FINANCE_WH"
    warehouse_size      = "MEDIUM"
    auto_suspend        = 600
    initially_suspended = false
    max_cluster_count   = 10
    min_cluster_count   = 1
    scaling_policy      = "STANDARD"
  }
]
```

## 🚀 Application Deployment

### Step 1: Configure dbt Profiles

Create environment-specific profiles:

```yaml
# ~/.dbt/profiles.yml
finance_data_platform:
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER_DEV') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD_DEV') }}"
      role: DBT_ROLE
      database: FINANCE_DB_DEV
      warehouse: FINANCE_WH_DEV
      schema: raw
      threads: 4
      
    staging:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER_STAGING') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD_STAGING') }}"
      role: DBT_ROLE
      database: FINANCE_DB_STAGING
      warehouse: FINANCE_WH_STAGING
      schema: raw
      threads: 8
      
    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER_PROD') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD_PROD') }}"
      role: DBT_ROLE
      database: FINANCE_DB
      warehouse: FINANCE_WH
      schema: raw
      threads: 16
      
  target: dev
```

### Step 2: Initial Data Load

1. **Prepare Source Data**
   ```bash
   # Upload CSV files to Snowflake stage
   snowsql -c prod_connection -f load_source_data.sql
   ```

2. **Run Initial dbt Build**
   ```bash
   dbt deps --target prod
   dbt seed --target prod
   dbt run --target prod --full-refresh
   dbt test --target prod
   ```

### Step 3: Deploy Airflow DAG

1. **Configure Airflow Variables**
   ```bash
   # Set via Airflow UI or CLI
   airflow variables set dbt_project_dir /opt/airflow/dbt
   airflow variables set dbt_profiles_dir /opt/airflow/.dbt
   airflow variables set snowflake_conn_id snowflake_default
   airflow variables set environment prod
   airflow variables set alert_email_recipients data-team@company.com
   ```

2. **Deploy DAG File**
   ```bash
   cp dbt_core_dag.py $AIRFLOW_HOME/dags/
   ```

3. **Test DAG**
   ```bash
   airflow dags test finance_data_pipeline 2024-01-01
   ```

## 📊 Monitoring Setup

### Step 1: Configure Data Quality Dashboard

1. **Set Environment Variables**
   ```bash
   export SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
   export SNOWFLAKE_USER=dashboard_user
   export SNOWFLAKE_PASSWORD=dashboard_password
   export SNOWFLAKE_WAREHOUSE=FINANCE_WH
   export SNOWFLAKE_DATABASE=FINANCE_DB
   export SNOWFLAKE_SCHEMA=TEST_FAILURES
   ```

2. **Deploy Dashboard**
   ```bash
   pip install -r requirements.txt
   streamlit run monitoring/data_quality_dashboard.py
   ```

### Step 2: Configure Alerting

1. **Set Alert Environment Variables**
   ```bash
   export TEST_FAILURE_THRESHOLD=5
   export FRESHNESS_THRESHOLD_HOURS=48
   export PASS_RATE_THRESHOLD=95.0
   export CRITICAL_MODELS=fct_daily_order_revenue,dim_customers
   export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   export ALERT_EMAIL_RECIPIENTS=data-team@company.com
   ```

2. **Schedule Alert Monitoring**
   ```bash
   # Add to crontab
   */15 * * * * /path/to/venv/bin/python /path/to/monitoring/alerts.py
   ```

## 🔄 CI/CD Pipeline Setup

### Step 1: Enable GitHub Actions

1. **Verify Workflow Files**
   ```bash
   ls .github/workflows/
   # Should show: ci.yml, cd.yml, terraform.yml
   ```

2. **Configure Branch Protection**
   - Require pull request reviews
   - Require status checks (CI pipeline)
   - Require branches to be up to date
   - Include administrators

### Step 2: Environment Configuration

1. **Create GitHub Environments**
   - `development` - Auto-deploy from develop branch
   - `staging` - Auto-deploy from main branch
   - `production` - Manual approval required

2. **Configure Environment Secrets**
   - Each environment should have specific Snowflake credentials
   - Production requires manual approval gates

## 📈 Performance Optimization

### Step 1: Warehouse Optimization

1. **Monitor Usage**
   ```sql
   -- Query warehouse usage
   SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
   WHERE WAREHOUSE_NAME = 'FINANCE_WH'
   ORDER BY START_TIME DESC;
   ```

2. **Adjust Scaling**
   ```hcl
   # In terraform/variables.tf
   warehouses = [
     {
       name                = "FINANCE_WH"
       warehouse_size      = "LARGE"  # Scale up if needed
       max_cluster_count   = 5        # Adjust based on concurrency
       min_cluster_count   = 1
       scaling_policy      = "ECONOMY"  # or "STANDARD"
     }
   ]
   ```

### Step 2: Query Optimization

1. **Enable Query Tagging**
   ```yaml
   # dbt_project.yml
   query-comment: "dbt-{{ invocation_id }}-{{ model.unique_id }}"
   ```

2. **Monitor Performance**
   ```sql
   -- Monitor dbt query performance
   SELECT 
     query_text,
     execution_time,
     warehouse_size,
     total_elapsed_time
   FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
   WHERE query_text LIKE '%dbt%'
   ORDER BY total_elapsed_time DESC;
   ```

## 🔍 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Terraform apply fails** | Missing permissions | Verify AWS/Snowflake credentials |
| **dbt connection error** | Wrong credentials | Check profiles.yml configuration |
| **CI pipeline fails** | Missing secrets | Verify GitHub secrets are set |
| **Models not updating** | Warehouse suspended | Check warehouse auto-resume settings |
| **Tests failing** | Data quality issues | Review test logic and source data |

### Debug Commands

```bash
# Test Snowflake connection
snowsql -a your-account -u your-user -d FINANCE_DB

# Test dbt connection
dbt debug --target prod

# Validate Terraform
terraform validate
terraform plan

# Check Airflow DAG
airflow dags list
airflow tasks list finance_data_pipeline

# Test alerting system
python monitoring/alerts.py --dry-run
```

## 📚 Additional Resources

- [Snowflake Documentation](https://docs.snowflake.com/)
- [dbt Documentation](https://docs.getdbt.com/)
- [Terraform Snowflake Provider](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)

## 🆘 Support

For deployment issues:
- **Slack**: `#data-engineering` channel
- **Email**: data-engineering@company.com
- **On-call**: Check PagerDuty rotation

## ✅ Post-Deployment Checklist

- [ ] Infrastructure deployed successfully
- [ ] All environments configured
- [ ] dbt models running without errors
- [ ] Tests passing consistently
- [ ] Airflow DAG scheduled and running
- [ ] Monitoring dashboard accessible
- [ ] Alerts configured and tested
- [ ] CI/CD pipeline functional
- [ ] Documentation updated
- [ ] Team trained on new system
- [ ] Runbooks created
- [ ] Backup and recovery tested
