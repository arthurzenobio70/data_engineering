# 🚀 Getting Started - Finance Data Platform
## Simple Step-by-Step Guide for Beginners

Welcome! This guide will help you run the Finance Data Platform from scratch, even if you're not a technical expert.

---

## 📋 What You'll Need Before Starting

### Required Software (Download These First):
1. **Python 3.8+** - [Download here](https://www.python.org/downloads/)
   - ✅ Make sure to check "Add Python to PATH" during installation
2. **Git** - [Download here](https://git-scm.com/downloads)
3. **A Snowflake Account** - [Sign up for free trial](https://signup.snowflake.com/)
4. **A Text Editor** - VS Code (recommended) or Notepad++

### Information You'll Need:
- Your Snowflake account URL (looks like: `abc123.snowflakecomputing.com`)
- Your Snowflake username and password
- Email address for notifications

---

## 🎯 Part 1: Setup Your Computer (15 minutes)

### Step 1: Open Command Prompt/Terminal

**Windows Users:**
- Press `Windows + R`
- Type `cmd` and press Enter

**Mac Users:**
- Press `Cmd + Space`
- Type `Terminal` and press Enter

### Step 2: Navigate to Your Project

```bash
# Go to your project folder
cd dbt_snowflake_project

# Check you're in the right place (should show project files)
dir    # Windows
ls     # Mac/Linux
```

### Step 3: Create a Safe Environment

```bash
# Create a virtual environment (like a sandbox for this project)
python -m venv dbt-env

# Activate it
# Windows:
dbt-env\Scripts\activate
# Mac/Linux:
source dbt-env/bin/activate
```

**✅ Success Check:** You should see `(dbt-env)` at the beginning of your command line

### Step 4: Install Required Software

```bash
# Install the basic tools needed
pip install -r requirements-core.txt
```

**Wait for this to finish (2-3 minutes)**

```bash
# Install dbt packages
dbt deps
```

**✅ Success Check:** Run this command and you should see version numbers:
```bash
dbt --version
```

---

## 🏗️ Part 2: Connect to Snowflake (10 minutes)

### Step 5: Get Your Snowflake Information

1. **Log into Snowflake** in your web browser
2. **Look at the URL** - copy the part before `.snowflakecomputing.com`
   - Example: If URL is `https://abc123.snowflakecomputing.com`, your account is `abc123`
3. **Note your username and password**

### Step 6: Create Configuration File

**Windows Users:**
```bash
# Create the config folder
mkdir %USERPROFILE%\.dbt

# Create the config file
notepad %USERPROFILE%\.dbt\profiles.yml
```

**Mac/Linux Users:**
```bash
# Create the config folder
mkdir -p ~/.dbt

# Create the config file
nano ~/.dbt/profiles.yml
```

### Step 7: Add Your Snowflake Details

**Copy and paste this into the file, then replace the YOUR_* parts:**

```yaml
finance_data_platform:
  outputs:
    dev:
      type: snowflake
      account: YOUR_ACCOUNT_HERE      # Example: abc123
      user: YOUR_USERNAME_HERE        # Your Snowflake username
      password: YOUR_PASSWORD_HERE    # Your Snowflake password
      role: ACCOUNTADMIN
      database: FINANCE_DB_DEV
      warehouse: COMPUTE_WH
      schema: raw
      threads: 4
      client_session_keep_alive: False
      query_tag: dbt-dev
  target: dev
```

**Save the file and close the editor**

### Step 8: Test Your Connection

```bash
# Test if everything is connected
dbt debug
```

**✅ Success Check:** You should see `Connection test: [OK connection ok]`

**❌ If it fails:** Double-check your account name, username, and password

---

## 🏢 Part 3: Create Your Data Infrastructure (15 minutes)

### Step 9: Set Up Infrastructure with Terraform

```bash
# Go to the terraform folder
cd terraform

# Copy the example settings
copy terraform.tfvars.example terraform.tfvars     # Windows
cp terraform.tfvars.example terraform.tfvars       # Mac/Linux
```

### Step 10: Edit Terraform Settings

**Open the file in your text editor:**
```bash
notepad terraform.tfvars     # Windows
nano terraform.tfvars        # Mac/Linux
```

**Edit these lines with your information:**
```hcl
# Replace these with your actual details
environment = "dev"
project_name = "finance-data-platform"
owner = "your-name"

snowflake_account = "YOUR_ACCOUNT.snowflakecomputing.com"
snowflake_username = "YOUR_USERNAME"
snowflake_password = "YOUR_PASSWORD"
snowflake_role = "ACCOUNTADMIN"
```

**Save and close the file**

### Step 11: Build Your Infrastructure

```bash
# Initialize terraform
terraform init

# See what will be created
terraform plan -var-file="terraform.tfvars"

# Create everything (type 'yes' when asked)
terraform apply -var-file="terraform.tfvars"
```

**This will take 2-3 minutes and create databases, warehouses, and users in Snowflake**

**✅ Success Check:** You should see `Apply complete!` message

---

## 📊 Part 4: Add Your Data (10 minutes)

### Step 12: Upload Sample Data

1. **Log into Snowflake** in your web browser
2. **Click on "Data" → "Databases"**
3. **Find and click "FINANCE_DB_DEV"**
4. **Click on "RAW" schema**
5. **You'll see 4 empty tables:** customers, orders, order_items, products

### Step 13: Load Data into Each Table

**For each table, do this:**

1. **Click on the table name** (e.g., "CUSTOMERS")
2. **Click "Load Data" button**
3. **Upload the matching CSV file** from your `Data_Files` folder:
   - customers table ← upload `customers.csv`
   - orders table ← upload `orders.csv`
   - order_items table ← upload `order_items.csv`
   - products table ← upload `products.csv`
4. **Use these settings:**
   - File format: CSV
   - Skip first line: Yes (checked)
   - Click "Load"

**Repeat for all 4 tables**

### Step 14: Verify Data Loaded

**In Snowflake, run this query:**
```sql
SELECT COUNT(*) FROM customers;   -- Should show about 100 rows
SELECT COUNT(*) FROM orders;      -- Should show about 300 rows
SELECT COUNT(*) FROM order_items; -- Should show about 800 rows
SELECT COUNT(*) FROM products;    -- Should show about 50 rows
```

---

## 🚀 Part 5: Run the Data Pipeline (5 minutes)

### Step 15: Go Back to Command Line

```bash
# Navigate back to main project folder
cd ..
```

### Step 16: Run the Complete Data Pipeline

```bash
# Build all the data models
dbt run
```

**This will take 2-3 minutes and create all your analytics tables**

```bash
# Test data quality
dbt test
```

**This runs 50+ quality checks on your data**

```bash
# Generate documentation
dbt docs generate
```

**✅ Success Check:** You should see messages like "Completed successfully"

---

## 📊 Part 6: View Your Results (5 minutes)

### Step 17: Open the Data Dashboard

```bash
# Start the monitoring dashboard
streamlit run monitoring/data_quality_dashboard.py
```

**A web page will open at:** `http://localhost:8501`

**You'll see:**
- Data quality metrics
- Test results
- Freshness monitoring

### Step 18: View Documentation

**Open a new command prompt/terminal and run:**
```bash
# Navigate to project
cd dbt_snowflake_project

# Activate environment
dbt-env\Scripts\activate     # Windows
source dbt-env/bin/activate  # Mac/Linux

# Start documentation server
dbt docs serve --port 8002
```

**Open your browser to:** `http://localhost:8002`

**You'll see:**
- Data model documentation
- Column descriptions
- Data lineage diagrams

### Step 19: Explore Your Data in Snowflake

**Log into Snowflake and explore these new tables:**

**In STAGING schema:**
- `stg_customers` - Clean customer data
- `stg_orders` - Clean order data
- `stg_order_items` - Clean order item data
- `stg_products` - Clean product data

**In MARTS schema:**
- `dim_customers` - Customer analytics with segments
- `fct_daily_order_revenue` - Daily sales analytics
- `fct_order_line_items` - Detailed order analysis

---

## 🎉 Congratulations! You're Done!

### What You've Accomplished:

✅ **Built a Professional Data Platform** with industry best practices
✅ **Created 50+ Data Quality Tests** that run automatically
✅ **Generated Analytics Tables** for business insights
✅ **Set Up Monitoring** with real-time dashboards
✅ **Created Documentation** that updates automatically

### What You Can Do Now:

1. **Explore Your Data:** Query the new analytics tables in Snowflake
2. **Monitor Quality:** Check the dashboard at `localhost:8501`
3. **Read Documentation:** Browse the docs at `localhost:8002`
4. **Add More Data:** Upload new CSV files and re-run `dbt run`
5. **Share Insights:** Use the analytics tables for reports and dashboards

---

## 🔄 Daily Usage (After First Setup)

### To Update Your Data:
```bash
# Activate environment
dbt-env\Scripts\activate     # Windows
source dbt-env/bin/activate  # Mac/Linux

# Update everything
dbt run
dbt test
```

### To View Dashboards:
```bash
# Start monitoring dashboard
streamlit run monitoring/data_quality_dashboard.py

# Start documentation (in new terminal)
dbt docs serve --port 8002
```

---

## 🆘 Help! Something Went Wrong

### Common Issues and Solutions:

**"Command not found" errors:**
- Make sure you activated the virtual environment: `dbt-env\Scripts\activate`

**Connection errors to Snowflake:**
- Double-check your account name, username, and password in `~/.dbt/profiles.yml`
- Make sure your Snowflake account is active

**"No data found" errors:**
- Verify you uploaded the CSV files to the correct tables in Snowflake
- Check the data loaded by running count queries

**Permission errors:**
- Make sure your Snowflake user has ACCOUNTADMIN role
- Check that you can create databases in Snowflake manually

### Getting Additional Help:

1. **Check the logs:** Look at `logs/dbt.log` for detailed error messages
2. **Read the full documentation:** Check `README.md` for technical details
3. **Search online:** Most dbt errors have solutions on Stack Overflow
4. **Ask for help:** Create an issue in the project repository

---

## 📞 Support Contacts

- **Technical Issues:** Check the GitHub repository issues
- **Snowflake Problems:** Snowflake support documentation
- **General Questions:** dbt Community Slack

**Remember:** You've built a professional-grade data platform! Take some time to explore and experiment with your new analytics capabilities.

---

*Happy Data Engineering! 🎯*
