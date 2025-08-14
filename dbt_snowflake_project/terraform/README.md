# Snowflake Infrastructure with Terraform

This directory contains Terraform configurations for provisioning and managing Snowflake resources for the finance data platform.

## Prerequisites

1. **Terraform**: Install Terraform >= 1.0
2. **Snowflake Account**: Active Snowflake account with admin privileges
3. **AWS Account**: For Terraform state backend (optional but recommended)

## Quick Start

### 1. Configure Variables

Copy the example variables file and update with your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your Snowflake credentials and configuration.

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan Infrastructure

```bash
terraform plan
```

### 4. Apply Infrastructure

```bash
terraform apply
```

## Infrastructure Components

### Databases
- **FINANCE_DB**: Primary production database
- **FINANCE_DB_DEV**: Development database

### Schemas (per database)
- **RAW**: Raw data ingestion layer
- **STAGING**: Intermediate transformation layer
- **MARTS**: Final analytics layer
- **UTILS**: Utility functions and objects

### Warehouses
- **FINANCE_WH**: Production warehouse (auto-scaling)
- **FINANCE_WH_DEV**: Development warehouse

### Users & Roles
- **DBT_USER/DBT_ROLE**: Service account for dbt transformations
- **AIRFLOW_USER/AIRFLOW_ROLE**: Service account for Airflow orchestration
- **ANALYST_ROLE**: Read-only access to marts for analysts
- **DATA_ENGINEER_ROLE**: Full development access

### Security & Governance
- Resource monitors for cost control
- Role-based access controls (RBAC)
- Data retention policies
- Automated suspend/resume for warehouses

## Environment Management

The configuration supports multiple environments through the `environment` variable:

- **dev**: Development environment with minimal resources
- **staging**: Pre-production environment
- **prod**: Production environment with full resources and monitoring

## Cost Optimization Features

1. **Auto-suspend**: Warehouses auto-suspend after inactivity
2. **Resource Monitors**: Credit quota monitoring and alerts
3. **Scaling Policies**: Multi-cluster warehouses for production
4. **Right-sizing**: Environment-specific warehouse sizes

## Security Features

1. **Principle of Least Privilege**: Minimal required permissions
2. **Service Accounts**: Dedicated users for automation
3. **Role Separation**: Clear separation between roles
4. **Network Security**: Database and schema isolation

## Terraform State Management

This configuration uses remote state storage for team collaboration:

- **S3 Backend**: Centralized state storage
- **DynamoDB Locking**: Prevents concurrent modifications
- **State Encryption**: Encrypted state files

## Customization

### Adding New Environments

1. Update `variables.tf` with new environment validation
2. Create environment-specific `terraform.tfvars` files
3. Adjust resource sizing in variables

### Adding New Roles

1. Add role definition to `variables.tf`
2. Create appropriate grants in `snowflake_resources.tf`
3. Update role hierarchy as needed

### Scaling Warehouses

Warehouse auto-scaling is configured based on environment:

```hcl
max_cluster_count = var.environment == "prod" ? 10 : 3
min_cluster_count = 1
scaling_policy    = "STANDARD"
```

## Monitoring & Alerting

Resource monitors are configured with:
- Credit quotas per environment
- Email notifications at 80%, 90% usage
- Automatic suspension at 95% usage
- Immediate suspension at 100% usage

## Troubleshooting

### Common Issues

1. **Insufficient Privileges**: Ensure your user has ACCOUNTADMIN role
2. **Resource Conflicts**: Check for existing resources with same names
3. **Network Issues**: Verify Snowflake account accessibility

### Useful Commands

```bash
# View current state
terraform show

# Import existing resources
terraform import snowflake_database.example EXISTING_DB_NAME

# Refresh state
terraform refresh

# Destroy specific resource
terraform destroy -target=snowflake_warehouse.dev
```

## Best Practices

1. **Version Control**: Always commit Terraform files to version control
2. **State Backup**: Regularly backup Terraform state
3. **Plan Before Apply**: Always review plans before applying
4. **Environment Separation**: Use separate state files per environment
5. **Resource Tagging**: Consistent tagging for cost tracking
6. **Documentation**: Keep this README updated with changes

## Contributing

1. Create feature branch from main
2. Make changes and test in dev environment
3. Update documentation if needed
4. Submit pull request with clear description
5. Ensure CI/CD tests pass

## Support

For issues or questions:
- Create GitHub issue for bugs
- Contact data engineering team for access requests
- Refer to Snowflake documentation for platform-specific questions
