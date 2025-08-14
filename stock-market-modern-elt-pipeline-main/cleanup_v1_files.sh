#!/bin/bash
# Bash script to clean up v1 files and replace them with v2 versions
# This script will:
# 1. Backup original files
# 2. Replace them with v2 versions
# 3. Provide guidance for next steps

set -e  # Exit on any error

echo "🧹 Cleaning up v1 files and promoting v2 to main versions..."

# Create backup directory
BACKUP_DIR="backup_v1_files"
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "✅ Created backup directory: $BACKUP_DIR"
fi

# Backup original files
echo "📦 Backing up original files..."
cp "dags/stock_market_dag.py" "$BACKUP_DIR/stock_market_dag.py.backup"
cp "dataproc_jobs/transform_stock_data_pipeline.py" "$BACKUP_DIR/transform_stock_data_pipeline.py.backup"

# Replace original files with v2 versions
echo "🔄 Replacing files with v2 versions..."

# Replace DAG file
mv "dags/stock_market_dag_v2.py" "dags/stock_market_dag.py"
echo "✅ Replaced DAG: stock_market_dag.py"

# Replace Dataproc job file  
mv "dataproc_jobs/transform_stock_data_v2.py" "dataproc_jobs/transform_stock_data_pipeline.py"
echo "✅ Replaced Dataproc job: transform_stock_data_pipeline.py"

echo "🎉 Cleanup completed successfully!"
echo "📋 Summary:"
echo "  - Original files backed up to: $BACKUP_DIR/"
echo "  - DAG updated to modern version"
echo "  - Dataproc job updated to modern version"
echo "  - All references now point to the refactored code"

echo ""
echo "⚠️  Next steps:"
echo "  1. Update Terraform references if needed"
echo "  2. Test the pipeline to ensure everything works"
echo "  3. Delete backup files when confident (optional)"

# Make script executable
chmod +x "$0"
