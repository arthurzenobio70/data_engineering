# 📊 Data Lineage Setup Guide

This guide shows you how to set up and view beautiful data lineage visualizations for your Finance Data Platform.

---

## 🎯 What is Data Lineage?

Data lineage shows you:
- **Where your data comes from** (sources)
- **How it flows through transformations** (models)
- **Which columns depend on which** (column-level lineage)
- **What tests validate your data** (test coverage)

## 🚀 Quick Setup (2 minutes)

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
python setup_profiles.py
```

Follow the prompts to enter your Snowflake credentials.

### Option 2: Manual Setup

1. **Copy the template:**
   ```bash
   cp profiles_template.yml ~/.dbt/profiles.yml
   ```

2. **Edit with your credentials:**
   ```bash
   # Windows
   notepad %USERPROFILE%\.dbt\profiles.yml
   
   # Mac/Linux  
   nano ~/.dbt/profiles.yml
   ```

3. **Replace these values:**
   - `YOUR_ACCOUNT.snowflakecomputing.com` → Your Snowflake account
   - `YOUR_USERNAME` → Your Snowflake username
   - `YOUR_PASSWORD` → Your Snowflake password

## 📈 View Data Lineage

### Step 1: Generate Documentation

```bash
# Build your models first
dbt run

# Generate documentation with lineage
dbt docs generate
```

### Step 2: Start Documentation Server

```bash
# Start the docs server
dbt docs serve

# Or specify a port
dbt docs serve --port 8080
```

### Step 3: Open in Browser

Open your browser to: **http://localhost:8080**

## 🔍 Exploring the Lineage

### Model Lineage View

1. **Click on any model** in the docs
2. **Click the "Lineage" tab**
3. **See the visual graph** showing:
   - 📊 Source tables (green)
   - 🔄 Staging models (blue)
   - 🏗️ Intermediate models (orange)
   - 📈 Mart models (purple)

### Column Lineage View

1. **Click on a model**
2. **Click the "Columns" tab**
3. **Click on any column name**
4. **See which source columns** feed into it

### Graph Navigation

- **Zoom:** Mouse wheel or +/- buttons
- **Pan:** Click and drag
- **Focus:** Double-click on a model
- **Expand:** Use the +/- buttons on nodes

## 🎨 Lineage Features Enabled

### 1. Model Dependencies
```
sources → staging → intermediate → marts
```

### 2. Column-Level Tracking
See exactly which source columns create each final column.

### 3. Test Coverage
Visual indicators showing which models have tests.

### 4. Performance Monitoring
Query tags help track model performance in Snowflake.

### 5. Interactive Exploration
- Click any node to see details
- Follow the data flow visually
- Understand impact analysis

## 🔧 Advanced Configuration

### Custom Query Tags

The profiles.yml includes smart query tagging:

```yaml
query_tag: "dbt-{{ invocation_id }}-{{ model.unique_id }}"
```

This enables:
- **Performance tracking** in Snowflake
- **Cost attribution** by model
- **Debugging** specific runs

### Multi-Environment Lineage

The setup includes profiles for:
- **dev** - Development work
- **staging** - Testing environment  
- **prod** - Production deployment

Switch between them:
```bash
# Use staging environment
dbt run --target staging

# Use production environment  
dbt run --target prod
```

## 📊 Lineage Views Available

### 1. **Project Overview**
- Shows all models and their relationships
- Color-coded by layer (staging/marts/etc.)

### 2. **Model Detail View**
- Upstream and downstream dependencies
- Column mappings
- Documentation and tests

### 3. **Source Analysis**
- Which models use each source
- Data freshness indicators
- Test results

### 4. **Performance View**
- Model run times
- Resource usage
- Optimization opportunities

## 🎯 Using Lineage for Analysis

### Impact Analysis
**Question:** "If I change this source table, what breaks?"

**Answer:** 
1. Find the source in lineage
2. Follow downstream dependencies
3. See all affected models

### Root Cause Analysis
**Question:** "Why is this data wrong?"

**Answer:**
1. Start at the problem model
2. Trace back through lineage
3. Find the source of the issue

### Performance Optimization
**Question:** "Which models are expensive?"

**Answer:**
1. Check query tags in Snowflake
2. Use lineage to find alternatives
3. Optimize critical paths

## 🔍 Troubleshooting Lineage

### Common Issues

**Lineage not showing?**
- Run `dbt docs generate` after model changes
- Refresh your browser
- Check that models compiled successfully

**Missing column lineage?**
- Ensure you're using dbt 1.6+
- Use explicit column references in SQL
- Avoid `SELECT *` where possible

**Performance issues?**
- Reduce threads in profiles.yml
- Use smaller warehouse for docs generation
- Generate docs on subset: `dbt docs generate --select tag:core`

### Debug Commands

```bash
# Test connection
dbt debug

# Compile models (check for errors)
dbt compile

# Generate docs for specific models
dbt docs generate --select staging

# Serve docs on different port
dbt docs serve --port 8081
```

## 🚀 Next Steps

1. **Explore Your Lineage**: Click through all your models
2. **Add Descriptions**: Document your models and columns
3. **Monitor Performance**: Use query tags in Snowflake
4. **Share with Team**: Send the docs URL to stakeholders
5. **Keep Updated**: Re-generate docs after changes

## 📞 Getting Help

**Lineage not working?**
- Check `logs/dbt.log` for errors
- Verify profiles.yml configuration
- Test connection with `dbt debug`

**Want more advanced features?**
- Consider dbt Cloud for hosted docs
- Use dbt packages for enhanced lineage
- Integrate with data catalogs

---

**🎉 Enjoy exploring your data lineage!**

Your Finance Data Platform now has enterprise-grade lineage visualization that helps you understand, debug, and optimize your data transformations.
