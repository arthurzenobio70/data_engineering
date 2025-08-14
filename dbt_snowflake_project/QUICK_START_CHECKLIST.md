# ✅ Quick Start Checklist - Finance Data Platform

Print this page and check off each step as you complete it!

---

## 📋 Before You Start

- [ ] Python 3.8+ installed
- [ ] Git installed  
- [ ] Snowflake account created
- [ ] Text editor available (VS Code/Notepad++)
- [ ] Have your Snowflake account URL, username, and password ready

---

## 🔧 Part 1: Setup (15 min)

- [ ] Open command prompt/terminal
- [ ] Navigate to project folder: `cd dbt_snowflake_project`
- [ ] Create virtual environment: `python -m venv dbt-env`
- [ ] Activate environment: `dbt-env\Scripts\activate` (Windows) or `source dbt-env/bin/activate` (Mac/Linux)
- [ ] Install packages: `pip install -r requirements-core.txt`
- [ ] Install dbt packages: `dbt deps`
- [ ] Verify installation: `dbt --version` (should show version numbers)

---

## 🔗 Part 2: Connect to Snowflake (10 min)

- [ ] Create config folder: `mkdir ~/.dbt` (Mac/Linux) or `mkdir %USERPROFILE%\.dbt` (Windows)
- [ ] Create profiles.yml file
- [ ] Add your Snowflake credentials to profiles.yml
- [ ] Test connection: `dbt debug` (should show "Connection test: [OK connection ok]")

---

## 🏗️ Part 3: Infrastructure (15 min)

- [ ] Go to terraform folder: `cd terraform`
- [ ] Copy settings file: `cp terraform.tfvars.example terraform.tfvars`
- [ ] Edit terraform.tfvars with your Snowflake details
- [ ] Initialize terraform: `terraform init`
- [ ] Plan infrastructure: `terraform plan -var-file="terraform.tfvars"`
- [ ] Apply infrastructure: `terraform apply -var-file="terraform.tfvars"` (type 'yes')
- [ ] Wait for completion (should see "Apply complete!")

---

## 📊 Part 4: Load Data (10 min)

- [ ] Log into Snowflake web interface
- [ ] Navigate to Data → Databases → FINANCE_DB_DEV → RAW
- [ ] Upload customers.csv to customers table
- [ ] Upload orders.csv to orders table  
- [ ] Upload order_items.csv to order_items table
- [ ] Upload products.csv to products table
- [ ] Verify data loaded (run COUNT queries)

---

## 🚀 Part 5: Run Pipeline (5 min)

- [ ] Go back to main folder: `cd ..`
- [ ] Build models: `dbt run` (should complete successfully)
- [ ] Run tests: `dbt test` (should pass all tests)
- [ ] Generate docs: `dbt docs generate`

---

## 📈 Part 6: View Results (5 min)

- [ ] Start dashboard: `streamlit run monitoring/data_quality_dashboard.py`
- [ ] Open browser to: `http://localhost:8501`
- [ ] Start docs server: `dbt docs serve --port 8002` (in new terminal)
- [ ] Open browser to: `http://localhost:8002`
- [ ] Explore new tables in Snowflake

---

## ✅ Success Checklist

Your platform is working if you can see:

- [ ] Dashboard shows data quality metrics at `localhost:8501`
- [ ] Documentation shows model lineage at `localhost:8002`
- [ ] Snowflake contains these new schemas: STAGING, MARTS
- [ ] All dbt tests are passing
- [ ] No error messages in the command line

---

## 🎯 Quick Commands Reference

**Daily usage:**
```bash
# Activate environment
dbt-env\Scripts\activate

# Update data
dbt run
dbt test

# View dashboards
streamlit run monitoring/data_quality_dashboard.py
```

**If something breaks:**
```bash
# Check connection
dbt debug

# View detailed logs
cat logs/dbt.log

# Reset everything
dbt clean
dbt deps
dbt run
```

---

## 📞 Emergency Contacts

- **Can't connect to Snowflake?** Check account URL format and credentials
- **Terraform errors?** Verify you have ACCOUNTADMIN role in Snowflake  
- **dbt errors?** Check `logs/dbt.log` for detailed error messages
- **No data showing?** Verify CSV files uploaded correctly to Snowflake tables

---

**🎉 Total Time: ~60 minutes**

**💡 Tip:** Keep this checklist handy for future setups or when helping others!
