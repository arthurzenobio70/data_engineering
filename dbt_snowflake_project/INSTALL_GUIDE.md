# Installation Guide - Finance Data Platform

Follow these steps to install and run the project successfully.

## 🚀 Quick Installation (Recommended)

### Step 1: Install Core Python Packages

```bash
# Navigate to your project directory
cd dbt_snowflake_project

# Install core requirements
pip install -r requirements-core.txt
```

If you encounter any issues, try installing packages individually:

```bash
# Install dbt core and Snowflake adapter
pip install "dbt-core>=1.6.0,<2.0.0"
pip install "dbt-snowflake>=1.6.0,<2.0.0"

# Install monitoring tools
pip install "streamlit>=1.25.0"
pip install "pandas>=1.5.0"
pip install "snowflake-connector-python>=3.0.0"

# Install utilities
pip install python-dotenv pyyaml requests
```

### Step 2: Install dbt Packages

```bash
# Install dbt packages (dbt-utils, dbt-expectations, etc.)
dbt deps
```

### Step 3: Verify Installation

```bash
# Check if dbt is working
dbt --version

# Should show something like:
# Core:
#   - installed: 1.6.x
#   - latest:    1.7.x
# 
# Plugins:
#   - snowflake: 1.6.x - Up to date!
```

## 🔧 Alternative Installation Methods

### Method 1: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv dbt-env

# Activate virtual environment
# On Windows:
dbt-env\Scripts\activate
# On macOS/Linux:
source dbt-env/bin/activate

# Install packages
pip install -r requirements-core.txt
dbt deps
```

### Method 2: Using Conda

```bash
# Create conda environment
conda create -n dbt-project python=3.11

# Activate environment
conda activate dbt-project

# Install packages
pip install -r requirements-core.txt
dbt deps
```

### Method 3: Docker (Advanced)

```bash
# Build Docker image
docker build -t finance-data-platform .

# Run container
docker run -it --rm finance-data-platform
```

## 🐛 Troubleshooting Common Issues

### Issue 1: Package Version Conflicts

**Error**: `ERROR: Could not find a version that satisfies the requirement...`

**Solution**:
```bash
# Update pip first
python -m pip install --upgrade pip

# Try installing with no dependencies first
pip install --no-deps dbt-core
pip install --no-deps dbt-snowflake

# Then install dependencies
pip install -r requirements-core.txt
```

### Issue 2: dbt-utils Not Found

**Error**: `ERROR: No matching distribution found for dbt-utils`

**Solution**: 
```bash
# dbt-utils is NOT a pip package - it's installed via dbt deps
# Don't try to pip install it!

# Instead, run:
dbt deps
```

### Issue 3: Snowflake Connection Issues

**Error**: `Connection failed` or `Account not found`

**Solution**:
```bash
# Check your Snowflake account format
# Should be one of:
# - account.snowflakecomputing.com
# - account.region.snowflakecomputing.com
# - account.region.cloud.snowflakecomputing.com

# Test connection
dbt debug
```

### Issue 4: Python Version Issues

**Error**: `requires python_version >= "3.8"`

**Solution**:
```bash
# Check Python version
python --version

# If using older Python, upgrade to 3.8+
# Or use pyenv/conda to manage versions
```

## 📋 Minimum System Requirements

- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk Space**: 2GB free space
- **Operating System**: Windows 10, macOS 10.14+, or Linux
- **Internet**: Required for package downloads and Snowflake connection

## 🎯 Package Verification

After installation, verify these packages are available:

```bash
# Check dbt installation
dbt --version

# Check Python packages
python -c "import dbt.main; print('dbt-core: OK')"
python -c "import dbt.adapters.snowflake; print('dbt-snowflake: OK')"
python -c "import streamlit; print('streamlit: OK')"
python -c "import pandas; print('pandas: OK')"
python -c "import snowflake.connector; print('snowflake-connector: OK')"
```

## 🔄 Next Steps After Installation

1. **Configure Snowflake Connection**:
   ```bash
   # Create profiles.yml
   mkdir -p ~/.dbt
   # Edit ~/.dbt/profiles.yml with your Snowflake credentials
   ```

2. **Test Connection**:
   ```bash
   dbt debug
   ```

3. **Run the Project**:
   ```bash
   dbt run
   dbt test
   ```

4. **Start Monitoring Dashboard**:
   ```bash
   streamlit run monitoring/data_quality_dashboard.py
   ```

## 🆘 Getting Help

If you're still having issues:

1. **Check the logs**: Look for detailed error messages
2. **Update packages**: `pip install --upgrade pip setuptools wheel`
3. **Clear cache**: `pip cache purge`
4. **Use virtual environment**: Isolate dependencies
5. **Install individually**: Install packages one by one to identify conflicts

## 📞 Support

- **GitHub Issues**: [Create an issue](https://github.com/your-org/finance-data-platform/issues)
- **dbt Community**: [dbt Slack](https://www.getdbt.com/community/)
- **Documentation**: [dbt Docs](https://docs.getdbt.com/)

Remember: The most important packages are `dbt-core` and `dbt-snowflake`. Everything else is optional for basic functionality!
