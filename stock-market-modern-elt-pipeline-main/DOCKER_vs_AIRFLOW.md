# Docker vs Airflow: Clear Separation of Concerns

## 🎯 Purpose & Scope

This document clarifies the distinct roles of Docker and Airflow in the stock market data pipeline to prevent confusion and conflicts.

## 📋 Summary

| Component | Purpose | Environment | Data Processing | Use Cases |
|-----------|---------|-------------|-----------------|-----------|
| **Docker** | Development & Testing | Local Machine | ❌ **NO Production Jobs** | Code development, unit testing, exploration |
| **Airflow** | Production Orchestration | Google Cloud Platform | ✅ **Production Data Processing** | Daily pipeline execution, data transformation |

## 🐳 Docker: Development Environment

### What Docker IS Used For:
- **✅ Local Development**: Code editing and testing
- **✅ Unit Testing**: Running pytest in isolated environments  
- **✅ Data Exploration**: Jupyter notebooks for analysis
- **✅ Configuration Testing**: Validating setup without affecting production
- **✅ Dependency Management**: Consistent development environments
- **✅ Code Quality**: Running linting, formatting, type checking

### What Docker is NOT Used For:
- **❌ Production Data Processing**: No real stock data extraction
- **❌ GCS Data Operations**: No uploading to production buckets
- **❌ BigQuery Operations**: No loading to production tables
- **❌ Dataproc Jobs**: No Spark processing on real data
- **❌ Production Scheduling**: No automated daily runs

### Docker Services Explained:

```yaml
# Development environment
stock-pipeline-dev:
  purpose: "Code development and testing"
  command: "bash (interactive shell)"
  
# Test runner  
test-runner:
  purpose: "Run unit tests with pytest"
  command: "pytest tests/ -v"
  
# Jupyter notebook
jupyter:
  purpose: "Data exploration and analysis"
  command: "jupyter lab"
  
# Local testing
stock-pipeline-local-test:
  purpose: "Test configurations locally"
  command: "Informational message + sleep"
  
# Pipeline development testing
pipeline-dev-test:
  purpose: "Safe development testing"
  command: "Development instructions + bash"
```

## ✈️ Airflow: Production Orchestration

### What Airflow IS Used For:
- **✅ Daily Scheduling**: Automated daily pipeline execution
- **✅ Data Extraction**: Real Yahoo Finance data retrieval
- **✅ Data Processing**: Dataproc Serverless Spark jobs
- **✅ Data Loading**: BigQuery table updates
- **✅ Error Handling**: Production-grade error recovery
- **✅ Monitoring**: Pipeline health and alerting
- **✅ Orchestration**: Managing task dependencies

### Airflow Tasks:
1. **extract_yahoo_finance_data**: Fetch real stock data from Yahoo Finance
2. **wait_for_erp_companies_file**: Wait for ERP data availability
3. **run_spark_transformation**: Execute PySpark on Dataproc Serverless
4. **load_fact_table**: Load fact data to BigQuery
5. **load_dimension_tables**: Load dimension data to BigQuery

## 🚫 Previous Conflict (Now Resolved)

### The Problem:
- **Dockerfile** originally had: `CMD ["python", "-m", "dataproc_jobs.transform_stock_data_v2"]`
- This would run the **same production job** that Airflow orchestrates
- Created potential conflicts between local and production environments

### The Solution:
- **Dockerfile** now has: `CMD ["bash"]` (development shell)
- Docker services have clear, non-conflicting purposes
- Production data processing **only** happens through Airflow

## 📍 Clear Boundaries

### Local Development Workflow:
```bash
# 1. Code development
make docker-dev
# Edit code in containers

# 2. Run tests
make test-docker
# Validate code quality

# 3. Explore data
make docker-jupyter
# Analyze sample data

# 4. Test configurations
make docker-local-test
# Validate settings without production impact
```

### Production Deployment Workflow:
```bash
# 1. Deploy infrastructure
make tf-apply

# 2. Upload code and data
# (Terraform handles this automatically)

# 3. Monitor Airflow
# Access Cloud Composer UI

# 4. Verify results
# Check BigQuery for processed data
```

## 🛡️ Safety Measures

### Docker Safety:
- **No GCP Credentials**: Development containers don't access production GCP
- **No Production Commands**: Default commands are safe for development
- **Isolated Networks**: Docker networks are local only
- **Clear Messaging**: Containers display warnings about their purpose

### Airflow Safety:
- **Scheduled Execution**: Runs only on defined schedule
- **Error Handling**: Comprehensive error recovery
- **Resource Isolation**: Uses dedicated GCP resources
- **Monitoring**: Full observability and alerting

## 🔧 Development Best Practices

### Using Docker for Development:
```bash
# Start development environment
make docker-dev

# Inside container - safe operations:
python -m pytest tests/
python -m mypy src/
python -m ruff check .
jupyter lab

# What NOT to do in Docker:
# python -m dataproc_jobs.transform_stock_data_v2  # This is for Airflow only!
```

### Testing Pipeline Logic:
```bash
# Test individual components
make test-docker

# Test configuration parsing
python -c "from src.config.settings import get_config; print(get_config())"

# Test extractors with mock data
python -c "from src.extractors.yahoo_finance import YahooFinanceExtractor; print('OK')"
```

## 📊 Monitoring & Observability

### Docker Monitoring:
- **Local Logs**: Container logs for debugging
- **Test Results**: pytest output and coverage reports
- **Development Metrics**: Code quality reports

### Airflow Monitoring:
- **Task Status**: Success/failure of each pipeline step
- **Data Quality**: Volume and validation metrics
- **Performance**: Execution times and resource usage
- **Alerts**: Email notifications for failures

## 🎯 Summary

The separation is now crystal clear:

- **🐳 Docker = Development Environment** (Local, Safe, Interactive)
- **✈️ Airflow = Production Pipeline** (Cloud, Automated, Scheduled)

This ensures:
- **No Conflicts**: Each tool has a distinct purpose
- **Safe Development**: Local testing doesn't affect production
- **Clear Workflow**: Developers know which tool to use when
- **Production Reliability**: Production jobs run only through proper orchestration

**Remember**: When in doubt, use Docker for development and testing, Airflow for production data processing!
